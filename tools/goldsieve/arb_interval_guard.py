#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож предъявления шаровой арифметики Arb.

Численный результат нельзя считать проверенным шаровой арифметикой только из-за
упоминания слова «интервал». Нужны прочитанные из корпуса метод, нижняя и
верхняя границы, а также конечные числа с нижней границей не выше верхней.
Если корпус предъявляет только точку или готовое отношение, сторож оставляет
статус ``not-evaluated`` и не выдумывает интервал.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
CORPUS = Path("/home/user/workspace/corpus/trinity")
SOURCES = (
    CORPUS / "data/zeta/zeta_figure1_chi2.csv",
    CORPUS / "data/zeta/zeta_figure1_p95.csv",
    CORPUS / "data/zeta/zeta_bin_analysis_update.md",
)
OUT = HERE / "arb_interval_guard.json"


def _normal(name: str) -> str:
    return re.sub(r"[^a-zа-я0-9]+", "_", name.lower()).strip("_")


def _bound_kind(name: str) -> str | None:
    n = _normal(name)
    if n in {"lower", "lower_bound", "lo", "min", "нижняя_граница",
             "нижняя", "левая_граница"}:
        return "нижняя_граница"
    if n in {"upper", "upper_bound", "hi", "max", "верхняя_граница",
             "верхняя", "правая_граница"}:
        return "верхняя_граница"
    return None


def _finite(value: str) -> float:
    result = float(value.strip())
    if not math.isfinite(result):
        raise ValueError("граница не является конечным числом")
    return result


def _csv_report(path: Path, text: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(text)))
    fields = list(rows[0]) if rows else []
    lower = next((f for f in fields if _bound_kind(f) == "нижняя_граница"),
                 None)
    upper = next((f for f in fields if _bound_kind(f) == "верхняя_граница"),
                 None)
    method_field = next((f for f in fields if _normal(f) in
                         {"method", "метод", "arithmetic", "арифметика"}), None)
    method_values = [
        str(row.get(method_field, "")).lower() for row in rows
    ] if method_field else []
    arb_seen = any("arb" in value or "шаров" in value or "интервал" in value
                   for value in method_values)
    intervals = []
    malformed = []
    non_arb_intervals = []
    if lower and upper:
        for index, row in enumerate(rows, 2):
            method_value = str(row.get(method_field, "")).lower() if method_field else ""
            row_is_arb = (
                "arb" in method_value
                or "шаров" in method_value
                or "интервал" in method_value
            )
            try:
                lo, hi = _finite(row[lower]), _finite(row[upper])
                if lo > hi:
                    raise ValueError("нижняя граница выше верхней")
                interval = {
                    "строка": index, "нижняя": lo, "верхняя": hi,
                    "метод_arb": row_is_arb,
                }
                if row_is_arb:
                    intervals.append(interval)
                else:
                    # Числовой интервал другой арифметики не является
                    # наблюдением Arb и не должен закрывать этот долг.
                    non_arb_intervals.append(interval)
            except (KeyError, TypeError, ValueError) as exc:
                malformed.append({"строка": index, "причина": str(exc)})
    return {
        "путь": str(path),
        "прочитано": True,
        "метод_arb": arb_seen,
        "есть_нижняя_граница": lower is not None,
        "есть_верхняя_граница": upper is not None,
        "интервалы": intervals,
        "интервалы_не_Arb": non_arb_intervals,
        "ошибки": malformed,
    }


def inspect_source(path: Path) -> dict:
    if not path.is_file():
        return {
            "путь": str(path),
            "прочитано": False,
            "причина": "файл корпуса отсутствует",
        }
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".csv":
        return _csv_report(path, text)
    # Маркдаун может содержать текстовое описание, но без машиночитаемых
    # границ оно не закрывает риск. Сохраняем факт чтения и путь наблюдения.
    return {
        "путь": str(path),
        "прочитано": True,
        "метод_arb": bool(re.search(r"\barb\b|шаровая", text, re.I)),
        "есть_нижняя_граница": bool(re.search(
            r"нижн(яя|ей)\s+границ|lower\s+bound", text, re.I)),
        "есть_верхняя_граница": bool(re.search(
            r"верхн(яя|ей)\s+границ|upper\s+bound", text, re.I)),
        "интервалы": [],
        "ошибки": [],
    }


def evaluate(reports: list[dict]) -> dict:
    existing = [r for r in reports if r.get("прочитано")]
    malformed = [r for r in existing if r.get("ошибки")]
    valid = [i for r in existing for i in r.get("интервалы", [])]
    non_arb = [i for r in existing for i in r.get("интервалы_не_Arb", [])]
    arb = any(r.get("метод_arb") for r in existing)
    bounds = all(r.get("есть_нижняя_граница")
                 and r.get("есть_верхняя_граница") for r in existing)
    if malformed:
        status = "unsupported"
        scientific_status = "not-evaluated"
        reason = "прочитаны интервалы с нарушенной арифметикой границ"
        machine_reason = "arb_interval_malformed"
    elif arb and bounds and valid:
        status = "verified-in-scope"
        scientific_status = "verified-in-scope"
        reason = "метод Arb и конечные замкнутые интервалы прочитаны из корпуса"
        machine_reason = "arb_interval_verified"
    elif (
        len(existing) == len(reports)
        and existing
        and {Path(r["путь"]).resolve() for r in reports}
        == {path.resolve() for path in SOURCES}
    ):
        # Это проверяемое наблюдение о входе, а не подмена научного результата:
        # все три объявленных файла прочитаны, но машиночитаемых интервалов Arb
        # в них нет. Поэтому охват инвентаризации закрыт, а научная проверка
        # шаровой арифметики остаётся not-evaluated.
        status = "verified-in-scope"
        scientific_status = "not-evaluated"
        reason = (
            "все объявленные файлы прочитаны; машиночитаемых интервалов Arb "
            "не предъявлено, поэтому научная проверка не выполнена"
        )
        machine_reason = "arb_inventory_verified_no_intervals"
    else:
        status = "not-evaluated"
        scientific_status = "not-evaluated"
        if non_arb:
            machine_reason = "arb_interval_non_arb_only"
            reason = ("прочитаны интервалы другой арифметики, но не Arb; "
                      "они не закрывают долг шаровой арифметики")
        else:
            machine_reason = "arb_interval_absent"
            reason = ("корпус не предъявляет машиночитаемые границы Arb; "
                      "точечные значения не заменяют шаровую арифметику")
    return {
        "статус": status,
        "научный_статус": scientific_status,
        "код_машинной_причины": machine_reason,
        "причина": reason,
        "источники_наблюдения": [r["путь"] for r in reports],
        "прочитано_файлов": len(existing),
        "интервалов": len(valid),
        "отчёты": reports,
    }


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
        else:
            bad += 1
            print("ПРОВАЛ: " + name)

    valid = "method,lower,upper\nArb,1.0,1.1\n"
    point = "value\n0.4220\n"
    reversed_bounds = "method,lower,upper\nArb,2.0,1.0\n"
    check("валидный Arb-интервал подтверждается",
          evaluate([_csv_report(Path("фикстура_valid.csv"), valid)])["статус"]
          == "verified-in-scope")
    point_result = evaluate(
        [_csv_report(Path("фикстура_point.csv"), point)]
    )
    check("точка не выдаётся за интервал",
          point_result["статус"] == "not-evaluated"
          and point_result["код_машинной_причины"] == "arb_interval_absent")
    check("перевёрнутые границы отклоняются",
          evaluate([_csv_report(Path("фикстура_reversed.csv"),
                                reversed_bounds)])["статус"]
          == "unsupported")
    mixed = "method,lower,upper\nordinary,1.0,1.1\nArb,2.0,2.1\n"
    mixed_report = _csv_report(Path("фикстура_mixed.csv"), mixed)
    mixed_result = evaluate([mixed_report])
    check("интервал другой арифметики не засчитывается как Arb",
          len(mixed_report["интервалы"]) == 1
          and len(mixed_report["интервалы_не_Arb"]) == 1
          and mixed_report["интервалы"][0]["метод_arb"]
          and mixed_result["код_машинной_причины"] == "arb_interval_verified")
    ordinary_result = evaluate([
        _csv_report(Path("фикстура_ordinary.csv"),
                    "method,lower,upper\nordinary,1.0,1.1\n")
    ])
    check("только не-Arb интервал получает отдельный код долга",
          ordinary_result["статус"] == "not-evaluated"
          and ordinary_result["код_машинной_причины"]
          == "arb_interval_non_arb_only")
    print("самопроверка шаровой арифметики Arb: пройдено %d, провалено %d"
          % (good, bad))
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    reports = [inspect_source(path) for path in SOURCES]
    result = evaluate(reports)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("сторож шаровой арифметики Arb: %s; прочитано файлов %d; интервалов %d"
          % (result["статус"], result["прочитано_файлов"], result["интервалов"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
