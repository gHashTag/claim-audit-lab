# -*- coding: utf-8 -*-
"""Аудит трёх предсказаний из сравнительного отчёта PELLIS/TRINITY.

Эталон каждой формулы вычисляется из её записи. Число из сводной таблицы
корпуса используется только как observed. Внешние цели отделены от корпуса.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "PELLIS_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/research/PELLIS_TRINITY_COMPARISON.md",
)
OBS_SOURCE = os.environ.get(
    "PELLIS_OBS_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/research/FORMULAS_SUMMARY.md",
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


def _read(path, markers):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError(f"строка корпуса не найдена: {marker}")


def omega_target():
    return {
        "value": 0.688,
        "uncertainty": 0.017,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def weak_angle_target():
    return {
        "value": 0.23129,
        "uncertainty": 0.00004,
        "source": "PDG 2024, https://pdg.lbl.gov/2024/reviews/rpp2024-rev-phys-constants.pdf",
    }


def electron_radius_target():
    return {
        "value": 2.8179403205,
        "uncertainty": 0.0000000013,
        "source": "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?re",
        "unit": "фм",
    }


def omega_reference():
    return 3.0 ** 8 * PHI ** -3 / (math.pi ** 5 * math.e ** 2)


def weak_angle_reference():
    return 2.0 * math.pi ** 3 * math.e / 729.0


def electron_radius_reference():
    return 54.0 * PHI / math.pi ** 3


def omega_reference_alt():
    return math.exp(8.0 * math.log(3.0) - 3.0 * math.log(PHI) - 5.0 * math.log(math.pi) - 2.0)


def weak_angle_reference_alt():
    return math.exp(math.log(2.0) + 3.0 * math.log(math.pi) + 1.0 - math.log(729.0))


def electron_radius_reference_alt():
    return math.exp(math.log(54.0) + math.log(PHI) - 3.0 * math.log(math.pi))


def omega_observed():
    _read(SOURCE, ["Ω_Λ = 6561φ⁻³/(π⁵e²) ≈ 0.6850", "Ω_Λ = 0.688 ± 0.017"])
    _read(OBS_SOURCE, ["| Ω_Λ (dark energy) | Ω_Λ = 6561φ⁻³/(π⁵e²) | 0.6850 | 0.688 ± 0.017 |"])
    return 0.6850


def weak_angle_observed():
    _read(SOURCE, ["**sin²θ_W** (Weinberg angle) | 2π³e/729 | 0.005%"])
    _read(OBS_SOURCE, ["| sin²θ_W (Weinberg) | 2π³e/729 | 0.231231 | 0.23121 |"])
    return 0.231231


def electron_radius_observed():
    _read(SOURCE, ["**r_e** (electron radius) | 54φ/π³ | <0.001%"])
    _read(OBS_SOURCE, ["| r_e (electron radius) | 54φ/π³ | 2.81794 fm | 2.81794 fm |"])
    return 2.81794


def _positive_omega():
    return omega_reference_alt()


def _positive_weak_angle():
    return weak_angle_reference_alt()


def _positive_electron_radius():
    return electron_radius_reference_alt()


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 0.1,
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
    return [v for v in values if low <= v <= high]


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


def _algebraic(target, coeffs, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": coeffs,
            "has_pi": True,
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


def _claim(name, source, reference, alternate, observed, target, stated_target,
           positive, params, notes):
    return Claim(
        name=name,
        source=source,
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        null_model=positive,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1e-6,
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
        algebraic=_algebraic(target, params, reference),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE, OBS_SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; погрешность внешней цели проверяется отдельно",
            "С9": "детерминированная формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        notes=(
            "Внешняя цель отделена от числа корпуса; проверяется буквальная формула, "
            "а не число, напечатанное рядом. Порог С15 выводится по Шидаку из "
            "search_size=123201. Сигмы, множественность, MDL, С20 и С21 остаются "
            "раздельными координатами. " + notes
        ),
    )


def _selfcheck():
    assert abs(omega_reference() - omega_reference_alt()) < 1e-12
    assert abs(weak_angle_reference() - weak_angle_reference_alt()) < 1e-12
    assert abs(electron_radius_reference() - electron_radius_reference_alt()) < 1e-12
    assert abs(_positive_omega() - omega_reference()) < 1e-12
    assert abs(_positive_weak_angle() - weak_angle_reference()) < 1e-12
    assert abs(_positive_electron_radius() - electron_radius_reference()) < 1e-12
    assert all(abs(w() - omega_reference()) > 1e-6 for w in _wrong(omega_reference))
    assert all(abs(w() - weak_angle_reference()) > 1e-6 for w in _wrong(weak_angle_reference))
    assert all(abs(w() - electron_radius_reference()) > 1e-6 for w in _wrong(electron_radius_reference))
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []
    assert omega_target()["uncertainty"] > 0
    assert weak_angle_target()["uncertainty"] > 0
    assert electron_radius_target()["uncertainty"] > 0


_selfcheck()

CLAIMS = [
    _claim(
        "Формула Ω_Λ = 6561φ⁻³/(π⁵e²) согласуется с Planck",
        "docs/research/PELLIS_TRINITY_COMPARISON.md:106-115",
        omega_reference,
        omega_reference_alt,
        omega_observed,
        omega_target,
        lambda: 0.688,
        _positive_omega,
        (8, -3, -5, -3, -2),
        "Внешняя цель Planck 2018: 0,688 ± 0,017.",
    ),
    _claim(
        "Формула sin²θ_W = 2π³e/729 согласуется с PDG",
        "docs/research/PELLIS_TRINITY_COMPARISON.md:126-129",
        weak_angle_reference,
        weak_angle_reference_alt,
        weak_angle_observed,
        weak_angle_target,
        lambda: 0.23121,
        _positive_weak_angle,
        (2, -6, 3, 0, 1),
        "Внешняя цель PDG 2024: sin²θ(M_Z) в схеме MS = 0,23129 ± 0,00004.",
    ),
    _claim(
        "Формула r_e = 54φ/π³ согласуется с CODATA",
        "docs/research/PELLIS_TRINITY_COMPARISON.md:138",
        electron_radius_reference,
        electron_radius_reference_alt,
        electron_radius_observed,
        electron_radius_target,
        lambda: 2.81794,
        _positive_electron_radius,
        (54, 0, -3, 1, 0),
        "Внешняя цель CODATA 2022: 2,8179403205(13) фм.",
    ),
]
