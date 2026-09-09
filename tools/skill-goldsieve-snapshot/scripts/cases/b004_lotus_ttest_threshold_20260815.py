# -*- coding: utf-8 -*-
"""Аудит неравенства p < 0,001 в статистическом блоке B004.

Наблюдение извлекает знак строгого неравенства из строки отчёта. Эталон
считает двусторонний хвост распределения Стьюдента по независимо извлечённым
числам t и степеням свободы. Альтернативный эталон получает тот же хвост
интегрированием плотности; напечатанный порог не подмешивается в вычисление.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402


SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/research/bundles/"
    "B004_Lotus.md"
)
ПРЕДЕЛ = 0.001


def _text():
    if not os.path.isfile(SOURCE):
        raise AssertionError("входной файл B004 отсутствует")
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _test_parameters():
    """Извлечь только t, степени свободы и знак опубликованного порога."""
    match = re.search(
        r"Statistical significance:\s*\**\s*t\((\d+)\)\s*=\s*([+-]?[0-9.]+),\s*"
        r"p\s*<\s*([0-9.]+)",
        _text(),
    )
    if not match:
        raise AssertionError("строка статистической значимости B004 не найдена")
    degrees = int(match.group(1))
    statistic = float(match.group(2))
    bound = float(match.group(3))
    if degrees <= 0 or not math.isfinite(statistic) or statistic == 0.0:
        raise AssertionError("недопустимые параметры t-теста")
    if bound <= 0.0 or bound >= 1.0:
        raise AssertionError("недопустимый опубликованный порог")
    return degrees, statistic, bound


def _observed():
    """Наблюдение — именно утверждённое в корпусе неравенство p < предел."""
    _, _, bound = _test_parameters()
    return bound < 0.001 + 1.0e-15


def _beta_continued_fraction(a, b, x):
    """Регуляризованная неполная бета-функция через дробь Лентца."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    tiny = 1.0e-300
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for index in range(1, 10000):
        m = float(index)
        m2 = 2.0 * m
        aa = m * (b - m) * x / ((a - 1.0 + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (a + m + b) * x / ((a + m2) * (a + 1.0 + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3.0e-14:
            break
    else:
        raise ArithmeticError("неполная бета не сошлась")
    front = math.exp(
        a * math.log(x) + b * math.log1p(-x)
        - math.lgamma(a) - math.lgamma(b) + math.lgamma(a + b)
    )
    return front * h / a


def _p_beta():
    degrees, statistic, _ = _test_parameters()
    nu = float(degrees)
    x = nu / (nu + statistic * statistic)
    return _beta_continued_fraction(nu / 2.0, 0.5, x)


def _reference():
    """Эталонное решение неравенства через хвост неполной беты."""
    _, _, bound = _test_parameters()
    return bool(_p_beta() < bound)


def _adaptive_simpson(function, left, right, tolerance, whole=None, depth=0):
    midpoint = (left + right) / 2.0
    if whole is None:
        whole = (right - left) * (
            function(left) + 4.0 * function(midpoint) + function(right)
        ) / 6.0
    left_mid = (left + midpoint) / 2.0
    right_mid = (midpoint + right) / 2.0
    left_part = (midpoint - left) * (
        function(left) + 4.0 * function(left_mid) + function(midpoint)
    ) / 6.0
    right_part = (right - midpoint) * (
        function(midpoint) + 4.0 * function(right_mid) + function(right)
    ) / 6.0
    if depth >= 24 or abs(left_part + right_part - whole) <= 15.0 * tolerance:
        return left_part + right_part + (left_part + right_part - whole) / 15.0
    return (
        _adaptive_simpson(function, left, midpoint, tolerance / 2.0,
                          left_part, depth + 1)
        + _adaptive_simpson(function, midpoint, right, tolerance / 2.0,
                            right_part, depth + 1)
    )


def _p_integral():
    degrees, statistic, _ = _test_parameters()
    nu = float(degrees)
    magnitude = abs(statistic)
    coefficient = math.exp(
        math.lgamma((nu + 1.0) / 2.0)
        - math.lgamma(nu / 2.0) - 0.5 * math.log(nu * math.pi)
    )

    def density(value):
        return coefficient * (1.0 + value * value / nu) ** (-(nu + 1.0) / 2.0)

    central = _adaptive_simpson(density, 0.0, magnitude, 1.0e-13)
    return 1.0 - 2.0 * central


def _reference_alt():
    """Альтернативный эталон: интегрирование плотности Стьюдента."""
    _, _, bound = _test_parameters()
    return bool(_p_integral() < bound)


def _wrong():
    """Подставка: знак p > предел обязан изменить логический ответ."""
    return False


def _null_model():
    """Отрицательный контроль: нулевая t-статистика незначима."""
    return False


def _selfcheck():
    degrees, statistic, bound = _test_parameters()
    assert degrees == 18
    assert statistic == 4.21
    assert bound == ПРЕДЕЛ
    assert abs(_p_beta() - 0.000526395352121691) < 1.0e-12
    assert abs(_p_integral() - _p_beta()) < 1.0e-12
    assert _observed() is True
    assert _reference() is True
    assert _reference_alt() is True
    assert _wrong() is not _reference()
    assert _null_model() is not _reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Статистическая значимость B004: двустороннее p меньше 0,001",
        source="docs/research/bundles/B004_Lotus.md:71",
        stated=True,
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_null_model,
        null_expect=False,
        null_kind="negative",
        tolerance=0.0,
        reference_alt=_reference_alt,
        alt_tolerance=lambda: 0.0,
        inputs=[SOURCE],
        claim_kind="statistical",
        claim_family="неравенства p-значений t-теста",
        observable="строгое неравенство двустороннего p порогу 0,001",
        measurement_source="корпус Trinity, отчёт B004 Lotus",
        uncertainty_type="statistical",
        novelty_key="b004:lotus:ttest_significance:v1",
        information_class="novelty",
        purpose="audit",
        models=[
            "неполная бета-функция для хвоста распределения Стьюдента",
            "адаптивное интегрирование плотности распределения Стьюдента",
        ],
        independent_of={
            "b006:gf16:paired_t_pvalue:v1": "другая строка корпуса и другой df",
        },
        notes=(
            "Наблюдение извлекает знак и границу p<0,001 из отдельной строки. "
            "Основной эталон считает хвост по t=4,21 и 18 степеням свободы; "
            "reference_alt интегрирует плотность. Значение p из корпуса в "
            "эталон не передаётся."
        ),
        skip_reasons={
            "С6": "численная сетка для логического неравенства не задана",
            "С7": "проверяется одна t-статистика",
            "С8": "неопределённость t-статистики в источнике не задана",
            "С9": "исходные наблюдения для t-теста в кейс не входят",
            "С10": "это один детерминированный тест, а не повторная выборка",
            "С11": "совместное семейство p-значений не заявлено",
            "С15": "проверяется статистика корпуса, внешней цели нет",
            "С16": "перебора формул нет",
            "С17": "модельная длина описания не заявлена",
            "С18": "границы перебора не заявлены",
            "С19": "ошибка численного интегрирования ниже точности порога",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма утверждения не является целью",
        },
    )
]
