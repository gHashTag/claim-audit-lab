#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож конечности чисел в машинных отчётах.

Стандартный json.loads принимает NaN и Infinity, хотя это не числа JSON.
Если такой токен попадёт в машинную суть или паспорт, последующее сравнение
может получить ложное «совпало». Сторож проверяет только целостность
предъявленных JSON-артефактов; он не делает научного вывода о zeta или GUE.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "numeric_domain_guard.json"
TARGETS = (
    "bblm_protocol.json",
    "bblm_elements.json",
    "chi2_dof_semantics_guard.json",
    "external_target_guard.json",
    "independence_assumption_guard.json",
    "meff_common_guard.json",
    "unit_consistency_guard.json",
    "zeta_passport_provenance_guard.json",
    "zeta_recipe_ambiguity_guard.json",
)


def _reject_constant(value: str) -> None:
    raise ValueError("недопустимое нечисловое значение JSON: " + value)


def _walk_nonfinite(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, float) and not math.isfinite(value):
        found.append(path)
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(_walk_nonfinite(child, path + "." + str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_nonfinite(child, "%s[%d]" % (path, index)))
    return found


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
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        record["статус"] = "unsupported"
        record["причина"] = "JSON не прошёл строгий разбор: " + str(exc)
        return record
    nonfinite = _walk_nonfinite(value)
    if nonfinite:
        record["статус"] = "unsupported"
        record["причина"] = "обнаружены нечисловые значения"
        record["пути_нечисловых"] = nonfinite
        return record
    record["статус"] = "verified-in-scope"
    record["причина"] = "все числовые значения конечны; научный вердикт не оценивается"
    return record


def scan(root: Path = ROOT) -> dict[str, Any]:
    reports = [inspect(root / name) for name in TARGETS]
    counts: dict[str, int] = {}
    for report in reports:
        status = report["статус"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "статус": (
            "verified-in-scope"
            if counts.get("unsupported", 0) == 0
            and counts.get("not-evaluated", 0) == 0
            else "not-evaluated"
        ),
        "проверка": "конечность чисел в машинных JSON-отчётах",
        "сводка": counts,
        "артефакты": reports,
        "ограничение": "целостность чисел не является научным подтверждением zeta/GUE",
    }


def _selftest() -> int:
    import tempfile

    failures = 0

    def check(label: str, condition: bool) -> None:
        nonlocal failures
        print("  %s %s" % ("ок " if condition else "ПРОВАЛ ", label))
        if not condition:
            failures += 1

    with tempfile.TemporaryDirectory(prefix="goldsieve-numeric-") as td:
        root = Path(td)
        finite = root / "finite.json"
        finite.write_text('{"значение": 1.25, "список": [0, -2]}', encoding="utf-8")
        result = inspect(finite)
        check("конечные числа принимаются",
              result["статус"] == "verified-in-scope")

        nan = root / "nan.json"
        nan.write_text('{"значение": NaN}', encoding="utf-8")
        result = inspect(nan)
        check("NaN отклоняется строгим разбором",
              result["статус"] == "unsupported")

        infinity = root / "infinity.json"
        infinity.write_text('{"значение": Infinity}', encoding="utf-8")
        result = inspect(infinity)
        check("Infinity отклоняется строгим разбором",
              result["статус"] == "unsupported")

        malformed = root / "malformed.json"
        malformed.write_text('{"значение":', encoding="utf-8")
        result = inspect(malformed)
        check("оборванный JSON не становится покрытием",
              result["статус"] == "unsupported")

    print("самопроверка конечности чисел: %d провалов" % failures)
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv not in ([], ["--scan"]):
        print("использование: numeric_domain_guard.py [--selftest|--scan]")
        return 2
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож конечности чисел: %s; файлов %d; сводка %s"
          % (report["статус"], len(report["артефакты"]),
             json.dumps(report["сводка"], ensure_ascii=False, sort_keys=True)))
    return 0 if report["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
