# -*- coding: utf-8 -*-
"""Проверка явно заданного рецепта сводки Khinchin.

Кейс закрывает открытую неоднозначность не повторным сравнением с числом 2,685,
а фиксацией наблюдаемого рецепта: десять высотных корзин, среднее K и
популяционный разброс по колонке CSV. Наблюдение читается из Markdown-сводки,
эталон — из CSV; альтернативный эталон разбирает таблицу Markdown и использует
стандартную библиотеку. Это новый класс рецепта, а не новая табличная арифметика
без бюджета новизны.
"""

import csv
import re
import statistics
import sys
from decimal import Decimal
from pathlib import Path

from goldsieve.sieve import Claim

if __name__ in sys.modules:
    raise RuntimeError("guard: кейс зарегистрирован в sys.modules")

КОРЕНЬ = Path("/home/user/workspace/corpus/trinity/data/zeta")
CSV_ИСТОЧНИК = КОРЕНЬ / "zeta_figure1_K.csv"
MD_ИСТОЧНИК = КОРЕНЬ / "zeta_bin_analysis_update.md"


def _текст():
    return MD_ИСТОЧНИК.read_text(encoding="utf-8")


def _наблюдение():
    match = re.search(r"\| Khinchin K \| ([0-9.]+) ± ([0-9.]+) \|", _текст())
    if not match:
        raise AssertionError("сводка Khinchin не найдена")
    return {"mean": float(match.group(1)), "std": float(match.group(2))}


def _k_csv():
    with CSV_ИСТОЧНИК.open(encoding="utf-8", newline="") as поток:
        rows = list(csv.DictReader(поток))
    values = [Decimal(row["Khinchin_K"]) for row in rows]
    if len(values) != 10:
        raise AssertionError("ожидалось десять высотных корзин в CSV")
    return values


def _эталон():
    values = _k_csv()
    mean = sum(values) / Decimal(len(values))
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    return {"mean": float(mean), "std": float(variance.sqrt())}


def _эталон_альт():
    values = []
    for line in _текст().splitlines():
        if not re.match(r"^\| (?:[1-9]|10) \|", line):
            continue
        cells = [cell.strip().replace("**", "") for cell in line.strip().strip("|").split("|")]
        if len(cells) == 9:
            values.append(float(cells[4]))
    if len(values) != 10:
        raise AssertionError("ожидалось десять K в таблице Markdown")
    return {"mean": statistics.fmean(values), "std": statistics.pstdev(values)}


def _подстановка():
    return {"mean": 2.685, "std": 0.0}


def _контроль():
    return {"mean": 1.0, "std": 0.0}


def _выборка():
    return [float(value) for value in _k_csv()]


def _самопроверка():
    observed = _наблюдение()
    reference = _эталон()
    alternate = _эталон_альт()
    assert observed == {"mean": 2.6201, "std": 0.0293}
    assert abs(reference["mean"] - 2.62011) < 1e-12
    assert abs(reference["std"] - 0.02926125253641749) < 1e-12
    assert abs(reference["mean"] - alternate["mean"]) < 1e-12
    assert abs(reference["std"] - alternate["std"]) < 1e-12
    assert _подстановка() != reference
    assert _контроль() != reference


_самопроверка()

_ПРОПУСКИ = {
    "С6": "сетка эталона не заявлена",
    "С7": "проверяется фиксированный набор десяти высотных корзин",
    "С8": "погрешности отдельных корзин не заданы",
    "С9": "десять корзин образуют полный набор наблюдений",
    "С10": "сырые повторные выборки не входят в источник",
    "С11": "проверяется одна сводка",
    "С15": "внешней измерительной цели нет",
    "С16": "перебор формул не заявлен",
    "С17": "закон формул не проверяется",
    "С18": "границы перебора не объявлены",
    "С19": "ошибка float меньше точности сводки",
    "С20": "эффективная кратность для десяти фиксированных корзин неприменима",
    "С21": "алгебраическая форма не заявлена",
}

CLAIMS = [
    Claim(
        name="Сводка Khinchin K по десяти корзинам равна 2,6201 ± 0,0293",
        source="data/zeta/zeta_bin_analysis_update.md:12-14,31-40",
        stated=_наблюдение(),
        reference=_эталон,
        observed=_наблюдение,
        wrong=_подстановка,
        null_model=_контроль,
        null_expect={"mean": 1.0, "std": 0.0},
        null_kind="negative",
        tolerance=0.01,
        reference_alt=_эталон_альт,
        alt_tolerance=lambda: 1e-12,
        inputs=[str(CSV_ИСТОЧНИК), str(MD_ИСТОЧНИК)],
        claim_family="рецепт сводной статистики Khinchin",
        observable="среднее и популяционный разброс K по десяти высотным корзинам",
        measurement_source="CSV zeta_figure1_K и таблица zeta_bin_analysis_update",
        uncertainty_type="descriptive",
        novelty_key="zeta:khinchin_estimator_recipe:v1",
        information_class="novelty",
        purpose="audit",
        models=["среднее и pstdev по CSV", "среднее и pstdev по таблице Markdown"],
        independent_of={"observable": "явно заданный рецепт агрегирования", "source": "CSV против Markdown"},
        notes=(
            "Наблюдение читает сводную строку Markdown. Эталон считает десять "
            "значений K из CSV через Decimal; reference_alt получает те же "
            "десять значений из Markdown и statistics. Это фиксирует рецепт "
            "сводки, но не доказывает универсальность константы Khinchin."
        ),
        skip_reasons=_ПРОПУСКИ,
    )
]
