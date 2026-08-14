# -*- coding: utf-8 -*-
"""Аудит двух предсказаний из formulas.md против внешних измерений.

Числа корпуса используются только как observed. Эталон вычисляется из
формулы, а внешние цели взяты из независимых публикаций с погрешностями.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_FORMULAS_PRECISION_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/formulas.md",
)
SEARCH_SIZE = 123201
PHI = (1.0 + math.sqrt(5.0)) / 2.0
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}


def _require_markers(markers):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)


def g2_reference():
    return (math.pi - 3.0) * 1.0e-9


def g2_reference_alt():
    return math.exp(math.log(math.pi - 3.0) - math.log(1.0e9))


def g2_observed():
    _require_markers([
        "**Δa<sub>μ</sub> = 251 × 10⁻¹¹**",
        "| Measured (FNAL E989) | 251 ± 59 × 10⁻¹¹ |",
        "**Formula**: Δa<sub>μ</sub> = (π - 3) × 10⁻⁹",
    ])
    return 251.0e-11


def g2_target():
    return {
        "value": 251.0e-11,
        "uncertainty": 59.0e-11,
        "source": (
            "Fermilab Muon g-2, arXiv:2311.12730, "
            "https://arxiv.org/abs/2311.12730"
        ),
    }


def proton_radius_reference():
    return PHI / (math.pi + 1.0)


def proton_radius_reference_alt():
    return math.exp(math.log(PHI) - math.log(math.pi + 1.0))


def proton_radius_observed():
    _require_markers([
        "**r<sub>p</sub> = 0.841 ± 0.007 fm**",
        "| Measured | 0.8414(19) fm (muonic H) |",
        "**Formula**: r<sub>p</sub> = φ / (π + 1) fm",
    ])
    return 0.841


def proton_radius_target():
    return {
        "value": 0.84087,
        "uncertainty": 0.00039,
        "source": (
            "Pohl et al., Proton size from precision experiments on hydrogen "
            "and muonic hydrogen atoms, arXiv:2009.11520, "
            "https://arxiv.org/abs/2009.11520"
        ),
    }


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() * 1.01,
    ]


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _multiplicity(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        fraction, expected = family.empirical_multiplicity(
            (-1, 4), eps, ranges=RANGES, trials=1000, seed=20260814
        )
        return {
            "expected_hits": expected,
            "p_global": fraction,
            "fraction_random_targets_hit": fraction,
            "search_size": SEARCH_SIZE,
        }
    return run


def _family_values(target):
    values = family.enumerate_family(RANGES)
    tgt = target()
    low = float(tgt["value"]) / 5.0
    high = float(tgt["value"]) * 5.0
    return [value for value in values if low <= value <= high]


def _meff(target, reference):
    def run():
        tgt = target()
        return {
            "values": _family_values(target),
            "eps": float(tgt["uncertainty"]) / abs(float(tgt["value"])),
            "sigma": abs((reference() - tgt["value"]) / tgt["uncertainty"]),
            "search_size": SEARCH_SIZE,
        }
    return run


def _mdl(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        return {
            "description_bits": math.log2(SEARCH_SIZE),
            "match_bits": math.log2(1.0 / (2.0 * eps)),
        }
    return run


def _domain():
    assert family.declared_size(RANGES) == SEARCH_SIZE
    return []


def _algebraic(target, coeffs, has_pi, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": coeffs,
            "has_pi": has_pi,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": 12,
            "free_coeff_limit": 6,
        }
    return run


def _arithmetic(params, target):
    def run():
        tgt = target()
        return {
            "params": params,
            "rel_uncertainty": abs(tgt["uncertainty"] / tgt["value"]),
        }
    return run


def _claim(name, source_line, reference, alternate, observed, target,
           stated_target, params, has_pi, notes):
    return Claim(
        name=name,
        source=source_line,
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        # Позитивный контроль получает эталон по независимому маршруту log/exp.
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1.0e-6,
        sample=_sample(observed),
        statistics={"value": _mean},
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        external_target=target,
        stated_target=stated_target,
        multiplicity=_multiplicity(target),
        mdl=_mdl(target),
        declared_domain=_domain,
        arithmetic=_arithmetic(params, target),
        meff=_meff(target, reference),
        algebraic=_algebraic(target, params, has_pi, reference),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; погрешность внешней цели проверяется отдельно",
            "С9": "детерминированная формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        notes=(
            "Внешняя цель отделена от числа корпуса; число из строки корпуса "
            "используется только как observed. Порог С15 выводится по Шидаку из "
            "search_size=123201. Сигмы, множественность, MDL, С20 и С21 остаются "
            "раздельными координатами. " + notes
        ),
    )


def _selfcheck():
    for reference, alternate in (
        (g2_reference, g2_reference_alt),
        (proton_radius_reference, proton_radius_reference_alt),
    ):
        assert abs(reference() - alternate()) / abs(reference()) < 1.0e-12
        assert all(abs(w() - reference()) > 1.0e-12 for w in _wrong(reference))
    assert abs(g2_reference() - 251.0e-11) > 1.0e-12
    assert abs(proton_radius_reference() - 0.841) > 1.0e-3
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []
    for target in (g2_target, proton_radius_target):
        assert target()["uncertainty"] > 0
        assert "https://" in target()["source"]


_selfcheck()

CLAIMS = [
    _claim(
        "Формула Δaμ = (π−3)×10⁻⁹ согласуется с измерением FNAL E989",
        "docs/docs/math-foundations/formulas.md:305-319",
        g2_reference,
        g2_reference_alt,
        g2_observed,
        g2_target,
        lambda: 251.0e-11,
        (1, 0, 0, 0, 0),
        True,
        "Внешняя цель: (251 ± 59)×10⁻¹¹, разность измерения и теории в публикации Fermilab.",
    ),
    _claim(
        "Формула rₚ = φ/(π+1) согласуется с измерением радиуса протона",
        "docs/docs/math-foundations/formulas.md:321-333",
        proton_radius_reference,
        proton_radius_reference_alt,
        proton_radius_observed,
        proton_radius_target,
        lambda: 0.841,
        (1, 0, 0, 0, 0),
        True,
        "Внешняя цель: 0,84087 ± 0,00039 фм, спектроскопия мюонного водорода.",
    ),
]
