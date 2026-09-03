#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож общего M_eff для нескольких результатов одного запуска.

С20 сообщает M_eff для отдельной цели. Если в одном архивном запуске
несколько целей используют один и тот же перебор, суммирование этих чисел
может повторно посчитать одни и те же попытки. Этот сторож не подменяет
статистический вывод: он делает молчание о совместном M_eff явным машинным
статусом ``not-evaluated`` и сохраняет пути наблюдаемых архивов.

Режимы:
    python3 meff_common_guard.py --selftest
    python3 meff_common_guard.py --scan
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "meff_common_guard.json"


def _finite_number(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _entries(document: object, source: str) -> list[dict]:
    """Извлечь только наблюдаемые записи С20 из одного JSON-файла."""
    if not isinstance(document, list):
        return []
    found: list[dict] = []
    for number, item in enumerate(document):
        if not isinstance(item, dict):
            continue
        results = item.get("results")
        if not isinstance(results, list):
            continue
        for result_number, result in enumerate(results):
            if not isinstance(result, dict) or result.get("sieve") != "С20 эффективное число попыток":
                continue
            numbers = result.get("numbers")
            if not isinstance(numbers, dict):
                continue
            if not (_finite_number(numbers.get("M"))
                    and _finite_number(numbers.get("M_eff"))):
                continue
            found.append({
                "источник_наблюдения": source,
                "запись": number,
                "сито": result_number,
                "M": float(numbers["M"]),
                "M_eff": float(numbers["M_eff"]),
                "общий_M_eff": numbers.get("M_eff_общий"),
                "идентификатор_общего_ансамбля":
                    numbers.get("идентификатор_общего_ансамбля"),
            })
    return found


def inspect(document: object, source: str) -> dict:
    """Классифицировать общий ансамбль без восстановления пропущенных данных."""
    records = _entries(document, source)
    if len(records) < 2:
        return {
            "статус": "not-evaluated",
            "причина": "недостаточно записей С20 в одном архиве",
            "источник_наблюдения": source,
            "записей_С20": len(records),
            "наблюдения": records,
        }

    m_values = {round(item["M"], 12) for item in records}
    explicit = [
        item for item in records
        if item["общий_M_eff"] is not None
        or item["идентификатор_общего_ансамбля"] is not None
    ]
    if len(m_values) != 1:
        return {
            "статус": "not-evaluated",
            "причина": "общий ансамбль не объявлен и значения M различаются",
            "источник_наблюдения": source,
            "записей_С20": len(records),
            "наблюдения": records,
        }
    if not explicit:
        return {
            "статус": "not-evaluated",
            "причина": "общий_M_eff не объявлен для нескольких записей одного M",
            "источник_наблюдения": source,
            "записей_С20": len(records),
            "наблюдения": records,
        }
    if len(explicit) != len(records):
        return {
            "статус": "not-evaluated",
            "причина": "общий_M_eff объявлен не для каждой записи общего ансамбля",
            "источник_наблюдения": source,
            "записей_С20": len(records),
            "наблюдения": records,
        }
    common = {round(float(item["общий_M_eff"]), 12)
              for item in records if item["общий_M_eff"] is not None}
    if len(common) != 1:
        return {
            "статус": "not-evaluated",
            "причина": "значения общего_M_eff расходятся между записями",
            "источник_наблюдения": source,
            "записей_С20": len(records),
            "наблюдения": records,
        }
    return {
        "статус": "verified-in-scope",
        "причина": "общий_M_eff объявлен единообразно",
        "источник_наблюдения": source,
        "записей_С20": len(records),
        "наблюдения": records,
        "общий_M_eff": next(iter(common)),
    }


def scan(root: Path = ROOT) -> dict:
    reports = []
    for path in sorted(root.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        report = inspect(document, str(path))
        if report["записей_С20"] >= 2:
            reports.append(report)
    return {
        "статус": "not-evaluated" if any(
            item["статус"] == "not-evaluated" for item in reports
        ) else "verified-in-scope",
        "причина": "совместный M_eff явно проверен; открытые архивы перечислены"
        if reports else "в корпусе инструмента нет архивов с несколькими записями С20",
        "архивов_с_несколькими_С20": len(reports),
        "открытых_архивов": sum(
            item["статус"] == "not-evaluated" for item in reports
        ),
        "наблюдения": reports,
    }


def selftest() -> int:
    good = 0
    bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            bad += 1
            print("  ПРОВАЛ  " + name)

    base = {
        "results": [
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 123201, "M_eff": 80000}},
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 123201, "M_eff": 70000}},
        ]
    }
    missing = inspect([base, base], "фикстура/общий-m-eff.json")
    check("одинаковый M без общего M_eff получает not-evaluated",
          missing["статус"] == "not-evaluated"
          and missing["причина"].startswith("общий_M_eff не объявлен"))

    declared = {
        "results": [
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 123201, "M_eff": 80000,
                         "M_eff_общий": 80000}},
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 123201, "M_eff": 70000,
                         "M_eff_общий": 80000}},
        ]
    }
    ok = inspect([declared], "фикстура/объявленный-m-eff.json")
    check("единый общий M_eff получает verified-in-scope",
          ok["статус"] == "verified-in-scope")

    different = {
        "results": [
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 123201, "M_eff": 80000}},
            {"sieve": "С20 эффективное число попыток",
             "numbers": {"M": 99, "M_eff": 40}},
        ]
    }
    diff = inspect([different], "фикстура/разный-m.json")
    check("разный M не объявляется общим ансамблем",
          diff["статус"] == "not-evaluated"
          and "M различаются" in diff["причина"])
    print("самопроверка общего M_eff: пройдено %d, провалено %d" % (good, bad))
    return bad


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv == ["--scan"]:
        report = scan()
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        print("сторож общего M_eff: архивов %d, открытых %d" %
              (report["архивов_с_несколькими_С20"], report["открытых_архивов"]))
        return 0
    print("использование: --selftest или --scan")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
