#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож формы машинной сути тика.

Числа в паспорте progress_guard являются входом для запрета холостого тика.
Если поле исчезло, стало строкой или получило другую размерность, сравнение
может молча потерять именно ту часть прогресса, которую обязано измерять.
Этот сторож проверяет форму, но не превращает её в научный вердикт.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any


REQUIRED = ("гейт", "регресс", "ос_матрица", "bblm", "изменённые_файлы")


def _ints(value: Any, length: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) == length
        and all(isinstance(item, int) and not isinstance(item, bool)
                and item >= 0 for item in value)
    )


def validate(value: Any) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return False, "корень сути не является объектом"
    missing = [name for name in REQUIRED if name not in value]
    if missing:
        return False, "отсутствуют поля: " + ", ".join(missing)
    if not _ints(value["гейт"], 3):
        return False, "гейт обязан иметь три неотрицательных целых числа"
    if value["гейт"][2] != 0:
        return False, "гейт содержит провалы"
    if not _ints(value["регресс"], 6):
        return False, "регресс обязан иметь шесть неотрицательных целых чисел"
    if not _ints(value["ос_матрица"], 2):
        return False, "ос_матрица обязана иметь пару неотрицательных целых чисел"
    if value["ос_матрица"][0] > value["ос_матрица"][1]:
        return False, "успешных заданий ОС-матрицы больше общего числа"
    bblm = value["bblm"]
    if not (
        isinstance(bblm, list)
        and len(bblm) == 2
        and isinstance(bblm[0], int)
        and not isinstance(bblm[0], bool)
        and bblm[0] >= 0
        and isinstance(bblm[1], bool)
    ):
        return False, "bblm обязан иметь число закрытых элементов и флаг вопроса"
    files = value["изменённые_файлы"]
    if not isinstance(files, list) or not files or not all(
            isinstance(item, str) and item for item in files):
        return False, "изменённые_файлы обязаны быть непустым списком строк"
    return True, "форма сути корректна"


def selftest() -> int:
    good = {
        "гейт": [103, 2, 0],
        "регресс": [7, 109, 0, 0, 0, 0],
        "ос_матрица": [6, 6],
        "bblm": [7, True],
        "изменённые_файлы": ["audit_substance_guard.py"],
    }
    cases = [
        ("положительная форма", good, True),
        ("нет поля регресса", {k: v for k, v in good.items() if k != "регресс"},
         False),
        ("строка вместо числа", {**good, "гейт": ["103", 2, 0]}, False),
        ("провал гейта", {**good, "гейт": [103, 2, 1]}, False),
        ("неполный регресс", {**good, "регресс": [7, 109]}, False),
        ("лишний успех ОС", {**good, "ос_матрица": [7, 6]}, False),
        ("флаг BBLM не bool", {**good, "bblm": [7, 1]}, False),
        ("пустой список файлов", {**good, "изменённые_файлы": []}, False),
    ]
    failed = 0
    for name, value, expected in cases:
        actual, _ = validate(value)
        if actual != expected:
            failed += 1
            print("  ПРОВАЛ  " + name)
        else:
            print("  ок  " + name)
    print(f"самопроверка формы машинной сути: пройдено {len(cases) - failed}, "
          f"провалено {failed}")
    return 1 if failed else 0


def check(path: Path) -> int:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"форма машинной сути: ПРОВАЛ — {path}: {exc}")
        return 1
    ok, reason = validate(value)
    print(f"форма машинной сути: {'ok' if ok else 'ПРОВАЛ'} — {reason}")
    print(f"источник: {path}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.check:
        return check(args.check)
    parser.error("укажите --selftest или --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
