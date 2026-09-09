# -*- coding: utf-8 -*-
"""Аудит трёх предсказаний из FORMULAS_SUMMARY против внешних измерений.

Печатное Calculated используется только как observed. Эталон каждой формулы
пересчитывается независимо, а внешняя цель имеет собственный URL и погрешность.
"""
import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_FORMULAS_SUMMARY",
    "/home/user/workspace/corpus/trinity/docs/research/FORMULAS_SUMMARY.md",
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


def alpha_reference():
    return 36.0 / (math.pi ** 4 * PHI ** 4 * math.e ** 2)


def alpha_reference_alt():
    return math.exp(math.log(36.0) - 4.0 * math.log(math.pi)
                       - 4.0 * math.log(PHI) - 2.0)


def alpha_observed():
    return _read(["| α (fine-structure)", "0.007297"], 0.007297)


def alpha_target():
    return {
        "value": 0.0072973525643,
        "uncertainty": 1.1e-12,
        "source": "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?alph",
    }


def alpha_stated_target():
    return 0.0072973


def alpha_s_reference():
    return 4.0 * PHI ** 2 / (9.0 * math.pi ** 2)


def alpha_s_reference_alt():
    return math.exp(math.log(4.0) + 2.0 * math.log(PHI)
                     - math.log(9.0) - 2.0 * math.log(math.pi))


def alpha_s_observed():
    return _read(["| α_s (strong coupling)", "0.11789"], 0.11789)


def alpha_s_target():
    return {
        "value": 0.1179,
        "uncertainty": 0.0009,
        "source": "PDG 2024, https://pdg.lbl.gov/2024/reviews/rpp2024-rev-qcd.pdf",
    }


def alpha_s_stated_target():
    return 0.11790


def tcmb_reference():
    return 5.0 * math.pi ** 4 * PHI ** 5 / (729.0 * math.e)


def tcmb_reference_alt():
    return math.exp(math.log(5.0) + 4.0 * math.log(math.pi)
                     + 5.0 * math.log(PHI) - math.log(729.0) - 1.0)


def tcmb_observed():
    return _read(["| T_CMB (temperature)", "2.72575 K"], 2.72575)


def tcmb_target():
    return {
        "value": 2.7255,
        "uncertainty": 0.0006,
        "source": "Planck Collaboration 2018, https://arxiv.org/abs/1807.06209",
    }


def tcmb_stated_target():
    return 2.72550


def _wrong(reference):
    return [lambda: reference() * 1.5, lambda: reference() * 0.5,
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


def _algebraic(target, coeffs, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": coeffs,
            "has_pi": True,
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
           stated_target, params, tolerance, notes):
    return Claim(
        name=name,
        source=source,
        claim_kind="prediction",
        # stated — число Calculated из той же строки корпуса; external_target
        # остаётся независимым измерением и хранится отдельно.
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        # Позитивный контроль воспроизводит эталон другим вычислительным
        # путём (через exp/log), а не возвращает число из корпуса.
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=tolerance,
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
        algebraic=_algebraic(target, params, reference),
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; внешняя погрешность проверяется отдельно",
            "С9": "детерминированная формула, выборочной конечности нет",
            "С11": "одна статистика; проверка нескольких статистик неприменима",
        },
        notes=("Внешняя цель отделена от числа Calculated в корпусе; "
               "сигмы, множественность и MDL остаются раздельными координатами. " + notes),
    )


def _selfcheck():
    assert abs(alpha_reference() - alpha_reference_alt()) < 1e-12
    assert abs(alpha_s_reference() - alpha_s_reference_alt()) < 1e-12
    assert abs(tcmb_reference() - tcmb_reference_alt()) < 1e-12
    assert abs(alpha_reference() - alpha_observed()) > 1e-8
    assert abs(alpha_s_reference() - alpha_s_observed()) > 1e-8
    assert abs(tcmb_reference() - tcmb_observed()) > 1e-8
    assert family.declared_size(RANGES) == SEARCH_SIZE
    for ref in (alpha_reference, alpha_s_reference, tcmb_reference):
        for wrong in _wrong(ref):
            assert abs(wrong() - ref()) > 1e-6


_selfcheck()

CLAIMS = [
    _claim(
        "Формула α = 36/(π⁴φ⁴e²) согласуется с измеренной постоянной тонкой структуры",
        "docs/research/FORMULAS_SUMMARY.md:42",
        alpha_reference, alpha_reference_alt, alpha_observed, alpha_target,
        alpha_stated_target, (36, 0, -4, -4, -2), 1.0e-4,
        "CODATA знает α с относительной точностью порядка 1,5×10⁻¹⁰; проверка идёт в сигмах CODATA, не в процентах.",
    ),
    _claim(
        "Формула α_s = 4φ²/(9π²) согласуется с измеренной сильной связью",
        "docs/research/FORMULAS_SUMMARY.md:43",
        alpha_s_reference, alpha_s_reference_alt, alpha_s_observed, alpha_s_target,
        alpha_s_stated_target, (4, 0, -2, 2, 0), 5.0e-5,
        "Внешняя цель — значение α_s(M_Z) из обзора PDG; это не внутренняя колонка Error корпуса.",
    ),
    _claim(
        "Формула T_CMB = 5π⁴φ⁵/(729e) согласуется с температурой реликтового излучения",
        "docs/research/FORMULAS_SUMMARY.md:53",
        tcmb_reference, tcmb_reference_alt, tcmb_observed, tcmb_target,
        tcmb_stated_target, (5, 0, 4, 5, -1), 2.0e-6,
        "Внешняя цель Planck указана с экспериментальной погрешностью; округлённое Calculated не используется как эталон.",
    ),
]
