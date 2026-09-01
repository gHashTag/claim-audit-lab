# -*- coding: utf-8 -*-
"""Аудит формулы H₀ из таблицы космологических параметров Trinity.

Наблюдаемое число читается из файла корпуса, а внешний эталон — из публикации
Planck. Формула пересчитывается из параметров таблицы и не берёт число из
строки Computed. Цель добавлена для проверки реальной разрешающей способности
сита после запрета вырожденных внешних сверок.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_H0_EXTERNAL",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md",
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}


def _row():
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    marker = "| $H_0$ (km/s/Mpc) | 67.40 | $(4, 3, -3, 2, 2)$ | 67.381 |"
    if marker not in text:
        raise AssertionError("строка H₀ с наблюдаемым значением не найдена")
    return 67.40


def reference():
    # (n, k, m, p, q) = (4, 3, -3, 2, 2)
    return 4.0 * 3.0**3 * math.pi**-3 * PHI**2 * math.e**2


def reference_alt():
    # Независимая логарифмическая сборка той же формулы.
    return math.exp(
        math.log(4.0) + 3.0 * math.log(3.0) - 3.0 * math.log(math.pi)
        + 2.0 * math.log(PHI) + 2.0
    )


def positive_control():
    # Контроль строится отдельно от строки корпуса.
    return math.exp(
        math.log(4.0) + math.log(27.0) - math.log(math.pi**3)
        + math.log(PHI**2) + 2.0
    )


def _wrong():
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 1.0,
    ]


def _mean(values):
    return float(sum(values) / len(values))


def _sample():
    return [_row()]


def external_target():
    return {
        "value": 67.4,
        "uncertainty": 0.5,
        "source": (
            "Planck 2018, космологические параметры, "
            "https://doi.org/10.1051/0004-6361/201833910"
        ),
    }


def stated_target():
    return _row()


def multiplicity():
    target = external_target()
    eps = target["uncertainty"] / abs(target["value"])
    fraction, expected = family.empirical_multiplicity(
        (-12, 12), eps, ranges=RANGES, trials=1000, seed=20260823
    )
    return {
        "expected_hits": expected,
        "p_global": fraction,
        "fraction_random_targets_hit": fraction,
        "search_size": SEARCH_SIZE,
    }


def declared_domain():
    assert family.declared_size(RANGES) == SEARCH_SIZE
    return []


def mdl():
    target = external_target()
    eps = target["uncertainty"] / abs(target["value"])
    return {
        "description_bits": math.log2(SEARCH_SIZE),
        "match_bits": math.log2(1.0 / (2.0 * eps)),
    }


def arithmetic():
    target = external_target()
    return {
        "params": (4, 3, -3, 2, 2),
        "rel_uncertainty": target["uncertainty"] / abs(target["value"]),
    }


def meff():
    target = external_target()
    eps = target["uncertainty"] / abs(target["value"])
    values = family.enumerate_family(RANGES)
    low, high = target["value"] / 5.0, target["value"] * 5.0
    return {
        "values": [v for v in values if low <= v <= high],
        "eps": eps,
        "sigma": abs((reference() - target["value"]) / target["uncertainty"]),
        "search_size": SEARCH_SIZE,
    }


def algebraic():
    target = external_target()
    return {
        "target": target["value"],
        "coeffs": (4, 3, -3, 2, 2),
        "has_pi": True,
        "rel_deviation": abs(reference() - target["value"]) / abs(target["value"]),
        "max_coeff": 4,
        "free_coeff_limit": 6,
    }


_SKIP = {
    "С6": "замкнутая формула; независимая сетка или разрешение отсутствуют",
    "С7": "один законный оцениватель; альтернативные оценки не заданы",
    "С8": "погрешность входа формулы не задана; внешняя погрешность учтена в С15",
    "С9": "детерминированная формула; конечная выборка неприменима",
    "С11": "одна внешняя статистика; проверка нескольких статистик неприменима",
}


assert abs(reference() - reference_alt()) < 1e-13
assert abs(reference() - positive_control()) < 1e-13
assert all(abs(w() - reference()) > 1e-8 for w in _wrong())
assert family.declared_size(RANGES) == SEARCH_SIZE

CLAIMS = [
    Claim(
        name="Формула H₀ = 4·3³·π⁻³·φ²·e² согласуется с Planck",
        source="docs/docs/math-foundations/sacred-formulas.md:74",
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=_row,
        wrong=_wrong(),
        null_model=positive_control,
        null_expect=reference(),
        null_kind="positive",
        tolerance=0.01,
        sample=_sample,
        statistics={"value": _mean},
        reference_alt=reference_alt,
        alt_tolerance=lambda: max(
            abs(reference() - reference_alt()) / abs(reference()),
            2.0 * math.ulp(reference()) / abs(reference()),
        ),
        external_target=external_target,
        stated_target=stated_target,
        multiplicity=multiplicity,
        mdl=mdl,
        declared_domain=declared_domain,
        arithmetic=arithmetic,
        meff=meff,
        algebraic=algebraic,
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons=dict(_SKIP),
        notes=(
            "Наблюдаемое 67,40 прочитано из корпуса, формула пересчитана "
            "из параметров (4, 3, −3, 2, 2), внешняя цель Planck имеет "
            "значение 67,4 ± 0,5; отклонение в сигмах и множественность "
            "учтены раздельно."
        ),
    )
]
