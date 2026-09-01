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
from urllib.parse import urlparse


EXPECTED = {
    "windows-latest / py3.12",
    "windows-latest / py3.13",
    "ubuntu-latest / py3.12",
    "ubuntu-latest / py3.13",
    "macos-latest / py3.12",
    "macos-latest / py3.13",
}
PROVENANCE_FIELDS = (
    "expected_run_id",
    "expected_branch",
    "expected_head_sha",
    "expected_run_url",
    "expected_workflow",
    "expected_workflow_path",
    "expected_run_attempt",
    "expected_run_status",
    "expected_run_conclusion",
)
OUT = Path(__file__).with_name("os_matrix_audit.json")


def _valid_job_id(value: object) -> bool:
    """GitHub job id must be a positive integer, not JSON boolean."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _url_run_id(value: object) -> int | None:
    """Извлекает id запуска из API- или HTML-URL GitHub."""
    if not isinstance(value, str):
        return None
    path = urlparse(value).path.rstrip("/")
    marker = "/actions/runs/"
    if marker not in path:
        return None
    suffix = path.rsplit(marker, 1)[1]
    return int(suffix) if suffix.isdigit() else None


def audit(
    payload: dict,
    expected_run_id: int | None = None,
    expected_branch: str | None = None,
    expected_head_sha: str | None = None,
    expected_run_url: str | None = None,
    expected_workflow: str | None = None,
    expected_workflow_path: str | None = None,
    expected_run_attempt: int | None = None,
    expected_run_status: str | None = None,
    expected_run_conclusion: str | None = None,
) -> dict:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return {
            "verdict": "FAIL",
            "reason_code": "matrix_payload_invalid",
            "missing": sorted(EXPECTED),
            "unexpected": [],
            "duplicates": [],
            "not_success": [],
            "run_id_mismatch": [],
            "run_metadata_mismatch": [],
            "provenance_mismatch": [],
            "run_url_mismatch": [],
            "run_attempt_mismatch": [],
            "run_execution_mismatch": [],
            "malformed_jobs": [],
            "total_count_mismatch": [],
            "provenance_expectations_missing": [],
        }
    # Без полного набора ожиданий ответ API нельзя считать проверенным:
    # вызывающая сторона могла передать живой снимок, не связанный с нужной
    # веткой, SHA, workflow или попыткой запуска. Раньше такой вызов молча
    # принимался как PASS и оставлял происхождение на совести вызывающего
    # кода. Теперь структурная полнота и происхождение — единый контракт.
    expected_values = {
        "expected_run_id": expected_run_id,
        "expected_branch": expected_branch,
        "expected_head_sha": expected_head_sha,
        "expected_run_url": expected_run_url,
        "expected_workflow": expected_workflow,
        "expected_workflow_path": expected_workflow_path,
        "expected_run_attempt": expected_run_attempt,
        "expected_run_status": expected_run_status,
        "expected_run_conclusion": expected_run_conclusion,
    }
    missing_expectations = [
        key for key in PROVENANCE_FIELDS if expected_values[key] is None
    ]
    if missing_expectations:
        return {
            "verdict": "FAIL",
            "reason_code": "provenance_expectations_required",
            "expected_count": len(EXPECTED),
            "observed_count": len(jobs),
            "expected": sorted(EXPECTED),
            "observed": sorted(
                j.get("name") for j in jobs if isinstance(j, dict)
            ),
            "provenance_expectations_missing": missing_expectations,
            "missing": [],
            "unexpected": [],
            "duplicates": [],
            "missing_ids": [],
            "duplicate_ids": [],
            "not_success": [],
            "run_id_mismatch": [],
            "run_metadata_mismatch": [],
            "provenance_mismatch": [],
            "run_path_mismatch": [],
            "run_url_mismatch": [],
            "run_attempt_mismatch": [],
            "run_execution_mismatch": [],
            "malformed_jobs": [],
            "total_count_mismatch": [],
        }
    total_count_mismatch = []
    if "total_count" in payload:
        total_count = payload.get("total_count")
        if (
            not isinstance(total_count, int)
            or isinstance(total_count, bool)
            or total_count != len(jobs)
        ):
            total_count_mismatch = [total_count]
    malformed_jobs = sorted(
        index for index, job in enumerate(jobs) if not isinstance(job, dict)
    )
    names = [j.get("name") for j in jobs if isinstance(j, dict)]
    expected_jobs = [
        j for j in jobs
        if isinstance(j, dict) and j.get("name") in EXPECTED
    ]
    missing_ids = sorted(
        j.get("name", "<без имени>") for j in expected_jobs
        if not _valid_job_id(j.get("id"))
    )
    id_to_names: dict[int, list[str]] = {}
    for job in expected_jobs:
        job_id = job.get("id")
        if _valid_job_id(job_id):
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
    run_id_mismatch = []
    if expected_run_id is not None:
        run_id_mismatch = sorted(
            j.get("name", "<без имени>")
            for j in jobs
            if isinstance(j, dict) and j.get("run_id") != expected_run_id
        )
    # Связь job с запуском недостаточна: повреждённая или ошибочно
    # объединённая запись может сохранить правильные run_id у всех заданий,
    # но подменить сам объект запуска. Проверяем его числовой id отдельно.
    run_metadata_mismatch = []
    run_meta = payload.get("run")
    if expected_run_id is not None:
        if not isinstance(run_meta, dict) or run_meta.get("id") != expected_run_id:
            run_metadata_mismatch = ["id"]
    provenance_mismatch = []
    run_path_mismatch = []
    run_url_mismatch = []
    run_attempt_mismatch = []
    if expected_workflow_path is not None:
        run_meta = payload.get("run")
        actual_path = run_meta.get("path") if isinstance(run_meta, dict) else None
        if actual_path != expected_workflow_path:
            run_path_mismatch = [str(actual_path)]
    if expected_run_attempt is not None:
        run_attempt_mismatch = sorted(
            j.get("name", "<без имени>")
            for j in jobs
            if isinstance(j, dict)
            and j.get("run_attempt") != expected_run_attempt
        )
    run_execution_mismatch = []
    if expected_run_status is not None or expected_run_conclusion is not None:
        if not isinstance(run_meta, dict):
            run_execution_mismatch = ["run"]
        else:
            if (expected_run_status is not None
                    and run_meta.get("status") != expected_run_status):
                run_execution_mismatch.append("status")
            if (expected_run_conclusion is not None
                    and run_meta.get("conclusion") != expected_run_conclusion):
                run_execution_mismatch.append("conclusion")
    # Jobs API exposes ``run_url`` as the canonical API URL, while a human
    # usually supplies the HTML URL copied from the run page.  Treating the
    # latter as a job URL produced a false FAIL for a valid six-job response.
    # Accept either URL only when it is present on the run object, and always
    # require every job's run_url to equal the run object's canonical API URL.
    if expected_run_url is not None:
        if isinstance(run_meta, dict) and (
            run_meta.get("url") is not None or run_meta.get("html_url") is not None
        ):
            accepted_urls = {
                value for value in (run_meta.get("url"), run_meta.get("html_url"))
                if isinstance(value, str)
            }
            if expected_run_url not in accepted_urls:
                run_url_mismatch.append("run")
            canonical_url = run_meta.get("url")
            if not isinstance(canonical_url, str):
                run_url_mismatch.append("run.url")
            else:
                if _url_run_id(canonical_url) != expected_run_id:
                    run_url_mismatch.append("run.url_run_id")
                run_url_mismatch.extend(
                    j.get("name", "<без имени>")
                    for j in jobs
                    if isinstance(j, dict) and j.get("run_url") != canonical_url
                )
        else:
            # Keep the small, metadata-free unit fixtures strict: in that
            # shape expected_run_url is also the only available URL.
            run_url_mismatch.extend(
                j.get("name", "<без имени>")
                for j in jobs
                if isinstance(j, dict) and j.get("run_url") != expected_run_url
            )
    if any(value is not None for value in (
        expected_branch, expected_head_sha, expected_workflow
    )):
        for job in jobs:
            if not isinstance(job, dict):
                continue
            mismatch = (
                (expected_branch is not None
                 and job.get("head_branch") != expected_branch)
                or (expected_head_sha is not None
                    and job.get("head_sha") != expected_head_sha)
                or (expected_workflow is not None
                    and job.get("workflow_name") != expected_workflow)
            )
            if mismatch:
                provenance_mismatch.append(job.get("name", "<без имени>"))
        provenance_mismatch.sort()
    ok = not (
        missing or unexpected or duplicates or not_success
        or missing_ids or duplicate_ids or run_id_mismatch
        or run_metadata_mismatch
        or provenance_mismatch or run_path_mismatch or run_url_mismatch
        or malformed_jobs
        or run_attempt_mismatch or run_execution_mismatch or total_count_mismatch
    ) and set(names) == EXPECTED
    return {
        "verdict": "PASS" if ok else "FAIL",
        "reason_code": "matrix_complete_success" if ok else "matrix_incomplete_or_failed",
        "expected_count": len(EXPECTED),
        "observed_count": len(jobs),
        "expected_run_id": expected_run_id,
        "expected_branch": expected_branch,
        "expected_head_sha": expected_head_sha,
        "expected_run_url": expected_run_url,
        "expected_workflow": expected_workflow,
        "expected_workflow_path": expected_workflow_path,
        "expected": sorted(EXPECTED),
        "observed": sorted(names),
        "missing": missing,
        "unexpected": unexpected,
        "duplicates": duplicates,
        "missing_ids": missing_ids,
        "duplicate_ids": duplicate_ids,
        "not_success": not_success,
        "run_id_mismatch": run_id_mismatch,
        "run_metadata_mismatch": run_metadata_mismatch,
        "provenance_mismatch": provenance_mismatch,
        "run_path_mismatch": run_path_mismatch,
        "run_url_mismatch": sorted(set(run_url_mismatch)),
        "run_attempt_mismatch": run_attempt_mismatch,
        "run_execution_mismatch": run_execution_mismatch,
        "malformed_jobs": malformed_jobs,
        "total_count_mismatch": total_count_mismatch,
        "provenance_expectations_missing": [],
    }


def check(rows: list[dict], name: str, passed: bool, detail: str) -> None:
    rows.append({"name": name, "passed": bool(passed), "detail": detail})
    print("  %s %s" % ("ок  " if passed else "ПРОВАЛ  ", name))


def fixture(
    names: list[str] | None = None,
    bad: str | None = None,
    run_id: int = 4242,
    branch: str = "tools/test",
    head_sha: str = "a" * 40,
    run_url: str = "https://github.com/example/repo/actions/runs/4242",
    workflow: str = "cross-platform-selftest.yml",
    workflow_path: str = ".github/workflows/cross-platform-selftest.yml",
    run_attempt: int = 1,
    run_status: str = "completed",
    run_conclusion: str = "success",
) -> dict:
    names = EXPECTED if names is None else names
    jobs = [
        {"id": i + 1, "name": n, "status": "completed",
         "conclusion": "success", "run_id": run_id,
         "head_branch": branch, "head_sha": head_sha,
         "run_url": run_url, "workflow_name": workflow,
         "run_attempt": run_attempt}
        for i, n in enumerate(sorted(names))
    ]
    if bad is not None:
        for job in jobs:
            if job["name"] == bad:
                job["status"] = "in_progress"
                job["conclusion"] = None
    return {"run": {"id": run_id, "path": workflow_path, "status": run_status,
                    "conclusion": run_conclusion}, "jobs": jobs}


_TEST_EXPECTATIONS = {
    "expected_run_id": 4242,
    "expected_branch": "tools/test",
    "expected_head_sha": "a" * 40,
    "expected_run_url": "https://github.com/example/repo/actions/runs/4242",
    "expected_workflow": "cross-platform-selftest.yml",
    "expected_workflow_path": ".github/workflows/cross-platform-selftest.yml",
    "expected_run_attempt": 1,
    "expected_run_status": "completed",
    "expected_run_conclusion": "success",
}


def _test_audit(payload: dict, **overrides) -> dict:
    expectations = dict(_TEST_EXPECTATIONS)
    expectations.update(overrides)
    return audit(payload, **expectations)


def selftest() -> int:
    rows: list[dict] = []
    missing_expectations = audit(fixture())
    check(rows, "вызов без ожиданий происхождения отвергается",
          missing_expectations["verdict"] == "FAIL"
          and missing_expectations["reason_code"]
             == "provenance_expectations_required"
          and set(missing_expectations["provenance_expectations_missing"])
             == set(PROVENANCE_FIELDS),
          "негативная мутация поймана 1/1")

    good = _test_audit(fixture())
    check(rows, "полная матрица принимается",
          good["verdict"] == "PASS", "6/6 сочетаний")

    failed_run = fixture(run_conclusion="failure")
    failed_run_result = _test_audit(failed_run)
    check(rows, "мутация итога общего запуска ловится",
          failed_run_result["verdict"] == "FAIL"
          and failed_run_result["run_execution_mismatch"] == ["conclusion"],
          "мутация поймана 1/1")

    wrong_run = fixture()
    wrong_run["jobs"][0]["run_id"] = 4243
    wrong_run_result = _test_audit(wrong_run)
    check(rows, "мутация связи job с запуском ловится",
          wrong_run_result["verdict"] == "FAIL"
          and wrong_run_result["run_id_mismatch"] == [wrong_run["jobs"][0]["name"]],
          "мутация поймана 1/1")

    wrong_run_metadata = fixture()
    wrong_run_metadata["run"]["id"] = 4243
    wrong_run_metadata_result = _test_audit(wrong_run_metadata)
    check(rows, "мутация идентификатора общего запуска ловится",
          wrong_run_metadata_result["verdict"] == "FAIL"
          and wrong_run_metadata_result["run_metadata_mismatch"] == ["id"],
          "мутация поймана 1/1")

    human_url = fixture()
    human_url["run"]["url"] = "https://api.github.com/repos/example/repo/actions/runs/4242"
    human_url["run"]["html_url"] = "https://github.com/example/repo/actions/runs/4242"
    for job in human_url["jobs"]:
        job["run_url"] = human_url["run"]["url"]
    human_url_result = _test_audit(
        human_url, expected_run_url=human_url["run"]["html_url"]
    )
    check(rows, "человеческий URL запуска принимается как ссылка на тот же объект",
          human_url_result["verdict"] == "PASS",
          "API и HTML URL сведены к одному объекту 1/1")

    wrong_canonical_url = json.loads(json.dumps(human_url))
    wrong_canonical_url["jobs"][0]["run_url"] = wrong_canonical_url["run"]["html_url"]
    wrong_canonical_url_result = _test_audit(
        wrong_canonical_url, expected_run_url=wrong_canonical_url["run"]["html_url"]
    )
    check(rows, "мутация канонического URL задания ловится",
          wrong_canonical_url_result["verdict"] == "FAIL"
          and wrong_canonical_url_result["run_url_mismatch"]
             == [wrong_canonical_url["jobs"][0]["name"]],
          "мутация поймана 1/1")

    wrong_url_run_id = json.loads(json.dumps(human_url))
    wrong_url_run_id["run"]["url"] = (
        "https://api.github.com/repos/example/repo/actions/runs/4243"
    )
    for job in wrong_url_run_id["jobs"]:
        job["run_url"] = wrong_url_run_id["run"]["url"]
    wrong_url_run_id_result = _test_audit(
        wrong_url_run_id, expected_run_url=wrong_url_run_id["run"]["html_url"]
    )
    check(rows, "мутация связи канонического URL с id запуска ловится",
          wrong_url_run_id_result["verdict"] == "FAIL"
          and "run.url_run_id" in wrong_url_run_id_result["run_url_mismatch"],
          "мутация поймана 1/1")

    wrong_provenance = fixture()
    wrong_provenance["jobs"][0]["head_branch"] = "main"
    wrong_provenance_result = _test_audit(wrong_provenance)
    check(rows, "мутация происхождения задания ловится",
          wrong_provenance_result["verdict"] == "FAIL"
          and wrong_provenance_result["provenance_mismatch"]
             == [wrong_provenance["jobs"][0]["name"]],
          "мутация ветки поймана 1/1")

    wrong_workflow_path = fixture()
    wrong_workflow_path["run"]["path"] = ".github/workflows/other.yml"
    wrong_workflow_path_result = _test_audit(wrong_workflow_path)
    check(rows, "мутация пути workflow ловится",
          wrong_workflow_path_result["verdict"] == "FAIL"
          and wrong_workflow_path_result["run_path_mismatch"]
             == [".github/workflows/other.yml"],
          "мутация поймана 1/1")

    wrong_run_attempt = fixture()
    wrong_run_attempt["jobs"][0]["run_attempt"] = 2
    wrong_run_attempt_result = _test_audit(wrong_run_attempt)
    check(rows, "мутация номера попытки запуска ловится",
          wrong_run_attempt_result["verdict"] == "FAIL"
          and wrong_run_attempt_result["run_attempt_mismatch"]
             == [wrong_run_attempt["jobs"][0]["name"]],
          "мутация поймана 1/1")

    missing_name = "macos-latest / py3.13"
    missing = _test_audit(fixture([n for n in EXPECTED if n != missing_name]))
    check(rows, "мутация удаления задания ловится",
          missing["verdict"] == "FAIL" and missing["missing"] == [missing_name],
          "мутация поймана 1/1")

    bad_name = "windows-latest / py3.12"
    failed = _test_audit(fixture(bad=bad_name))
    check(rows, "мутация незавершённого задания ловится",
          failed["verdict"] == "FAIL" and failed["not_success"] == [bad_name],
          "мутация поймана 1/1")

    duplicate = _test_audit(fixture(list(EXPECTED) + ["ubuntu-latest / py3.12"]))
    check(rows, "мутация дублирования задания ловится",
          duplicate["verdict"] == "FAIL"
          and duplicate["duplicates"] == ["ubuntu-latest / py3.12"],
          "мутация поймана 1/1")

    unexpected = _test_audit(fixture(list(EXPECTED - {"ubuntu-latest / py3.12"})
                                     + ["freebsd-latest / py3.13"]))
    check(rows, "мутация неизвестной платформы ловится",
          unexpected["verdict"] == "FAIL"
          and unexpected["unexpected"] == ["freebsd-latest / py3.13"],
          "мутация поймана 1/1")

    duplicate_id_jobs = fixture()
    duplicate_id_jobs["jobs"][1]["id"] = duplicate_id_jobs["jobs"][0]["id"]
    duplicate_id = _test_audit(duplicate_id_jobs)
    check(rows, "мутация повторного идентификатора задания ловится",
          duplicate_id["verdict"] == "FAIL"
          and duplicate_id["duplicate_ids"] == [duplicate_id_jobs["jobs"][0]["id"]],
          "мутация поймана 1/1")

    missing_id_jobs = fixture()
    missing_id_name = missing_id_jobs["jobs"][0]["name"]
    missing_id_jobs["jobs"][0]["id"] = "нечисловой-id"
    missing_id = _test_audit(missing_id_jobs)
    check(rows, "мутация отсутствующего числового идентификатора ловится",
          missing_id["verdict"] == "FAIL"
          and missing_id["missing_ids"] == [missing_id_name],
          "мутация поймана 1/1")

    boolean_id_jobs = fixture()
    boolean_id_name = boolean_id_jobs["jobs"][0]["name"]
    boolean_id_jobs["jobs"][0]["id"] = True
    boolean_id = _test_audit(boolean_id_jobs)
    check(rows, "мутация логического идентификатора ловится",
          boolean_id["verdict"] == "FAIL"
          and boolean_id["missing_ids"] == [boolean_id_name],
          "мутация поймана 1/1")

    malformed = audit({})
    check(rows, "повреждённый ответ API не принимается",
          malformed["verdict"] == "FAIL"
          and malformed["reason_code"] == "matrix_payload_invalid",
          "нет поля jobs")

    malformed_job = fixture()
    malformed_job["jobs"].append("повреждённая строка задания")
    malformed_job_result = _test_audit(malformed_job)
    check(rows, "необъектная строка задания ловится",
          malformed_job_result["verdict"] == "FAIL"
          and malformed_job_result["malformed_jobs"] == [len(EXPECTED)],
          "мутация поймана 1/1")

    drifted_total_count = fixture()
    drifted_total_count["total_count"] = len(EXPECTED) + 1
    total_count_result = _test_audit(drifted_total_count)
    check(rows, "мутация total_count ловится",
          total_count_result["verdict"] == "FAIL"
          and total_count_result["total_count_mismatch"] == [len(EXPECTED) + 1],
          "мутация поймана 1/1")

    drifted_name = fixture()
    drifted_name["jobs"][0]["name"] = drifted_name["jobs"][0]["name"] + " "
    drift = _test_audit(drifted_name)
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
            "удаление, незавершённость, дублирование, подмена задания, "
            "повторный, нечисловой или логический идентификатор задания, пробельный "
            "дрейф имени, total_count либо дрейф ветки, SHA, URL запуска или "
            "канонического URL задания, рабочего процесса, номера попытки запуска "
            "либо идентификатора общего запуска"
        ),
        "sensitivity": (
            f"{len(rows) - 1}/{len(rows) - 1} мутаций пойманы; "
            "положительный контроль 1/1"
        ),
        "status_class": "verified-in-scope",
    }
    print("самопроверка полноты матрицы: пройдено %d, провалено %d"
          % (passed, len(rows) - passed))
    return 0 if result["verdict"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--expected-run-id", type=int,
                        help="ожидаемый числовой идентификатор запуска")
    parser.add_argument("--expected-branch",
                        help="ожидаемая ветка запуска")
    parser.add_argument("--expected-head-sha",
                        help="ожидаемый SHA исходников запуска")
    parser.add_argument("--expected-run-url",
                        help="ожидаемый URL запуска")
    parser.add_argument("--expected-workflow",
                        help="ожидаемое имя рабочего процесса")
    parser.add_argument("--expected-workflow-path",
                        help="ожидаемый путь файла рабочего процесса")
    parser.add_argument("--expected-run-attempt", type=int,
                        help="ожидаемый номер попытки запуска")
    parser.add_argument("--expected-run-status",
                        help="ожидаемый статус общего запуска")
    parser.add_argument("--expected-run-conclusion",
                        help="ожидаемый итог общего запуска")
    parser.add_argument("--json-out", type=Path, default=OUT)
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.input is None:
        parser.error("нужен --input с ответом API GitHub")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = audit(
        payload,
        expected_run_id=args.expected_run_id,
        expected_branch=args.expected_branch,
        expected_head_sha=args.expected_head_sha,
        expected_run_url=args.expected_run_url,
        expected_workflow=args.expected_workflow,
        expected_workflow_path=args.expected_workflow_path,
        expected_run_attempt=args.expected_run_attempt,
        expected_run_status=args.expected_run_status,
        expected_run_conclusion=args.expected_run_conclusion,
    )
    args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    print("матрица ОС: %s, заданий %d, пропущено %d, неуспешно %d"
          % (result["verdict"], result.get("observed_count", 0),
             len(result.get("missing", [])), len(result.get("not_success", []))))
    print("JSON: %s" % args.json_out)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
