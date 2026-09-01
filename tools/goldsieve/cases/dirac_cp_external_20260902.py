# -*- coding: utf-8 -*-
"""Внешняя сверка формулы фазы Дирака CP с обзором PDG 2024.

Наблюдаемое извлекается из строки корпуса, эталон вычисляется независимо,
а внешняя оценка хранится с симметризованной неопределённостью. Итог
определяет каскад золотого сита; ноль сигм не считается подтверждением.
"""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_DIRAC_CP_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/"
    "sacred-formulas.md",
)
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _observed() -> float:
    marker = "| **Dirac CP phase** |"
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if marker in line and "| 222.0 |" in line:
                return 222.0
    raise AssertionError("строка корпуса для фазы Дирака CP не найдена")


def _reference() -> float:
    return 7.0 * 3.0**-2 * math.pi**4 * PHI**-4 * math.e**3


def _reference_alt() -> float:
    return math.exp(
        math.log(7.0) - 2.0 * math.log(3.0) + 4.0 * math.log(math.pi)
        - 4.0 * math.log(PHI) + 3.0
    )


def _external_target() -> dict:
    return {
        "value": 197.0,
        # PDG reports +42/-25 degrees; the scalar interface uses their
        # arithmetic mean as a conservative symmetric uncertainty.
        "uncertainty": 33.5,
        "source": "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-neutrino-mixing.pdf",
        "название": "фаза Дирака CP, наилучшая оценка при нормальном порядке",
    }


def _wrong():
    return [
        lambda: _reference() + 5.0,
        lambda: _reference() - 5.0,
        lambda: _reference() * 1.1,
    ]


def _positive():
    return _reference_alt()


def _sample():
    return [_observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance():
    a, b = _reference(), _reference_alt()
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _multiplicity():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    fraction, expected = family.empirical_multiplicity(
        (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260902
    )
    return {
        "expected_hits": expected,
        "p_global": fraction,
        "fraction_random_targets_hit": fraction,
        "search_size": SEARCH_SIZE,
    }


def _family_values():
    target = _external_target()
    low, high = target["value"] / 5.0, target["value"] * 5.0
    return [v for v in family.enumerate_family(RANGES) if low <= v <= high]


def _meff():
    target = _external_target()
    return {
        "values": _family_values(),
        "eps": target["uncertainty"] / abs(target["value"]),
        "sigma": abs((_reference() - target["value"]) / target["uncertainty"]),
        "search_size": SEARCH_SIZE,
    }


def _mdl():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    return {
        "description_bits": math.log2(SEARCH_SIZE),
        "match_bits": math.log2(1.0 / (2.0 * eps)),
    }


def _domain():
    assert family.declared_size(RANGES) == SEARCH_SIZE
    return []


def _arithmetic():
    target = _external_target()
    return {
        "params": (7, -2, 4, -4, 3),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (7, -2, 4, -4, 3),
        "has_pi": True,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="Формула фазы Дирака CP против внешней оценки PDG",
        source="docs/docs/math-foundations/sacred-formulas.md:202",
        claim_kind="prediction",
        stated=_reference,
        reference=_reference,
        observed=_observed,
        wrong=_wrong(),
        null_model=_positive,
        null_expect=_reference(),
        null_kind="positive",
        tolerance=1e-6,
        sample=_sample,
        statistics={"value": _mean},
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        external_target=_external_target,
        stated_target=_observed,
        multiplicity=_multiplicity,
        mdl=_mdl,
        declared_domain=_domain,
        arithmetic=_arithmetic,
        meff=_meff,
        algebraic=_algebraic,
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        alpha=0.05,
        skip_reasons={
            "С6": "формула замкнута; сеток и разрешений нет",
            "С7": "один детерминированный оцениватель",
            "С8": "погрешность формулы не задана; внешняя погрешность проверяется С15",
            "С9": "формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        claim_family="dirac_cp_phase",
        observable="фаза Дирака CP (градусы)",
        measurement_source="PDG 2024, обзор нейтринного смешивания",
        uncertainty_type="both",
        expected_effect_sigma=0.75,
        resolution_sigma=1.0,
        novelty_key="neutrino:dirac_cp_phase:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "оценка PDG 2024"],
        independent_of=["zeta", "BBLM", "CKM", "нейтринные углы смешивания"],
        precision_gain=None,
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "222.0 прочитано из строки корпуса; внешняя оценка PDG "
            "197 +42/-25 градусов симметризована до 197 ±33.5 градусов. "
            "Сигмы и множественность остаются отдельными координатами."
        ),
    )
]
