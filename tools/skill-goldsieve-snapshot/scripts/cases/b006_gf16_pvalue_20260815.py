# -*- coding: utf-8 -*-
"""Аудит p-значения парного t-теста в отчёте B006 GF16.

Наблюдение извлекается из строки с t-статистикой и p-значением. Эталон
вычисляет двусторонний хвост распределения Стьюдента через регуляризованную
неполную бета-функцию. Альтернативный путь интегрирует плотность распределения
Стьюдента адаптивным методом Симпсона; напечатанное p-значение эталону не
передаётся.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402


SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/research/bundles/"
    "B006_GF16.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _test_parameters():
    match = re.search(
        r"Paired t-test:\s*t\((\d+)\)\s*=\s*([+-]?[0-9.]+),\s*p\s*=\s*([0-9.]+)",
        _text(),
    )
    if not match:
        raise AssertionError("строка парного t-теста не найдена")
    return int(match.group(1)), float(match.group(2)), float(match.group(3))


def _observed():
    """Наблюдение читается только из напечатанного p-значения."""
    return _test_parameters()[2]


def _beta_continued_fraction(a, b, x):
    """Неполная бета через continued fraction без внешнего пакета."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    max_iter = 10000
    eps = 3.0e-14
    tiny = 1.0e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for index in range(1, max_iter + 1):
        m = float(index)
        m2 = 2.0 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= eps:
            break
    else:
        raise ArithmeticError("неполная бета не сошлась")
    front = math.exp(
        a * math.log(x)
        + b * math.log1p(-x)
        - math.lgamma(a)
        - math.lgamma(b)
        + math.lgamma(a + b)
    )
    return front * h / a


def _reference():
    """Эталон: p = I_(nu/(nu+t²))(nu/2, 1/2)."""
    degrees, statistic, _ = _test_parameters()
    nu = float(degrees)
    x = nu / (nu + statistic * statistic)
    return _beta_continued_fraction(nu / 2.0, 0.5, x)


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
        _adaptive_simpson(function, left, midpoint, tolerance / 2.0, left_part, depth + 1)
        + _adaptive_simpson(function, midpoint, right, tolerance / 2.0, right_part, depth + 1)
    )


def _reference_alt():
    """Альтернативный путь: интеграл плотности t от 0 до |t|."""
    degrees, statistic, _ = _test_parameters()
    nu = float(degrees)
    magnitude = abs(statistic)
    coefficient = math.exp(
        math.lgamma((nu + 1.0) / 2.0)
        - math.lgamma(nu / 2.0)
        - 0.5 * math.log(nu * math.pi)
    )

    def density(value):
        return coefficient * (1.0 + value * value / nu) ** (-(nu + 1.0) / 2.0)

    central_mass = _adaptive_simpson(density, 0.0, magnitude, 1.0e-13)
    return 1.0 - 2.0 * central_mass


def _wrong():
    """Подставка: ошибочный односторонний хвост не равен эталону."""
    return _reference() / 2.0


def _negative_control():
    """Отрицательный контроль для нулевой статистики: p = 1."""
    return 1.0


def _selfcheck():
    degrees, statistic, stated = _test_parameters()
    assert degrees == 14
    assert statistic == 0.16
    assert stated == 0.87
    assert abs(_reference() - 0.8751666274241385) < 1.0e-12
    assert abs(_reference_alt() - _reference()) < 1.0e-12
    assert abs(_observed() - 0.87) < 1.0e-12
    assert _wrong() != _reference()
    assert _negative_control() != _reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Двустороннее p-значение парного t-теста равно 0,87",
        source="docs/research/bundles/B006_GF16.md:76-79",
        stated=_observed(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_negative_control,
        null_expect=1.0,
        null_kind="negative",
        tolerance=0.01,
        reference_alt=_reference_alt,
        alt_tolerance=lambda: 1.0e-12,
        inputs=[SOURCE],
        claim_kind="statistical",
        claim_family="двусторонние p-значения парного t-теста",
        observable="двустороннее p-значение при t(14)=0,16",
        measurement_source="корпус Trinity, отчёт B006 GF16",
        uncertainty_type="statistical",
        novelty_key="b006:gf16:paired_t_pvalue:v1",
        information_class="novelty",
        purpose="audit",
        models=[
            "регуляризованная неполная бета-функция",
            "численное интегрирование плотности Стьюдента",
        ],
        independent_of=["b006:gf16:ppl_delta:v1"],
        notes=(
            "Наблюдение извлекает p из строки Paired t-test. Эталон вычисляет "
            "двусторонний хвост по t и числу степеней свободы; альтернативный "
            "путь интегрирует плотность. Подставка проверяет ошибочный "
            "односторонний хвост, отрицательный контроль задаёт p=1."
        ),
        skip_reasons={
            "С6": "сетка численного разрешения для p-значения не задана",
            "С7": "проверяется одна заранее заданная t-статистика",
            "С8": "неопределённость p-значения в источнике не задана",
            "С9": "повторные оценки теста в источник не входят",
            "С10": "это один детерминированный пример, а не выборка повторных тестов",
            "С11": "проверяется одно p-значение, совместная вероятность не заявлена",
            "С15": "проверяется статистика корпуса, внешней цели нет",
            "С16": "перебора формул нет",
            "С17": "модельная длина описания не заявлена",
            "С18": "границы перебора не заявлены",
            "С19": "численная ошибка ниже точности напечатанного p-значения",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма утверждения не заявлена",
        },
    )
]
