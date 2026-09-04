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
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "zeta_recipe_ambiguity_guard.json"
PASSPORT = HERE / "zeta_passport.py"


def evaluate(
    source: str,
    observed: object,
    variants: dict[str, object],
    hits: list[str],
) -> dict:
    """Классифицировать число воспроизводящих рецептов без научного вывода."""
    if not source:
        status = "not-evaluated"
        reason = "источник наблюдаемого не предъявлен"
    elif not hits:
        status = "not-evaluated"
        reason = "ни один предъявленный вариант рецепта не воспроизводит наблюдаемое"
    elif len(hits) == 1:
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
        "источник_наблюдения": source,
        "наблюдаемое": observed,
        "вариантов_рецепта": len(variants),
        "воспроизводящих_вариантов": len(hits),
        "воспроизводящие_варианты": list(hits),
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
        different = evaluate(source, 0.4009, {"a": 0.4}, ["a"])
        check(
            "один вариант получает verified-in-scope",
            different["статус"] == "verified-in-scope",
        )
        ambiguous = evaluate(
            source,
            0.4009,
            {"a": 0.4, "b": 0.4},
            ["a", "b"],
        )
        check(
            "два варианта получают not-evaluated",
            ambiguous["статус"] == "not-evaluated"
            and ambiguous["воспроизводящих_вариантов"] == 2,
        )
        absent = evaluate(source, 0.4009, {"a": 0.4}, [])
        check(
            "отсутствие попадания не становится покрытием",
            absent["статус"] == "not-evaluated",
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
        "воспроизводящих вариантов %d; источник %s"
        % (
            result["статус"],
            result["воспроизводящих_вариантов"],
            result["источник_наблюдения"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
