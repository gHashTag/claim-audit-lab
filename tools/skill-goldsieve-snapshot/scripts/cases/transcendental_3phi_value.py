"""Аудит численного значения 3^φ из корпуса Trinity.

Проверяется числовая часть утверждения. Эталон вычисляется из определения
φ=(1+sqrt(5))/2 и округляется до пяти знаков после запятой — именно с такой
точностью число напечатано в источнике. Никакой вердикт не выводится вручную:
его возвращает каскад золотого сита.
"""

from decimal import Decimal, localcontext, ROUND_HALF_UP
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/transcendental-numbers.md"
DISPLAY_QUANTUM = Decimal("0.00001")


def _phi_decimal():
    return (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)


def _display_decimal(value):
    return value.quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)


def reference():
    """Эталон: независимое высокоточное вычисление 3^φ через exp(φ·ln 3)."""
    with localcontext() as ctx:
        ctx.prec = 60
        value = (_phi_decimal() * Decimal(3).ln()).exp()
        return float(_display_decimal(value))


def reference_alt():
    """Альтернативный путь: стандартная двоичная арифметика pow."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(3.0, phi), 5))


def observed_from_corpus():
    """Извлекает напечатанное значение, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "3^\\varphi = 3^{(1+\\sqrt{5})/2}" in line:
                match = re.search(r"=\s*([0-9]+\.[0-9]{5})\.\.\.", line)
                if match:
                    return float(match.group(1))
    raise ValueError("строка с числом 3^φ не найдена")


def wrong_plus_one():
    """Подставка: ошибка на единицу в напечатанном числе."""
    return reference() + 1.0


def wrong_other_base():
    """Подставка: значение 2^φ вместо 3^φ."""
    with localcontext() as ctx:
        ctx.prec = 60
        return float(_display_decimal((_phi_decimal() * Decimal(2).ln()).exp()))


def negative_control():
    """Негативный контроль: та же степень, но случайно заменённое основание 2."""
    return wrong_other_base()


def deterministic_sample():
    """Сырая наблюдаемая величина из строки корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Порог второго пути из половины единицы последнего напечатанного знака."""
    return float(Decimal("0.000005") / Decimal(str(reference())))


CLAIMS = [
    Claim(
        name="3^φ напечатано как 5,91559",
        source="docs/docs/math-foundations/transcendental-numbers.md:169",
        stated=observed_from_corpus(),
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_plus_one, wrong_other_base],
        null_model=negative_control,
        null_expect=wrong_other_base(),
        null_kind="negative",
        tolerance=0.0,
        sample=deterministic_sample,
        statistics={"value": sample_mean},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={
            "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity); для одиночного утверждения перебор не воспроизводим",
            "С21": "алгебраическая объяснимость разбирается на семействе формул целиком (случай sacred_fit_multiplicity); здесь линейная форма в логарифмах не задана",
            "С15": "утверждение о числе в документе, внешней величины нет",
            "С16": "перебора формул в этом утверждении нет",
            "С17": "длина описания неприменима: это не закон, а запись числа",
            "С18": "объявленных границ перебора это утверждение не касается",
            "С6": "число вычисляется по фиксированному определению; сетка или разрешение не являются частью утверждения",
            "С7": "проверяется точное числовое значение, а не статистическая оценка с несколькими оценивателями",
            "С8": "погрешность входа не задана: это округлённое отображение, а не измерительный прибор",
            "С9": "утверждение не является выборочным измерением, зависящим от конечного размера данных",
            "С11": "есть только одна статистика одного детерминированного значения; множественный тест слишком хорошего согласия неприменим",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes="Число проверяется в точности отображения источника: пять знаков после запятой.",
    ),
]
