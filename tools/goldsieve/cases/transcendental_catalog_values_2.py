"""Аудит трёх следующих чисел из каталога трансцендентных выражений.

Эталон вычисляется из определения выражения, а наблюдение извлекается из
корпуса. Вердикт возвращает только каскад золотого сита.
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
QUANTUM = Decimal("0.00001")


def _phi():
    return (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)


def _round(value):
    return float(value.quantize(QUANTUM, rounding=ROUND_HALF_UP))


def _reference(exponent):
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((_phi() * exponent).exp())


def _reference_alt(exponent):
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.exp(phi * exponent), 5))


def reference_3_phi2():
    """Эталон 3^(φ²), через exp(φ²·ln 3)."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((_phi() ** 2 * Decimal(3).ln()).exp())


def reference_3_phi2_alt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(3.0, phi**2), 5))


def reference_3_inv_phi2():
    """Эталон 3^(1/φ²), через exp((φ⁻²)·ln 3)."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((_phi() ** -2 * Decimal(3).ln()).exp())


def reference_3_inv_phi2_alt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(3.0, phi**-2), 5))


def reference_3_sqrt5():
    """Эталон 3^√5, через exp(√5·ln 3)."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((Decimal(5).sqrt() * Decimal(3).ln()).exp())


def reference_3_sqrt5_alt():
    return float(round(math.pow(3.0, math.sqrt(5.0)), 5))


def _observed(expression):
    patterns = {
        "3^(φ²)": r"\$3\^\{\\varphi\^2\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "3^(1/φ²)": r"\$3\^\{1/\\varphi\^2\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "3^√5": r"\$3\^\{\\sqrt\{5\}\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
    }
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            match = re.search(patterns[expression], line)
            if match:
                return float(match.group(1))
    raise ValueError("не найдено выражение %s" % expression)


def observed_3_phi2():
    return _observed("3^(φ²)")


def observed_3_inv_phi2():
    return _observed("3^(1/φ²)")


def observed_3_sqrt5():
    return _observed("3^√5")


def _plus_one(reference):
    return reference() + 1.0


def _wrong_base():
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((_phi() ** 2 * Decimal(2).ln()).exp())


def _wrong_exponent():
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((_phi() * Decimal(3).ln()).exp())


def _wrong_sqrt_exponent():
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((Decimal(3).sqrt() * Decimal(3).ln()).exp())


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    values = [reference(), alternate()]
    return max(abs(value - values[-1]) for value in values) / abs(values[-1])


def _skips():
    return {
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


def _claim(name, line, reference, alternate, observed, wrong):
    return Claim(
        name=name,
        source=f"docs/docs/math-foundations/transcendental-numbers.md:{line}",
        stated=observed(),
        reference=reference,
        observed=observed,
        wrong=[lambda: _plus_one(reference), wrong],
        null_model=wrong,
        null_expect=wrong(),
        null_kind="negative",
        tolerance=0.0,
        sample=_sample(observed),
        statistics={"value": _mean},
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        inputs=[SOURCE],
        skip_reasons=_skips(),
        notes="Эталон вычислен из определения выражения и округлён до пяти знаков.",
    )


def _selfcheck():
    assert reference_3_phi2() == 17.74678
    assert reference_3_phi2_alt() == reference_3_phi2()
    assert reference_3_inv_phi2() == 1.52140
    assert reference_3_inv_phi2_alt() == reference_3_inv_phi2()
    assert reference_3_sqrt5() == 11.66475
    assert reference_3_sqrt5_alt() == reference_3_sqrt5()
    assert abs(_plus_one(reference_3_phi2) - reference_3_phi2()) > 0.1
    assert abs(_wrong_base() - reference_3_phi2()) > 0.1
    assert abs(_wrong_exponent() - reference_3_inv_phi2()) > 0.1
    assert abs(_wrong_sqrt_exponent() - reference_3_sqrt5()) > 0.1


_selfcheck()


CLAIMS = [
    _claim(
        "3^(φ²) напечатано как 17,74678",
        185,
        reference_3_phi2,
        reference_3_phi2_alt,
        observed_3_phi2,
        _wrong_base,
    ),
    _claim(
        "3^(1/φ²) напечатано как 1,52140",
        186,
        reference_3_inv_phi2,
        reference_3_inv_phi2_alt,
        observed_3_inv_phi2,
        _wrong_exponent,
    ),
    _claim(
        "3^√5 напечатано как 11,66475",
        187,
        reference_3_sqrt5,
        reference_3_sqrt5_alt,
        observed_3_sqrt5,
        _wrong_sqrt_exponent,
    ),
]
