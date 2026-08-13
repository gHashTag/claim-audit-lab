"""Аудит трёх чисел из каталога трансцендентных выражений.

Каждый эталон вычисляется из определения выражения, а наблюдение извлекается
из корпуса. Вердикт возвращает только каскад золотого сита. Вторая реализация
эталона нужна для независимой проверки вычисления; ручной вывод здесь не
используется.
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
    "transcendental-numbers.md"
)
DISPLAY_QUANTUM = Decimal("0.00001")


def _phi_decimal():
    return (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)


def _round_decimal(value):
    return float(value.quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP))


def _high_precision_power(base, exponent):
    """Вычислить base**exponent через Decimal ln/exp."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _round_decimal(
            (Decimal(str(base)).ln() * exponent).exp()
        )


def _high_precision_exp(exponent):
    with localcontext() as ctx:
        ctx.prec = 70
        return _round_decimal(exponent.exp())


def _high_precision_ln(value):
    with localcontext() as ctx:
        ctx.prec = 70
        return _round_decimal(value.ln())


def reference_3_inv_phi():
    """Эталон для 3^(1/φ), вычисленный через Decimal ln/exp."""
    with localcontext() as ctx:
        ctx.prec = 70
        phi = _phi_decimal()
        return _round_decimal((phi**-1 * Decimal(3).ln()).exp())


def reference_3_inv_phi_alt():
    """Второй путь для 3^(1/φ): двоичная арифметика pow."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(3.0, 1.0 / phi), 5))


def reference_e_phi():
    """Эталон для e^φ, вычисленный через Decimal.exp."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _high_precision_exp(_phi_decimal())


def reference_e_phi_alt():
    """Второй путь для e^φ: math.exp."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.exp(phi), 5))


def reference_ln3():
    """Эталон для ln(3), вычисленный через Decimal.ln."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _high_precision_ln(Decimal(3))


def reference_ln3_alt():
    """Второй путь для ln(3): math.log."""
    return float(round(math.log(3.0), 5))


def _observed(expression):
    """Извлечь значение нужного выражения из таблицы корпуса."""
    patterns = {
        "3^(1/φ)": r"\$3\^\{1/\\varphi\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "e^φ": r"\$e\^\\varphi\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "ln(3)": r"\$\\ln\(3\)\$\s*\|\s*([0-9]+\.[0-9]{5})",
    }
    pattern = patterns[expression]
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            match = re.search(pattern, line)
            if match:
                return float(match.group(1))
    raise ValueError("не найдено выражение %s" % expression)


def observed_3_inv_phi():
    return _observed("3^(1/φ)")


def observed_e_phi():
    return _observed("e^φ")


def observed_ln3():
    return _observed("ln(3)")


def wrong_plus_one(reference):
    """Подставка, отличающаяся на единицу."""
    return reference() + 1.0


def wrong_neighbour(reference):
    """Подставка, отличающаяся на одну десятитысячную."""
    return reference() + 0.0001


def wrong_other_expression():
    """Подставка: выражение с другим основанием или аргументом."""
    return _high_precision_power(2, _phi_decimal())


def wrong_other_exp():
    """Подставка для e^φ: e^(1/φ), а не e^φ."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _high_precision_exp(_phi_decimal() ** -1)


def wrong_ln():
    """Подставка для ln(3): ln(φ), а не ln(3)."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _high_precision_ln(_phi_decimal())


def _alt_tolerance(reference, alternate):
    values = [reference(), alternate()]
    return max(abs(value - values[-1]) for value in values) / abs(values[-1])


def _sample(observed):
    return lambda: [observed()]


def _sample_mean(values):
    return float(sum(values) / len(values))


def _skip_reasons():
    return {
        "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity)",
        "С21": "линейная форма в логарифмах для этого утверждения не задана; алгебраическая объяснимость разбирается на семействе",

        "С6": "фиксированное математическое выражение не имеет сетки или разрешения",
        "С7": "проверяется одно детерминированное значение, а не несколько оценивателей",
        "С8": "погрешность входных данных не заявлена; число является округлённой записью",
        "С9": "утверждение не является выборочной оценкой конечной выборки",
        "С11": "одна статистика детерминированного значения; тест слишком хорошего согласия неприменим",
        "С15": "утверждение о математическом числе, внешняя физическая цель отсутствует",
        "С16": "перебор формул и поиск цели в этом утверждении не заявлены",
        "С17": "длина описания неприменима к записи математического числа",
        "С18": "объявленная область перебора к этому утверждению не относится",
        "С19": "ошибка double несопоставимо меньше шага округления числа",
    }


def _claim(name, source, reference, alternate, observed, wrong, null_model):
    return Claim(
        name=name,
        source=source,
        stated=observed(),
        reference=reference,
        observed=observed,
        wrong=wrong,
        null_model=null_model,
        null_expect=null_model(),
        null_kind="negative",
        tolerance=0.0,
        sample=_sample(observed),
        statistics={"value": _sample_mean},
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        inputs=[SOURCE],
        skip_reasons=_skip_reasons(),
        notes=(
            "Эталон вычисляется по определению выражения и округляется до "
            "пяти знаков после запятой — как в строке корпуса."
        ),
    )


def _selfcheck():
    """Проверки модулей-эталонов и подставок до запуска каскада."""
    assert reference_3_inv_phi() == 1.97186
    assert reference_3_inv_phi_alt() == reference_3_inv_phi()
    assert reference_e_phi() == 5.04317
    assert reference_e_phi_alt() == reference_e_phi()
    assert reference_ln3() == 1.09861
    assert reference_ln3_alt() == reference_ln3()
    assert abs(wrong_plus_one(reference_3_inv_phi) - reference_3_inv_phi()) > 0.1
    assert abs(wrong_neighbour(reference_3_inv_phi) - reference_3_inv_phi()) > 0.00001
    assert abs(wrong_other_expression() - reference_3_inv_phi()) > 0.1
    assert abs(wrong_other_exp() - reference_e_phi()) > 0.1
    assert abs(wrong_ln() - reference_ln3()) > 0.1


_selfcheck()


CLAIMS = [
    _claim(
        "3^(1/φ) напечатано как 1,97186",
        "docs/docs/math-foundations/transcendental-numbers.md:184",
        reference_3_inv_phi,
        reference_3_inv_phi_alt,
        observed_3_inv_phi,
        [
            lambda: wrong_plus_one(reference_3_inv_phi),
            lambda: wrong_neighbour(reference_3_inv_phi),
            wrong_other_expression,
        ],
        wrong_other_expression,
    ),
    _claim(
        "e^φ напечатано как 5,04317",
        "docs/docs/math-foundations/transcendental-numbers.md:201",
        reference_e_phi,
        reference_e_phi_alt,
        observed_e_phi,
        [
            lambda: wrong_plus_one(reference_e_phi),
            lambda: wrong_neighbour(reference_e_phi),
            wrong_other_exp,
        ],
        wrong_other_exp,
    ),
    _claim(
        "ln(3) напечатано как 1,09861",
        "docs/docs/math-foundations/transcendental-numbers.md:215",
        reference_ln3,
        reference_ln3_alt,
        observed_ln3,
        [
            lambda: wrong_plus_one(reference_ln3),
            lambda: wrong_neighbour(reference_ln3),
            wrong_ln,
        ],
        wrong_ln,
    ),
]
