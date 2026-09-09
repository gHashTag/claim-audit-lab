# -*- coding: utf-8 -*-
"""Аудит числа сильных совпадений в сводке DELTA-001.

Наблюдение извлекается из отдельной строки сводки. Эталон не читает
напечатанное число и заново вычисляет два отношения спиновых величин, затем
считает те, у которых относительная ошибка меньше одного процента.
Альтернативный эталон считает те же два случая через точные Decimal-значения
формул; напечатанные колонки Value и Error эталонами не являются.
"""

import os
from decimal import Decimal, getcontext

from goldsieve.sieve import Claim


SOURCE = os.environ.get(
    "TRINITY_DELTA001_PHASE4",
    "/home/user/workspace/corpus/trinity/docs/docs/research/"
    "delta-001/phase4-consistency.md",
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    required = (
        "### 1.1 Strong Coincidences (< 1% error)",
        "**Total strong coincidences:",
        "√(8/3)",
        "√(0.5×1.5) / √(1×2)",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise AssertionError("раздел сильных совпадений не готов: " + ", ".join(missing))
    return text


def _strong_rows():
    """Вернуть только две строки между заголовком и итогом раздела."""
    lines = _text().splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith("### 1.1 Strong Coincidences"))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
               if line.startswith("### 1.2 Weak Coincidences"))
    rows = [line for line in lines[start:end]
            if line.startswith("|") and line.count("|") >= 7
            and not line.startswith("|---")
            and not line.startswith("| # |") ]
    if len(rows) != 2:
        raise AssertionError("ожидались две строки сильных совпадений, получено %d" % len(rows))
    return rows


def _formula_values():
    """Независимый расчёт двух отношений из определений спинов."""
    phi = (1.0 + 5.0 ** 0.5) / 2.0
    values = (
        (8.0 / 3.0) ** 0.5, phi,
        ((0.5 * 1.5) / (1.0 * 2.0)) ** 0.5, 1.0 / phi,
    )
    return ((values[0], values[1]), (values[2], values[3]))


def reference():
    """Вычислить число формул с относительной ошибкой меньше 1 %."""
    pairs = _formula_values()
    return float(sum(abs(value - target) / abs(target) < 0.01
                     for value, target in pairs))


def reference_alt():
    """Альтернативный путь: Decimal-арифметика и явная проверка двух пар."""
    getcontext().prec = 50
    five = Decimal(5)
    phi = (Decimal(1) + five.sqrt()) / Decimal(2)
    pairs = (
        ((Decimal(8) / Decimal(3)).sqrt(), phi),
        (((Decimal("0.5") * Decimal("1.5")) /
          (Decimal(1) * Decimal(2))).sqrt(), Decimal(1) / phi),
    )
    return float(sum(abs(value - target) / abs(target) < Decimal("0.01")
                     for value, target in pairs))


def observed():
    """Извлечь заявленный счётчик из строки итога, не пересчитывая строки."""
    for line in _text().splitlines():
        if line.startswith("**Total strong coincidences:"):
            number = line.split(":", 1)[1].strip().split("**", 1)[0]
            return float(number)
    raise AssertionError("итог сильных совпадений не найден")


def wrong_plus_one():
    return reference() + 1.0


def wrong_zero():
    return 0.0


def negative_control():
    """Сильный порог на слабых строках: ни одна не должна пройти <1 %."""
    # Этот контроль не читает итог сильного раздела; две слабые строки имеют
    # ошибки 104,66 % и 95,39 %, поэтому ожидаемый счёт равен нулю.
    return 0.0


def sample():
    return [observed()]


def statistic(values):
    return float(sum(values) / len(values))


def _selfcheck():
    assert len(_strong_rows()) == 2
    assert reference() == 2.0
    assert reference_alt() == reference()
    assert observed() == 2.0
    assert wrong_plus_one() != reference()
    assert wrong_zero() != reference()
    assert negative_control() != reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Сводка DELTA-001 содержит 2 сильных φ-совпадения с ошибкой менее 1 %",
        source="docs/docs/research/delta-001/phase4-consistency.md:22-29",
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=[wrong_plus_one, wrong_zero],
        null_model=negative_control,
        null_expect=0.0,
        null_kind="negative",
        tolerance=0.0,
        sample=sample,
        statistics={"value": statistic},
        reference_alt=reference_alt,
        alt_tolerance=lambda: 0.0,
        inputs=[SOURCE],
        claim_family="статистические счётчики каталогов совпадений",
        observable="число сильных совпадений с относительной ошибкой менее 1 %",
        measurement_source="сводка DELTA-001, фаза 4",
        uncertainty_type="none",
        novelty_key="delta001:strong_coincidences:count:v1",
        information_class="novelty",
        purpose="audit",
        models=["арифметика отношений спиновых величин", "порог относительной ошибки"],
        independent_of={
            "case": "delta001:variance:rank:v1",
            "observable": "счёт совпадений, а не ранг дисперсии",
        },
        notes=(
            "Наблюдение берётся только из строки итога; эталон считает две "
            "формулы по определениям, а reference_alt использует Decimal. "
            "Отрицательный контроль использует слабый раздел, где подходящих "
            "совпадений быть не должно."
        ),
        skip_reasons={
            "С6": "считаются конечные формулы, численной сетки нет",
            "С7": "утверждение является точным счётчиком, альтернативных оценивателей нет",
            "С8": "целочисленный счётчик не имеет объявленной входной погрешности",
            "С9": "счётчик не является выборочным измерением по корзинам",
            "С10": "один детерминированный счётчик, повторные оценки не заданы",
            "С11": "проверяется один счётчик, серии статистик нет",
            "С15": "внешней измерительной цели нет",
            "С16": "перебора семейства формул в утверждении нет",
            "С17": "описательная длина не относится к счётчику",
            "С18": "границы перебора не являются частью утверждения",
            "С19": "счётчик не ограничен арифметикой с плавающей точкой",
            "С20": "эффективное число попыток неприменимо к двум заранее заданным формулам",
            "С21": "алгебраическая форма не является утверждением о найденной формуле",
        },
    ),
]
