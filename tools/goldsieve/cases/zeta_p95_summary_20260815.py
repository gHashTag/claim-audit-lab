"""Аудит сводки p95 для десяти высотных корзин.

Наблюдение извлекается из сводной строки корпуса. Вычисляемый эталон заново
считает среднее и популяционный разброс по десяти строкам таблицы. Второй путь
использует стандартную библиотеку statistics и вещественные значения.
"""

import re
import statistics
from decimal import Decimal, getcontext

from goldsieve.sieve import Claim


SOURCE = (
    "/home/user/workspace/corpus/trinity/data/zeta/"
    "zeta_bin_analysis_update.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.read()


def _rows():
    """Извлекает p95 из десяти строк таблицы, не используя сводку."""
    rows = []
    for line in _text().splitlines():
        if not re.match(r"^\| (?:[1-9]|10) \|", line):
            continue
        cells = [cell.strip().replace("**", "") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 9:
            continue
        try:
            rows.append(Decimal(cells[6]))
        except Exception:
            continue
    if len(rows) != 10:
        raise AssertionError("ожидалось десять значений p95")
    return rows


def _summary():
    match = re.search(
        r"\| p95 spacing \| ([0-9.]+) ± ([0-9.]+) \|", _text()
    )
    if not match:
        raise AssertionError("сводка p95 не найдена")
    return {"mean": float(match.group(1)), "std": float(match.group(2))}


def _reference():
    values = _rows()
    mean = sum(values) / Decimal(len(values))
    spread = (sum((value - mean) ** 2 for value in values) / Decimal(len(values))).sqrt()
    return {"mean": float(mean), "std": float(spread)}


def _observed():
    """Наблюдение берётся из напечатанной сводной строки корпуса."""
    return _summary()


def _reference_alt():
    """Независимый путь: statistics считает те же строки как float."""
    values = [float(value) for value in _rows()]
    return {
        "mean": statistics.fmean(values),
        "std": statistics.pstdev(values),
    }


def _wrong():
    return {"mean": 1.0, "std": 1.0}


def _null_model():
    return {"mean": 1.0, "std": 1.0}


def _sample():
    return [float(value) for value in _rows()]


def _mean(values):
    return sum(values) / len(values)


def _std(values):
    mean = _mean(values)
    return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5


def _alt_tolerance():
    primary = _reference()
    alternate = _reference_alt()
    return max(
        1.0e-12,
        abs(primary["mean"] - alternate["mean"]),
        abs(primary["std"] - alternate["std"]),
    ) * 10.0


def _selfcheck():
    getcontext().prec = 40
    assert len(_rows()) == 10
    assert _summary() == {"mean": 1.7186, "std": 0.0045}
    assert abs(_reference()["mean"] - 1.7252) < 1.0e-12
    assert _reference()["std"] > 0.02
    assert abs(_reference_alt()["mean"] - _reference()["mean"]) < 1.0e-12
    assert abs(_reference_alt()["std"] - _reference()["std"]) < 1.0e-12
    assert _wrong() != _reference()


_selfcheck()


CLAIMS = [
    Claim(
        name="Сводка p95 расстояний равна 1,7186 ± 0,0045",
        source="data/zeta/zeta_bin_analysis_update.md:12-16",
        stated=_observed(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_null_model,
        null_expect={"mean": 1.0, "std": 1.0},
        null_kind="negative",
        tolerance=0.01,
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        inputs=[SOURCE],
        claim_family="сводная статистика высотных корзин дзета",
        observable="среднее и популяционный разброс p95 расстояний",
        measurement_source="корпус Trinity, таблица десяти высотных корзин",
        uncertainty_type="statistical",
        novelty_key="zeta:p95_summary:v1",
        information_class="novelty",
        purpose="audit",
        models=["пересчёт Decimal по строкам таблицы", "statistics по строкам таблицы"],
        independent_of=[],
        notes=(
            "Наблюдение читает сводную строку. Эталон независимо считает "
            "десять табличных значений p95; альтернативный путь использует "
            "statistics.pstdev. Напечатанные 1,7186 и 0,0045 не подмешаны "
            "в вычисляемый эталон."
        ),
        skip_reasons={
            "С6": "сетка эталона отсутствует",
            "С7": "проверяется одна сводка десяти корзин",
            "С8": "погрешность отдельных табличных p95 не задана",
            "С9": "десять корзин корпуса являются полным набором наблюдений",
            "С10": "сырой ряд расстояний для повторной выборки не входит в кейс",
            "С11": "проверяется одна сводная статистика",
            "С15": "внешней цели нет, проверяется статистика корпуса",
            "С16": "перебора гипотез нет",
            "С17": "модельная формула не заявлена",
            "С18": "границы перебора не заявлены",
            "С19": "ошибка вещественной арифметики меньше точности таблицы",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма не заявлена",
        },
    )
]
