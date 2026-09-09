# -*- coding: utf-8 -*-
"""Аудит предсказания G из гравитационной сводки Trinity.

Число из корпуса используется только как observed/stated_target. Эталон
вычисляется из определения phi и формулы G = pi^3 gamma^2 / phi при
 gamma = phi^-3; внешняя цель берётся из CODATA, а не из той же строки.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_G_EXTERNAL",
    "/home/user/workspace/corpus/trinity/docs/docs/research/papers/gravitational-constants.md",
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
GAMMA = PHI ** -3
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}


def _read():
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    if "G = π³γ²/φ" not in text or "6.674×10⁻¹¹" not in text:
        raise AssertionError("строка предсказания G не найдена в корпусе")
    return 6.674e-11


def reference():
    return math.pi ** 3 * GAMMA ** 2 / PHI


def reference_alt():
    # Независимый маршрут: логарифмическая сборка произведения.
    return math.exp(3.0 * math.log(math.pi) + 2.0 * math.log(GAMMA) - math.log(PHI))


def positive_control():
    # Контроль не читает observed и не использует печатное значение корпуса.
    gamma = math.exp(-3.0 * math.log(PHI))
    return math.exp(3.0 * math.log(math.pi) + 2.0 * math.log(gamma) - math.log(PHI))


def _wrong():
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 1.0,
    ]


def _mean(values):
    return float(sum(values) / len(values))


def _sample():
    return [_read()]


def external_target():
    return {
        "value": 6.67430e-11,
        "uncertainty": 1.5e-15,
        "source": (
            "CODATA 2022, Newtonian constant of gravitation, "
            "https://physics.nist.gov/cuu/Constants/"
        ),
    }


def stated_target():
    return _read()


def multiplicity():
    target = external_target()
    eps = target["uncertainty"] / abs(target["value"])
    fraction, expected = family.empirical_multiplicity(
        (-12, 12), eps, ranges=RANGES, trials=1000, seed=20260814
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
        "params": (1, 0, 3, -7, 0),
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
        "coeffs": (1, 0, 3, -7, 0),
        "has_pi": True,
        "rel_deviation": abs(reference() - target["value"]) / abs(target["value"]),
        "max_coeff": 7,
        "free_coeff_limit": 6,
    }


_SKIP = {
    "С6": "замкнутая формула; независимая сетка или разрешение отсутствуют",
    "С7": "один законный оцениватель; альтернативные оценки не заданы",
    "С8": "погрешность входа формулы не задана; внешняя погрешность учтена в С15",
    "С9": "детерминированная формула; конечная выборка неприменима",
    "С11": "одна внешняя статистика; проверка нескольких статистик неприменима",
}


assert abs(reference() - reference_alt()) < 1e-14
assert abs(reference() - positive_control()) < 1e-14
assert all(abs(w() - reference()) > 1e-8 for w in _wrong())
assert family.declared_size(RANGES) == SEARCH_SIZE

CLAIMS = [
    Claim(
        name="Формула G = π³γ²/φ согласуется с CODATA",
        source="docs/docs/research/papers/gravitational-constants.md:10-15",
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=_read,
        wrong=_wrong(),
        null_model=positive_control,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1e-6,
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
            "Эталон строится из gamma=phi^-3 и не берёт число из строки Result. "
            "Внешняя цель — CODATA; сигмы, множественность и MDL остаются "
            "раздельными осями."
        ),
    )
]
