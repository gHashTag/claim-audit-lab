"""Аудит значения формулы m_s/m_e в каталоге Trinity.

Проверяется ровно одно численное утверждение. Эталон — вычисление формулы
32*pi^(-1)*phi^6. Наблюдение извлекается из строки каталога, а второй эталон
вычисляется высокоточной Decimal-арифметикой.
"""

from decimal import Decimal, localcontext
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md"
TARGET = 182.8


def _phi_float():
    return (1.0 + math.sqrt(5.0)) / 2.0


def _computed_float(p_exponent=6):
    return 32.0 * math.pi ** (-1) * _phi_float() ** p_exponent


def reference():
    """Эталон: значение формулы из таблицы."""
    return _computed_float()


def _atan_decimal(x):
    """Ряд arctan для независимого вычисления pi в Decimal-арифметике."""
    total = Decimal(0)
    term = x
    power = x * x
    sign = Decimal(1)
    for denominator in range(1, 500, 2):
        total += sign * term / Decimal(denominator)
        term *= power
        sign = -sign
    return total


def _pi_decimal():
    return Decimal(16) * _atan_decimal(Decimal(1) / Decimal(5)) - Decimal(4) * _atan_decimal(Decimal(1) / Decimal(239))


def _computed_decimal(precision):
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return Decimal(32) / _pi_decimal() * phi ** 6


def reference_alt():
    """Второй метод: Decimal, sqrt и формула pi через ряд Machin."""
    return float(_computed_decimal(80))


def observed_from_corpus():
    """Извлекает заявленное значение из строки каталога, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if re.match(r"^\|\s*m_s/m_e\s*\|", line):
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) != 4:
                    raise ValueError("строка m_s/m_e имеет неожиданный формат")
                match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", cells[1])
                if not match:
                    raise ValueError("значение m_s/m_e в строке не найдено")
                return float(match.group(1))
    raise ValueError("строка m_s/m_e не найдена")


def wrong_minus_one():
    """Подставка: значение на единицу меньше вычисляемого."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на единицу больше вычисляемого."""
    return reference() + 1.0


def wrong_changed_exponent():
    """Подставка: вычисление по изменённой степени phi, p=5."""
    return _computed_float(p_exponent=5)


def negative_control():
    """Негативный контроль: изменённая формула не должна дать тот же эффект."""
    return _computed_float(p_exponent=5)


def deterministic_sample():
    """Сырая наблюдаемая величина из одной строки каталога."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Порог из разброса Decimal по точности и двойной арифметики."""
    values = [float(_computed_decimal(p)) for p in (60, 80, 100)]
    high = values[-1]
    decimal_spread = max(abs(v - high) for v in values) / abs(high)
    float_roundoff = abs(reference() - high) / abs(high)
    return 2.0 * max(decimal_spread, float_roundoff, 1e-18)


def _selfcheck():
    """Самопроверка эталона с подставкой и независимым методом."""
    assert reference() > 0.0
    assert abs(wrong_minus_one() - reference()) > 1e-6
    assert abs(wrong_plus_one() - reference()) > 1e-6
    assert abs(wrong_changed_exponent() - reference()) > 1e-6
    assert abs(reference_alt() - reference()) < 1e-10


_selfcheck()


CLAIMS = [
    Claim(
        name="Для m_s/m_e в каталоге указано значение 182,8",
        source="deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md:37",
        stated=TARGET,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_changed_exponent],
        null_model=negative_control,
        null_expect=wrong_changed_exponent(),
        null_kind="negative",
        tolerance=0.000001,
        sample=deterministic_sample,
        statistics={"value": sample_mean},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={
            "С15": "утверждение о числе в документе, внешней величины нет",
            "С16": "перебора формул в этом утверждении нет",
            "С17": "длина описания неприменима: это не закон, а запись числа",
            "С18": "объявленных границ перебора это утверждение не касается",
            "С6": "эталон — точный расчёт по фиксированной формуле; сетки или разрешения нет",
            "С7": "проверяется одна относительная ошибка, законных оценивателей нет",
            "С8": "цель и формула заданы детерминированно; погрешность входа не заявлена",
            "С9": "это воспроизводимый расчёт по строке каталога, а не выборочное измерение",
            "С11": "доступна одна статистика детерминированного значения; тест слишком хорошего согласия неприменим",
        },
        notes=(
            "Вычисляемый эталон получает значение 32*pi^(-1)*phi^6. "
            "Независимый путь использует Decimal и ряд Machin для pi."
        ),
    ),
]
