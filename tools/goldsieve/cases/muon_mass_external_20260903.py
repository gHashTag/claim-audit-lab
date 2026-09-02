# -*- coding: utf-8 -*-
"""Внешняя сверка формулы массы мюона.

Наблюдаемое значение читается из строки корпуса, формула считается отдельно,
а оценка PDG хранится с положительной неопределённостью и URL. Вердикт
выносит каскад золотого сита; простое подтверждение не выпускается.
"""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_MUON_MASS_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md",
)
SEARCH_SIZE = 123201
RANGES = {
    "n": range(1, 10),
    "k": range(-6, 7),
    "m": range(-4, 5),
    "p": range(-6, 7),
    "q": range(-4, 5),
}
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _observed() -> float:
    marker = r"105.66 | $(8, 1, 0, 1, 1)$ | 105.559 |"
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if marker in line:
                return 105.66
    raise AssertionError("строка корпуса с массой мюона не найдена")


def _reference() -> float:
    return 8.0 * 3.0 * PHI * math.e


def _reference_alt() -> float:
    return math.exp(
        math.log(8.0) + math.log(3.0) + math.log(PHI) + 1.0
    )


def _external_target() -> dict:
    return {
        "value": 105.6583755,
        "uncertainty": 0.0000023,
        "source": (
            "https://pdg.lbl.gov/2024/tables/"
            "rpp2024-sum-leptons.pdf"
        ),
        "название": "масса мюона по PDG 2024",
    }


def _wrong():
    return [
        lambda: _reference() + 1.0,
        lambda: _reference() - 1.0,
        lambda: _reference() * 1.1,
    ]


def _positive():
    return _reference_alt()


def _sample():
    return [_observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance():
    a, b = _reference(), _reference_alt()
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _multiplicity():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    fraction, expected = family.empirical_multiplicity(
        (0, 4), eps, ranges=RANGES, trials=1000, seed=20260903
    )
    return {
        "expected_hits": expected,
        "p_global": fraction,
        "fraction_random_targets_hit": fraction,
        "search_size": SEARCH_SIZE,
    }


def _family_values():
    target = _external_target()
    low, high = target["value"] / 5.0, target["value"] * 5.0
    return [v for v in family.enumerate_family(RANGES) if low <= v <= high]


def _meff():
    target = _external_target()
    return {
        "values": _family_values(),
        "eps": target["uncertainty"] / abs(target["value"]),
        "sigma": abs((_reference() - target["value"]) / target["uncertainty"]),
        "search_size": SEARCH_SIZE,
    }


def _mdl():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    return {
        "description_bits": math.log2(SEARCH_SIZE),
        "match_bits": math.log2(1.0 / (2.0 * eps)),
    }


def _domain():
    assert family.declared_size(RANGES) == SEARCH_SIZE
    return []


def _arithmetic():
    target = _external_target()
    return {
        "params": (8, 1, 0, 1, 1),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (8, 1, 0, 1, 1),
        "has_pi": False,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="Формула массы мюона против внешней оценки PDG 2024",
        source="docs/docs/math-foundations/sacred-formulas.md:49",
        claim_kind="prediction",
        stated=_reference(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong(),
        null_model=_positive,
        null_expect=_reference(),
        null_kind="positive",
        tolerance=1e-6,
        sample=_sample,
        statistics={"value": _mean},
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        external_target=_external_target,
        stated_target=_observed,
        multiplicity=_multiplicity,
        mdl=_mdl,
        declared_domain=_domain,
        arithmetic=_arithmetic,
        meff=_meff,
        algebraic=_algebraic,
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        alpha=0.05,
        skip_reasons={
            "С6": "формула замкнута; сеток и разрешений нет",
            "С7": "один детерминированный оцениватель",
            "С8": "погрешность формулы не задана; внешняя погрешность проверяется С15",
            "С9": "формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        claim_family="muon_mass",
        observable="масса мюона (МэВ)",
        measurement_source="PDG 2024, сводная таблица свойств лептонов",
        uncertainty_type="both",
        expected_effect_sigma=abs(_reference() - 105.6583755) / 0.0000023,
        resolution_sigma=1.0,
        novelty_key="lepton:muon_mass:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "масса мюона PDG 2024"],
        independent_of=[
            "zeta",
            "BBLM",
            "CKM",
            "нейтринное смешивание",
            "масса t-кварка",
            "масса электрона",
        ],
        precision_gain=None,
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "105,66 прочитано из строки корпуса; внешняя цель "
            "105,6583755 ± 0,0000023 МэВ взята из таблицы лептонов PDG 2024. "
            "Формула даёт 105,5589 МэВ; итог берётся из сит и не является новым "
            "простым подтверждением."
        ),
    )
]
