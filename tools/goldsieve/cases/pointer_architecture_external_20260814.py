# -*- coding: utf-8 -*-
"""Аудит трёх внешних предсказаний из Pointer Architecture Companion.

Числа Result из корпуса используются только как observed. Эталон каждой
формулы пересчитывается независимо, а внешняя цель взята из CODATA/Planck.
Печатная сверка не подменяет проверку предсказания.
"""
import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_POINTER_COMPANION",
    "/home/user/workspace/corpus/trinity/docs/research/pointer_architecture_companion.md",
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10), "k": range(-6, 7), "m": range(-4, 5),
    "p": range(-6, 7), "q": range(-4, 5),
}


def _read(markers, value):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)
    return value


def h0_reference():
    return 4.0 * 3.0**3 * math.pi**-3 * PHI**2 * math.e**2


def h0_reference_alt():
    return math.exp(math.log(4.0) + 3.0 * math.log(3.0)
                     - 3.0 * math.log(math.pi) + 2.0 * math.log(PHI) + 2.0)


def h0_observed():
    return _read(["Standard: H₀ ≈ 67.4 km/s/Mpc (Planck 2018)",
                  "Result: 67.381 vs 67.4"], 67.381)


def h0_target():
    return {
        "value": 67.4,
        "uncertainty": 0.5,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def h0_stated_target():
    return 67.4


def omega_reference():
    return 4.0 * 3.0**2 * PHI**-2 * math.e**-3


def omega_reference_alt():
    return math.exp(math.log(4.0) + 2.0 * math.log(3.0)
                     - 2.0 * math.log(PHI) - 3.0)


def omega_observed():
    return _read(["Standard: Ω_Λ ≈ 0.685", "Result: 0.6846 vs 0.685"], 0.6846)


def omega_target():
    return {
        "value": 0.6847,
        "uncertainty": 0.0073,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def omega_stated_target():
    return 0.6847


def alpha_inverse_reference():
    return 4.0 * 3.0**2 * math.pi**-1 * PHI * math.e**2


def alpha_inverse_reference_alt():
    return math.exp(math.log(4.0) + 2.0 * math.log(3.0)
                     - math.log(math.pi) + math.log(PHI) + 2.0)


def alpha_inverse_observed():
    return _read(["Standard: 1/α = 137.036", "Result: 137.0027 vs 137.036"], 137.0027)


def alpha_inverse_target():
    return {
        "value": 137.035999177,
        "uncertainty": 0.000000021,
        "source": "CODATA 2022/NIST, https://physics.nist.gov/cgi-bin/cuu/Value?alphinv",
    }


def alpha_inverse_stated_target():
    return 137.035999177


def _wrong(reference):
    return [lambda: reference() * 1.5,
            lambda: reference() * 0.5,
            lambda: reference() + 0.1]


def _alt_tolerance(reference, alternate):
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _multiplicity(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        fraction, expected = family.empirical_multiplicity(
            (-1, 4), eps, ranges=RANGES, trials=1000, seed=20260814)
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


def _algebraic(target, coeffs, reference, has_pi):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": coeffs,
            "has_pi": has_pi,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": 9,
            "free_coeff_limit": 6,
        }
    return run


def _arithmetic(params, target):
    def run():
        tgt = target()
        return {
            "params": params,
            "rel_uncertainty": float(tgt["uncertainty"]) / abs(float(tgt["value"])),
        }
    return run


def _claim(name, source, reference, alternate, observed, target,
           stated_target, params, has_pi, notes):
    return Claim(
        name=name,
        source=source,
        claim_kind="prediction",
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        # Контроль воспроизводит эталон через log/exp, не читает число корпуса.
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
        search_size=SEARCH_SIZE,
        multiplicity=_multiplicity(target),
        mdl=_mdl(target),
        declared_domain=_domain,
        arithmetic=_arithmetic(params, target),
        meff=_meff(target, reference),
        algebraic=_algebraic(target, params, reference, has_pi),
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; внешняя погрешность проверяется отдельно",
            "С9": "детерминированная формула, выборочной конечности нет",
            "С11": "одна статистика; проверка нескольких статистик неприменима",
        },
        notes=("Внешняя цель отделена от строки Result; сигмы, множественность и "
               "MDL остаются раздельными координатами. " + notes),
    )


def _selfcheck():
    refs = ((h0_reference, h0_reference_alt, h0_observed),
            (omega_reference, omega_reference_alt, omega_observed),
            (alpha_inverse_reference, alpha_inverse_reference_alt, alpha_inverse_observed))
    for reference, alternate, observed in refs:
        assert abs(reference() - alternate()) < 1.0e-12
        assert abs(reference() - observed()) > 1.0e-8
        for wrong in _wrong(reference):
            assert abs(wrong() - reference()) > 1.0e-6
    assert family.declared_size(RANGES) == SEARCH_SIZE


_selfcheck()

CLAIMS = [
    _claim(
        "Формула H₀ = 4·3³·π⁻³·φ²·e² согласуется с оценкой Planck",
        "docs/research/pointer_architecture_companion.md:212-220",
        h0_reference, h0_reference_alt, h0_observed, h0_target,
        h0_stated_target, (4, 3, -3, 2, 2), True,
        "Planck даёт внешнюю оценку H₀ с неопределённостью; число Result не используется как эталон.",
    ),
    _claim(
        "Формула Ω_Λ = 4·3²·φ⁻²·e⁻³ согласуется с оценкой Planck",
        "docs/research/pointer_architecture_companion.md:223-231",
        omega_reference, omega_reference_alt, omega_observed, omega_target,
        omega_stated_target, (4, 2, 0, -2, -3), False,
        "Для Ω_Λ используется отдельная внешняя цель Planck; отсутствие π объявлено для С21 явно.",
    ),
    _claim(
        "Формула 1/α = 4·3²·π⁻¹·φ·e² согласуется с CODATA",
        "docs/research/pointer_architecture_companion.md:234-244",
        alpha_inverse_reference, alpha_inverse_reference_alt,
        alpha_inverse_observed, alpha_inverse_target,
        alpha_inverse_stated_target, (4, 2, -1, 1, 2), True,
        "Отклонение измеряется в сигмах CODATA, а не в процентах; соседнее число Result — только observed.",
    ),
]
