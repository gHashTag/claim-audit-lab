"""Аудит численного значения формулы размерности M-теории.

Проверяется одно утверждение из корпуса Trinity: формула
4·3^(-4)·φ^5·e^3 даёт 11,0001. Эталон вычисляется из определения
констант, наблюдение извлекается из строки корпуса, а второй метод
использует Decimal и ряд для e.
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
DISPLAY_QUANTUM = Decimal("0.0001")


def _phi_float():
    """Вычислить золотое сечение из его определения."""
    return (1.0 + math.sqrt(5.0)) / 2.0


def _exact_float(phi_power=5):
    """Вычислить 4·3^(-4)·φ^5·e^3, не читая число из корпуса."""
    return 4.0 * 3.0 ** (-4) * _phi_float() ** phi_power * math.e ** 3


def _display(value):
    """Округлить значение до четырёх знаков, как в таблице корпуса."""
    return float(
        Decimal(str(value)).quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)
    )


def reference():
    """Эталон: вычисляемая формула с точным показателем φ^5."""
    return _display(_exact_float())


def _exp_decimal():
    """Вычислить e рядом суммы 1/k! в Decimal-арифметике."""
    total = Decimal(1)
    term = Decimal(1)
    for k in range(1, 240):
        term /= Decimal(k)
        total += term
    return total


def _exact_decimal(precision, phi_power=5):
    """Второй вычислимый путь: Decimal, sqrt и ряд для e."""
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return (
            Decimal(4)
            * Decimal(3) ** Decimal(-4)
            * phi ** Decimal(phi_power)
            * _exp_decimal() ** Decimal(3)
        )


def reference_alt():
    """Независимый эталон через Decimal и ряд для числа e."""
    return _display(_exact_decimal(80))


def observed_from_corpus():
    """Извлечь заявленное значение из строки таблицы, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "M-theory dim" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                raise ValueError("строка M-теории имеет неожиданный формат")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[2])
            if not match:
                raise ValueError("значение размерности не найдено")
            return float(match.group(1))
    raise ValueError("строка M-theory dim не найдена")


def wrong_minus_one():
    """Подставка: значение на единицу меньше вычисляемого эталона."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на единицу больше вычисляемого эталона."""
    return reference() + 1.0


def wrong_changed_exponent():
    """Подставка: та же конструкция с ошибочной степенью φ^4."""
    return _display(_exact_float(phi_power=4))


def negative_control():
    """Негативный контроль: ошибочная степень φ не должна совпасть с эталоном."""
    return wrong_changed_exponent()


def deterministic_sample():
    """Сырая наблюдаемая величина из одной строки таблицы корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Терпимость второго метода из его разброса по рабочей точности."""
    values = [_display(_exact_decimal(precision)) for precision in (60, 80, 100)]
    high = values[-1]
    spread = max(abs(value - high) for value in values)
    return spread / abs(high) if high else 0.0


def _selfcheck():
    """Самопроверка эталона, альтернативы и подставок."""
    assert reference() > 0.0
    assert reference_alt() == reference()
    assert abs(wrong_minus_one() - reference()) > 0.01
    assert abs(wrong_plus_one() - reference()) > 0.01
    assert abs(wrong_changed_exponent() - reference()) > 0.1


_selfcheck()


CLAIMS = [
    Claim(
        name="Формула размерности M-теории даёт 11,0001",
        source="docs/docs/math-foundations/sacred-formulas.md:197",
        stated=11.0001,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_changed_exponent],
        null_model=negative_control,
        null_expect=wrong_changed_exponent(),
        null_kind="negative",
        tolerance=0.00001,
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
            "Сравнение выполняется на точности источника: четыре знака после "
            "запятой. Строка помечена в корпусе как согласующаяся с теорией; "
            "это не расширяется до проверки физической модели."
        ),
    ),
]
