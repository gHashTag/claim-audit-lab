"""Честные контрпримеры для калибровки детектора тождественности.

Во всех трёх утверждениях наблюдение читает строку корпуса, а эталон получает
то же целое другим способом. Намеренно покрыты три формы, которые не должны
вызывать ложное срабатывание: изменяемое глобальное состояние,
functools.partial и lambda. Наблюдение нигде не вызывает эталон.
"""

import functools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402

SOURCE = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md"
MARKER = "| 10 |"

# Источник состояния намеренно изменяемый: детектор должен видеть чтение
# корпуса, а не считать имя глобальной переменной доказательством тождества.
_STATE = {"source": SOURCE, "marker": MARKER}


def _read_catalog_number(path, marker):
    """Извлечь число из таблицы отдельным путём."""
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if marker in line:
                match = re.search(r"\|\s*10\s*\|\s*(\d+)\s*\|", line)
                if match:
                    return int(match.group(1))
    raise ValueError("число каталога не найдено")


def reference_formula():
    """Эталон из определения: произведение вычисляется без чтения таблицы."""
    return 3 * 41


def reference_lucas():
    """Второй эталон: независимая целочисленная рекурсия Лукаса."""
    a, b = 2, 1
    for _ in range(10):
        a, b = b, a + b
    return a


def observed_global():
    """Наблюдение через изменяемое глобальное состояние и чтение корпуса."""
    return _read_catalog_number(_STATE["source"], _STATE["marker"])


# partial не имеет собственного тела, поэтому это отдельная форма честного
# наблюдения, а не обёртка эталона.
observed_partial = functools.partial(_read_catalog_number, SOURCE, MARKER)

# lambda также читает корпус; она не является вызовом reference_formula.
observed_lambda = lambda: _read_catalog_number(SOURCE, MARKER)


def wrong_value():
    """Подставка: соседнее значение не должно пройти каскад."""
    return reference_formula() + 1


def null_value():
    """Негативный контроль: значение, отличное от эталона."""
    return reference_formula() - 1


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


def make_claim(name, observed):
    return Claim(
        name=name,
        source="deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md:138",
        stated=123,
        reference=reference_formula,
        observed=observed,
        wrong=wrong_value,
        null_model=null_value,
        null_expect=122,
        null_kind="negative",
        tolerance=0.0,
        sample=sample(observed),
        statistics={"value": mean},
        reference_alt=reference_lucas,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        claim_family="калибровка детектора тождественности",
        observable="число L(10) из строки таблицы",
        measurement_source="корпус Trinity, таблица каталога",
        uncertainty_type="none",
        novelty_key="tool:identity:honest-controls:v1",
        information_class="high",
        purpose="tool_selftest",
        models=["чтение корпуса", "вычисляемый эталон"],
        independent_of={"path": "наблюдение читает строку корпуса, эталон считает число"},
        notes="Честный контроль для калибровки; совпадение значений не является признаком тождества, потому что пути вычисления различны.",
        skip_reasons=skips(),
    )


def _selfcheck():
    assert observed_global() == reference_formula() == reference_lucas()
    assert observed_partial() == reference_formula()
    assert observed_lambda() == reference_formula()
    assert wrong_value() != reference_formula()
    assert null_value() != reference_formula()
    # Guard изменяемого состояния: после возврата к штатному пути наблюдение
    # обязано снова читать тот же файл, а не захватывать эталон.
    old = dict(_STATE)
    _STATE["marker"] = "| 10 |"
    assert observed_global() == 123
    _STATE.clear()
    _STATE.update(old)


_selfcheck()


CLAIMS = [
    make_claim(
        "Чтение каталога через глобальное состояние не тождественно эталону",
        observed_global,
    ),
    make_claim(
        "Чтение каталога через functools.partial не тождественно эталону",
        observed_partial,
    ),
    make_claim(
        "Чтение каталога через lambda не тождественно эталону",
        observed_lambda,
    ),
]
