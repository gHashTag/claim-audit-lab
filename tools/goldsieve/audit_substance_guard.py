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
import re
import tempfile
from pathlib import Path
from typing import Any


REQUIRED = ("гейт", "регресс", "ос_матрица", "bblm", "изменённые_файлы")
TICK_ROOT = Path("/home/user/workspace/cron_tracking/20fee222")
OUT = Path(__file__).resolve().with_suffix(".json")


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


def _latest_substance(root: Path = TICK_ROOT) -> Path | None:
    """Найти предъявленный паспорт сути с наибольшим номером тика.

    Это чтение настоящего артефакта текущего аудита, а не восстановление
    значений из соседних докладов. Номер тика извлекается из имени файла,
    чтобы лексикографическая сортировка не поставила tick99 после tick100.
    """
    candidates: list[tuple[int, Path]] = []
    for path in root.glob("tick*-progress-substance.json"):
        match = re.fullmatch(r"tick(\d+)-progress-substance\.json", path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    return max(candidates, default=None, key=lambda item: item[0])[1] if candidates else None


def scan(path: Path | None = None) -> int:
    """Проверить форму настоящей машинной сути и предъявить область входа."""
    source = path or _latest_substance()
    result: dict[str, Any] = {
        "проверка": "форма машинной сути предъявленного паспорта тика",
        "ограничение": (
            "проверка формы не подтверждает научную истинность счётчиков "
            "и не закрывает долги zeta/GUE"
        ),
    }
    if source is None:
        result.update({
            "статус": "not-evaluated",
            "причина": "настоящий паспорт tickNNN-progress-substance.json не найден",
        })
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        print("статус входа: not-evaluated")
        print("форма машинной сути: настоящий паспорт не найден")
        return 1
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        result.update({
            "статус": "unsupported",
            "вход": str(source),
            "причина": "паспорт не прочитан: " + str(exc),
        })
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        print("статус входа: unsupported")
        print("форма машинной сути: паспорт не прочитан — %s" % exc)
        return 1
    ok, reason = validate(value)
    result.update({
        "статус": "verified-in-scope" if ok else "unsupported",
        "вход": str(source),
        "проверенные_поля": sorted(value) if isinstance(value, dict) else [],
        "причина": reason,
    })
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("статус входа: %s" % result["статус"])
    print("форма машинной сути: %s — %s" %
          ("ok" if ok else "ПРОВАЛ", reason))
    print("вход: %s" % source)
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--check", type=Path)
    group.add_argument("--scan", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.check:
        return check(args.check)
    return scan()


if __name__ == "__main__":
    raise SystemExit(main())
