#!/usr/bin/env python3
"""Проверка полноты отчёта межплатформенной матрицы.

Риск: служба CI может завершить общий прогон успешно, одновременно молча
исключив одно из шести сочетаний ОС и CPython. Этот модуль не запускает сеть:
он проверяет сохранённый ответ API GitHub, а самопроверка использует локальные
фикстуры. Поэтому результат не подменяет область гейта корпуса.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "windows-latest / py3.12",
    "windows-latest / py3.13",
    "ubuntu-latest / py3.12",
    "ubuntu-latest / py3.13",
    "macos-latest / py3.12",
    "macos-latest / py3.13",
}
OUT = Path(__file__).with_name("os_matrix_audit.json")


def audit(payload: dict) -> dict:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return {
            "verdict": "FAIL",
            "reason_code": "matrix_payload_invalid",
            "missing": sorted(EXPECTED),
            "unexpected": [],
            "duplicates": [],
            "not_success": [],
        }
    names = [j.get("name") for j in jobs if isinstance(j, dict)]
    expected_jobs = [
        j for j in jobs
        if isinstance(j, dict) and j.get("name") in EXPECTED
    ]
    missing_ids = sorted(
        j.get("name", "<без имени>") for j in expected_jobs
        if not isinstance(j.get("id"), int)
    )
    id_to_names: dict[int, list[str]] = {}
    for job in expected_jobs:
        job_id = job.get("id")
        if isinstance(job_id, int):
            id_to_names.setdefault(job_id, []).append(job.get("name", "<без имени>"))
    duplicate_ids = sorted(
        job_id for job_id, id_names in id_to_names.items()
        if len(id_names) > 1
    )
    missing = sorted(EXPECTED - set(names))
    unexpected = sorted(set(names) - EXPECTED)
    duplicates = sorted({n for n in names if names.count(n) > 1 and n in EXPECTED})
    not_success = sorted(
        j.get("name", "<без имени>")
        for j in jobs
        if isinstance(j, dict)
        and j.get("name") in EXPECTED
        and (j.get("status") != "completed" or j.get("conclusion") != "success")
    )
    ok = not (
        missing or unexpected or duplicates or not_success
        or missing_ids or duplicate_ids
    ) and set(names) == EXPECTED
    return {
        "verdict": "PASS" if ok else "FAIL",
        "reason_code": "matrix_complete_success" if ok else "matrix_incomplete_or_failed",
        "expected_count": len(EXPECTED),
        "observed_count": len(jobs),
        "expected": sorted(EXPECTED),
        "observed": sorted(names),
        "missing": missing,
        "unexpected": unexpected,
        "duplicates": duplicates,
        "missing_ids": missing_ids,
        "duplicate_ids": duplicate_ids,
        "not_success": not_success,
    }


def check(rows: list[dict], name: str, passed: bool, detail: str) -> None:
    rows.append({"name": name, "passed": bool(passed), "detail": detail})
    print("  %s %s" % ("ок  " if passed else "ПРОВАЛ  ", name))


def fixture(names: list[str] | None = None, bad: str | None = None) -> dict:
    names = EXPECTED if names is None else names
    jobs = [
        {"id": i + 1, "name": n, "status": "completed",
         "conclusion": "success"}
        for i, n in enumerate(sorted(names))
    ]
    if bad is not None:
        for job in jobs:
            if job["name"] == bad:
                job["status"] = "in_progress"
                job["conclusion"] = None
    return {"jobs": jobs}


def selftest() -> int:
    rows: list[dict] = []
    good = audit(fixture())
    check(rows, "полная матрица принимается",
          good["verdict"] == "PASS", "6/6 сочетаний")

    missing_name = "macos-latest / py3.13"
    missing = audit(fixture([n for n in EXPECTED if n != missing_name]))
    check(rows, "мутация удаления задания ловится",
          missing["verdict"] == "FAIL" and missing["missing"] == [missing_name],
          "мутация поймана 1/1")

    bad_name = "windows-latest / py3.12"
    failed = audit(fixture(bad=bad_name))
    check(rows, "мутация незавершённого задания ловится",
          failed["verdict"] == "FAIL" and failed["not_success"] == [bad_name],
          "мутация поймана 1/1")

    duplicate = audit(fixture(list(EXPECTED) + ["ubuntu-latest / py3.12"]))
    check(rows, "мутация дублирования задания ловится",
          duplicate["verdict"] == "FAIL"
          and duplicate["duplicates"] == ["ubuntu-latest / py3.12"],
          "мутация поймана 1/1")

    unexpected = audit(fixture(list(EXPECTED - {"ubuntu-latest / py3.12"})
                              + ["freebsd-latest / py3.13"]))
    check(rows, "мутация неизвестной платформы ловится",
          unexpected["verdict"] == "FAIL"
          and unexpected["unexpected"] == ["freebsd-latest / py3.13"],
          "мутация поймана 1/1")

    duplicate_id_jobs = fixture()
    duplicate_id_jobs["jobs"][1]["id"] = duplicate_id_jobs["jobs"][0]["id"]
    duplicate_id = audit(duplicate_id_jobs)
    check(rows, "мутация повторного идентификатора задания ловится",
          duplicate_id["verdict"] == "FAIL"
          and duplicate_id["duplicate_ids"] == [duplicate_id_jobs["jobs"][0]["id"]],
          "мутация поймана 1/1")

    malformed = audit({})
    check(rows, "повреждённый ответ API не принимается",
          malformed["verdict"] == "FAIL"
          and malformed["reason_code"] == "matrix_payload_invalid",
          "нет поля jobs")

    drifted_name = fixture()
    drifted_name["jobs"][0]["name"] = drifted_name["jobs"][0]["name"] + " "
    drift = audit(drifted_name)
    check(rows, "мутация пробельного дрейфа имени задания ловится",
          drift["verdict"] == "FAIL"
          and len(drift["missing"]) == 1
          and len(drift["unexpected"]) == 1,
          "мутация поймана 1/1")

    passed = sum(r["passed"] for r in rows)
    result = {
        "title": "Проверка полноты межплатформенной матрицы",
        "verdict": "PASS" if passed == len(rows) else "FAIL",
        "checks": rows,
        "expected_matrix": sorted(EXPECTED),
        "mutation_target": (
            "удаление, незавершённость, дублирование, подмена задания "
            "повторный идентификатор задания или пробельный дрейф имени"
        ),
        "sensitivity": "6/6 мутаций пойманы; положительный контроль 1/1",
        "status_class": "verified-in-scope",
    }
    print("самопроверка полноты матрицы: пройдено %d, провалено %d"
          % (passed, len(rows) - passed))
    return 0 if result["verdict"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--json-out", type=Path, default=OUT)
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.input is None:
        parser.error("нужен --input с ответом API GitHub")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(payload)
    args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print("матрица ОС: %s, заданий %d, пропущено %d, неуспешно %d"
          % (result["verdict"], result.get("observed_count", 0),
             len(result.get("missing", [])), len(result.get("not_success", []))))
    print("JSON: %s" % args.json_out)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
