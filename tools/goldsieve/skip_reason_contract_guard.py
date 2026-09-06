#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож формы ключей ``skip_reasons`` в кейсах корпуса.

С13 проверяет, что фактический пропуск объявлен. Отдельная неоднозначность
остаётся у самого словаря: опечатанный ключ или пустое объяснение может тихо
пережить разбор, если соответствующее сито в конкретном прогоне не сработало.
Сторож проверяет литеральные словари в AST и не исполняет код кейсов.
Динамически собранные словари перечисляются как неоценённые, а не считаются
покрытыми.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
OUT = HERE / "skip_reason_contract_guard.json"
KEY_RE = re.compile(r"^С(?:[1-9]|1[0-9]|2[01])$")


def _literal_entries(node: ast.AST) -> tuple[list[tuple[str, str]], int]:
    """Вернуть литеральные пары ключ/значение и число динамических частей."""
    if not isinstance(node, ast.Dict):
        return [], 1
    entries: list[tuple[str, str]] = []
    unresolved = 0
    for key, value in zip(node.keys, node.values):
        if key is None:
            unresolved += 1
            continue
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            unresolved += 1
            continue
        try:
            text = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            unresolved += 1
            continue
        entries.append((key.value, text if isinstance(text, str) else ""))
    return entries, unresolved


def scan(cases_dir: Path = CASES) -> dict:
    rows = []
    violations = []
    calls = 0
    literal_keys = 0
    unresolved = 0
    for path in sorted(cases_dir.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            violations.append({"файл": path.name, "причина": "не удалось разобрать: %s" % exc})
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            keyword = next((item for item in node.keywords
                            if item.arg == "skip_reasons"), None)
            if keyword is None:
                continue
            calls += 1
            entries, unknown = _literal_entries(keyword.value)
            literal_keys += len(entries)
            unresolved += unknown
            row = {"файл": path.name, "литеральных_ключей": len(entries),
                   "динамических_частей": unknown}
            rows.append(row)
            for key, reason in entries:
                if not KEY_RE.fullmatch(key):
                    violations.append({
                        "файл": path.name,
                        "ключ": key,
                        "причина": "ключ должен иметь вид С1…С21",
                    })
                if not reason.strip():
                    violations.append({
                        "файл": path.name,
                        "ключ": key,
                        "причина": "объяснение пропуска не должно быть пустым",
                    })
    status = "unsupported" if violations else "verified-in-scope"
    return {
        "статус": status,
        "проверено_кейсов": len({row["файл"] for row in rows}),
        "вызовов_сита": calls,
        "литеральных_ключей": literal_keys,
        "динамических_частей": unresolved,
        "нарушения": violations,
        "примечание": (
            "динамически собранные словари не объявлены покрытыми; "
            "проверены только литеральные ключи и их текст"
        ),
        "строки": rows,
    }


def _selftest() -> int:
    cases = [
        ("положительный ключ", 'skip_reasons={"С10": "нет измерения"}', True),
        ("ключ вне словаря", 'skip_reasons={"С0": "ошибка"}', False),
        ("пустое объяснение", 'skip_reasons={"С11": ""}', False),
        ("динамическая часть не считается покрытием",
         'skip_reasons={**часть, "С12": "нет второго метода"}', True),
    ]
    failed = 0
    for name, text, expected in cases:
        tree = ast.parse("Claim(" + text + ")")
        keyword = tree.body[0].value.keywords[0]
        entries, unresolved = _literal_entries(keyword.value)
        actual = all(KEY_RE.fullmatch(key) and reason.strip()
                     for key, reason in entries)
        actual = actual and not any(
            not KEY_RE.fullmatch(key) or not reason.strip()
            for key, reason in entries
        )
        if actual != expected:
            failed += 1
            print("  ПРОВАЛ  " + name)
        else:
            print("  ok      " + name)
    print("самопроверка ключей skip_reasons: пройдено %d, провалено %d"
          % (len(cases) - failed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("контракт ключей skip_reasons: %s; кейсов %d, вызовов %d, "
          "литеральных ключей %d, динамических частей %d, нарушений %d"
          % (report["статус"], report["проверено_кейсов"],
             report["вызовов_сита"], report["литеральных_ключей"],
             report["динамических_частей"], len(report["нарушения"])))
    return 0 if report["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
