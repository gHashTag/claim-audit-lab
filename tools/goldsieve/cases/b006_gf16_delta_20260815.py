# -*- coding: utf-8 -*-
"""Аудит заявленной разности PPL в отчёте B006 GF16.

Наблюдение извлекается из отдельной строки ``Difference``. Вычисляемый
эталон заново вычитает две строки с исходным и кодированным PPL. Второй путь
повторяет арифметику через Decimal по строкам-источникам, не читая строку
с разностью.
"""

import re
from decimal import Decimal

from goldsieve.sieve import Claim


SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/research/bundles/"
    "B006_GF16.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _paired_ppl():
    text = _text()
    original = re.search(
        r"^- Original PPL:\s*([0-9.]+)\s*±\s*([0-9.]+)\s*$",
        text,
        re.MULTILINE,
    )
    encoded = re.search(
        r"^- GF16 encoded/decoded:\s*([0-9.]+)\s*±\s*([0-9.]+)\s*$",
        text,
        re.MULTILINE,
    )
    if not original or not encoded:
        raise AssertionError("две строки PPL не найдены")
    return original, encoded


def _observed():
    """Наблюдение берётся из напечатанной строки Difference."""
    match = re.search(r"^- Difference:\s*Δ\s*=\s*([+-]?[0-9.]+)", _text(), re.MULTILINE)
    if not match:
        raise AssertionError("строка Difference не найдена")
    return float(match.group(1))


def _reference():
    """Эталон вычисляется из двух строк PPL, без строки Difference."""
    original, encoded = _paired_ppl()
    return float(float(encoded.group(1)) - float(original.group(1)))


def _reference_alt():
    """Независимый путь: точное вычитание Decimal по тем же двум строкам."""
    original, encoded = _paired_ppl()
    return float(Decimal(encoded.group(1)) - Decimal(original.group(1)))


def _wrong():
    return 1.0


def _null_model():
    return 1.0


def _selfcheck():
    assert abs(_observed() - 0.2) < 1.0e-12
    assert abs(_reference() - 0.2) < 1.0e-12
    assert abs(_reference_alt() - 0.2) < 1.0e-12
    assert _wrong() != _reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Разность PPL GF16 и исходной модели равна +0,2",
        source="docs/research/bundles/B006_GF16.md:50-54",
        stated=_observed(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_null_model,
        null_expect=1.0,
        null_kind="negative",
        tolerance=0.01,
        reference_alt=_reference_alt,
        alt_tolerance=lambda: 1.0e-12,
        inputs=[SOURCE],
        claim_kind="statistical",
        claim_family="разности показателей качества форматов",
        observable="разность среднего PPL до и после кодирования GF16",
        measurement_source="корпус Trinity, отчёт B006 GF16",
        uncertainty_type="statistical",
        novelty_key="b006:gf16:ppl_delta:v1",
        information_class="novelty",
        purpose="audit",
        models=[
            "вычитание исходного и кодированного PPL",
            "точное Decimal-вычитание",
        ],
        independent_of=[],
        notes=(
            "Наблюдение читает строку Difference. Эталон вычисляет разность "
            "из строк Original PPL и GF16 encoded/decoded; альтернативный "
            "путь использует Decimal. Значение +0,2 не подставляется в эталон."
        ),
        skip_reasons={
            "С6": "сетка эталона отсутствует",
            "С7": "сравнивается одна пара средних PPL",
            "С8": "погрешность разности в источнике отдельно не задана",
            "С9": "источник содержит одну фиксированную пару измерений",
            "С10": "сырые повторные измерения в кейс не входят",
            "С11": "проверяется одна разность, а не выборочная оценка",
            "С15": "внешней цели нет, проверяется статистика корпуса",
            "С16": "перебора гипотез нет",
            "С17": "модельная формула не заявлена",
            "С18": "границы перебора не заявлены",
            "С19": "ошибка арифметики меньше точности таблицы",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма не заявлена",
        },
    )
]
