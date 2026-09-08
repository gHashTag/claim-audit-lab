#!/usr/bin/env python3
"""Сторож кэша отпечатков файлов инкрементального регресса.

Кэш ускоряет регресс, но не является самостоятельным источником истины:
решение о повторном использовании отпечатка принимается по свежему
``stat``. Поэтому этот сторож отдельно предъявляет настоящий вход —
``baseline/regression-file-cache.json`` — и проверяет, что его записи всё ещё
соответствуют существующим файлам корпуса. Это подтверждает область
прочитанного кэша, но не закрывает научные долги и не заменяет сам регресс.

Режимы:
    python3 regression_cache_guard.py --selftest
    python3 regression_cache_guard.py --audit
    python3 regression_cache_guard.py --scan
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from goldsieve.cli import (
    _cached_file_sha256,
    _source_files,
    _source_has_unresolved_fragment,
)

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "baseline" / "regression-file-cache.json"
FINGERPRINTS = ROOT / "baseline" / "regression-fingerprints.json"
OUT = ROOT / "regression_cache_guard.json"
STATUSES = ("verified-in-scope", "not-evaluated", "unsupported",
            "platform-unverified")


def _metadata(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
        "inode": stat.st_ino,
    }


def _valid_digest(value: object) -> bool:
    return (isinstance(value, str)
            and len(value) == 64
            and all(char in "0123456789abcdef" for char in value.lower()))


def inspect_cache(cache_path: Path = CACHE,
                  fingerprints_path: Path = FINGERPRINTS) -> dict:
    """Проверить настоящие файлы кэша без восстановления пропущенных данных."""
    result = {
        "проверка": "область входа кэша отпечатков регресса",
        "ограничение": (
            "проверка формы и актуальности кэша не подтверждает вердикты "
            "регресса и не закрывает научные долги"
        ),
        "статус": "not-evaluated",
        "статус_входа": "not-evaluated",
        "входы": [str(cache_path), str(fingerprints_path)],
    }
    if not cache_path.is_file() or not fingerprints_path.is_file():
        result["причина"] = "настоящий кэш или снимок отпечатков отсутствует"
        return result
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        fingerprints = json.loads(
            fingerprints_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        result["статус"] = "unsupported"
        result["статус_входа"] = "unsupported"
        result["причина"] = "машинный вход не разобран: " + str(exc)
        return result

    files = cache.get("files") if isinstance(cache, dict) else None
    cases = fingerprints.get("cases") if isinstance(fingerprints, dict) else None
    if (not isinstance(files, dict) or not files
            or not isinstance(cases, dict) or not cases):
        result["статус"] = "unsupported"
        result["статус_входа"] = "unsupported"
        result["причина"] = "снимки не содержат непустых отображений files и cases"
        return result

    malformed = []
    missing = []
    stale = []
    for raw_path, record in files.items():
        if (not isinstance(raw_path, str)
                or not isinstance(record, dict)
                or not _valid_digest(record.get("sha256"))
                or any(not isinstance(record.get(name), int)
                       or isinstance(record.get(name), bool)
                       or record.get(name) < 0
                       for name in ("size", "mtime_ns", "ctime_ns", "inode"))):
            malformed.append(str(raw_path))
            continue
        path = Path(raw_path)
        if not path.is_file():
            missing.append(str(path))
            continue
        try:
            current = _metadata(path)
        except OSError:
            missing.append(str(path))
            continue
        expected = {name: record[name] for name in current}
        if current != expected:
            stale.append(str(path))

    result.update({
        "записей_файлов": len(files),
        "записей_кейсов": len(cases),
        "неверных_записей": len(malformed),
        "отсутствующих_файлов": len(missing),
        "устаревших_метаданных": len(stale),
    })
    if malformed:
        result["статус"] = "unsupported"
        result["статус_входа"] = "unsupported"
        result["причина"] = "часть записей кэша имеет неверную форму"
    elif missing:
        result["статус"] = "not-evaluated"
        result["статус_входа"] = "not-evaluated"
        result["причина"] = "часть файлов из кэша отсутствует"
    elif stale:
        result["статус"] = "not-evaluated"
        result["статус_входа"] = "not-evaluated"
        result["причина"] = "метаданные кэша устарели относительно входов"
    else:
        result["статус"] = "verified-in-scope"
        result["статус_входа"] = "verified-in-scope"
        result["причина"] = (
            "прочитаны непустые снимки кэша и отпечатков; все "
            "предъявленные метаданные совпадают с настоящими файлами"
        )
    return result


def audit() -> int:
    report = inspect_cache()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("статус входа: %s" % report["статус_входа"])
    print("статус кэша регресса: %s — %s"
          % (report["статус"], report["причина"]))
    if "записей_файлов" in report:
        print("прочитано записей файлов: %d; кейсов: %d"
              % (report["записей_файлов"], report["записей_кейсов"]))
    return 0 if report["статус_входа"] == "verified-in-scope" else 1


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

        cache_path = os.path.join(td, "cache.json")
        fingerprints_path = os.path.join(td, "fingerprints.json")
        cache_file = os.path.join(td, "наблюдение.txt")
        with open(cache_file, "w", encoding="utf-8") as fh:
            fh.write("настоящий вход")
        metadata = _metadata(Path(cache_file))
        metadata["sha256"] = hashlib.sha256(
            Path(cache_file).read_bytes()).hexdigest()
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump({"version": 1, "files": {cache_file: metadata}}, fh)
        with open(fingerprints_path, "w", encoding="utf-8") as fh:
            json.dump({"version": 1, "cases": {"cases/example.py": {}}},
                      fh)
        checked = inspect_cache(Path(cache_path), Path(fingerprints_path))
        check(checked["статус_входа"] == "verified-in-scope",
              "настоящий снимок кэша получает verified-in-scope")
        metadata["size"] += 1
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump({"version": 1, "files": {cache_file: metadata}}, fh)
        stale = inspect_cache(Path(cache_path), Path(fingerprints_path))
        check(stale["статус_входа"] == "not-evaluated",
              "устаревший снимок не становится покрытием")

    print("самопроверка кэша регресса: пройдено %d, провалено %d"
          % (passed, failed))
    return 1 if failed else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--audit", action="store_true")
    group.add_argument("--scan", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    return audit()


if __name__ == "__main__":
    raise SystemExit(main())
