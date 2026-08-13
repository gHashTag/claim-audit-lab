"""Машинный аудит трёх следующих строк каталога трансцендентных чисел.

Эталон каждого числа вычисляется из определения выражения через Decimal с
повышенной точностью и округлением до пяти знаков. Наблюдение извлекается из
корпуса отдельно. Вердикт не формулируется вручную: его возвращает каскад
золотого сита.
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


def _power(base, exponent):
    """Вычисляем степень через exp(exponent*ln(base))."""
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((base.ln() * exponent).exp())


def reference_phi_phi():
    return _power(_phi(), _phi())


def reference_phi_inv_phi():
    phi = _phi()
    return _power(phi, phi ** -1)


def reference_phi_phi2():
    phi = _phi()
    return _power(phi, phi ** 2)


def reference_phi_phi_alt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(phi, phi), 5))


def reference_phi_inv_phi_alt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(phi, 1.0 / phi), 5))


def reference_phi_phi2_alt():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return float(round(math.pow(phi, phi ** 2), 5))


def _observed(expression):
    patterns = {
        "φ^φ": r"\$\\varphi\^\\varphi\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "φ^(1/φ)": r"\$\\varphi\^\{1/\\varphi\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
        "φ^(φ²)": r"\$\\varphi\^\{\\varphi\^2\}\$\s*\|\s*([0-9]+\.[0-9]{5})",
    }
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            match = re.search(patterns[expression], line)
            if match:
                return float(match.group(1))
    raise ValueError("не найдено выражение %s" % expression)


def observed_phi_phi():
    return _observed("φ^φ")


def observed_phi_inv_phi():
    return _observed("φ^(1/φ)")


def observed_phi_phi2():
    return _observed("φ^(φ²)")


def _plus_one(reference):
    return reference() + 1.0


def _wrong_exponent():
    phi = _phi()
    return _power(phi, phi ** -2)


def _wrong_base():
    with localcontext() as ctx:
        ctx.prec = 70
        return _round((Decimal(2).ln() * _phi()).exp())


def _wrong_phi2_exponent():
    phi = _phi()
    return _power(phi, phi)


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    values = [reference(), alternate()]
    return max(abs(value - values[-1]) for value in values) / abs(values[-1])


def _skip_reasons():
    return {
        "С6": "фиксированное математическое выражение не имеет сетки или разрешения",
        "С7": "проверяется одно детерминированное значение, законных оценивателей нет",
        "С8": "погрешность входных данных не задана; число является округлённой записью",
        "С9": "утверждение не является выборочной оценкой конечной выборки",
        "С11": "одна статистика детерминированного значения; тест нескольких статистик неприменим",
        "С15": "математическое утверждение не является предсказанием физической величины",
        "С16": "перебор формул и случайная цель для этого утверждения не заявлены",
        "С17": "MDL для отдельной записи математического числа не заявлен",
        "С18": "объявленная область перебора к этому утверждению не относится",
        "С19": "проверяется округлённое математическое число; специальный целочисленный параметрический путь С19 неприменим",
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
        skip_reasons=_skip_reasons(),
        notes="Эталон вычислен из определения степени и округлён до пяти знаков, как в строке корпуса.",
    )


def _selfcheck():
    assert reference_phi_phi() == 2.17846
    assert reference_phi_inv_phi() == 1.34636
    assert reference_phi_phi2() == 3.52482
    assert reference_phi_phi_alt() == reference_phi_phi()
    assert reference_phi_inv_phi_alt() == reference_phi_inv_phi()
    assert reference_phi_phi2_alt() == reference_phi_phi2()
    assert observed_phi_phi() == 2.17846
    assert observed_phi_inv_phi() == 1.34636
    assert observed_phi_phi2() == 3.52482
    assert abs(_plus_one(reference_phi_phi) - reference_phi_phi()) > 0.1
    assert abs(_wrong_exponent() - reference_phi_phi()) > 0.1
    assert abs(_wrong_base() - reference_phi_inv_phi()) > 0.1
    assert abs(_wrong_phi2_exponent() - reference_phi_phi2()) > 0.1


_selfcheck()


CLAIMS = [
    _claim(
        "φ^φ напечатано как 2,17846",
        188,
        reference_phi_phi,
        reference_phi_phi_alt,
        observed_phi_phi,
        _wrong_exponent,
    ),
    _claim(
        "φ^(1/φ) напечатано как 1,34636",
        189,
        reference_phi_inv_phi,
        reference_phi_inv_phi_alt,
        observed_phi_inv_phi,
        _wrong_base,
    ),
    _claim(
        "φ^(φ²) напечатано как 3,52482",
        190,
        reference_phi_phi2,
        reference_phi_phi2_alt,
        observed_phi_phi2,
        _wrong_phi2_exponent,
    ),
]
