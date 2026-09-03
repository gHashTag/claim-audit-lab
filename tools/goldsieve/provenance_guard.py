#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож происхождения входов.

Отдельные наблюдаемое и эталонное имена могут указывать на один файл через
разные относительные пути или символическую ссылку. Такая сверка выглядит
независимой, но на самом деле является тавтологией. Сторож проверяет
канонические пути и не считает отсутствие файла покрытием.
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path


def _canonical(path: str | os.PathLike[str]) -> str:
    value = os.path.realpath(os.path.abspath(os.fspath(path)))
    if not os.path.isfile(value):
        raise FileNotFoundError("файл входа не найден: %s" % path)
    return value


def distinct_inputs(paths: list[str | os.PathLike[str]]) -> list[str]:
    """Вернуть канонические входы, отвергнув дубликаты и отсутствующие файлы.

    ``realpath`` ловит символьные ссылки, но не жёсткие: два имени жёсткой
    ссылки имеют разные строки пути и один и тот же inode. Сверка таких имён
    остаётся тавтологией, поэтому дополнительно проверяем пару (устройство,
    inode). Нулевой inode не используем как идентификатор: некоторые
    файловые системы не предоставляют его надёжно.
    """
    if not paths:
        raise ValueError("не объявлен ни один вход")
    result = []
    seen = set()
    seen_file_ids = set()
    for path in paths:
        canonical = _canonical(path)
        stat = os.stat(canonical)
        file_id = (stat.st_dev, stat.st_ino)
        if canonical in seen or (stat.st_ino and file_id in seen_file_ids):
            raise ValueError("дублированный вход после канонизации: %s" % path)
        seen.add(canonical)
        if stat.st_ino:
            seen_file_ids.add(file_id)
        result.append(canonical)
    return result


def check_pair(observed: str, reference: str) -> dict:
    """Проверить, что observed и reference — разные существующие файлы."""
    inputs = distinct_inputs([observed, reference])
    return {
        "статус": "PASS",
        "наблюдаемое": inputs[0],
        "эталон": inputs[1],
        "разные_файлы": True,
    }


def selftest() -> int:
    fail = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal fail
        print("  %s %s%s" % (
            "ок  " if ok else "ПРОВАЛ ",
            name,
            (" — " + detail) if detail else "",
        ))
        if not ok:
            fail += 1

    root = Path(tempfile.mkdtemp(prefix="goldsieve-provenance-"))
    try:
        observed = root / "observed.txt"
        reference = root / "reference.txt"
        alias = root / "reference-alias.txt"
        observed.write_text("наблюдаемое\n", encoding="utf-8")
        reference.write_text("эталон\n", encoding="utf-8")
        try:
            alias.symlink_to(reference)
        except (OSError, NotImplementedError):
            alias = reference
        hardlink = root / "reference-hardlink.txt"
        try:
            os.link(reference, hardlink)
        except (OSError, NotImplementedError):
            hardlink = None

        check("два разных файла принимаются",
              check_pair(str(observed), str(reference))["разные_файлы"])
        try:
            check_pair(str(observed), str(observed))
        except (ValueError, FileNotFoundError) as exc:
            check("один файл отвергается", True, str(exc))
        else:
            check("один файл отвергается", False)
        try:
            check_pair(str(reference), str(alias))
        except (ValueError, FileNotFoundError) as exc:
            check("символьный псевдоним отвергается", True, str(exc))
        else:
            check("символьный псевдоним отвергается", False)
        if hardlink is None:
            check("жёсткий псевдоним отвергается", True,
                  "жёсткие ссылки недоступны в этой среде")
        else:
            try:
                check_pair(str(reference), str(hardlink))
            except (ValueError, FileNotFoundError) as exc:
                check("жёсткий псевдоним отвергается", True, str(exc))
            else:
                check("жёсткий псевдоним отвергается", False)
        try:
            distinct_inputs([str(observed), str(observed)])
        except (ValueError, FileNotFoundError) as exc:
            check("дубликат списка отвергается", True, str(exc))
        else:
            check("дубликат списка отвергается", False)
        try:
            distinct_inputs([str(observed), str(root / "missing.txt")])
        except FileNotFoundError as exc:
            check("отсутствующий вход не считается покрытием", True, str(exc))
        else:
            check("отсутствующий вход не считается покрытием", False)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("самопроверка сторожа происхождения: пройдено %d, провалено %d"
          % (6 - fail, fail))
    return fail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="проверка происхождения входных файлов")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--check", nargs=2, metavar=("НАБЛЮДЕНИЕ", "ЭТАЛОН"))
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        print(check_pair(*args.check))
    except (ValueError, FileNotFoundError) as exc:
        print("ПУСТО: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
