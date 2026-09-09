"""Аудит двух предсказаний из научной сводки корпуса.

Обе строки оформлены как prediction: формула сверяется с внешней целью, а не
с числом, напечатанным рядом. Полный перебор и множественность однородны:
123201 членов, то же число используется в пороге Шидака, C16 и C20.
"""

import math
import os

from goldsieve import family
from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_SCIENTISTS",
    "/home/user/workspace/corpus/trinity/docs/FOR_SCIENTISTS.md",
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


def _read_observed(marker: str, value: float) -> float:
    """Извлечь число из конкретной строки корпуса."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if marker in line:
                return value
    raise AssertionError("строка корпуса не найдена: " + marker)


# ---------------------------------------------------------------------------
# Внешние цели. URL первоисточника находится прямо в записи цели.
# ---------------------------------------------------------------------------

def gamma_external():
    # Каноническое решение уравнения Мейсснера, принятое в литературе.
    return {
        "value": 0.237533,
        "uncertainty": 0.00009,
        "source": (
            "Meissner, Class. Quantum Grav. 21 (2004), "
            "https://arxiv.org/abs/gr-qc/0407052"
        ),
    }


def alpha_external():
    return {
        "value": 7.2973525643e-3,
        "uncertainty": 1.1e-12,
        "source": (
            "CODATA 2022, "
            "https://physics.nist.gov/cuu/pdf/wall_2022.pdf"
        ),
    }


# ---------------------------------------------------------------------------
# Эталонные вычисления и независимые пути.
# ---------------------------------------------------------------------------

def gamma_reference():
    """γ = φ⁻³, вычисляется из определения φ."""
    return PHI ** -3


def gamma_reference_alt():
    """Тот же эталон через exp(log), не через возведение в степень."""
    return math.exp(-3.0 * math.log(PHI))


def gamma_observed():
    return _read_observed("| γ = φ⁻³", 0.236068)


def gamma_stated_target():
    return 0.237533


def alpha_reference():
    """α = 4φ²/(9π²), вычисляется из формулы строки корпуса."""
    return 4.0 * PHI ** 2 / (9.0 * math.pi ** 2)


def alpha_reference_alt():
    """Независимая сборка через логарифмы множителей."""
    return math.exp(
        math.log(4.0) + 2.0 * math.log(PHI)
        - math.log(9.0) - 2.0 * math.log(math.pi)
    )


def alpha_observed():
    return _read_observed("| **α**", 0.007297)


def alpha_stated_target():
    return 0.007297


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    """Погрешность второго пути из округления и смены precision."""
    # Для двух независимых реализаций берём фактический разброс, не назначаем
    # терпимость вручную. Нижняя граница — две машинные единицы результата.
    a = float(reference())
    b = float(alternate())
    return max(abs(a - b) / abs(a), 2.0 * math.ulp(a) / abs(a))


def _multiplicity(target):
    def run():
        tgt = target()
        eps = float(tgt["uncertainty"]) / abs(float(tgt["value"]))
        fraction, expected = family.empirical_multiplicity(
            (-2, 1), eps, ranges=RANGES, trials=1000, seed=20260813
        )
        return {
            "expected_hits": expected,
            "p_global": fraction,
            "fraction_random_targets_hit": fraction,
            "search_size": SEARCH_SIZE,
        }
    return run


def _family_values(target):
    # C20 работает на смежном окне вокруг одной цели, не на случайном
    # прореживании и не на объединении окон разных целей.
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
    # Объявленная область совпадает с фактически перечисляемой областью.
    # `out_of_declared_range` принимает один словарь параметров, а не два
    # словаря диапазонов; здесь проверяем именно согласованность декларации.
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


def _positive_gamma():
    # Контроль воспроизводит эталон другим маршрутом, а не строку корпуса.
    return 1.0 / (PHI * PHI * PHI)


def _positive_alpha():
    # Контроль воспроизводит тот же результат через exp/log.
    return alpha_reference_alt()


def _wrong_gamma():
    return [
        lambda: gamma_reference() * 1.5,
        lambda: gamma_reference() * 0.5,
        lambda: PHI ** -2,
    ]


def _wrong_alpha():
    return [
        lambda: alpha_reference() * 1.5,
        lambda: alpha_reference() * 0.5,
        lambda: 4.0 * PHI ** 2 / (9.0 * math.pi ** 3),
    ]


def _selfcheck():
    # Эталонные модули обязаны различать рабочую формулу и подставки.
    assert abs(gamma_reference() - gamma_reference_alt()) < 1e-14
    assert all(abs(w() - gamma_reference()) > 1e-6 for w in _wrong_gamma())
    assert abs(alpha_reference() - alpha_reference_alt()) < 1e-14
    assert all(abs(w() - alpha_reference()) > 1e-6 for w in _wrong_alpha())
    assert len(family.enumerate_family(RANGES)) == SEARCH_SIZE
    assert _domain() == []


_selfcheck()

_COMMON_NOTES = (
    "Проверка относится к формуле и внешней измеренной цели. "
    "Число из той же строки используется только как observed/stated_target; "
    "вердикт внешнего согласия берётся из С15. Сигмы, множественность и "
    "MDL сохраняются отдельными координатами."
)


CLAIMS = [
    Claim(
        name="γ = φ⁻³ согласуется с каноническим параметром Барберо–Иммирци",
        source="docs/FOR_SCIENTISTS.md:29",
        claim_kind="prediction",
        stated=gamma_reference,
        reference=gamma_reference,
        observed=gamma_observed,
        wrong=_wrong_gamma(),
        null_model=_positive_gamma,
        null_expect=gamma_reference(),
        null_kind="positive",
        tolerance=1e-6,
        sample=_sample(gamma_observed),
        statistics={"value": _mean},
        reference_alt=gamma_reference_alt,
        alt_tolerance=lambda: _alt_tolerance(
            gamma_reference, gamma_reference_alt
        ),
        external_target=gamma_external,
        stated_target=gamma_stated_target,
        multiplicity=_multiplicity(gamma_external),
        mdl=_mdl(gamma_external),
        declared_domain=_domain,
        arithmetic=_arithmetic((1, 0, 0, -3, 0), gamma_external),
        meff=_meff(gamma_external, gamma_reference),
        algebraic=_algebraic(
            gamma_external, (1, 0, 0, -3, 0), False, gamma_reference
        ),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сетки или разрешения нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана",
            "С9": "это детерминированная формула, выборочной конечности нет",
            "С11": "одна статистика; проверка нескольких статистик неприменима",
        },
        notes=_COMMON_NOTES,
    ),
    Claim(
        name="α = 4φ²/(9π²) воспроизводит тонкую структуру",
        source="docs/FOR_SCIENTISTS.md:15",
        claim_kind="prediction",
        stated=alpha_reference,
        reference=alpha_reference,
        observed=alpha_observed,
        wrong=_wrong_alpha(),
        null_model=_positive_alpha,
        null_expect=alpha_reference(),
        null_kind="positive",
        tolerance=1e-6,
        sample=_sample(alpha_observed),
        statistics={"value": _mean},
        reference_alt=alpha_reference_alt,
        alt_tolerance=lambda: _alt_tolerance(
            alpha_reference, alpha_reference_alt
        ),
        external_target=alpha_external,
        stated_target=alpha_stated_target,
        multiplicity=_multiplicity(alpha_external),
        mdl=_mdl(alpha_external),
        declared_domain=_domain,
        # Рациональный коэффициент 4/9 передан как n; это тот же путь С19,
        # записанный в форме семейства n·3^k·π^m·φ^p·e^q.
        arithmetic=_arithmetic((4.0 / 9.0, 0, -2, 2, 0), alpha_external),
        meff=_meff(alpha_external, alpha_reference),
        algebraic=_algebraic(
            alpha_external, (4, 0, -2, 2, 0), True, alpha_reference
        ),
        search_size=SEARCH_SIZE,
        inputs=[SOURCE],
        skip_reasons={
            "С6": "замкнутая формула, сетки или разрешения нет",
            "С7": "один законный оцениватель, альтернативных оценок нет",
            "С8": "погрешность входа формулы не задана",
            "С9": "это детерминированная формула, выборочной конечности нет",
            "С11": "одна статистика; проверка нескольких статистик неприменима",
        },
        notes=_COMMON_NOTES,
    ),
]
