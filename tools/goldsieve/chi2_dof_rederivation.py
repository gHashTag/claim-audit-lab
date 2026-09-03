#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Повторное построение сводки χ²/dof из наблюдаемой таблицы корпуса.

Контракт ``chi2_dof_guard.py`` проверяет форму входа, но сам по себе не
воспроизводит сводку. Этот модуль закрывает отдельный долг: читает
``zeta_figure1_chi2.csv``, самостоятельно считает среднее и популяционное
стандартное отклонение десяти строк и сверяет их с напечатанной сводкой в
``zeta_bin_analysis_update.md``. Значения не вшиваются в инструмент.

Статус ``verified-in-scope`` относится только к этим двум указанным файлам
корпуса и выбранному рецепту округления до двух знаков. Это не научный вывод
о точном законе GUE.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
import tempfile
from pathlib import Path

CORPUS = Path("/home/user/workspace/corpus/trinity")
CSV_PATH = CORPUS / "data/zeta/zeta_figure1_chi2.csv"
DOC_PATH = CORPUS / "data/zeta/zeta_bin_analysis_update.md"
OUT = Path(__file__).resolve().parent / "chi2_dof_rederivation.json"


def _read_csv(path: Path) -> list[float]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or set(rows[0]) != {"T_mid", "chi2_dof"}:
        raise ValueError("таблица χ²/dof имеет неожиданные столбцы")
    values: list[float] = []
    for number, row in enumerate(rows, 1):
        try:
            value = float(row["chi2_dof"])
        except (TypeError, ValueError) as exc:
            raise ValueError("строка %d содержит нечисловой χ²/dof" % number) from exc
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("строка %d содержит недопустимый χ²/dof" % number)
        values.append(value)
    return values


def _read_document(path: Path) -> tuple[float, float]:
    text = path.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\|\s*χ²/dof\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*±\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*\|",
        text,
        flags=re.MULTILINE,
    )
    if len(rows) != 1:
        raise ValueError("ожидалась ровно одна сводная строка χ²/dof")
    mean, spread = (float(x) for x in rows[0])
    if not (math.isfinite(mean) and math.isfinite(spread)
            and mean >= 0.0 and spread >= 0.0):
        raise ValueError("сводка χ²/dof нечисловая или отрицательная")
    return mean, spread


def rederive(csv_path: Path = CSV_PATH, doc_path: Path = DOC_PATH) -> dict:
    values = _read_csv(csv_path)
    reported_mean, reported_spread = _read_document(doc_path)
    mean = sum(values) / len(values)
    spread = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
    tolerance = 0.005 + 1e-12
    mean_ok = abs(mean - reported_mean) <= tolerance
    spread_ok = abs(spread - reported_spread) <= tolerance
    if not (mean_ok and spread_ok):
        raise ValueError(
            "сводка не воспроизводится: вычислено %.12g ± %.12g, "
            "напечатано %.12g ± %.12g"
            % (mean, spread, reported_mean, reported_spread)
        )
    return {
        "статус": "verified-in-scope",
        "наблюдение": {
            "источник_наблюдения": str(csv_path),
            "строк": len(values),
            "значения": values,
        },
        "сводка_документа": {
            "источник": str(doc_path),
            "среднее": reported_mean,
            "популяционное_стандартное_отклонение": reported_spread,
        },
        "пересчёт": {
            "среднее": mean,
            "популяционное_стандартное_отклонение": spread,
            "правило": "среднее и sqrt(sum((x−mean)^2)/N), округление до двух знаков",
        },
        "ограничение": (
            "проверена арифметическая воспроизводимость сводки двух файлов; "
            "научная пригодность χ²/dof и точный закон GUE не оцениваются"
        ),
    }


def selftest() -> int:
    ok = fail = 0

    def check(name: str, condition: bool) -> None:
        nonlocal ok, fail
        print("  %s %s" % ("ok  " if condition else "ПРОВАЛ", name))
        if condition:
            ok += 1
        else:
            fail += 1

    with tempfile.TemporaryDirectory(prefix="chi2-red-") as tmp:
        root = Path(tmp)
        table = root / "values.csv"
        doc = root / "report.md"
        table.write_text(
            "T_mid,chi2_dof\n1,1\n2,2\n3,3\n", encoding="utf-8"
        )
        doc.write_text("| χ²/dof | 2.00 ± 0.82 | ~1 |\n", encoding="utf-8")
        result = rederive(table, doc)
        check("сводка из фикстуры воспроизводится", result["статус"] == "verified-in-scope")

        table.write_text(
            "T_mid,chi2_dof\n1,1\n2,2\n3,9\n", encoding="utf-8"
        )
        try:
            rederive(table, doc)
        except ValueError:
            check("мутация наблюдаемой строки отвергается", True)
        else:
            check("мутация наблюдаемой строки отвергается", False)

        table.write_text(
            "T_mid,chi2_dof\n1,nan\n2,2\n", encoding="utf-8"
        )
        try:
            _read_csv(table)
        except ValueError:
            check("нефинитное значение отвергается", True)
        else:
            check("нефинитное значение отвергается", False)

        table.write_text(
            "T_mid,chi2_dof\n1,1\n2,2\n3,3\n", encoding="utf-8"
        )
        doc.write_text(
            "| χ²/dof | 2.00 ± 0.82 | ~1 |\n"
            "| χ²/dof | 2.00 ± 0.82 | ~1 |\n",
            encoding="utf-8",
        )
        try:
            _read_document(doc)
        except ValueError:
            check("дублированная сводка отвергается", True)
        else:
            check("дублированная сводка отвергается", False)

    print("самопроверка повторного построения χ²/dof: %d пройдено, %d провалено"
          % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    report = rederive()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
