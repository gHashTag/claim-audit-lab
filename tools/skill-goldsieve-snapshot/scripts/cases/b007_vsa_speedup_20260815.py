# -*- coding: utf-8 -*-
"""Проверка табличного ускорения VSA в B007.

Наблюдение читается из отдельной строки Speedup. Эталон заново получает
отношение времени Kanerva к времени Trinity для операции bind. Это не чтение
той же ячейки, а независимый расчёт по двум исходным столбцам.
"""

from decimal import Decimal
import re

from goldsieve.sieve import Claim


SOURCE = (
    "/home/user/workspace/corpus/trinity/docs/research/bundles/"
    "B007_VSA.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _table_rows():
    rows = {}
    for name, trinity, kanerva, poduval in re.findall(
        r"^\|\s*(bind|bundle3|similarity)\s*\|\s*([0-9.]+)\s*µs\s*\|\s*([0-9.]+)\s*µs\s*\|\s*([0-9.]+)\s*µs\s*\|$",
        _text(),
        re.MULTILINE,
    ):
        rows[name] = (trinity, kanerva, poduval)
    if "bind" not in rows:
        raise AssertionError("строка bind не найдена")
    return rows


def _observed():
    """Наблюдение берётся из выделенной строки Speedup."""
    match = re.search(
        r"^\|\s*\*\*Speedup\*\*\s*\|\s*\*\*([0-9.]+)×\*\*\s*\|",
        _text(),
        re.MULTILINE,
    )
    if not match:
        raise AssertionError("строка Speedup не найдена")
    return float(match.group(1))


def _reference():
    """Эталон вычисляется как отношение базового времени к времени Trinity."""
    trinity, kanerva, _ = _table_rows()["bind"]
    return float(kanerva) / float(trinity)


def _reference_alt():
    """Второй путь: точное отношение Decimal без float-арифметики."""
    trinity, kanerva, _ = _table_rows()["bind"]
    return float(Decimal(kanerva) / Decimal(trinity))


def _wrong():
    return 2.0


def _null_model():
    return 2.0


def _selfcheck():
    assert abs(_observed() - 1.5) < 1.0e-12
    assert abs(_reference() - 1.5) < 1.0e-12
    assert abs(_reference_alt() - 1.5) < 1.0e-12
    assert _wrong() != _reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Табличное ускорение VSA равно 1,5×",
        source="docs/research/bundles/B007_VSA.md:39-46",
        stated=_observed(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_null_model,
        null_expect=2.0,
        null_kind="negative",
        tolerance=0.01,
        reference_alt=_reference_alt,
        alt_tolerance=lambda: 1.0e-12,
        inputs=[SOURCE],
        claim_kind="statistical",
        claim_family="отношения времени выполнения операций",
        observable="ускорение bind относительно базовой реализации",
        measurement_source="корпус Trinity, таблица производительности B007 VSA",
        uncertainty_type="statistical",
        novelty_key="b007:vsa:bind_speedup:v1",
        information_class="novelty",
        purpose="audit",
        models=[
            "отношение времени Kanerva к времени Trinity для bind",
            "точное отношение Decimal тех же двух времён",
        ],
        independent_of=[],
        notes=(
            "Наблюдение извлекается из строки Speedup. Основной эталон "
            "вычисляет отношение 1,2 мкс к 0,8 мкс из строки bind; "
            "reference_alt использует Decimal. Значение Speedup в эталон "
            "не передаётся."
        ),
        skip_reasons={
            "С6": "сеточного разрешения нет",
            "С7": "сравнивается одно отношение времён",
            "С8": "погрешности бенчмарка в источнике не заданы",
            "С9": "сырые прогоны и размер выборки не входят в кейс",
            "С10": "выборочная неопределённость времени не задана",
            "С11": "источник содержит одну фиксированную таблицу",
            "С15": "внешней цели нет, проверяется статистика корпуса",
            "С16": "перебора формул нет",
            "С17": "модельная формула не заявлена",
            "С18": "границы семейства не заявлены",
            "С19": "ошибка деления намного меньше точности таблицы",
            "С20": "эффективное число испытаний неприменимо",
            "С21": "алгебраическая форма не является целью утверждения",
        },
    )
]
