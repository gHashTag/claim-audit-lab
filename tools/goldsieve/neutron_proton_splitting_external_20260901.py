# -*- coding: utf-8 -*-
"""Внешний аудит формулы разности масс нейтрона и протона.

Наблюдаемое значение читается из строки корпуса, а внешний эталон NIST
хранится отдельно. Никакой новый простой вердикт или подтверждение не
выпускается: итог отдаётся каскаду золотого сита.
"""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_NEUTRON_PROTON_SOURCE",
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
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "| $\\Delta m(n{-}p)$ (MeV) |" in line and "| 1.2934 |" in line:
                return 1.2934
    raise AssertionError("строка корпуса разности масс нейтрона и протона не найдена")


def _reference() -> float:
    return 4.0 * 3.0**2 * math.pi**-2 * PHI**2 * math.e**-2


def _reference_alt() -> float:
    return math.exp(
        math.log(4.0) + 2.0 * math.log(3.0) - 2.0 * math.log(math.pi)
        + 2.0 * math.log(PHI) - 2.0
    )


def _external_target() -> dict:
    return {
        "value": 1.29333251,
        "uncertainty": 0.00000038,
        "source": (
            "NIST/CODATA, neutron-proton mass difference energy equivalent, "
            "https://physics.nist.gov/cgi-bin/cuu/Value?mnmmpc2mev"
        ),
        "название": "энергетический эквивалент разности масс нейтрона и протона",
    }


def _wrong():
    return [
        lambda: _reference() + 0.1,
        lambda: _reference() - 0.1,
        lambda: _reference() * 1.01,
    ]


def _positive():
    return _reference_alt()


def _sample():
    return [_observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance():
    return max(
        abs(_reference() - _reference_alt()) / abs(_reference()),
        2.0 * math.ulp(_reference()) / abs(_reference()),
    )


def _multiplicity():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    fraction, expected = family.empirical_multiplicity(
        (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260901
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
        "params": (4, 2, -2, 2, -2),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (4, 2, -2, 2, -2),
        "has_pi": True,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="Формула разности масс нейтрона и протона согласуется с внешним значением NIST",
        source="docs/docs/math-foundations/sacred-formulas.md:206",
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
        claim_family="neutron_proton_mass_splitting",
        observable="разность масс нейтрона и протона (МэВ)",
        measurement_source="NIST/CODATA",
        uncertainty_type="both",
        expected_effect_sigma=2453.97,
        resolution_sigma=1.0,
        novelty_key="neutron:proton_mass_splitting:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "NIST/CODATA"],
        independent_of=["zeta", "BBLM", "CKM", "нейтринное смешивание"],
        precision_gain=None,
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "1.2934 прочитано из строки корпуса; внешняя цель "
            "1.29333251 ± 0.00000038 МэВ отделена URL NIST. "
            "Большое расхождение проверяется ситом и не является новым "
            "подтверждённым вердиктом."
        ),
    )
]
