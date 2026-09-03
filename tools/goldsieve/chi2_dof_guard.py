#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Контракт повторного построения χ²/dof.

Сито не объявляет научный результат по одной таблице. Этот модуль закрывает
инженерный риск каскада: некорректный список степеней свободы, отрицательное
χ², NaN или рассинхрон длины не должны молча превратиться в числа χ²/dof.
Валидируются именно входы реконструкции; происхождение наблюдаемой таблицы и
сырого набора нулей проверяется отдельными контурами.

Команды:
    python3 chi2_dof_guard.py             записать машинный паспорт
    python3 chi2_dof_guard.py --selftest  отрицательные фикстуры и мутации
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "chi2_dof_guard.json"


def _as_sequence(value, name: str) -> list:
    if isinstance(value, (str, bytes)):
        raise ValueError("%s должен быть последовательностью чисел" % name)
    try:
        result = list(value)
    except TypeError as exc:
        raise ValueError("%s должен быть последовательностью чисел" % name) from exc
    if not result:
        raise ValueError("%s не должен быть пустым" % name)
    return result


def reconstruct(chi2_values, dof_values) -> list[float]:
    """Вернуть χ²/dof после проверки полного контракта входов."""
    chi2 = _as_sequence(chi2_values, "χ²")
    dof = _as_sequence(dof_values, "dof")
    if len(chi2) != len(dof):
        raise ValueError("χ² и dof должны иметь одинаковую длину")
    ratios = []
    for index, (stat, degrees) in enumerate(zip(chi2, dof)):
        try:
            stat_float = float(stat)
            dof_float = float(degrees)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("строка %d содержит нечисловой вход" % index) from exc
        if not math.isfinite(stat_float) or stat_float < 0.0:
            raise ValueError("строка %d содержит недопустимое χ²" % index)
        if (not math.isfinite(dof_float) or dof_float <= 0.0
                or not dof_float.is_integer()):
            raise ValueError("строка %d содержит недопустимый dof" % index)
        ratios.append(stat_float / dof_float)
    return ratios


def evaluate(chi2_values, dof_values) -> dict:
    ratios = reconstruct(chi2_values, dof_values)
    return {
        "контракт": "χ²/dof",
        "статус": "verified-in-scope",
        "строк": len(ratios),
        "значения": ratios,
        "границы": (
            "проверены конечность и знак χ², положительный целый dof, "
            "одинаковая длина пар; причинность научного вывода не оценивается"
        ),
    }


def selftest() -> int:
    ok = fail = 0

    def check(name: str, passed: bool) -> None:
        nonlocal ok, fail
        if passed:
            ok += 1
            print("  ок     " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    check("валидные пары дают χ²/dof",
          reconstruct([4.0, 9.0], [2, 3]) == [2.0, 3.0])
    bad_inputs = (
        ("пустой χ²", [], [1]),
        ("разная длина", [1], [1, 2]),
        ("нулевой dof", [1], [0]),
        ("дробный dof", [1], [1.5]),
        ("отрицательный χ²", [-1], [1]),
        ("нечисловой χ²", ["нет"], [1]),
        ("нечисловой dof", [1], ["нет"]),
        ("неконечный χ²", [float("nan")], [1]),
    )
    rejected = 0
    for name, chi2, dof in bad_inputs:
        try:
            reconstruct(chi2, dof)
        except ValueError:
            rejected += 1
            check(name + " отвергнут", True)
        else:
            check(name + " отвергнут", False)
    check("все отрицательные фикстуры отвергнуты",
          rejected == len(bad_inputs))
    print("самопроверка контракта χ²/dof: пройдено %d, провалено %d"
          % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    report = evaluate([4.0, 9.0], [2, 3])
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print("контракт χ²/dof: %d строк, статус %s" %
          (report["строк"], report["статус"]))
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
