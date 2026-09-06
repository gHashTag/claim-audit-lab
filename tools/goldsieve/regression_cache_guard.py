#!/usr/bin/env python3
"""Самопроверка кэша отпечатков файлов инкрементального регресса."""

import os
import sys
import tempfile

from goldsieve.cli import (
    _cached_file_sha256,
    _source_files,
    _source_has_unresolved_fragment,
)


def _selftest():
    passed = 0
    failed = 0

    def check(condition, title):
        nonlocal passed, failed
        if condition:
            print("  ok   %s" % title)
            passed += 1
        else:
            print("  ПРОВАЛ   %s" % title)
            failed += 1

    with tempfile.TemporaryDirectory(prefix="goldsieve-regression-cache-") as td:
        path = os.path.join(td, "наблюдение.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("старое содержимое")
        cache = {}
        stats = {"hits": 0, "misses": 0}
        first = _cached_file_sha256(path, cache, stats)
        second = _cached_file_sha256(path, cache, stats)
        check(first is not None, "первое чтение создаёт отпечаток")
        check(first == second and stats == {"hits": 1, "misses": 1},
              "неизменившийся файл берётся из кэша")

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("новое содержимое")
        third = _cached_file_sha256(path, cache, stats)
        check(third != first, "изменившийся файл перечитывается")
        check(stats == {"hits": 1, "misses": 2},
              "изменение не маскируется старым отпечатком")

        missing = _cached_file_sha256(
            os.path.join(td, "нет-такого-файла"), cache, stats)
        check(missing is None, "отсутствующий файл не становится покрытием")

        first_source = os.path.join(td, "__gold-sieve-source-a.txt")
        second_source = os.path.join(td, "__gold-sieve-source-b.txt")
        with open(first_source, "w", encoding="utf-8") as fh:
            fh.write("первое наблюдение")
        with open(second_source, "w", encoding="utf-8") as fh:
            fh.write("второе наблюдение")
        source_key = "__gold-sieve-source-a.txt; __gold-sieve-source-b.txt"
        paths = _source_files(td, source_key)
        check(paths == [first_source, second_source],
              "составная ссылка включает все локальные наблюдения")
        check(not _source_has_unresolved_fragment(td, source_key),
              "полная составная ссылка не помечается потерянной")

        os.unlink(second_source)
        paths_after_delete = _source_files(td, source_key)
        check(paths_after_delete == [first_source],
              "после удаления сохраняется отпечаток оставшегося наблюдения")
        check(_source_has_unresolved_fragment(td, source_key),
              "удалённое наблюдение не маскируется старым снимком")
        url_plus_local = (
            "https://example.invalid/не-читается; __gold-sieve-source-a.txt")
        check(_source_files(td, url_plus_local) == [first_source],
              "URL не отбрасывает соседнее локальное наблюдение")
        check(not _source_has_unresolved_fragment(td, url_plus_local),
              "URL не считается потерянным локальным входом")

    print("самопроверка кэша регресса: пройдено %d, провалено %d"
          % (passed, failed))
    return 1 if failed else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv != ["--selftest"]:
        print("использование: regression_cache_guard.py --selftest")
        return 2
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
