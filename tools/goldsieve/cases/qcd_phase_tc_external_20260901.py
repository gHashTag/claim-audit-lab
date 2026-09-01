# -*- coding: utf-8 -*-
"""Внешняя проверка формулы температуры кроссовера КХД.

Число observed читается из строки корпуса; reference вычисляется из формулы.
Внешняя цель взята из отдельной работы HotQCD и не является числом корпуса.
"""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_QCD_TC_SOURCE",
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
            if "| QCD phase $T_c$ |" in line and "| 156.5 |" in line:
                return 156.5
    raise AssertionError("строка корпуса QCD phase $T_c$ со значением 156.5 не найдена")


def _exact_reference() -> float:
    return 7.0 * math.pi * PHI**2 * math.e


def _reference() -> float:
    # Корпус печатает T_c с одним знаком после запятой.
    return round(_exact_reference(), 1)


def _reference_alt() -> float:
    with __import__("decimal").localcontext() as ctx:
        ctx.prec = 60
        dec = __import__("decimal").Decimal
        phi = (dec(1) + dec(5).sqrt()) / dec(2)
        exact = dec(7) * dec(str(math.pi)) * phi**2 * dec(1).exp()
        return float(exact.quantize(dec("0.1")))


def _external_target() -> dict:
    return {
        "value": 156.5,
        "uncertainty": 1.5,
        "source": (
            "HotQCD, Chiral crossover in QCD, "
            "https://arxiv.org/abs/1812.08235"
        ),
        "название": "псевдокритическая температура при μB=0",
    }


def _wrong():
    return [
        lambda: _reference() + 10.0,
        lambda: _reference() - 10.0,
        lambda: _reference() * 1.1,
    ]


def _positive():
    return _reference_alt()


def _sample():
    return [_observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance():
    return max(abs(_reference() - _reference_alt()) / abs(_reference()),
               2.0 * math.ulp(_reference()) / abs(_reference()))


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
        "params": (7, 0, 1, 2, 1),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (7, 0, 1, 2, 1),
        "has_pi": True,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="Формула T_c = 7·π·φ²·e против внешнего значения HotQCD",
        source="docs/docs/math-foundations/sacred-formulas.md:201",
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
        claim_family="qcd_transition",
        observable="псевдокритическая температура T_c (МэВ)",
        measurement_source="HotQCD, arXiv:1812.08235",
        uncertainty_type="both",
        expected_effect_sigma=0.0,
        resolution_sigma=1.0,
        novelty_key="qcd:transition_temperature:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "внешняя оценка HotQCD"],
        independent_of=["zeta", "BBLM", "CKM", "нейтринное смешивание"],
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "156.5 прочитано из указанной строки корпуса; внешняя цель "
            "156.5 ± 1.5 МэВ прочитана из HotQCD отдельно. Нулевое "
            "отклонение не превращается в новый подтверждённый вердикт: "
            "сито отдельно учитывает множественность."
        ),
    )
]
