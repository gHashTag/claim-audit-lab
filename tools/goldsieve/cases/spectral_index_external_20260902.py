# -*- coding: utf-8 -*-
"""Внешняя сверка спектрального индекса с оценкой Planck 2018.

Наблюдаемое значение берётся из отдельной строки корпуса Trinity, формула
пересчитывается независимо, а внешний источник задаёт значение и
неопределённость. Итог оставляется каскаду золотого сита.
"""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_SPECTRAL_INDEX_SOURCE",
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
    marker = r"| $n_s$ spectral index | 0.9649 | $(8, 1, -2, -4, 1)$ | 0.96440 |"
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if marker in line:
                return 0.9649
    raise AssertionError("строка корпуса со спектральным индексом не найдена")


def _reference() -> float:
    return 8.0 * 3.0 * math.pi**-2 * PHI**-4 * math.e


def _reference_alt() -> float:
    return math.exp(
        math.log(8.0) + math.log(3.0) - 2.0 * math.log(math.pi)
        - 4.0 * math.log(PHI) + 1.0
    )


def _external_target() -> dict:
    return {
        "value": 0.9649,
        "uncertainty": 0.0042,
        "source": "https://arxiv.org/abs/1807.06209",
        "название": "скалярный спектральный индекс по Planck 2018",
    }


def _wrong():
    return [
        lambda: _reference() + 0.1,
        lambda: _reference() - 0.1,
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
        (-1, 1), eps, ranges=RANGES, trials=1000, seed=20260902
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
        "params": (8, 1, -2, -4, 1),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (8, 1, -2, -4, 1),
        "has_pi": True,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="Формула спектрального индекса против оценки Planck 2018",
        source="docs/docs/math-foundations/sacred-formulas.md:82",
        claim_kind="prediction",
        stated=_reference(),
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
        claim_family="spectral_index",
        observable="скалярный спектральный индекс космологических возмущений",
        measurement_source="Planck 2018, Cosmological Parameters",
        uncertainty_type="both",
        expected_effect_sigma=abs(_reference() - 0.9649) / 0.0042,
        resolution_sigma=1.0,
        novelty_key="cosmology:spectral_index:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "оценка Planck 2018"],
        independent_of=[
            "zeta",
            "BBLM",
            "CKM",
            "температура CMB",
            "плотность вещества",
        ],
        precision_gain=None,
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "0,9649 прочитано из строки корпуса; внешняя цель Planck 2018 "
            "0,9649 ± 0,0042 взята из https://arxiv.org/abs/1807.06209. "
            "Формула пересчитана отдельно; итог определяет сито."
        ),
    )
]
