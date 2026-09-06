#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож словаря статусов машинных отчётов.

Опечатка в машинном статусе может быть принята потребителем как новый статус
или тихо потерять смысл ``not-evaluated``. Этот сторож проверяет только
верхнеуровневое поле статуса у перечисленных отчётов. Отсутствие такого поля
не считается покрытием; научный вердикт и содержимое отчёта не оцениваются.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "status_domain_guard.json"
TARGETS = (
    "arb_interval_guard.json",
    "artifact_path_guard.json",
    "artifact_uniqueness_guard.json",
    "bblm_elements.json",
    "bblm_height.json",
    "bblm_protocol.json",
    "chi2_dof_guard.json",
    "chi2_dof_rederivation.json",
    "chi2_dof_semantics_guard.json",
    "external_target_guard.json",
    "external_uncertainty_type_guard.json",
    "independence_assumption_guard.json",
    "journal_signature_guard.json",
    "journal_signature_scope_guard.json",
    "json_duplicate_key_guard.json",
    "json_numeric_type_guard.json",
    "meff_common_guard.json",
    "numeric_domain_guard.json",
    "unit_consistency_guard.json",
    "zeta_passport_provenance_guard.json",
    "zeta_recipe_ambiguity_guard.json",
)
ALLOWED = frozenset({
    "verified-in-scope",
    "not-evaluated",
    "unsupported",
    "platform-unverified",
})
STATUS_KEYS = ("статус", "status_class", "status")


def inspect(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "путь": str(path),
        "прочитано": False,
        "статус": "not-evaluated",
    }
    if not path.is_file():
        record["причина"] = "файл отчёта отсутствует"
        return record
    record["прочитано"] = True
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        record["статус"] = "unsupported"
        record["причина"] = "JSON не прошёл разбор: " + str(exc)
        return record
    if not isinstance(value, dict):
        record["статус"] = "unsupported"
        record["причина"] = "верхний уровень отчёта не является объектом"
        return record
    present = [key for key in STATUS_KEYS if key in value]
    if not present:
        record["причина"] = "верхнеуровневое поле статуса отсутствует"
        return record
    if len(present) > 1:
        record["статус"] = "unsupported"
        record["поля"] = present
        record["причина"] = "верхний уровень содержит несколько полей статуса"
        return record
    key = present[0]
    status = value[key]
    record["поле"] = key
    record["значение"] = status
    if not isinstance(status, str) or status not in ALLOWED:
        record["статус"] = "unsupported"
        record["причина"] = "статус отсутствует в разрешённом словаре"
        return record
    record["статус"] = status
    record["причина"] = "статус входит в разрешённый словарь"
    return record


def scan(root: Path = ROOT) -> dict[str, Any]:
    reports = [inspect(root / name) for name in TARGETS]
    counts: dict[str, int] = {}
    for report in reports:
        status = report["статус"]
        counts[status] = counts.get(status, 0) + 1
    issues = [report for report in reports if report["статус"] == "unsupported"]
    result_status = "unsupported" if issues else (
        "not-evaluated" if counts.get("not-evaluated", 0) else "verified-in-scope"
    )
    return {
        "статус": result_status,
        "проверка": "словарь верхнеуровневых статусов машинных отчётов",
        "разрешённые_статусы": sorted(ALLOWED),
        "сводка": counts,
        "отчёты": reports,
        "ограничение": "проверка словаря статусов не является научным подтверждением zeta/GUE",
    }


def _selftest() -> int:
    import tempfile

    failures = 0

    def check(label: str, condition: bool) -> None:
        nonlocal failures
        print("  %s %s" % ("ок " if condition else "ПРОВАЛ ", label))
        if not condition:
            failures += 1

    with tempfile.TemporaryDirectory(prefix="goldsieve-status-domain-") as td:
        root = Path(td)
        good = root / "good.json"
        good.write_text('{"статус": "not-evaluated"}', encoding="utf-8")
        check("разрешённый статус принимается",
              inspect(good)["статус"] == "not-evaluated")

        typo = root / "typo.json"
        typo.write_text('{"статус": "not_evaluated"}', encoding="utf-8")
        check("опечатка статуса отвергается",
              inspect(typo)["статус"] == "unsupported")

        absent = root / "absent.json"
        absent.write_text('{"причина": "нет данных"}', encoding="utf-8")
        check("отсутствующий статус не становится покрытием",
              inspect(absent)["статус"] == "not-evaluated")

        non_string = root / "non-string.json"
        non_string.write_text('{"статус": 0}', encoding="utf-8")
        check("нестроковый статус отвергается",
              inspect(non_string)["статус"] == "unsupported")

    print("самопроверка словаря статусов: пройдено %d, провалено %d"
          % (4 - failures, failures))
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv not in ([], ["--scan"]):
        print("использование: status_domain_guard.py [--selftest|--scan]")
        return 2
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож словаря статусов: %s; файлов %d; сводка %s"
          % (report["статус"], len(report["отчёты"]),
             json.dumps(report["сводка"], ensure_ascii=False, sort_keys=True)))
    return 0 if report["статус"] != "unsupported" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
