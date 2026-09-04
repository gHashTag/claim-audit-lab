#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож контракта машинного доклада тика.

Доклад — не доказательство сам по себе: его числовая суть должна быть
предъявлена отдельно, а структура должна оставаться ровно из четырёх
разделов приказа. Этот сторож ловит оборванный доклад, лишний раздел и
неполный JSON ``progress-substance``. Он не восстанавливает значения из
соседних тиков и не оценивает научный результат.

Команды:
    python3 report_contract_guard.py
    python3 report_contract_guard.py --selftest
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path("/home/user/workspace/cron_tracking/8dff7aa3")
OUT = Path(__file__).resolve().parent / "report_contract_guard.json"
FIELDS = ("гейт", "регресс", "ос_матрица", "bblm", "изменённые_файлы")


def _latest_report(root: Path) -> Path:
    reports = sorted(root.glob("tick*-report.md"))
    if not reports:
        raise FileNotFoundError("доклад tickNNN-report.md не предъявлен")
    return reports[-1]


def _substance_for(report: Path, root: Path) -> Path:
    match = re.search(r"tick(\d+)-report\.md$", report.name)
    if not match:
        raise ValueError("имя доклада не содержит номера тика")
    name = f"tick{match.group(1)}-progress-substance.json"
    for candidate in (
        root / name,
        Path("/home/user/workspace/cron_tracking/20fee222") / name,
        Path("/home/user/workspace/goldsieve") / name,
    ):
        if candidate.exists():
            return candidate
    return root / name


def inspect(report: Path, substance: Path) -> dict:
    text = report.read_text(encoding="utf-8")
    headings = re.findall(r"(?m)^##\s+(.+?)\s*$", text)
    numbered = [
        heading for heading in headings
        if re.match(r"^\([1-4]\)\s+", heading)
    ]
    required = [
        "(1) что исправлено в инструменте",
        "(2) что установлено о zeta/GUE",
        "(3) что осталось недоказанным",
        "(4) какие артефакты и тесты это подтверждают",
    ]
    section_ok = headings == required and numbered == required
    distinction_ok = "чем этот тик отличается от предыдущего" in text
    payload = json.loads(substance.read_text(encoding="utf-8"))
    fields_ok = set(payload) == set(FIELDS) and all(
        isinstance(payload[field], list) and payload[field]
        for field in FIELDS
    )
    files_ok = (
        fields_ok
        and isinstance(payload["изменённые_файлы"], list)
        and all(isinstance(item, str) and item for item
                in payload["изменённые_файлы"])
    )
    status = (
        "verified-in-scope"
        if section_ok and distinction_ok and fields_ok and files_ok
        else "not-evaluated"
    )
    reasons = []
    if not section_ok:
        reasons.append("структура доклада не совпадает с четырьмя обязательными разделами")
    if not distinction_ok:
        reasons.append("нет строки отличия текущего тика от предыдущего")
    if not fields_ok:
        reasons.append("progress-substance не содержит ровно пять машинных полей")
    if not files_ok:
        reasons.append("изменённые_файлы не предъявлены непустым списком")
    return {
        "статус": status,
        "доклад": str(report),
        "суть": str(substance),
        "разделы": headings,
        "структура_проверена": section_ok,
        "отличие_проверено": distinction_ok,
        "поля_сути_проверены": fields_ok,
        "изменённые_файлы_проверены": files_ok,
        "причина": "; ".join(reasons) if reasons else "контракт доклада предъявлен полностью",
        "ограничение": "контракт формы не подтверждает научную истинность утверждений",
    }


def scan(root: Path = ROOT) -> dict:
    report = _latest_report(root)
    return inspect(report, _substance_for(report, root))


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

    valid_report = """# Доклад
## (1) что исправлено в инструменте
чем этот тик отличается от предыдущего: новый контракт.
## (2) что установлено о zeta/GUE
Нового научного вердикта нет.
## (3) что осталось недоказанным
Долги перечислены.
## (4) какие артефакты и тесты это подтверждают
Тесты предъявлены.
"""
    valid_substance = {
        "гейт": [1, 0, 0],
        "регресс": [0, 1, 0],
        "ос_матрица": [6, 6],
        "bblm": [4, True],
        "изменённые_файлы": ["guard.py"],
    }
    with tempfile.TemporaryDirectory(prefix="report-contract-") as tmp:
        root = Path(tmp)
        report = root / "tick1-report.md"
        substance = root / "tick1-progress-substance.json"
        report.write_text(valid_report, encoding="utf-8")
        substance.write_text(
            json.dumps(valid_substance, ensure_ascii=False), encoding="utf-8"
        )
        result = inspect(report, substance)
        check("полный доклад получает verified-in-scope",
              result["статус"] == "verified-in-scope")

        malformed = root / "malformed.md"
        malformed.write_text(valid_report.replace(
            "## (4) какие артефакты и тесты это подтверждают",
            "## (5) лишний раздел"
        ), encoding="utf-8")
        result = inspect(malformed, substance)
        check("лишний раздел не считается покрытием",
              result["статус"] == "not-evaluated"
              and not result["структура_проверена"])

        incomplete = root / "incomplete.json"
        incomplete.write_text(json.dumps({"гейт": [1, 0, 0]}),
                              encoding="utf-8")
        result = inspect(report, incomplete)
        check("неполная машинная суть не считается покрытием",
              result["статус"] == "not-evaluated"
              and not result["поля_сути_проверены"])

    print("самопроверка контракта доклада: %d пройдено, %d провалено" % (good, bad))
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv not in ([], ["--scan"]):
        print("использование: --selftest или --scan")
        return 2
    try:
        result = scan()
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("сторож контракта доклада: not-evaluated; %s" % exc)
        return 1
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож контракта доклада: %s" % result["статус"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
