"""Аудит формул масс бозонов против внешних измерений.

Это не сверка с числами, напечатанными рядом: reference пересчитывает
буквально записанное выражение, observed читает отдельную строку корпуса,
а claim_kind=prediction требует независимую внешнюю цель.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = os.environ.get(
    "TRINITY_FORMULAS",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/formulas.md",
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
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    for marker in markers:
        if marker not in text:
            raise AssertionError("строка корпуса не найдена: " + marker)
    return value


# Внешние цели взяты из первичных листингов PDG, а не из корпуса.
def w_target():
    return {
        "value": 80.3692,
        "uncertainty": 0.0133,
        "source": "PDG 2024, https://pdg.lbl.gov/2024/listings/rpp2024-list-w-boson.pdf",
    }


def higgs_target():
    return {
        "value": 125.20,
        "uncertainty": 0.11,
        "source": "PDG 2024, https://pdg.lbl.gov/2024/listings/rpp2024-list-higgs-boson.pdf",
    }


# Эталон вычисляется из определения формулы, не цитируется.
def w_reference():
    return 3.0 ** 4 * PHI * math.pi


def w_reference_alt():
    return math.exp(4.0 * math.log(3.0) + math.log(PHI) + math.log(math.pi))


def higgs_reference():
    return 3.0 ** 3 * PHI ** 3 * math.pi ** 2 / math.e


def higgs_reference_alt():
    return math.exp(3.0 * math.log(3.0) + 3.0 * math.log(PHI) + 2.0 * math.log(math.pi) - 1.0)


# Это observed: отдельное число, напечатанное в строке Calculated корпуса.
def w_observed():
    return _read_observed(["M(W) = 3^4 * phi * pi GeV/c^2", "**Calculated**: 80.39"], 80.39)


def higgs_observed():
    return _read_observed(["M(H) = 3^3 * phi^3 * pi^2 / e GeV/c^2", "**Calculated**: ~125.1"], 125.1)


def w_stated_target():
    return 80.38


def higgs_stated_target():
    return 125.1


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
            (-1, 4), eps, ranges=RANGES, trials=1000, seed=20260813
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


# Позитивный контроль вычисляет тот же reference независимым логарифмическим путём.
def _positive_w():
    return math.exp(4.0 * math.log(3.0) + math.log(PHI) + math.log(math.pi))


def _positive_higgs():
    return math.exp(3.0 * math.log(3.0) + 3.0 * math.log(PHI) + 2.0 * math.log(math.pi) - 1.0)


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() + 100.0,
    ]


def _selfcheck():
    assert abs(w_reference() - w_reference_alt()) < 1e-12
    assert abs(higgs_reference() - higgs_reference_alt()) < 1e-12
    assert abs(_positive_w() - w_reference()) < 1e-12
    assert abs(_positive_higgs() - higgs_reference()) < 1e-12
    assert all(abs(w() - w_reference()) > 1e-6 for w in _wrong(w_reference))
    assert all(abs(w() - higgs_reference()) > 1e-6 for w in _wrong(higgs_reference))
    assert family.declared_size(RANGES) == SEARCH_SIZE
    assert _domain() == []
    assert w_target()["uncertainty"] > 0 and higgs_target()["uncertainty"] > 0


_selfcheck()

_COMMON_SKIP = {
    "С6": "замкнутая формула, сеток или разрешений нет",
    "С7": "один законный оцениватель, альтернативных оценок нет",
    "С8": "погрешность входа формулы не задана; погрешность внешней цели проверяется отдельно",
    "С9": "это детерминированная формула, выборочной конечности нет",
    "С11": "одна статистика; проверка нескольких статистик неприменима",
}


def _claim(name, source, reference, alternate, observed, target, stated_target,
           positive, params, notes):
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
        skip_reasons=dict(_COMMON_SKIP),
        notes=(
            "Буквальная формула корпуса проверена против внешнего PDG-листинга. "
            "Число из Calculated используется только как observed; stated_target "
            "отделён от external_target. Сигмы, множественность и MDL остаются "
            "раздельными координатами. " + notes
        ),
    )


CLAIMS = [
    _claim(
        "Формула M(W) = 3^4·φ·π согласуется с массой W-бозона",
        "docs/docs/math-foundations/formulas.md:202-206",
        w_reference,
        w_reference_alt,
        w_observed,
        w_target,
        w_stated_target,
        _positive_w,
        (1, 4, 1, 1, 0),
        "Внешняя цель PDG 2024: 80,3692 ± 0,0133 ГэВ; проверяется именно буквальная запись формулы.",
    ),
    _claim(
        "Формула M(H) = 3^3·φ^3·π^2/e согласуется с массой бозона Хиггса",
        "docs/docs/math-foundations/formulas.md:226-230",
        higgs_reference,
        higgs_reference_alt,
        higgs_observed,
        higgs_target,
        higgs_stated_target,
        _positive_higgs,
        (1, 3, 2, 3, -1),
        "Внешняя цель PDG 2024: 125,20 ± 0,11 ГэВ; проверяется именно буквальная запись формулы.",
    ),
]
