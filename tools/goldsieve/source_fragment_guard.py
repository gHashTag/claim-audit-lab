#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож неоднозначных фрагментов источника в реестре.

Поле ``source`` участвует в отпечатке инкрементального регресса. Если рядом с
путём файла записать свободное описание через запятую или точку с запятой,
описание может стать «неразрешённым» входом: регресс будет вращать кейс
бесконечно, а читатель не поймёт, какой файл был наблюдаемым. Сторож требует,
чтобы каждый локальный фрагмент был существующим файлом корпуса или рабочей
копии. Внешний URL не является локальным входом и пропускается.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - проверяется штатным пропуском гейта
    yaml = None


HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "claims.yaml"
CORPUS = Path("/home/user/workspace/corpus/trinity").resolve()
OUT = HERE / "source_fragment_guard.json"


def _fragments(value: object) -> list[str]:
    """Разделить составное описание источника на локальные фрагменты."""
    text = str(value or "").strip()
    return [
        item.strip()
        for item in re.split(r";", text)
        if item.strip()
    ]


def _resolve(fragment: str) -> Path | None:
    if fragment.startswith(("http://", "https://")):
        return None
    raw_values = [fragment]
    # Реестр допускает строку или диапазон строк после двоеточия. Сначала
    # проверяем полный фрагмент, затем путь до двоеточия; произвольный текст
    # после запятой намеренно не отбрасываем и считаем неоднозначностью.
    if ":" in fragment and not fragment.startswith("/"):
        raw_values.append(fragment.split(":", 1)[0].strip())
    for raw_value in raw_values:
        raw = Path(raw_value)
        candidates = [raw] if raw.is_absolute() else [
            CORPUS / raw,
            HERE / raw,
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file():
                return resolved
    return None


def scan(registry: Path = REGISTRY) -> dict:
    """Проверить все фрагменты source, не читая внешние URL."""
    if yaml is None:
        return {
            "статус": "unsupported",
            "причина": "модуль yaml отсутствует",
            "реестр": str(registry),
        }
    data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    entries = data.get("claims", [])
    unresolved: list[dict] = []
    resolved_count = 0
    url_count = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            unresolved.append({"индекс": index, "причина": "запись не словарь"})
            continue
        source = entry.get("source")
        for fragment in _fragments(source):
            if fragment.startswith(("http://", "https://")):
                url_count += 1
                continue
            path = _resolve(fragment)
            if path is None:
                unresolved.append({
                    "индекс": index,
                    "case": entry.get("case", ""),
                    "фрагмент": fragment,
                })
            else:
                resolved_count += 1
    status = "verified-in-scope" if not unresolved else "not-evaluated"
    return {
        "статус": status,
        "реестр": str(registry),
        "записей": len(entries),
        "разрешённых_файлов": resolved_count,
        "внешних_URL": url_count,
        "неразрешённых_фрагментов": unresolved,
        "ограничение": (
            "существующий путь доказывает только разрешимость входа; "
            "содержательная независимость observed/reference не установлена"
        ),
    }


def selftest() -> int:
    if yaml is None:
        print("самопроверка сторожа фрагментов: unsupported (нет yaml)")
        return 0
    with tempfile.TemporaryDirectory(prefix="goldsieve-source-fragments-") as tmp:
        root = Path(tmp)
        observed = root / "observed.md"
        observed.write_text("наблюдаемое\n", encoding="utf-8")
        good = root / "good.yaml"
        good.write_text(
            "claims:\n"
            "  - source: %s; https://example.invalid/public\n"
            "    case: cases/x.py\n" % observed,
            encoding="utf-8",
        )
        bad = root / "bad.yaml"
        bad.write_text(
            "claims:\n"
            "  - source: %s, четыре полосы высот\n"
            "    case: cases/x.py\n" % observed,
            encoding="utf-8",
        )
        good_result = scan(good)
        bad_result = scan(bad)
    checks = [
        good_result["статус"] == "verified-in-scope",
        bad_result["статус"] == "not-evaluated",
        len(bad_result["неразрешённых_фрагментов"]) == 1,
    ]
    passed = sum(checks)
    failed = len(checks) - passed
    print("самопроверка сторожа фрагментов источника: "
          "пройдено %d, провалено %d" % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="проверка фрагментов source")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = scan()
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("сторож фрагментов источника: %s; файлов %d; "
          "неразрешённых %d" % (
              result["статус"],
              result.get("разрешённых_файлов", 0),
              len(result.get("неразрешённых_фрагментов", [])),
          ))
    return 0 if result["статус"] in ("verified-in-scope", "unsupported") else 1


if __name__ == "__main__":
    raise SystemExit(main())
