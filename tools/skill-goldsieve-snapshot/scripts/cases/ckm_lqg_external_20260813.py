"""Аудит трёх предсказаний против внешних измерений.

Проверяются только утверждения-предсказания: формулы корпуса сравниваются с
внешними целями PDG и литературной оценкой параметра Барберо–Иммирци. Числа,
напечатанные рядом с формулами, используются только как observed/stated_target;
они не являются эталоном.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_CKM_LQG",
    "/home/user/workspace/corpus/trinity/docs/papers/README_FOR_SCIENTISTS.md",
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


def _read_observed(markers, value):
    """Убедиться, что формула и её строка результата есть в корпусе."""
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)
    return value


# Внешние измерения: значения и погрешности не берутся из вычисления формулы.
def gamma_target():
    return {
        "value": 0.237533,
        "uncertainty": 0.00009,
        "source": (
            "каноническая оценка по Мейсснеру, "
            "https://arxiv.org/abs/gr-qc/0407052"
        ),
    }


def vus_target():
    return {
        "value": 0.2245,
        "uncertainty": 0.0008,
        "source": (
            "PDG 2024, обзор CKM, "
            "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf"
        ),
    }


def vcb_target():
    return {
        "value": 0.0409,
        "uncertainty": 0.0011,
        "source": (
            "PDG 2024, обзор CKM, "
            "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf"
        ),
    }


# Эталон каждой формулы вычисляется из определений, а не цитируется.
def gamma_reference():
    return PHI ** -3


def gamma_reference_alt():
    return math.exp(-3.0 * math.log(PHI))


def vus_reference():
    return 3.0 * PHI ** -3 / math.pi


def vus_reference_alt():
    return math.exp(math.log(3.0) - 3.0 * math.log(PHI) - math.log(math.pi))


def vcb_reference():
    return PHI ** -9 * math.pi


def vcb_reference_alt():
    return math.exp(-9.0 * math.log(PHI) + math.log(math.pi))


# observed — только значение, напечатанное корпусом рядом с формулой.
def gamma_observed():
    return _read_observed(["γ = φ⁻³", "0.236068"], 0.236068)


def vus_observed():
    return _read_observed(["|V_us| ≈ 3γ/π", "0.225"], 0.225)


def vcb_observed():
    return _read_observed(["|V_cb| ≈ γ³ π", "0.041"], 0.041)


def gamma_stated_target():
    return 0.237533


def vus_stated_target():
    return 0.225


def vcb_stated_target():
    return 0.041


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
            (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260813
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
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        return {
            "values": _family_values(target),
            "eps": eps,
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


# Позитивные контроли воспроизводят эталон другим маршрутом.
def _positive_gamma():
    return 1.0 / (PHI * PHI * PHI)


def _positive_vus():
    return 3.0 / (PHI * PHI * PHI * math.pi)


def _positive_vcb():
    return math.pi / (PHI ** 9)


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 0.1,
    ]


def _selfcheck():
    assert abs(gamma_reference() - gamma_reference_alt()) < 1e-14
    assert abs(vus_reference() - vus_reference_alt()) < 1e-14
    assert abs(vcb_reference() - vcb_reference_alt()) < 1e-14
    assert all(abs(w() - gamma_reference()) > 1e-6 for w in _wrong(gamma_reference))
    assert all(abs(w() - vus_reference()) > 1e-6 for w in _wrong(vus_reference))
    assert all(abs(w() - vcb_reference()) > 1e-6 for w in _wrong(vcb_reference))
    assert abs(_positive_gamma() - gamma_reference()) < 1e-14
    assert abs(_positive_vus() - vus_reference()) < 1e-14
    assert abs(_positive_vcb() - vcb_reference()) < 1e-14
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []


_selfcheck()

_COMMON_SKIP = {
    "С6": "замкнутая формула, сетки или разрешения нет",
    "С7": "один законный оцениватель, альтернативных оценок нет",
    "С8": "погрешность входа формулы не задана; проверяется погрешность внешней цели",
    "С9": "это детерминированная формула, выборочной конечности нет",
    "С11": "одна статистика; проверка нескольких статистик неприменима",
}


def _claim(name, source, reference, alternate, observed, target, stated,
           positive, params, has_pi, notes):
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
        stated_target=stated,
        multiplicity=_multiplicity(target),
        mdl=_mdl(target),
        declared_domain=_domain,
        arithmetic=_arithmetic(params, target),
        meff=_meff(target, reference),
        algebraic=_algebraic(target, params, has_pi, reference),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons=dict(_COMMON_SKIP),
        notes=(
            "Проверка формулы против внешнего измерения; число из строки "
            "корпуса используется только как observed/stated_target. "
            "Сигмы, множественность и MDL — раздельные координаты. " + notes
        ),
    )


CLAIMS = [
    _claim(
        "γ = φ⁻³ согласуется с внешней оценкой параметра Барберо–Иммирци",
        "docs/papers/README_FOR_SCIENTISTS.md:20",
        gamma_reference,
        gamma_reference_alt,
        gamma_observed,
        gamma_target,
        gamma_stated_target,
        _positive_gamma,
        (1, 0, 0, -3, 0),
        False,
        "Внешняя литературная оценка дана с погрешностью ±0,00009.",
    ),
    _claim(
        "|V_us| = 3γ/π согласуется с внешним значением CKM",
        "docs/papers/README_FOR_SCIENTISTS.md:47,95",
        vus_reference,
        vus_reference_alt,
        vus_observed,
        vus_target,
        vus_stated_target,
        _positive_vus,
        (3, 0, -1, -3, 0),
        True,
        "Внешняя цель PDG 2024 указана как 0,2245 ± 0,0008.",
    ),
    _claim(
        "|V_cb| = γ³π согласуется с внешним значением CKM",
        "docs/papers/README_FOR_SCIENTISTS.md:49,96",
        vcb_reference,
        vcb_reference_alt,
        vcb_observed,
        vcb_target,
        vcb_stated_target,
        _positive_vcb,
        (1, 0, 1, -9, 0),
        True,
        "Внешняя цель PDG 2024 указана как 0,0409 ± 0,0011.",
    ),
]
