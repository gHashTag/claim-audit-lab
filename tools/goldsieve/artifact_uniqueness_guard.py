#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож неоднозначности списка артефактов запуска.

Повтор одного и того же пути в поле ``artifacts`` не доказывает два
независимых артефакта: потребитель может посчитать запись дважды или не
заметить, что один результат предъявлен вместо двух. Сторож проверяет только
структуру списка и не объявляет содержимое файлов доказанным.

Команды:
    python3 artifact_uniqueness_guard.py
    python3 artifact_uniqueness_guard.py --selftest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LOG = Path("/home/user/workspace/cron_tracking/8dff7aa3/runs.jsonl")
OUT = HERE / "artifact_uniqueness_guard.json"


def _key(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def inspect_record(record: object, line: int) -> dict:
    if not isinstance(record, dict):
        return {
            "строка": line,
            "статус": "unsupported",
            "причина": "запись журнала не является объектом",
        }
    artifacts = record.get("artifacts")
    if artifacts is None:
        return {
            "строка": line,
            "статус": "not-evaluated",
            "причина": "поле artifacts отсутствует",
        }
    if not isinstance(artifacts, list):
        return {
            "строка": line,
            "статус": "unsupported",
            "причина": "поле artifacts не является списком",
        }
    seen = set()
    duplicates = []
    for item in artifacts:
        key = _key(item)
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    if duplicates:
        return {
            "строка": line,
            "статус": "unsupported",
            "причина": "список artifacts содержит повторяющийся элемент",
            "повторы": duplicates,
        }
    if not artifacts:
        return {
            "строка": line,
            "статус": "not-evaluated",
            "причина": "список artifacts пуст",
        }
    return {
        "строка": line,
        "статус": "verified-in-scope",
        "причина": "элементы списка artifacts различаются",
        "количество": len(artifacts),
    }


def scan(path: Path = DEFAULT_LOG) -> dict:
    if not path.exists():
        return {
            "статус": "not-evaluated",
            "журнал": str(path),
            "прочитано": 0,
            "нарушения": [],
            "причина": "журнал запусков отсутствует",
        }
    rows = []
    malformed = 0
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(text)
        except json.JSONDecodeError:
            malformed += 1
            continue
        rows.append(inspect_record(record, number))
    issues = [row for row in rows if row["статус"] == "unsupported"]
    not_evaluated = sum(row["статус"] == "not-evaluated" for row in rows)
    status = (
        "unsupported" if issues
        else ("not-evaluated" if malformed or not_evaluated else "verified-in-scope")
    )
    return {
        "статус": status,
        "журнал": str(path),
        "прочитано": len(rows) + malformed,
        "проверено": sum(row["статус"] == "verified-in-scope" for row in rows),
        "not_evaluated": not_evaluated + malformed,
        "нарушения": issues,
        "некорректных_json": malformed,
    }


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            bad += 1
            print("  ПРОВАЛ  " + name)

    check(
        "различные артефакты проходят",
        inspect_record({"artifacts": ["/tmp/a", "/tmp/b"]}, 1)["статус"]
        == "verified-in-scope",
    )
    repeated = inspect_record({"artifacts": ["/tmp/a", "/tmp/a"]}, 2)
    check(
        "повтор артефакта получает unsupported",
        repeated["статус"] == "unsupported" and repeated["повторы"] == ["/tmp/a"],
    )
    check(
        "пустой список не считается покрытием",
        inspect_record({"artifacts": []}, 3)["статус"] == "not-evaluated",
    )
    check(
        "неверный контейнер не перебирается посимвольно",
        inspect_record({"artifacts": "/tmp/a"}, 4)["статус"] == "unsupported",
    )
    check(
        "отсутствующее поле не считается покрытием",
        inspect_record({}, 5)["статус"] == "not-evaluated",
    )
    print("самопроверка неоднозначности артефактов: пройдено %d, провалено %d" % (good, bad))
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "сторож неоднозначности артефактов: %s; прочитано %d; проверено %d; "
        "not-evaluated %d; нарушений %d"
        % (
            report["статус"],
            report["прочитано"],
            report["проверено"],
            report["not_evaluated"],
            len(report["нарушения"]),
        )
    )
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
