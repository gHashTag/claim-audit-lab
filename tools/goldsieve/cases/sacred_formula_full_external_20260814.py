"""Внешний аудит трёх формул из SACRED_FORMULA_FULL.md.

Числа из документа используются только для проверки контекста и поля
``stated_target``. Эталон каждой формулы вычисляется заново, а вердикт
предсказания берётся из внешней цели CODATA. Печатные числа рядом с формулами
не используются как внешний тест.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_SACRED_FULL",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/SACRED_FORMULA_FULL.md",
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


def _log_route(value):
    """Второй путь вычисления: сумма логарифмов и экспонента."""
    return math.exp(math.log(value["n"]) + value["k"] * math.log(3.0)
                    + value["m"] * math.log(math.pi)
                    + value["p"] * math.log(PHI) + value["q"])


def _formula(params):
    n, k, m, p, q = params
    return n * 3.0**k * math.pi**m * PHI**p * math.e**q


def _target(value, uncertainty, url):
    return {"value": value, "uncertainty": uncertainty, "source": url}


TARGET_MP_ME = lambda: _target(
    1836.152673426, 3.2e-8,
    "CODATA 2022, https://physics.nist.gov/cuu/pdf/wall_2022.pdf",
)
TARGET_MU_ME = lambda: _target(
    206.7682827, 4.6e-6,
    "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?mmusme",
)
TARGET_TAU_ME = lambda: _target(
    3477.23, 0.23,
    "CODATA 2022, https://physics.nist.gov/cgi-bin/cuu/Value?mtausme",
)


def mp_me_reference():
    return _formula((6, 0, 5, 0, 0))


def mp_me_alt():
    return _log_route({"n": 6, "k": 0, "m": 5, "p": 0, "q": 0})


def mp_me_observed():
    return _read(
        ["$$\\boxed{\\frac{m_p}{m_e} = 6\\pi^5}$$",
         "**Experimental**: 1836.15267343(11)"],
        mp_me_reference(),
    )


def mu_me_reference():
    return _formula((17, -2, 2, 5, 0))


def mu_me_alt():
    return _log_route({"n": 17, "k": -2, "m": 2, "p": 5, "q": 0})


def mu_me_observed():
    return _read(
        ["$$\\frac{m_\\mu}{m_e} = \\frac{17}{9} \\times \\pi^2 \\times \\varphi^5$$",
         "Experimental: 206.7682830"],
        mu_me_reference(),
    )


def tau_me_reference():
    return _formula((76, 2, 1, 1, 0))


def tau_me_alt():
    return _log_route({"n": 76, "k": 2, "m": 1, "p": 1, "q": 0})


def tau_me_observed():
    return _read(
        ["$$\\frac{m_\\tau}{m_e} = 76 \\times 3^2 \\times \\pi \\times \\varphi$$",
         "Experimental: 3477.23"],
        tau_me_reference(),
    )


def _wrong(reference):
    return [
        lambda: reference() * 1.5,
        lambda: reference() * 0.5,
        lambda: reference() * 1.01,
    ]


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
            (-1, 4), eps, ranges=RANGES, trials=1000, seed=20260814,
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


def _algebraic(target, params, reference):
    def run():
        tgt = target()
        return {
            "target": tgt["value"],
            "coeffs": params,
            "has_pi": True,
            "rel_deviation": abs(reference() - tgt["value"]) / abs(tgt["value"]),
            "max_coeff": max(abs(x) for x in params),
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


def _claim(name, source_line, params, reference, alternate, observed,
           target, stated_target, notes):
    return Claim(
        name=name,
        source=source_line,
        claim_kind="prediction",
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=_wrong(reference),
        # Позитивный контроль воспроизводит эталон через log/exp, не читая
        # печатное значение и не прореживая исходный расчёт.
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1.0e-6,
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
        notes=("Внешняя цель отделена от строки Experimental; сигмы, "
               "множественность и MDL остаются раздельными координатами. " + notes),
    )


def _selfcheck():
    for reference, alternate, observed in (
        (mp_me_reference, mp_me_alt, mp_me_observed),
        (mu_me_reference, mu_me_alt, mu_me_observed),
        (tau_me_reference, tau_me_alt, tau_me_observed),
    ):
        assert abs(reference() - alternate()) / abs(reference()) < 1.0e-12
        assert math.isfinite(observed())
        for wrong in _wrong(reference):
            assert abs(wrong() - reference()) > 1.0e-6
    assert family.declared_size(RANGES) == SEARCH_SIZE


_selfcheck()


CLAIMS = [
    _claim(
        "Формула 6π⁵ воспроизводит отношение масс протона и электрона",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_FULL.md:170-176",
        (6, 0, 5, 0, 0), mp_me_reference, mp_me_alt, mp_me_observed,
        TARGET_MP_ME, lambda: 1836.15267343,
        "CODATA знает отношение с относительной погрешностью около 1,7×10⁻¹¹; "
        "поэтому процент из корпуса не заменяет проверку в сигмах.",
    ),
    _claim(
        "Формула 17π²φ⁵/9 воспроизводит отношение масс мюона и электрона",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_FULL.md:180-185",
        (17, -2, 2, 5, 0), mu_me_reference, mu_me_alt, mu_me_observed,
        TARGET_MU_ME, lambda: 206.7682830,
        "Внешняя цель взята со страницы CODATA/NIST, а не из поля Error корпуса.",
    ),
    _claim(
        "Формула 76·3²·π·φ воспроизводит отношение масс тау-лептона и электрона",
        "deploy/trinity-nexus/docs/research/SACRED_FORMULA_FULL.md:187-192",
        (76, 2, 1, 1, 0), tau_me_reference, tau_me_alt, tau_me_observed,
        TARGET_TAU_ME, lambda: 3477.23,
        "Внешняя цель CODATA/NIST имеет стандартную неопределённость 0,23, "
        "что существенно шире округления корпуса.",
    ),
]
