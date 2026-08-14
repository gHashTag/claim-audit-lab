# -*- coding: utf-8 -*-
"""Аудит трёх формул масс бозонов из SACRED_FORMULA_COMPLETE_v2.

Печатные проценты ошибки не используются как внешний эталон. Эталон каждой
формулы вычисляется заново, а физическая проверка выполняется против таблиц PDG.
Положительный контроль использует независимый маршрут log/exp и не возвращает
число из корпуса.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_SACRED_COMPLETE_V2",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/SACRED_FORMULA_COMPLETE_v2.md",
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


def _read(markers):
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)


def _formula(params):
    n, k, m, p, q = params
    return n * 3.0**k * math.pi**m * PHI**p * math.e**q


def _log_route(params):
    """Независимый маршрут через сумму логарифмов и экспоненту."""
    n, k, m, p, q = params
    return math.exp(
        math.log(float(n))
        + k * math.log(3.0)
        + m * math.log(math.pi)
        + p * math.log(PHI)
        + q
    )


def _target(value, uncertainty, source):
    return {
        "value": value,
        "uncertainty": uncertainty,
        "source": source,
    }


def w_target():
    return _target(
        80.3692,
        0.0133,
        "PDG 2024, https://pdg.lbl.gov/2024/listings/rpp2024-list-w-boson.pdf",
    )


def z_target():
    return _target(
        91.1880,
        0.0020,
        "PDG 2024, https://pdg.lbl.gov/2024/listings/rpp2024-list-z-boson.pdf",
    )


def h_target():
    return _target(
        125.20,
        0.11,
        "PDG 2024, https://pdg.lbl.gov/2024/listings/rpp2024-list-higgs-boson.pdf",
    )


def w_reference():
    return _formula((25, 1, 5, 4, 0))


def z_reference():
    return _formula((5, 4, 7, -4, 0))


def h_reference():
    return _formula((40, 3, 6, -3, 0))


def w_reference_alt():
    return _log_route((25, 1, 5, 4, 0))


def z_reference_alt():
    return _log_route((5, 4, 7, -4, 0))


def h_reference_alt():
    return _log_route((40, 3, 6, -3, 0))


def w_observed():
    _read(["| W | 25×3×π⁵×φ⁴ | 0.0094% |"])
    return w_reference()


def z_observed():
    _read(["| Z | 5×3⁴×π⁷×φ⁻⁴ | 0.0085% |"])
    return z_reference()


def h_observed():
    _read(["| H | 40×3³×π⁶×φ⁻³ | **0.0006%** |"])
    return h_reference()


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


def _algebraic(target, params, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": params,
            "has_pi": True,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": max(abs(item) for item in params),
            "free_coeff_limit": 9,
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


def _claim(
    name,
    source_line,
    params,
    reference,
    alternate,
    observed,
    target,
    notes,
):
    return Claim(
        name=name,
        source=source_line,
        claim_kind="prediction",
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1.0e-6,
        sample=_sample(observed),
        statistics={"value": _mean},
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        external_target=target,
        # В корпусе нет отдельной числовой строки результата для этой таблицы:
        # заявленная физическая цель берётся из соответствующей записи PDG.
        stated_target=lambda: float(target()["value"]),
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
            "С7": "одна законная оценка; смена оценивателя неприменима",
            "С8": "погрешность входов формулы не задана; погрешность внешней цели проверяется отдельно",
            "С9": "детерминированная формула, конечной выборки нет",
            "С11": "одна статистика; сравнение нескольких статистик неприменимо",
        },
        notes=(
            "Печатный процент ошибки не является внешним эталоном. "
            "Формула проверяется против PDG; сигмы, множественность и MDL "
            "сохраняются отдельными координатами. "
            + notes
        ),
    )


def _selfcheck():
    for reference, alternate, observed in (
        (w_reference, w_reference_alt, w_observed),
        (z_reference, z_reference_alt, z_observed),
        (h_reference, h_reference_alt, h_observed),
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
        "Формула W = 25·3·π⁵·φ⁴ согласуется с внешней массой W-бозона",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_COMPLETE_v2.md:198-206",
        (25, 1, 5, 4, 0),
        w_reference,
        w_reference_alt,
        w_observed,
        w_target,
        "Внешняя цель PDG дана в ГэВ с погрешностью; строка корпуса не заменяет измерение.",
    ),
    _claim(
        "Формула Z = 5·3⁴·π⁷·φ⁻⁴ согласуется с внешней массой Z-бозона",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_COMPLETE_v2.md:198-206",
        (5, 4, 7, -4, 0),
        z_reference,
        z_reference_alt,
        z_observed,
        z_target,
        "Проверяется мировое среднее PDG, а не округлённый процент ошибки в таблице.",
    ),
    _claim(
        "Формула H = 40·3³·π⁶·φ⁻³ согласуется с внешней массой бозона Хиггса",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_COMPLETE_v2.md:198-206",
        (40, 3, 6, -3, 0),
        h_reference,
        h_reference_alt,
        h_observed,
        h_target,
        "Заявление о высокой точности проверяется только против внешней оценки PDG.",
    ),
]
