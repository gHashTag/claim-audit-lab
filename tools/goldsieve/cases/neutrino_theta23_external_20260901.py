"""Аудит формулы sin²(theta23) по строке корпуса и внешней оценке PDG."""
from __future__ import annotations

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_NEUTRINO_THETA23",
    "/home/user/workspace/corpus/trinity/docs/docs/research/formulas-catalog-2026.md",
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
    marker = "| PM3 | sin²θ₂₃ = 4πφ²/(3e³) | 0.545985 |"
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    if marker not in text:
        raise AssertionError("строка корпуса PM3 θ₂₃ не найдена")
    return 0.545985


def _reference() -> float:
    return 4.0 * math.pi * PHI**2 / (3.0 * math.e**3)


def _reference_alt() -> float:
    return math.exp(math.log(4.0) + math.log(math.pi) + 2.0 * math.log(PHI)
                    - math.log(3.0) - 3.0)


def _external_target() -> dict:
    return {
        "value": 0.558,
        "uncertainty": 0.022,
        "source": (
            "PDG 2024, Neutrino Mixing, "
            "https://pdg.ge.infn.it/2024/listings/rpp2024-list-neutrino-mixing.pdf"
        ),
        "название": "sin²(theta23), обзор PDG 2024",
    }


_WRONG = [lambda: _reference() * 1.5, lambda: _reference() * 0.5,
          lambda: _reference() + 0.1]


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
    return {"expected_hits": expected, "p_global": fraction,
            "fraction_random_targets_hit": fraction, "search_size": SEARCH_SIZE}


def _family_values():
    target = _external_target()
    low, high = target["value"] / 5.0, target["value"] * 5.0
    return [v for v in family.enumerate_family(RANGES) if low <= v <= high]


def _meff():
    target = _external_target()
    return {"values": _family_values(),
            "eps": target["uncertainty"] / abs(target["value"]),
            "sigma": abs((_reference() - target["value"]) / target["uncertainty"]),
            "search_size": SEARCH_SIZE}


def _mdl():
    target = _external_target()
    eps = target["uncertainty"] / abs(target["value"])
    return {"description_bits": math.log2(SEARCH_SIZE),
            "match_bits": math.log2(1.0 / (2.0 * eps))}


def _domain():
    assert family.declared_size(RANGES) == SEARCH_SIZE
    return []


def _arithmetic():
    target = _external_target()
    return {"params": (4, -1, 1, 2, -3),
            "rel_uncertainty": target["uncertainty"] / target["value"]}


def _algebraic():
    target = _external_target()
    return {"target": target["value"], "coeffs": (4, -1, 1, 2, -3),
            "has_pi": True,
            "rel_deviation": abs(_reference() - target["value"]) / target["value"],
            "max_coeff": 12, "free_coeff_limit": 6}


CLAIMS = [
    Claim(
        name="sin²(theta23) = 4πφ²/(3e³) против внешней оценки PDG",
        source="docs/docs/research/formulas-catalog-2026.md:144",
        claim_kind="prediction", stated=_reference, reference=_reference,
        observed=_observed, wrong=_WRONG, null_model=_positive,
        null_expect=_reference(), null_kind="positive", tolerance=1e-6,
        sample=_sample, statistics={"value": _mean},
        reference_alt=_reference_alt, alt_tolerance=_alt_tolerance,
        external_target=_external_target, stated_target=_observed,
        multiplicity=_multiplicity, mdl=_mdl, declared_domain=_domain,
        arithmetic=_arithmetic, meff=_meff, algebraic=_algebraic,
        search_size=SEARCH_SIZE, inputs=[SOURCE], alpha=0.05,
        skip_reasons={
            "С6": "замкнутая формула, сеток или разрешений нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана; внешняя цель проверяется отдельно",
            "С9": "детерминированная формула не является выборкой конечного размера",
            "С11": "нет нескольких независимых статистик согласия",
        },
        claim_family="neutrino_mixing_theta23",
        observable="sin²(theta23)", measurement_source="PDG 2024",
        uncertainty_type="both", expected_effect_sigma=0.55,
        resolution_sigma=1.0, novelty_key="neutrino:theta23:external:v1",
        information_class="novelty", purpose="audit",
        models=["формула Trinity", "PDG 2024"],
        independent_of=["zeta", "BBLM", "CKM", "neutrino theta13"],
        precision_gain=None, out_of_sample=True, tests_independent="unknown",
        notes="Наблюдаемое 0.545985 прочитано из корпуса; внешняя цель отделена от строки корпуса.",
    )
]
