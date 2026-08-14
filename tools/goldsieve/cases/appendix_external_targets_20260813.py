"""Машинный аудит трёх предсказаний из APPENDIX_COMPLETE_CATALOG.

Проверяется буквальная формула корпуса против внешней измеренной цели.
Число ``Calculated`` читается только как observed; оно не используется
как эталон. Все три утверждения имеют claim_kind="prediction".
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_APPENDIX",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/APPENDIX_COMPLETE_CATALOG.md",
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


def _read(markers, value):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)
    return value


def alpha_inverse_target():
    # CODATA 2022, NIST: alpha^{-1}=137.035999177(21).
    return {
        "value": 137.035999177,
        "uncertainty": 0.000000021,
        "source": "CODATA/NIST, https://physics.nist.gov/cgi-bin/cuu/Value?alphinv",
    }


def omega_m_target():
    return {
        "value": 0.315,
        "uncertainty": 0.007,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def ns_target():
    return {
        "value": 0.9649,
        "uncertainty": 0.0042,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def alpha_inverse_reference():
    return 4.0 * math.pi**3 + math.pi**2 + math.pi


def alpha_inverse_reference_alt():
    return math.fsum((4.0 * math.pi**3, math.pi**2, math.pi))


def alpha_inverse_observed():
    return _read(
        ["| Name | 1/α (inverse fine structure constant) |",
         "| Calculated | 137.036303775 |"],
        137.036303775,
    )


def omega_m_reference():
    return 1.0 / math.pi


def omega_m_reference_alt():
    return math.exp(-math.log(math.pi))


def omega_m_observed():
    return _read(
        ["| Name | Ω_m |", "| Calculated | 0.3183 |"],
        0.3183,
    )


def ns_reference():
    return 94.0 * math.pi**-4


def ns_reference_alt():
    return math.exp(math.log(94.0) - 4.0 * math.log(math.pi))


def ns_observed():
    return _read(
        ["| Name | n_s |", "| Calculated | 0.9650 |"],
        0.9650,
    )


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 0.1,
    ]


def _alt_tolerance(reference, alternate):
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _multiplicity(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        fraction, expected = family.empirical_multiplicity(
            (-1, 4),
            eps,
            ranges=RANGES,
            trials=1000,
            seed=20260813,
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


def _claim(name, source, reference, alternate, observed, target,
           stated_target, positive, params, notes):
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
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; внешняя погрешность проверяется отдельно",
            "С9": "детерминированная формула, выборочной конечности нет",
            "С11": "одна статистика; проверка нескольких статистик неприменима",
        },
        notes=(
            "Внешняя цель взята из независимого CODATA/Planck-источника. "
            "Число Calculated используется только как observed; stated_target "
            "отделён от external_target. Сигмы, множественность и MDL "
            "рассматриваются как раздельные координаты. " + notes
        ),
    )


def _selfcheck():
    assert abs(alpha_inverse_reference() - alpha_inverse_reference_alt()) < 1e-12
    assert abs(omega_m_reference() - omega_m_reference_alt()) < 1e-12
    assert abs(ns_reference() - ns_reference_alt()) < 1e-12
    assert abs(alpha_inverse_reference() - alpha_inverse_target()["value"]) > 1e-6
    assert all(abs(w() - omega_m_reference()) > 1e-6 for w in _wrong(omega_m_reference))
    assert all(abs(w() - ns_reference()) > 1e-6 for w in _wrong(ns_reference))
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []


_selfcheck()


CLAIMS = [
    _claim(
        "Формула 1/α = 4π³ + π² + π согласуется с CODATA",
        "deploy/trinity-nexus/docs/research/APPENDIX_COMPLETE_CATALOG.md:9-17",
        alpha_inverse_reference,
        alpha_inverse_reference_alt,
        alpha_inverse_observed,
        alpha_inverse_target,
        lambda: 137.035999084,
        lambda: math.exp(math.log(alpha_inverse_reference())),
        (4, 0, 3, 0, 0),
        "Внешняя цель CODATA/NIST: 137,035999177 ± 0,000000021.",
    ),
    _claim(
        "Формула Ω_m = 1/π согласуется с плотностью материи",
        "deploy/trinity-nexus/docs/research/APPENDIX_COMPLETE_CATALOG.md:184-193",
        omega_m_reference,
        omega_m_reference_alt,
        omega_m_observed,
        omega_m_target,
        lambda: 0.315,
        lambda: math.exp(-math.log(math.pi)),
        (1, 0, -1, 0, 0),
        "Внешняя цель Planck 2018: Ω_m = 0,315 ± 0,007.",
    ),
    _claim(
        "Формула n_s = 94π⁻⁴ согласуется со спектральным индексом",
        "deploy/trinity-nexus/docs/research/APPENDIX_COMPLETE_CATALOG.md:204-212",
        ns_reference,
        ns_reference_alt,
        ns_observed,
        ns_target,
        lambda: 0.9649,
        lambda: math.exp(math.log(94.0) - 4.0 * math.log(math.pi)),
        (94, 0, -4, 0, 0),
        "Внешняя цель Planck 2018: n_s = 0,9649 ± 0,0042.",
    ),
]
