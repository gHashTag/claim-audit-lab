"""Аудит строки о стандартном отклонении расстояний дзета.

Наблюдение читается из строки Comparison with Literature. Эталон не берётся
из напечатанного 0,4220: он вычисляется из плотности Вигнера численным
интегрированием. Второй путь использует замкнутую формулу для второго момента.
"""

import math
import re

from goldsieve.sieve import Claim


SOURCE = (
    "/home/user/workspace/corpus/trinity/data/zeta/"
    "zeta_bin_analysis_update.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _observed():
    """Наблюдение берётся только из строки Comparison with Literature."""
    match = re.search(
        # Подпись столбца уточнена в корпусе (пункт 1 приказа 2026-08-18):
        # 0,4220 — это std Wigner surmise, а не точный закон GUE. Парсер
        # принимает ОБА варианта подписи, чтобы уточнение терминологии не
        # выглядело изменением утверждения.
        r"\| Std vs GUE(?: Wigner surmise)? \| ([0-9.]+) vs ([0-9.]+) \("
        r"[−-][0-9.]+%\) \|",
        _text(),
    )
    if not match:
        raise AssertionError("строка Std vs GUE не найдена")
    return float(match.group(1))


def _wigner_density(x):
    return (32.0 / math.pi**2) * x**2 * math.exp(-4.0 * x**2 / math.pi)


def _reference():
    """Вычислить стандартное отклонение интегрированием плотности."""
    n = 20000
    hi = 8.0
    step = hi / n
    values = []
    for i in range(n + 1):
        x = i * step
        weight = 1.0 if i in (0, n) else (4.0 if i % 2 else 2.0)
        values.append(weight * x * x * _wigner_density(x))
    second_moment = step * math.fsum(values) / 3.0
    return math.sqrt(second_moment - 1.0)


def _reference_alt():
    """Второй путь: аналитический второй момент распределения Вигнера."""
    return math.sqrt(3.0 * math.pi / 8.0 - 1.0)


def _wrong():
    """Подставка, отличимая от эталона и от наблюдаемой строки."""
    return 0.5


def _negative_control():
    return 1.0


def _sample():
    return [_observed()]


def _mean(values):
    return sum(values) / len(values)


def _alt_tolerance():
    delta = abs(_reference() - _reference_alt())
    return max(1.0e-10, 10.0 * delta)


def _selfcheck():
    assert abs(_observed() - 0.4009) < 1.0e-12
    assert abs(_reference_alt() - 0.4220) < 2.0e-5
    assert abs(_reference() - _reference_alt()) < 1.0e-8
    assert abs(_wrong() - _reference()) > 0.05
    assert abs(_negative_control() - _reference()) > 0.5


_selfcheck()


CLAIMS = [
    Claim(
        name="Стандартное отклонение расстояний дзета равно 0,4009 против 0,4220 по GUE",
        source="data/zeta/zeta_bin_analysis_update.md:124",
        stated=_observed(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_negative_control,
        null_expect=1.0,
        null_kind="negative",
        tolerance=0.001,
        sample=_sample,
        statistics={"value": _mean},
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        inputs=[SOURCE],
        claim_family="сравнение стандартного отклонения расстояний с GUE",
        observable="стандартное отклонение нормированных расстояний",
        measurement_source="корпус Trinity, строка Std vs GUE",
        uncertainty_type="none",
        novelty_key="zeta:std_gue_comparison:v1",
        information_class="novelty",
        purpose="audit",
        models=["численное интегрирование плотности Вигнера",
                "аналитический второй момент плотности Вигнера"],
        independent_of={},
        notes=(
            "0,4009 извлекается из строки корпуса. 0,4220 не используется "
            "как эталон: reference получает его через интеграл, а "
            "reference_alt — через формулу второго момента. Подставка "
            "0,5 и контроль 1,0 различаются ситом."
        ),
        skip_reasons={
            "С6": "для замкнутого интеграла сетка сходимости не является частью утверждения",
            "С7": "проверяется одна статистика",
            "С8": "погрешность строки корпуса не задана",
            "С9": "это агрегат корпуса без выборочной модели",
            "С10": "сырая выборка расстояний в кейс не входит",
            "С11": "проверяется одна статистика",
            "С15": "внешней измеренной цели нет",
            "С16": "перебора гипотез нет",
            "С17": "описательная статистика не является формулой-кандидатом",
            "С18": "границы семейства формул не заявлены",
            "С19": "численная ошибка интеграла меньше округления строки",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма кандидата не заявлена",
        },
    )
]
