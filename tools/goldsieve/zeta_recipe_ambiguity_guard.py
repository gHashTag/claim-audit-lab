#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож неоднозначности рецепта наблюдаемого zeta.

Если несколько законных вариантов развёртки и оценки разброса воспроизводят
одно и то же число из корпуса, совпадение не выбирает рецепт. Сторож читает
паспорт и оставляет такой случай ``not-evaluated`` вместо превращения
множества допустимых рецептов в находку.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "zeta_recipe_ambiguity_guard.json"
PASSPORT = HERE / "zeta_passport.py"
OBSERVED_DISPLAY_TOLERANCE = 5.0e-5


def _variant_number(value: object) -> float | None:
    """Извлечь проверяемое число варианта, не принимая одно описание."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, dict):
        number = value.get("std")
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            return None
        number = float(number)
    else:
        return None
    return number if math.isfinite(number) else None


def _recomputed_hits(observed: object, variants: object) -> list[str]:
    """Пересчитать попадания из числа, а не доверять списку паспорта."""
    if (isinstance(observed, bool)
            or not isinstance(observed, (int, float))
            or not math.isfinite(float(observed))
            or not isinstance(variants, dict)):
        return []
    result: list[str] = []
    for name, value in variants.items():
        number = _variant_number(value)
        if number is not None and abs(number - float(observed)) <= OBSERVED_DISPLAY_TOLERANCE:
            result.append(name)
    return result


def evaluate(
    source: str,
    observed: object,
    variants: dict[str, object],
    hits: list[str],
) -> dict:
    """Классифицировать число воспроизводящих рецептов без научного вывода."""
    variant_count = len(variants) if isinstance(variants, dict) else 0
    hit_names = list(hits) if isinstance(hits, list) else []
    recomputed_hits = _recomputed_hits(observed, variants)
    source_is_file = (
        isinstance(source, str)
        and bool(source)
        and Path(source).is_file()
    )
    malformed = (
        not isinstance(variants, dict)
        or not isinstance(hits, list)
        or any(not isinstance(name, str) for name in hit_names)
        or len(set(hit_names)) != len(hit_names)
        or any(
            _variant_number(variants.get(name)) is None
            for name in hit_names
            if isinstance(variants, dict) and name in variants
        )
    )
    unknown = (
        [name for name in hit_names if name not in variants]
        if isinstance(variants, dict)
        else []
    )
    hits_consistent = (
        isinstance(variants, dict)
        and not malformed
        and set(hit_names) == set(recomputed_hits)
    )
    observed_is_number = (
        isinstance(observed, (int, float))
        and not isinstance(observed, bool)
        and math.isfinite(float(observed))
    )
    all_variants_numeric = (
        isinstance(variants, dict)
        and bool(variants)
        and all(_variant_number(value) is not None
                for value in variants.values())
    )
    # Это отдельный статус входа, а не вердикт о выборе рецепта. Он означает
    # только, что настоящий файл наблюдения и полный числовой набор вариантов
    # прочитаны в пределах контракта. При нескольких попаданиях итоговый
    # ``статус`` ниже по-прежнему остаётся not-evaluated.
    input_status = (
        "verified-in-scope"
        if (source_is_file and observed_is_number and all_variants_numeric
            and not malformed and not unknown and hits_consistent)
        else ("unsupported" if malformed or unknown else "not-evaluated")
    )
    if malformed or unknown:
        status = "unsupported"
        details = []
        if malformed:
            details.append("варианты или попадания имеют неправильную форму")
        if unknown:
            details.append("попадания отсутствуют среди предъявленных вариантов")
        reason = "; ".join(details)
    elif not hits_consistent:
        status = "unsupported"
        reason = (
            "список попаданий паспорта расходится с независимым пересчётом "
            "при допуске напечатанного наблюдаемого"
        )
    elif not source:
        status = "not-evaluated"
        reason = "источник наблюдаемого не предъявлен"
    elif not source_is_file:
        status = "not-evaluated"
        reason = "источник наблюдаемого не является существующим файлом"
    elif not hit_names:
        status = "not-evaluated"
        reason = "ни один предъявленный вариант рецепта не воспроизводит наблюдаемое"
    elif len(hit_names) == 1:
        status = "verified-in-scope"
        reason = "наблюдаемое воспроизводит ровно один предъявленный вариант"
    else:
        status = "not-evaluated"
        reason = (
            "наблюдаемое воспроизводят несколько законных вариантов; "
            "рецепт не идентифицирован однозначно"
        )
    return {
        "статус": status,
        "статус_входа": input_status,
        "источник_наблюдения": source,
        "наблюдаемое": observed,
        "источник_является_файлом": source_is_file,
        "вариантов_рецепта": variant_count,
        "воспроизводящих_вариантов": len(hit_names),
        "воспроизводящие_варианты": hit_names,
        "пересчитанные_воспроизводящие_варианты": recomputed_hits,
        "список_попаданий_согласован": hits_consistent,
        "допуск_сопоставления": OBSERVED_DISPLAY_TOLERANCE,
        "причина": reason,
        "ограничение": (
            "сторож проверяет неоднозначность рецепта, но не оценивает "
            "истинность закона GUE"
        ),
    }


def _passport() -> dict:
    result = subprocess.run(
        [sys.executable, str(PASSPORT)],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "паспорт рецепта завершился кодом %d: %s"
            % (result.returncode, result.stderr[-500:])
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("вывод паспорта не является JSON") from exc


def scan() -> dict:
    report = _passport()
    observed = report.get("наблюдаемое_из_корпуса") or {}
    variants = report.get("варианты_рецепта") or {}
    hits = report.get("воспроизводят_0_4009") or {}
    result = evaluate(
        str(observed.get("source", "")),
        observed.get("value"),
        variants,
        list(hits),
    )
    result["паспорт_прочитан"] = True
    result["хеш_набора_нулей"] = (report.get("паспорт_рецепта") or {}).get("sha256")
    result["путь_набора_нулей"] = (report.get("паспорт_рецепта") or {}).get(
        "набор_нулей"
    )
    return result


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            bad += 1
            print("  ПРОВАЛ  " + name)

    with tempfile.TemporaryDirectory(prefix="zeta-recipe-ambiguity-") as tmp:
        source = str(Path(tmp) / "наблюдение.md")
        Path(source).write_text("| Std deviation | 0,4009 |\n", encoding="utf-8")
        different = evaluate(source, 0.4009, {"a": 0.40091}, ["a"])
        check(
            "один вариант получает verified-in-scope",
            different["статус"] == "verified-in-scope",
        )
        ambiguous = evaluate(
            source,
            0.4009,
            {"a": 0.40091, "b": 0.40092},
            ["a", "b"],
        )
        check(
            "два варианта получают not-evaluated",
            ambiguous["статус"] == "not-evaluated"
            and ambiguous["воспроизводящих_вариантов"] == 2
            and ambiguous["статус_входа"] == "verified-in-scope",
        )
        absent = evaluate(source, 0.4009, {"a": 0.40091}, [])
        check(
            "отсутствие попадания не становится покрытием",
            absent["статус"] in {"not-evaluated", "unsupported"}
            and absent["статус"] != "verified-in-scope",
        )
        unknown = evaluate(source, 0.4009, {"a": 0.40091}, ["не предъявлен"])
        check(
            "неизвестное попадание не становится покрытием",
            unknown["статус"] == "unsupported"
            and "отсутствуют" in unknown["причина"],
        )
        duplicate = evaluate(source, 0.4009, {"a": 0.40091}, ["a", "a"])
        check(
            "дубликат попадания не становится неоднозначностью",
            duplicate["статус"] == "unsupported",
        )
        missing_source = evaluate(
            str(Path(tmp) / "нет.md"), 0.4009, {"a": 0.40091}, ["a"]
        )
        check(
            "несуществующий источник не становится покрытием",
            missing_source["статус"] == "not-evaluated"
            and missing_source["статус_входа"] == "not-evaluated",
        )
        nonfinite = evaluate(source, 0.4009, {"a": float("nan")}, ["a"])
        check(
            "нечисловой вариант не становится покрытием",
            nonfinite["статус"] == "unsupported",
        )
        inconsistent = evaluate(source, 0.4009, {"a": 0.40091, "b": 0.9}, ["b"])
        check(
            "список попаданий перепроверяется независимо",
            inconsistent["статус"] == "unsupported"
            and inconsistent["пересчитанные_воспроизводящие_варианты"] == ["a"]
            and not inconsistent["список_попаданий_согласован"],
        )
    print(
        "самопроверка неоднозначности рецепта zeta: пройдено %d, провалено %d"
        % (good, bad)
    )
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    result = scan()
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "сторож неоднозначности рецепта zeta: %s; "
        "статус входа %s; воспроизводящих вариантов %d; источник %s"
        % (
            result["статус"],
            result["статус_входа"],
            result["воспроизводящих_вариантов"],
            result["источник_наблюдения"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
