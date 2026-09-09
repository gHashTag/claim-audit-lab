# -*- coding: utf-8 -*-
"""Аудит трёх внешних предсказаний из deploy/trinity-nexus/docs/research/formulas.md.

Эталон каждой формулы вычисляется заново. Число Calculated из корпуса — только
observed; внешняя измеренная цель хранится отдельно. Позитивный контроль строит
тот же эталон через независимый маршрут log/exp.
"""
import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_DEPLOY_FORMULAS",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/formulas.md",
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10), "k": range(-6, 7), "m": range(-4, 5),
    "p": range(-6, 7), "q": range(-4, 5),
}


def _read(markers):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)


def _formula(params):
    n, k, m, p, q = params
    return n * 3.0 ** k * math.pi ** m * PHI ** p * math.e ** q


def _log_route(params):
    n, k, m, p, q = params
    return math.exp(
        math.log(float(n)) + k * math.log(3.0) + m * math.log(math.pi)
        + p * math.log(PHI) + q
    )


def mu_target():
    return {
        "value": 206.7682827,
        "uncertainty": 4.6e-6,
        "source": "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?mmusme",
    }


def tau_target():
    return {
        "value": 3477.23,
        "uncertainty": 0.23,
        "source": "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?mtausme",
    }


def omega_lambda_target():
    return {
        "value": 0.6847,
        "uncertainty": 0.0073,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def mu_reference():
    return 3.0 * (3.0 * math.pi - 1.0) ** 2 / math.pi


def tau_reference():
    return 3.0 * PHI * (6.0 * math.pi) ** 2


def omega_lambda_reference():
    return (math.pi - 1.0) / math.pi


def mu_reference_alt():
    return math.exp(math.log(3.0) + 2.0 * math.log(3.0 * math.pi - 1.0) - math.log(math.pi))


def tau_reference_alt():
    return math.exp(math.log(3.0) + math.log(PHI) + 2.0 * math.log(6.0 * math.pi))


def omega_lambda_reference_alt():
    return math.exp(math.log(math.pi - 1.0) - math.log(math.pi))


def mu_observed():
    _read(["m(mu)/m(e) = 3 * (3*pi - 1)^2 / pi", "**Calculated**: 206.77"])
    return 206.77


def tau_observed():
    _read(["m(tau)/m(e) = 3 * phi * (6*pi)^2", "**Calculated**: 3477.1"])
    return 3477.1


def omega_lambda_observed():
    _read(["Omega(Lambda) = (pi - 1)/pi", "**Calculated**: 0.6817"])
    return 0.6817


def _wrong(reference):
    return [lambda: reference() * 1.5, lambda: reference() * 0.5,
            lambda: reference() + 0.1]


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


def _algebraic(target, params, reference, has_pi=True):
    def run():
        tgt = target()
        return {
            "target": tgt["value"], "coeffs": params, "has_pi": has_pi,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": max(abs(item) for item in params), "free_coeff_limit": 9,
        }
    return run


def _arithmetic(params, target):
    def run():
        tgt = target()
        return {"params": params, "rel_uncertainty": float(tgt["uncertainty"]) / abs(float(tgt["value"]))}
    return run


_COMMON_SKIP = {
    "С6": "замкнутая формула, сеток или разрешений нет",
    "С7": "один законный оцениватель; альтернативных оценок нет",
    "С8": "погрешность входов формулы не задана; внешняя погрешность проверяется отдельно",
    "С9": "детерминированная формула, конечной выборки нет",
    "С11": "одна статистика; сравнение нескольких статистик неприменимо",
}


def _claim(name, source, params, reference, alternate, observed, target,
           stated_target, has_pi, notes):
    return Claim(
        name=name, source=source, claim_kind="prediction",
        stated=observed, reference=reference, observed=observed,
        wrong=_wrong(reference), null_model=alternate,
        null_expect=reference(), null_kind="positive", tolerance=1.0e-6,
        sample=_sample(observed), statistics={"value": _mean},
        reference_alt=alternate, alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        external_target=target, stated_target=stated_target,
        search_size=SEARCH_SIZE, multiplicity=_multiplicity(target), mdl=_mdl(target),
        declared_domain=_domain, arithmetic=_arithmetic(params, target),
        meff=_meff(target, reference), algebraic=_algebraic(target, params, reference, has_pi),
        inputs=[SOURCE], skip_reasons=dict(_COMMON_SKIP),
        notes=("Печатное Calculated используется только как observed; внешняя цель "
               "отделена от корпуса. Сигмы, множественность и MDL остаются "
               "раздельными координатами. " + notes),
    )


def _selfcheck():
    for reference, alternate, observed in (
        (mu_reference, mu_reference_alt, mu_observed),
        (tau_reference, tau_reference_alt, tau_observed),
        (omega_lambda_reference, omega_lambda_reference_alt, omega_lambda_observed),
    ):
        assert math.isfinite(reference())
        assert abs(reference() - alternate()) / abs(reference()) < 1.0e-12
        assert math.isfinite(observed())
        for wrong in _wrong(reference):
            assert abs(wrong() - reference()) > 1.0e-6
    assert family.declared_size(RANGES) == SEARCH_SIZE


_selfcheck()

CLAIMS = [
    _claim(
        "Формула m(μ)/m(e) = 3(3π−1)²/π согласуется с отношением масс мюона и электрона",
        "deploy/trinity-nexus/docs/research/formulas.md:88-98",
        (3, 0, 2, 0, 0), mu_reference, mu_reference_alt, mu_observed,
        mu_target, lambda: 206.77, True,
        "Внешняя цель CODATA/NIST: 206,7682827 ± 0,0000046; проверяется буквальная формула, а не соседнее число.",
    ),
    _claim(
        "Формула m(τ)/m(e) = 3φ(6π)² согласуется с отношением масс тау-лептона и электрона",
        "deploy/trinity-nexus/docs/research/formulas.md:100-110",
        (3, 0, 2, 1, 0), tau_reference, tau_reference_alt, tau_observed,
        tau_target, lambda: 3477.2, True,
        "Внешняя цель CODATA/NIST: 3477,23 ± 0,23; округление корпуса не является целью.",
    ),
    _claim(
        "Формула Ω_Λ = (π−1)/π согласуется с долей тёмной энергии",
        "deploy/trinity-nexus/docs/research/formulas.md:130-142",
        (1, 0, -1, 0, 0), omega_lambda_reference, omega_lambda_reference_alt,
        omega_lambda_observed, omega_lambda_target, lambda: 0.685, True,
        "Внешняя цель Planck 2018: Ω_Λ = 0,6847 ± 0,0073; проверяется измерение, а не строка Calculated.",
    ),
]
