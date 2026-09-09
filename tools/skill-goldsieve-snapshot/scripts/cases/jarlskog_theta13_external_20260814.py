# -*- coding: utf-8 -*-
"""Аудит двух внешних предсказаний из научной сводки Trinity.

Числа из таблицы корпуса используются только как observed/stated_target.
Эталон каждой формулы вычисляется независимо; печатная колонка не является
эталоном. Вердикт берётся только из каскада goldsieve.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_JARLSKOG_THETA13",
    "/home/user/workspace/corpus/trinity/docs/papers/README_FOR_SCIENTISTS.md",
)
PHI = (1.0 + math.sqrt(5.0)) / 2.0
GAMMA = PHI ** -3
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}


def _read(markers):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)


def jarlskog_reference():
    return 21.0 * GAMMA ** 5 / (math.pi ** 2 * PHI ** 4 * math.e ** 2)


def jarlskog_reference_alt():
    return math.exp(
        math.log(21.0) + 5.0 * math.log(GAMMA)
        - 2.0 * math.log(math.pi) - 4.0 * math.log(PHI)
        - 2.0
    )


def jarlskog_observed():
    _read(["| Jarlskog J | 21 γ⁵ / (π² φ⁴ e²) |", "3.04×10⁻⁵"])
    return 3.04e-5


def jarlskog_stated_target():
    return 3.04e-5


def jarlskog_external_target():
    return {
        "value": 3.00e-5,
        "uncertainty": 0.15e-5,
        "source": (
            "PDG 2024, обзор матрицы CKM, "
            "https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf"
        ),
    }


def theta13_reference():
    return 3.0 * GAMMA * PHI ** 2 / (math.pi ** 3 * math.e)


def theta13_reference_alt():
    return math.exp(
        math.log(3.0) + math.log(GAMMA) + 2.0 * math.log(PHI)
        - 3.0 * math.log(math.pi) - 1.0
    )


def theta13_observed():
    _read(["| sin² θ₁₃ | 3 γ φ² / (π³ e) |", "0.02236"])
    return 0.02236


def theta13_stated_target():
    return 0.02236


def theta13_external_target():
    return {
        "value": 0.02237,
        "uncertainty": 0.00062,
        "source": (
            "NuFIT 5.2, глобальная подгонка нейтринных осцилляций, "
            "https://arxiv.org/abs/2210.08015"
        ),
    }


def _mean(values):
    return float(sum(values) / len(values))


def _sample(observed):
    return lambda: [observed()]


def _alt_tolerance(reference, alternate):
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 0.1,
    ]


def _positive_jarlskog():
    # Другой путь: сначала собирается логарифм произведения множителей.
    return math.exp(
        math.log(21.0) + 5.0 * math.log(1.0 / (PHI * PHI * PHI))
        - 2.0 * math.log(math.pi) - 4.0 * math.log(PHI) - 2.0
    )


def _positive_theta13():
    # Другой путь: γ заменяется определением φ^-3 до логарифмической сборки.
    gamma = 1.0 / (PHI * PHI * PHI)
    return math.exp(
        math.log(3.0) + math.log(gamma) + 2.0 * math.log(PHI)
        - 3.0 * math.log(math.pi) - 1.0
    )


def _multiplicity(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        fraction, expected = family.empirical_multiplicity(
            (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260814
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


def _arithmetic(params, target):
    def run():
        tgt = target()
        return {
            "params": params,
            "rel_uncertainty": abs(float(tgt["uncertainty"]) / float(tgt["value"])),
        }
    return run


def _algebraic(target, coeffs, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": coeffs,
            "has_pi": True,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": max(abs(int(c)) for c in coeffs),
            "free_coeff_limit": 6,
        }
    return run


_COMMON_SKIP = {
    "С6": "замкнутая формула; независимая сетка или разрешение отсутствуют",
    "С7": "один законный оцениватель; альтернативные оценки не заданы",
    "С8": "погрешность входа формулы не задана; внешняя погрешность учтена в С15",
    "С9": "детерминированная формула; конечная выборка неприменима",
    "С11": "одна внешняя статистика на каждое предсказание; проверка нескольких статистик неприменима",
}


def _claim(name, observed, reference, alternate, target, stated, positive, params):
    return Claim(
        name=name,
        source="docs/papers/README_FOR_SCIENTISTS.md:37-43",
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
        algebraic=_algebraic(target, params, reference),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons=dict(_COMMON_SKIP),
        notes=(
            "Внешняя цель взята из PDG или журнальной глобальной подгонки; "
            "печатное число корпуса используется только как observed/stated_target. "
            "Сигмы, множественность и MDL не сводятся в один скаляр."
        ),
    )


# Самопроверки эталонов и позитивных контролей обязаны сработать до прогона.
assert abs(jarlskog_reference() - jarlskog_reference_alt()) < 1e-14
assert abs(theta13_reference() - theta13_reference_alt()) < 1e-14
assert abs(jarlskog_reference() - _positive_jarlskog()) < 1e-14
assert abs(theta13_reference() - _positive_theta13()) < 1e-14
assert all(abs(w() - jarlskog_reference()) > 1e-8 for w in _wrong(jarlskog_reference))
assert all(abs(w() - theta13_reference()) > 1e-8 for w in _wrong(theta13_reference))
assert family.declared_size(RANGES) == SEARCH_SIZE

CLAIMS = [
    _claim(
        "Формула Jarlskog J согласуется с внешней оценкой PDG",
        jarlskog_observed,
        jarlskog_reference,
        jarlskog_reference_alt,
        jarlskog_external_target,
        jarlskog_stated_target,
        _positive_jarlskog,
        (21, 5, -2, -4, 0),
    ),
    _claim(
        "Формула sin²θ₁₃ согласуется с внешней оценкой NuFIT",
        theta13_observed,
        theta13_reference,
        theta13_reference_alt,
        theta13_external_target,
        theta13_stated_target,
        _positive_theta13,
        (3, 1, -3, 2, 0),
    ),
]
