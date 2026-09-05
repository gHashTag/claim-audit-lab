#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож типов чисел в машинных JSON-отчётах.

Конечное число, записанное строкой, может пройти арифметический разбор
неодинаково в разных потребителях. Этот сторож проверяет только поля,
объявленные числовыми в машинных отчётах; он не выносит научный вердикт.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "json_numeric_type_guard.json"
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

# Имена полей, которые в этих отчётах являются числами. Не угадываем типы
# произвольных строк: область сторожа задаётся этим явным набором.
NUMERIC_KEYS = frozenset({
    "L", "L_bin", "M", "M_eff", "N_eff_cited", "alpha_best_pure_scale",
    "alpha_gap_in_sigma", "alpha_observed", "alpha_predicted_BBLM",
    "alpha_predicted_on_test", "архивов_с_несколькими_С20",
    "воспроизводящих_вариантов", "вариантов_рецепта", "checked",
    "c_cited_BBLM", "c_fitted_on_train", "degenerate_count",
    "deviation_sigma_cited_c", "deviation_sigma_fitted_c", "gamma_hi",
    "gamma_lo", "кейсов", "missing_count", "n_bins", "n_boot", "n_gaps",
    "open_count", "order_item", "p50", "p90", "p95", "present_count",
    "required_total", "seed", "sigma_alpha_test", "std", "строк",
    "строк_с_аналитическим_выражением", "строк_с_коэффициентом",
    "строк_с_упоминанием", "tick", "записей_С20",
})


def _walk(value: Any, path: str = "$", key: str | None = None) -> list[dict]:
    found: list[dict] = []
    if key in NUMERIC_KEYS and not isinstance(value, (int, float)):
        found.append({"путь": path, "поле": key,
                      "причина": "числовое поле имеет нечисловой тип"})
    elif key in NUMERIC_KEYS and (
            isinstance(value, bool) or not math.isfinite(float(value))):
        found.append({"путь": path, "поле": key,
                      "причина": "числовое поле не является конечным числом"})
    if isinstance(value, dict):
        for child_key, child in value.items():
            found.extend(_walk(child, path + "." + str(child_key),
                                str(child_key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk(child, "%s[%d]" % (path, index), key))
    return found


def inspect(path: Path) -> dict:
    result = {"путь": str(path), "прочитано": False,
              "статус": "not-evaluated"}
    if not path.is_file():
        result["причина"] = "файл отчёта отсутствует"
        return result
    result["прочитано"] = True
    try:
        value = json.loads(path.read_text(encoding="utf-8"),
                           parse_constant=lambda token: (_ for _ in ()).throw(
                               ValueError("нечисловая константа " + token)))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        result["статус"] = "unsupported"
        result["причина"] = "JSON не прошёл строгий разбор: " + str(exc)
        return result
    problems = _walk(value)
    result["статус"] = "unsupported" if problems else "verified-in-scope"
    result["поля_с_ошибкой"] = problems
    result["причина"] = (
        "все поля числового контракта имеют конечный числовой тип"
        if not problems else "обнаружен дрейф типа числового поля")
    return result


def scan(root: Path = ROOT) -> dict:
    reports = [inspect(root / name) for name in TARGETS]
    counts: dict[str, int] = {}
    for report in reports:
        counts[report["статус"]] = counts.get(report["статус"], 0) + 1
    return {
        "статус": ("verified-in-scope"
                   if counts.get("unsupported", 0) == 0
                   and counts.get("not-evaluated", 0) == 0
                   else "not-evaluated"),
        "проверка": "тип числовых полей в машинных JSON-отчётах",
        "сводка": counts,
        "артефакты": reports,
        "ограничение": "проверка типов не является научным подтверждением zeta/GUE",
    }


def selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory(prefix="goldsieve-json-types-") as td:
        root = Path(td)
        good = root / "good.json"
        good.write_text('{"std": 0.4, "tick": 3}', encoding="utf-8")
        bad = root / "bad.json"
        bad.write_text('{"std": "0.4"}', encoding="utf-8")
        malformed = root / "malformed.json"
        malformed.write_text('{"std":', encoding="utf-8")
        results = [inspect(good), inspect(bad), inspect(malformed)]
    checks = [
        ("числовой тип принимается", results[0]["статус"] == "verified-in-scope"),
        ("строка в числовом поле отклоняется",
         results[1]["статус"] == "unsupported"),
        ("оборванный JSON не становится покрытием",
         results[2]["статус"] == "unsupported"),
    ]
    for title, ok in checks:
        print("  %s %s" % ("ок " if ok else "ПРОВАЛ ", title))
    failed = sum(not ok for _, ok in checks)
    print("самопроверка типов числовых полей: %d пройдено, %d провалено"
          % (len(checks) - failed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv not in ([], ["--scan"]):
        print("использование: json_numeric_type_guard.py [--selftest|--scan]")
        return 2
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож типов числовых полей: %s; файлов %d; сводка %s"
          % (report["статус"], len(report["артефакты"]),
             json.dumps(report["сводка"], ensure_ascii=False,
                        sort_keys=True)))
    return 0 if report["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
