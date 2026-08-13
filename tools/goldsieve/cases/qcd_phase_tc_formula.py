"""Аудит численного значения формулы для температуры перехода КХД.

Проверяется одна строка корпуса Trinity: формула
7·3^0·π·φ²·e даёт 156,5 МэВ. Эталон вычисляется из самой формулы,
наблюдение извлекается из таблицы корпуса, а второй эталон использует
Decimal и формулу Машина для π. Сито, а не этот модуль, возвращает вердикт.
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
    return (1.0 + math.sqrt(5.0)) / 2.0


def _exact_float():
    """Вычислить формулу, не брать результат из корпуса."""
    return 7.0 * math.pi * _phi_float() ** 2 * math.e


def _display(value):
    """Округлить вычисленное значение до точности таблицы."""
    return float(
        Decimal(str(value)).quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)
    )


def reference():
    """Эталон: 7·3^0·π·φ²·e, отображаемый с одним знаком после запятой."""
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


def _exact_decimal(precision):
    """Второе вычисление с Decimal, sqrt и exp."""
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return Decimal(7) * _pi_decimal() * phi**2 * Decimal(1).exp()


def reference_alt():
    """Второй эталон, вычисленный в Decimal-арифметике."""
    return _display(_exact_decimal(80))


def observed_from_corpus():
    """Извлечь заявленное табличное значение, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "QCD phase" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                raise ValueError("строка QCD имеет неожиданный формат")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[2])
            if not match:
                raise ValueError("число QCD не найдено")
            return float(match.group(1))
    raise ValueError("строка QCD phase не найдена")


def wrong_minus_one():
    """Подставка: значение на одну единицу меньше эталона."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на одну единицу больше эталона."""
    return reference() + 1.0


def wrong_changed_phi_power():
    """Подставка: та же формула с ошибочной степенью φ³."""
    return _display(7.0 * math.pi * _phi_float() ** 3 * math.e)


def negative_control():
    """Негативный контроль: ошибочная степень φ должна быть отвергнута."""
    return wrong_changed_phi_power()


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
    """Проверить эталон и подставки до передачи Claim в сито."""
    assert reference() == 156.5
    assert reference_alt() == reference()
    assert abs(wrong_minus_one() - reference()) > 0.01
    assert abs(wrong_plus_one() - reference()) > 0.01
    assert abs(wrong_changed_phi_power() - reference()) > 10.0


_selfcheck()


CLAIMS = [
    Claim(
        name="Формула QCD phase даёт 156,5 МэВ",
        source="docs/docs/math-foundations/sacred-formulas.md:201",
        stated=156.5,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_changed_phi_power],
        null_model=negative_control,
        null_expect=wrong_changed_phi_power(),
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
                "проверяется одно детерминированное значение, а не "
                "статистическая оценка с несколькими оценивателями"
            ),
            "С8": (
                "источник задаёт округлённое табличное значение, но погрешность "
                "входных данных отдельно не заявлена"
            ),
            "С9": (
                "утверждение не является выборочным измерением, зависящим от "
                "конечного размера выборки"
            ),
            "С11": (
                "доступна одна детерминированная статистика; тест слишком "
                "хорошего согласия неприменим"
            ),
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes=(
            "Сравнение выполняется на точности источника: один знак после "
            "запятой. Статус строки «Unmeasured» не расширяется до проверки "
            "внешнего физического эксперимента."
        ),
    ),
]
