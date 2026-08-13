"""Аудит процента ошибки в строке отношения масс протона и электрона.

Проверяется одно численное утверждение из корпуса Trinity: для формулы
9·3^4·φ^4·e^(-1) в таблице указан процент ошибки 0,109 %. Эталон
вычисляется из формулы и округляется до трёх знаков процента; наблюдение
извлекается из таблицы корпуса. Вердикт возвращает только золотое сито.
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
DISPLAY_QUANTUM = Decimal("0.001")


def _phi_float():
    """Вычислить φ из определения золотого сечения."""
    return (1.0 + math.sqrt(5.0)) / 2.0


def _formula_float():
    """Вычислить значение формулы, не читая результат из корпуса."""
    return 9.0 * 3.0 ** 4 * _phi_float() ** 4 * math.e ** (-1)


def _error_percent(value, target):
    """Абсолютная относительная ошибка в процентах."""
    return abs(value - target) / abs(target) * 100.0


def _display(value):
    """Округлить процент ошибки до трёх знаков после запятой."""
    return float(Decimal(str(value)).quantize(DISPLAY_QUANTUM,
                                               rounding=ROUND_HALF_UP))


def reference():
    """Эталон: вычислимый процент ошибки формулы против табличной цели."""
    value = _formula_float()
    return _display(_error_percent(value, 1836.15))


def _exp_decimal():
    """Вычислить e рядом 1/k! в Decimal-арифметике."""
    total = Decimal(1)
    term = Decimal(1)
    for k in range(1, 240):
        term /= Decimal(k)
        total += term
    return total


def _formula_decimal(precision):
    """Второй путь: Decimal, sqrt(5) и ряд для e."""
    with localcontext() as ctx:
        ctx.prec = precision
        phi = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
        return Decimal(9) * Decimal(3) ** 4 * phi ** 4 * _exp_decimal() ** Decimal(-1)


def reference_alt():
    """Независимый эталон через Decimal и ряд для числа e."""
    with localcontext() as ctx:
        ctx.prec = 80
        value = _formula_decimal(80)
        target = Decimal("1836.15")
        error = abs(value - target) / abs(target) * Decimal(100)
        return float(Decimal(str(error)).quantize(DISPLAY_QUANTUM,
                                                  rounding=ROUND_HALF_UP))


def observed_from_corpus():
    """Извлечь поле Error из строки отношения масс, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "m_p/m_e" not in line:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 5:
                raise ValueError("строка m_p/m_e имеет неожиданный формат")
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*%", cells[4])
            if not match:
                raise ValueError("процент ошибки m_p/m_e не найден")
            return float(match.group(1))
    raise ValueError("строка m_p/m_e не найдена")


def wrong_minus_point_one():
    """Подставка: процент на 0,1 пункта ниже вычисляемого эталона."""
    return reference() - 0.1


def wrong_plus_point_one():
    """Подставка: процент на 0,1 пункта выше вычисляемого эталона."""
    return reference() + 0.1


def wrong_changed_exponent():
    """Подставка: ошибка при замене степени φ^4 на φ^3."""
    wrong_value = 9.0 * 3.0 ** 4 * _phi_float() ** 3 * math.e ** (-1)
    return _display(_error_percent(wrong_value, 1836.15))


def negative_control():
    """Негативный контроль: ошибная степень φ не должна совпасть с эталоном."""
    return wrong_changed_exponent()


def deterministic_sample():
    """Сырая наблюдаемая величина из одной строки таблицы корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Терпимость второго метода из разброса по рабочей точности."""
    values = []
    for precision in (60, 80, 100):
        with localcontext() as ctx:
            ctx.prec = precision
            value = _formula_decimal(precision)
            target = Decimal("1836.15")
            error = abs(value - target) / abs(target) * Decimal(100)
            values.append(float(Decimal(str(error)).quantize(DISPLAY_QUANTUM,
                                                              rounding=ROUND_HALF_UP)))
    high = values[-1]
    spread = max(abs(value - high) for value in values)
    return spread / abs(high) if high else 0.0


def _selfcheck():
    """Самопроверка эталонов и подставок до передачи Claim в сито."""
    assert reference() == 0.110
    assert reference_alt() == reference()
    assert abs(wrong_minus_point_one() - reference()) > 0.01
    assert abs(wrong_plus_point_one() - reference()) > 0.01
    assert abs(wrong_changed_exponent() - reference()) > 1.0


_selfcheck()


CLAIMS = [
    Claim(
        name="Для m_p/m_e указана ошибка 0,109 %",
        source="docs/docs/math-foundations/sacred-formulas.md:37",
        stated=0.109,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_point_one, wrong_plus_point_one, wrong_changed_exponent],
        null_model=negative_control,
        null_expect=wrong_changed_exponent(),
        null_kind="negative",
        tolerance=0.0,
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
            "С6": "эталон вычисляется по фиксированной формуле; численной сетки или разрешения нет",
            "С7": "проверяется детерминированный процент, а не статистическая оценка с несколькими оценивателями",
            "С8": "входная цель и округление таблицы заданы; отдельная погрешность физических входных данных не заявлена",
            "С9": "утверждение не является измерением конечной выборки",
            "С11": "одна детерминированная статистика; тест слишком хорошего согласия неприменим",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes=(
            "Сравнение выполняется в единицах процентных пунктов с точностью до "
            "трёх знаков после запятой. Проверяется арифметика столбца Error, "
            "а не физическая истинность целевого отношения масс."
        ),
    ),
]
