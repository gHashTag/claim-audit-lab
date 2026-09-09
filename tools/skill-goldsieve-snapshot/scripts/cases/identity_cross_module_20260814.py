"""Межмодульная калибровка детектора тождественности.

Положительная подставка проходит через `relay` в отдельном модуле и должна
получить ПУСТО. Честное наблюдение в том же межмодульном устройстве читает
строку корпуса отдельным парсером и должно получить ПОДТВЕРЖДЕНО. Оба кейса
загружаются через module_from_spec без регистрации в sys.modules.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve import identity_cross_helper as helper  # noqa: E402
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = helper.SOURCE


# Реальный объект эталона из другого модуля: это не локальная обёртка, иначе
# детектор видел бы только общий вспомогательный вызов, а не сам эталон.
reference_cross = helper.reference


def reference_honest():
    """Тот же эталон, вычисленный локально другим маршрутом."""
    a, b = 2, 1
    for _ in range(10):
        a, b = b, a + b
    return a


def reference_alt_lucas():
    """Второй независимый эталон для С12: рекурсия с другой инициализацией."""
    previous, current = 1, 3
    for _ in range(9):
        previous, current = current, previous + current
    return previous


def observed_cross():
    """Положительная подставка: цепочка наблюдение -> relay -> reference."""
    return helper.relay()


def observed_honest():
    """Честное наблюдение: helper самостоятельно читает файл корпуса."""
    return helper.read_catalog()


def wrong_value():
    return 124


def null_value():
    return 122


def sample(observed):
    return lambda: [observed()]


def mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    return 0.0


def skips():
    return {
        "С6": "фиксированное целое не требует численной сетки",
        "С7": "измеряется одно детерминированное значение",
        "С8": "погрешность входа в утверждении не задана",
        "С9": "это не выборочная оценка конечной выборки",
        "С11": "одна именованная статистика, тест нескольких статистик неприменим",
        "С15": "утверждение не является предсказанием внешней величины",
        "С16": "семейство формул не перебирается",
        "С17": "длина описания для калибровочного контроля не заявлена",
        "С18": "объявленная область перебора отсутствует",
        "С19": "арифметическая погрешность не является предметом утверждения",
        "С20": "эффективное число попыток для одного чтения не задано",
        "С21": "алгебраическая форма семейства не является предметом утверждения",
    }


def make_claim(name, reference, observed, notes):
    return Claim(
        name=name,
        source="deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md:138",
        stated=123,
        reference=reference,
        observed=observed,
        wrong=wrong_value,
        null_model=null_value,
        null_expect=122,
        null_kind="negative",
        tolerance=0.0,
        sample=sample(observed),
        statistics={"value": mean},
        reference_alt=reference_alt_lucas,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        claim_family="калибровка детектора тождественности",
        observable="число L(10) через межмодульную цепочку или чтение корпуса",
        measurement_source="корпус Trinity, таблица каталога",
        uncertainty_type="none",
        novelty_key="tool:identity:cross-module:v1",
        information_class="high",
        purpose="tool_selftest",
        models=["межмодульная цепочка", "вычисляемый эталон"],
        independent_of={
            "path": "наблюдение и эталон проходят через разные модули и пути"
        },
        notes=notes,
        skip_reasons=skips(),
    )


CLAIMS = [
    make_claim(
        "Межмодульная цепочка наблюдение→эталон распознаётся как тождество",
        reference_cross,
        observed_cross,
        "Положительная подставка: relay в отдельном модуле прозрачно вызывает "
        "эталон; ожидается ПУСТО, а не находка корпуса.",
    ),
    make_claim(
        "Межмодульное чтение корпуса не распознаётся как тождество",
        reference_honest,
        observed_honest,
        "Честный контроль: отдельный модуль читает строку корпуса; ожидается "
        "ПОДТВЕРЖДЕНО при совпадении значения и независимых путях.",
    ),
]


def _selfcheck():
    assert reference_cross() == 123
    assert reference_honest() == 123
    assert observed_cross() == 123
    assert observed_honest() == 123
    assert wrong_value() != 123
    assert null_value() != 123


_selfcheck()
