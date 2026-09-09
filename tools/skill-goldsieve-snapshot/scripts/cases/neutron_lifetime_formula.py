"""Аудит численного значения формулы времени жизни нейтрона.

Проверяется одно численное утверждение из корпуса Trinity: формула
2·3^4·π^4·φ^(-6) даёт 879,4 с. Эталон вычисляется заново, наблюдение
извлекается из таблицы корпуса, а второй метод использует Decimal и ряд
Машина для π. Вердикт возвращает только каскад золотого сита.
"""

from decimal import Decimal, ROUND_HALF_UP, localcontext
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md"
DISPLAY_QUANTUM = Decimal("0.1")


def _phi_float():
    return (1.0 + math.sqrt(5.0)) / 2.0


def _exact_float():
    """Вычислить формулу в двоичной арифметике, не брать число из текста."""
    return 2.0 * 3.0 ** 4 * math.pi ** 4 * _phi_float() ** (-6)


def _display(value):
    """Привести вычисление к одному знаку после запятой, как в источнике."""
    return float(Decimal(str(value)).quantize(DISPLAY_QUANTUM,
                                               rounding=ROUND_HALF_UP))


def reference():
    """Эталон: формула 2·3^4·π^4·φ^(-6), округлённая до точности таблицы."""
    return _display(_exact_float())


def _atan_decimal(x):
    """Ряд arctan для независимого вычисления π в Decimal-арифметике."""
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
    return (Decimal(16) * _atan_decimal(Decimal(1) / Decimal(5))
            - Decimal(4) * _atan_decimal(Decimal(1) / Decimal(239)))


def _exact_decimal(precision):
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return (Decimal(2) * Decimal(3) ** 4 * _pi_decimal() ** 4
                * phi ** Decimal(-6))


def reference_alt():
    """Второй эталон: Decimal, sqrt и ряд Машина для π."""
    return _display(_exact_decimal(80))


def observed_from_corpus():
    """Извлечь заявленное значение из таблицы, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "Neutron lifetime" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                raise ValueError("строка времени жизни нейтрона имеет неожиданный формат")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[2])
            if not match:
                raise ValueError("число времени жизни нейтрона не найдено")
            return float(match.group(1))
    raise ValueError("строка времени жизни нейтрона не найдена")


def wrong_minus_one():
    """Подставка: значение на одну секунду меньше вычисляемого эталона."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на одну секунду больше вычисляемого эталона."""
    return reference() + 1.0


def wrong_changed_exponent():
    """Подставка: та же формула с ошибочной степенью φ^(-5)."""
    return _display(2.0 * 3.0 ** 4 * math.pi ** 4 * _phi_float() ** (-5))


def negative_control():
    """Негативный контроль: изменение степени должно нарушить результат."""
    return wrong_changed_exponent()


def deterministic_sample():
    """Сырая наблюдаемая величина из одной строки таблицы корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Терпимость второго метода из его разброса по точности вычисления."""
    values = [_display(_exact_decimal(precision)) for precision in (60, 80, 100)]
    high = values[-1]
    spread = max(abs(value - high) for value in values)
    return spread / abs(high) if high else 0.0


def _selfcheck():
    """Самопроверка эталона и подставок до передачи Claim в сито."""
    assert reference() == 879.4
    assert reference_alt() == reference()
    assert abs(wrong_minus_one() - reference()) > 0.01
    assert abs(wrong_plus_one() - reference()) > 0.01
    assert abs(wrong_changed_exponent() - reference()) > 100.0


_selfcheck()


CLAIMS = [
    Claim(
        name="Формула времени жизни нейтрона даёт 879,4 с",
        source="docs/docs/math-foundations/sacred-formulas.md:194",
        stated=879.4,
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
            "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity); для одиночного утверждения перебор не воспроизводим",
            "С21": "алгебраическая объяснимость разбирается на семействе формул целиком (случай sacred_fit_multiplicity); здесь линейная форма в логарифмах не задана",
            "С16": "множественность разобрана отдельным случаем sacred_fit_multiplicity",
            "С17": "длина описания разобрана отдельным случаем sacred_fit_multiplicity",
            "С18": "объявленные границы разобраны отдельным случаем sacred_fit_multiplicity",
            "С6": "эталон вычисляется по фиксированной формуле; численной сетки или разрешения нет",
            "С7": "проверяется одно детерминированное значение, а не статистическая оценка с несколькими оценивателями",
            "С8": "источник задаёт округлённое табличное значение, но погрешность входных данных отдельно не заявлена",
            "С9": "утверждение не является выборочным измерением, зависящим от конечного размера выборки",
            "С11": "доступна одна детерминированная статистика; тест слишком хорошего согласия неприменим",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes=(
            "Сравнение выполняется на точности источника: один знак после запятой. "
            "Неизмеренный статус строки не расширяется до проверки внешнего физического эксперимента."
        ),
    ),
]
