# -*- coding: utf-8 -*-
"""Аудит трёх формул CKM против внешнего обзора PDG 2024.

Числа из документа корпуса используются только как observed. Внешние цели
берутся из отдельного обзора PDG; проверка печатного числа рядом с формулой
не является внешним тестом.
"""
import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_MIXING_SOURCE",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/MIXING_MATRICES.md",
)
PDG_URL = "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf"
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEARCH_SIZE = 123201
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


def cabibbo_reference():
    return PHI ** -3


def theta23_reference():
    return 4.0 * 3.0 ** -2 * math.pi ** -2


def delta_reference():
    return math.pi * PHI ** -2


def cabibbo_reference_alt():
    return math.exp(-3.0 * math.log(PHI))


def theta23_reference_alt():
    return math.exp(math.log(4.0) - 2.0 * math.log(3.0)
                     - 2.0 * math.log(math.pi))


def delta_reference_alt():
    return math.exp(math.log(math.pi) - 2.0 * math.log(PHI))


def cabibbo_observed():
    _require_markers([
        "**Better formula**: sin θ_C = φ⁻³",
        "Experimental: 0.2265",
    ])
    return 0.2265


def theta23_observed():
    _require_markers([
        "**Hypothesis**: sin θ₂₃ = 4 × 3⁻² × π⁻²",
        "Experimental: 0.0405",
    ])
    return 0.0405


def delta_observed():
    _require_markers([
        "**Hypothesis**: δ = π/φ²",
        "Experimental: 1.196 rad = 68.5°",
    ])
    return 1.196


def cabibbo_target():
    return {
        "value": 0.22501,
        "uncertainty": 0.00068,
        "source": "PDG 2024, CKM matrix, " + PDG_URL,
    }


def theta23_target():
    return {
        "value": 0.04183,
        # Консервативно взята верхняя сторона асимметричной ошибки PDG.
        "uncertainty": 0.00079,
        "source": "PDG 2024, CKM matrix, " + PDG_URL,
    }


def delta_target():
    return {
        "value": 1.147,
        "uncertainty": 0.026,
        "source": "PDG 2024, CKM matrix, " + PDG_URL,
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
        # Позитивный контроль воспроизводит эталон через независимый маршрут
        # exp/log, а не возвращает значение из корпуса.
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
    refs = [
        (cabibbo_reference, cabibbo_reference_alt),
        (theta23_reference, theta23_reference_alt),
        (delta_reference, delta_reference_alt),
    ]
    for reference, alternate in refs:
        assert abs(reference() - alternate()) / abs(reference()) < 1.0e-12
        assert all(abs(w() - reference()) > 1.0e-6 for w in _wrong(reference))
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []
    for target in (cabibbo_target, theta23_target, delta_target):
        assert target()["uncertainty"] > 0
        assert "https://" in target()["source"]


_selfcheck()

CLAIMS = [
    _claim(
        "Формула sin θ_C = φ⁻³ согласуется с внешним значением PDG",
        "deploy/trinity-nexus/docs/research/MIXING_MATRICES.md:64-69",
        cabibbo_reference,
        cabibbo_reference_alt,
        cabibbo_observed,
        cabibbo_target,
        lambda: 0.2265,
        (1, 0, 0, -3, 0),
        False,
        "Внешняя цель PDG 2024: sin(θ₁₂) = 0,22501 ± 0,00068.",
    ),
    _claim(
        "Формула sin θ₂₃ = 4·3⁻²·π⁻² согласуется с внешним значением PDG",
        "deploy/trinity-nexus/docs/research/MIXING_MATRICES.md:71-77",
        theta23_reference,
        theta23_reference_alt,
        theta23_observed,
        theta23_target,
        lambda: 0.0405,
        (4, -2, -2, 0, 0),
        True,
        "Внешняя цель PDG 2024: sin(θ₂₃) = 0,04183 +0,00079/−0,00069; использована консервативная верхняя сторона ошибки.",
    ),
    _claim(
        "Формула δ = π/φ² согласуется с внешним значением PDG",
        "deploy/trinity-nexus/docs/research/MIXING_MATRICES.md:87-93",
        delta_reference,
        delta_reference_alt,
        delta_observed,
        delta_target,
        lambda: 1.196,
        (1, 0, 1, -2, 0),
        True,
        "Внешняя цель PDG 2024: CKM-фаза δ = 1,147 ± 0,026 рад.",
    ),
]
