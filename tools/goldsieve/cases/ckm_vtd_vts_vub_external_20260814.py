"""Аудит трёх предсказаний CKM против внешнего обзора PDG 2024.

Числа из таблицы корпуса используются только как observed. Внешняя цель
берётся отдельно из обзора PDG; проверка печатного значения рядом с формулой
не является внешним тестом.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_CKM_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/docs/research/trinity-status-2026.md",
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


def vtd_target():
    return {
        "value": 8.6e-3,
        "uncertainty": 0.2e-3,
        "source": "PDG 2024, обзор CKM, https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf",
    }


def vts_target():
    return {
        "value": 41.5e-3,
        "uncertainty": 0.9e-3,
        "source": "PDG 2024, обзор CKM, https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf",
    }


def vub_target():
    return {
        "value": 3.82e-3,
        "uncertainty": 0.20e-3,
        "source": "PDG 2024, обзор CKM, https://pdg.lbl.gov/2024/reviews/rpp2024-rev-ckm-matrix.pdf",
    }


def vtd_reference():
    return math.e ** 3 / (81.0 * PHI ** 7)


def vts_reference():
    return 2916.0 / (math.pi ** 5 * PHI ** 3 * math.e ** 4)


def vub_reference():
    return 7.0 / (729.0 * PHI ** 2)


def vtd_reference_alt():
    return math.exp(3.0 - math.log(81.0) - 7.0 * math.log(PHI))


def vts_reference_alt():
    return math.exp(
        math.log(2916.0) - 5.0 * math.log(math.pi)
        - 3.0 * math.log(PHI) - 4.0
    )


def vub_reference_alt():
    return math.exp(math.log(7.0) - math.log(729.0) - 2.0 * math.log(PHI))


def vtd_observed():
    _require_markers(["| **V_td** | e³/(81φ⁷) | 0.008541 | 0.008540 | **0.006%** | 1 | -4 | 0 | -7 | 3 | 0 | 🔥 |"])
    return 0.008541


def vts_observed():
    _require_markers(["| **V_ts** | 2916/(π⁵φ³e⁴) | 0.041200 | 0.041200 | **0.00002%** | 4 | -6 | -5 | -3 | -4 | 0 | 🔥 |"])
    return 0.041200


def vub_observed():
    _require_markers(["| **V_ub** | 7/(729φ²) | 0.003668 | 0.003690 | **0.604%** | 7 | -6 | 0 | -2 | 0 | 0 | ⚠️ |"])
    return 0.003668


def _positive(reference_alt):
    return reference_alt()


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() * 1.01,
    ]


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
           stated_target, positive, params, has_pi, notes):
    return Claim(
        name=name,
        source=source_line,
        claim_kind="prediction",
        stated=reference,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        null_model=lambda: _positive(alternate),
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
        (vtd_reference, vtd_reference_alt),
        (vts_reference, vts_reference_alt),
        (vub_reference, vub_reference_alt),
    ]
    for reference, alternate in refs:
        assert abs(reference() - alternate()) / abs(reference()) < 1e-12
        assert all(abs(w() - reference()) > 1e-6 for w in _wrong(reference))
    assert abs(_positive(vtd_reference_alt) - vtd_reference()) < 1e-12
    assert abs(_positive(vts_reference_alt) - vts_reference()) < 1e-12
    assert abs(_positive(vub_reference_alt) - vub_reference()) < 1e-12
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []
    for target in (vtd_target, vts_target, vub_target):
        assert target()["uncertainty"] > 0
        assert "https://" in target()["source"]


_selfcheck()

CLAIMS = [
    _claim(
        "Формула V_td = e³/(81φ⁷) согласуется с внешним значением PDG",
        "docs/docs/research/trinity-status-2026.md:172-178",
        vtd_reference,
        vtd_reference_alt,
        vtd_observed,
        vtd_target,
        lambda: 0.008540,
        _positive,
        (1, -4, 0, -7, 3),
        False,
        "Внешняя цель PDG 2024: |V_td| = (8,6 ± 0,2)×10⁻³.",
    ),
    _claim(
        "Формула V_ts = 2916/(π⁵φ³e⁴) согласуется с внешним значением PDG",
        "docs/docs/research/trinity-status-2026.md:172-178",
        vts_reference,
        vts_reference_alt,
        vts_observed,
        vts_target,
        lambda: 0.041200,
        _positive,
        (4, -6, -5, -3, -4),
        True,
        "Внешняя цель PDG 2024: |V_ts| = (41,5 ± 0,9)×10⁻³.",
    ),
    _claim(
        "Формула V_ub = 7/(729φ²) согласуется с внешним значением PDG",
        "docs/docs/research/trinity-status-2026.md:172-178",
        vub_reference,
        vub_reference_alt,
        vub_observed,
        vub_target,
        lambda: 0.003690,
        _positive,
        (7, -6, 0, -2, 0),
        False,
        "Внешняя цель PDG 2024: |V_ub| = (3,82 ± 0,20)×10⁻³.",
    ),
]
