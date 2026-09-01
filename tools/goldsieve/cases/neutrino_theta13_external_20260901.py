"""Аудит формулы sin²(theta13) по наблюдаемой строке корпуса и PDG 2024."""

from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_NEUTRINO_THETA13",
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


def _observed() -> float:
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in ("| sin² θ₁₃ | 3 γ φ² / (π³ e) | 0.02236 |", "0.02236"):
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)
    return 0.02236


def _reference() -> float:
    return 3.0 * PHI ** -3 * PHI ** 2 / (math.pi ** 3 * math.e)


def _reference_alt() -> float:
    return math.exp(math.log(3.0) - math.log(PHI)
                    - 3.0 * math.log(math.pi) - 1.0)


def _external_target() -> dict:
    return {
        "value": 0.0219,
        "uncertainty": 0.0007,
        "source": (
            "PDG 2024, Neutrino Mixing listing, "
            "https://pdg.ge.infn.it/2024/listings/rpp2024-list-neutrino-mixing.pdf"
        ),
        "название": "sin²(theta13), среднее PDG 2024",
    }


_wrong = [
    lambda: _reference() * 1.5,
    lambda: _reference() * 0.5,
    lambda: _reference() + 0.1,
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
        (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260901
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
        "params": (3, 0, -3, 2, -1),
        "rel_uncertainty": target["uncertainty"] / target["value"],
    }


def _algebraic():
    target = _external_target()
    return {
        "target": target["value"],
        "coeffs": (3, 0, -3, 2, -1),
        "has_pi": True,
        "rel_deviation": abs(_reference() - target["value"]) / target["value"],
        "max_coeff": 12,
        "free_coeff_limit": 6,
    }


CLAIMS = [
    Claim(
        name="sin²(theta13) = 3γφ²/(π³e) против внешнего значения PDG",
        source="docs/papers/README_FOR_SCIENTISTS.md:58",
        claim_kind="prediction",
        stated=_reference,
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
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
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; погрешность внешней цели проверяется отдельно",
            "С9": "детерминированная формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        claim_family="neutrino_mixing",
        observable="sin²(theta13)",
        measurement_source="PDG 2024",
        uncertainty_type="both",
        expected_effect_sigma=0.14,
        resolution_sigma=1.0,
        novelty_key="neutrino:theta13:external:v1",
        information_class="novelty",
        purpose="audit",
        models=["формула Trinity", "PDG 2024"],
        independent_of=["zeta", "BBLM", "CKM V_us/V_cb/V_td/V_ts/V_ub"],
        precision_gain=None,
        out_of_sample=True,
        tests_independent="unknown",
        notes=(
            "Наблюдаемое 0.02236 прочитано из корпуса; внешняя цель отделена "
            "от строки корпуса. Сигмы, множественность и MDL — раздельные координаты."
        ),
    )
]
