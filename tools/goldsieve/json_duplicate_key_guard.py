#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож повторяющихся ключей в машинных JSON-отчётах.

Обычный ``json.loads`` оставляет только последнее значение повторяющегося
ключа. Поэтому повреждённый или неоднозначный отчёт может выглядеть корректно
после разбора. Этот сторож не выносит научный вердикт: он проверяет, что
машинный артефакт имеет однозначное представление.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "json_duplicate_key_guard.json"
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


class DuplicateKey(ValueError):
    """Повтор ключа в одном JSON-объекте."""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey("повторяющийся ключ JSON: " + str(key))
        result[key] = value
    return result


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
        json.loads(path.read_text(encoding="utf-8"),
                   object_pairs_hook=_unique_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError,
            DuplicateKey, ValueError) as exc:
        record["статус"] = "unsupported"
        record["причина"] = "JSON неоднозначен или повреждён: " + str(exc)
        return record
    record["статус"] = "verified-in-scope"
    record["причина"] = (
        "повторяющихся ключей не обнаружено; научный вердикт не оценивается"
    )
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
        "проверка": "однозначность ключей машинных JSON-отчётов",
        "сводка": counts,
        "артефакты": reports,
        "ограничение": (
            "однозначность JSON не является научным подтверждением zeta/GUE"
        ),
    }


def _selftest() -> int:
    import tempfile

    failures = 0

    def check(label: str, condition: bool) -> None:
        nonlocal failures
        print("  %s %s" % ("ок " if condition else "ПРОВАЛ ", label))
        if not condition:
            failures += 1

    with tempfile.TemporaryDirectory(prefix="goldsieve-json-keys-") as td:
        root = Path(td)
        finite = root / "finite.json"
        finite.write_text('{"значение": 1, "вложенный": {"x": 2}}',
                          encoding="utf-8")
        check("однозначный JSON принимается",
              inspect(finite)["статус"] == "verified-in-scope")

        duplicate = root / "duplicate.json"
        duplicate.write_text('{"значение": 1, "значение": 2}',
                             encoding="utf-8")
        check("повтор верхнего ключа отвергается",
              inspect(duplicate)["статус"] == "unsupported")

        nested = root / "nested.json"
        nested.write_text('{"outer": {"x": 1, "x": 2}}', encoding="utf-8")
        check("повтор вложенного ключа отвергается",
              inspect(nested)["статус"] == "unsupported")

        malformed = root / "malformed.json"
        malformed.write_text('{"значение":', encoding="utf-8")
        check("оборванный JSON не становится покрытием",
              inspect(malformed)["статус"] == "unsupported")

        missing = root / "missing.json"
        check("отсутствующий отчёт остаётся not-evaluated",
              inspect(missing)["статус"] == "not-evaluated")

    print("самопроверка однозначности ключей: %d провалов" % failures)
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv not in ([], ["--scan"]):
        print("использование: json_duplicate_key_guard.py [--selftest|--scan]")
        return 2
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож однозначности ключей: %s; файлов %d; сводка %s"
          % (report["статус"], len(report["артефакты"]),
             json.dumps(report["сводка"], ensure_ascii=False, sort_keys=True)))
    return 0 if report["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
