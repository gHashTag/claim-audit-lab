"""Аудит численного значения формулы для фазы Дирака CP.

Проверяется одна строка корпуса Trinity: формула
7·3^(-2)·π^4·φ^(-4)·e^3 даёт 222,0°. Эталон вычисляется из определения
констант, наблюдение извлекается из строки корпуса, а второй метод использует
Decimal, формулу Машина для π и ряд для e.
"""

from decimal import Decimal, ROUND_HALF_UP, localcontext
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/"
    "sacred-formulas.md"
)
DISPLAY_QUANTUM = Decimal("0.1")


def _phi_float():
    """Вычислить золотое сечение из его определения."""
    return (1.0 + math.sqrt(5.0)) / 2.0


def _exact_float(phi_power=-4):
    """Вычислить формулу, не читая результат из корпуса."""
    return (
        7.0
        * 3.0 ** (-2)
        * math.pi**4
        * _phi_float() ** phi_power
        * math.e**3
    )


def _display(value):
    """Округлить вычисленное значение до одного знака, как в таблице."""
    return float(
        Decimal(str(value)).quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)
    )


def reference():
    """Эталон: вычисляемая формула со степенью φ^(-4)."""
    return _display(_exact_float())


def _atan_decimal(x):
    """Ряд arctan для независимого вычисления π в Decimal."""
    total = Decimal(0)
    term = x
    power = x * x
    sign = Decimal(1)
    for denominator in range(1, 1200, 2):
        total += sign * term / Decimal(denominator)
        term *= power
        sign = -sign
    return total


def _pi_decimal():
    """Формула Машина: π = 16 arctan(1/5) − 4 arctan(1/239)."""
    return (
        Decimal(16) * _atan_decimal(Decimal(1) / Decimal(5))
        - Decimal(4) * _atan_decimal(Decimal(1) / Decimal(239))
    )


def _exp_decimal():
    """Вычислить e рядом суммы 1/k! в Decimal-арифметике."""
    total = Decimal(1)
    term = Decimal(1)
    for k in range(1, 240):
        term /= Decimal(k)
        total += term
    return total


def _exact_decimal(precision, phi_power=-4):
    """Второй вычислимый путь: Decimal, sqrt, π по Машину и ряд для e."""
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return (
            Decimal(7)
            * Decimal(3) ** Decimal(-2)
            * _pi_decimal() ** Decimal(4)
            * phi ** Decimal(phi_power)
            * _exp_decimal() ** Decimal(3)
        )


def reference_alt():
    """Независимый эталон через Decimal-арифметику."""
    return _display(_exact_decimal(80))


def observed_from_corpus():
    """Извлечь заявленное табличное значение, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "Dirac CP phase" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                raise ValueError("строка фазы Дирака имеет неожиданный формат")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[2])
            if not match:
                raise ValueError("значение фазы Дирака не найдено")
            return float(match.group(1))
    raise ValueError("строка Dirac CP phase не найдена")


def wrong_minus_one():
    """Подставка: значение на один градус меньше эталона."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на один градус больше эталона."""
    return reference() + 1.0


def wrong_changed_exponent():
    """Подставка: та же конструкция с ошибочной степенью φ^(-3)."""
    return _display(_exact_float(phi_power=-3))


def negative_control():
    """Негативный контроль: ошибочная степень φ не должна совпасть с эталоном."""
    return wrong_changed_exponent()


def deterministic_sample():
    """Сырая наблюдаемая величина из одной строки таблицы корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Терпимость второго метода из разброса по точности Decimal."""
    values = [_display(_exact_decimal(precision)) for precision in (60, 80, 100)]
    high = values[-1]
    spread = max(abs(value - high) for value in values)
    return spread / abs(high) if high else 0.0


def _selfcheck():
    """Проверить эталон, альтернативу и подставки до запуска сита."""
    assert reference() == 222.0
    assert reference_alt() == reference()
    assert abs(wrong_minus_one() - reference()) > 0.01
    assert abs(wrong_plus_one() - reference()) > 0.01
    assert abs(wrong_changed_exponent() - reference()) > 0.1


_selfcheck()


CLAIMS = [
    Claim(
        name="Формула фазы Дирака CP даёт 222,0°",
        source="docs/docs/math-foundations/sacred-formulas.md:202",
        stated=222.0,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_changed_exponent],
        null_model=negative_control,
        null_expect=wrong_changed_exponent(),
        null_kind="negative",
        tolerance=0.0,
        sample=deterministic_sample,
        statistics={"value": sample_mean},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        claim_kind="prediction",
        # фактический перебор семейства: 9*13*9*13*9 = 123 201 комбинация
        # (подтверждено обходом таблиц корпуса). Из него ВЫВОДИТСЯ порог С15.
        search_size=123201,
        skip_reasons={
            "С16": "множественность разобрана отдельным случаем sacred_fit_multiplicity",
            "С17": "длина описания разобрана отдельным случаем sacred_fit_multiplicity",
            "С18": "объявленные границы разобраны отдельным случаем sacred_fit_multiplicity",
            "С6": (
                "эталон вычисляется по фиксированной формуле; численной сетки "
                "или разрешения нет"
            ),
            "С7": (
                "проверяется одно детерминированное значение, а не оценка "
                "с несколькими законными оценивателями"
            ),
            "С8": (
                "формула и табличное округление заданы детерминированно; "
                "погрешность входных физических данных не заявлена"
            ),
            "С9": (
                "утверждение является расчётом по формуле, а не измерением "
                "конечной выборки"
            ),
            "С11": (
                "доступна одна детерминированная статистика; тест слишком "
                "хорошего согласия неприменим"
            ),
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes=(
            "Сравнение выполняется на точности источника: один знак после "
            "запятой. Строка помечена в корпусе как непроверенное предсказание; "
            "аудит вычисляет только численное значение формулы."
        ),
    ),
]
