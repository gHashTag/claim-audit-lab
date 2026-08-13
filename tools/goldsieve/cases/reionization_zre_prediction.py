# -*- coding: utf-8 -*-
"""Аудит предсказания красного смещения реионизации через внешнюю цель.

Сверяется не число, напечатанное рядом с формулой, а независимое измерение
Planck 2018: z_re = 7,67 +- 0,73. Все числа формулы пересчитываются здесь,
а окончательный вердикт выносит каскад золотого сита.
"""

from decimal import Decimal, ROUND_HALF_UP, localcontext
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/"
    "sacred-formulas.md"
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
DISPLAY_QUANTUM = Decimal("0.01")


def formula(n, k, m, p, q):
    return n * 3.0**k * math.pi**m * PHI**p * math.e**q


def reference():
    """Пересчитанный эталон с точностью, напечатанной в таблице корпуса."""
    raw = formula(2, -2, 4, 2, -2)
    return float(Decimal(str(raw)).quantize(DISPLAY_QUANTUM,
                                            rounding=ROUND_HALF_UP))


def _atan_decimal(x):
    total = Decimal(0)
    term = x
    power = x * x
    sign = Decimal(1)
    for denominator in range(1, 1200, 2):
        total += sign * term / Decimal(denominator)
        term *= power
        sign = -sign
    return total


def _pi_decimal():
    return (Decimal(16) * _atan_decimal(Decimal(1) / Decimal(5))
            - Decimal(4) * _atan_decimal(Decimal(1) / Decimal(239)))


def reference_alt():
    """Второй путь: Decimal, sqrt, exp и формула Машина для pi."""
    with localcontext() as ctx:
        ctx.prec = 80
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        raw = (Decimal(2) * Decimal(3) ** Decimal(-2) * _pi_decimal() ** 4
               * phi ** 2 * Decimal(1).exp() ** Decimal(-2))
        return float(raw.quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP))


def observed_from_corpus():
    """Извлечь заявленное табличное число, не вычисляя его из формулы."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "Reionization" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[2])
            if not match:
                raise ValueError("число z_re не найдено")
            return float(match.group(1))
    raise ValueError("строка Reionization не найдена")


def external_target():
    return {
        "value": 7.67,
        "uncertainty": 0.73,
        "source": "Planck 2018, https://arxiv.org/abs/1807.06209",
    }


def stated_target():
    return 7.67


def wrong_minus_one():
    return reference() - 1.0


def wrong_plus_one():
    return reference() + 1.0


def wrong_changed_phi_power():
    return float(Decimal(str(formula(2, -2, 4, 3, -2))).quantize(
        DISPLAY_QUANTUM, rounding=ROUND_HALF_UP))


def negative_control():
    """Негативный контроль: одна степень phi изменена, сигнал не воспроизводит."""
    return wrong_changed_phi_power()


def sample_from_corpus():
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    values = []
    for precision in (60, 80, 100):
        with localcontext() as ctx:
            ctx.prec = precision
            phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
            raw = (Decimal(2) * Decimal(3) ** Decimal(-2) * _pi_decimal() ** 4
                   * phi ** 2 * Decimal(1).exp() ** Decimal(-2))
            values.append(float(raw.quantize(DISPLAY_QUANTUM,
                                              rounding=ROUND_HALF_UP)))
    high = values[-1]
    return max(abs(value - high) for value in values) / abs(high)


def multiplicity():
    target = external_target()
    eps = target["uncertainty"] / abs(target["value"])
    ranges = {"n": range(1, 10), "k": range(-6, 7), "m": range(-4, 5),
              "p": range(-6, 7), "q": range(-4, 5)}
    fraction, expected = family.empirical_multiplicity(
        (-1, 4), eps, ranges=ranges, trials=600, seed=206)
    return {
        "expected_hits": expected,
        "p_global": fraction,
        "fraction_random_targets_hit": fraction,
    }


def mdl():
    """Сравнение стоимости описания члена с широкой полосой измерения."""
    eps = external_target()["uncertainty"] / external_target()["value"]
    match_bits = math.log2(1.0 / (2.0 * eps))
    description_bits = math.log2(123201.0)
    return {"description_bits": description_bits, "match_bits": match_bits}


def declared_domain():
    ranges = {"n": range(1, 10), "k": range(-6, 7), "m": range(-4, 5),
              "p": range(-6, 7), "q": range(-4, 5)}
    params = {"n": 2, "k": -2, "m": 4, "p": 2, "q": -2}
    return [(key, params[key], (min(values), max(values)))
            for key, values in ranges.items() if params[key] not in values]


def arithmetic():
    return {"params": (2, -2, 4, 2, -2),
            "rel_uncertainty": external_target()["uncertainty"]
            / external_target()["value"]}


def _selfcheck():
    assert reference() == 7.67
    assert reference_alt() == reference()
    assert observed_from_corpus() == 7.67
    assert abs(wrong_minus_one() - reference()) > 0.01
    assert abs(wrong_plus_one() - reference()) > 0.01
    assert abs(wrong_changed_phi_power() - reference()) > 0.01
    assert not declared_domain()


_selfcheck()


CLAIMS = [
    Claim(
        name="Формула реионизации z_re даёт 7,67",
        source="docs/docs/math-foundations/sacred-formulas.md:206",
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_changed_phi_power],
        null_model=negative_control,
        null_expect=wrong_changed_phi_power(),
        null_kind="negative",
        tolerance=0.0,
        sample=sample_from_corpus,
        statistics={"value": sample_mean},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        external_target=external_target,
        stated_target=stated_target,
        multiplicity=multiplicity,
        mdl=mdl,
        declared_domain=declared_domain,
        arithmetic=arithmetic,
        search_size=123201,
        inputs=[SOURCE],
        skip_reasons={
            "С6": "фиксированная закрытая формула, сетки и разрешения нет",
            "С7": "одно детерминированное вычисление, законных оценивателей нет",
            "С8": "входная погрешность не задана отдельно; внешняя погрешность учтена в С15",
            "С9": "это скалярное предсказание, а не выборочная оценка",
            "С11": "одна статистика, тест нескольких статистик неприменим",
            "С15": "внешняя цель уже подана; пропуск не ожидается",
            "С16": "внешняя цель и множественность проверяются отдельным полем",
            "С17": "MDL вычисляется в отдельном поле mdl",
            "С18": "объявленная область проверяется отдельным полем declared_domain",
            "С19": "арифметика проверяется полем arithmetic",
        },
        notes=(
            "Формула сопоставлена с Planck 2018, а не с напечатанным рядом "
            "числом. Внешняя цель имеет широкую погрешность 0,73, поэтому "
            "процентное совпадение само по себе не является свидетельством."
        ),
    )
]
