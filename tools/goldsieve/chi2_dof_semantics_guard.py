#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож смысла показателя χ²/dof.

Число с именем ``χ²/dof`` нельзя считать полностью реконструированным, если
в наблюдаемом файле есть только уже поделённое отношение и нет исходного
числа степеней свободы. Этот сторож не выдумывает знаменатель: он фиксирует
точно наблюдаемый пробел как ``not-evaluated`` и оставляет арифметическую
воспроизводимость отдельному ``chi2_dof_rederivation.py``.

Команды:
    python3 chi2_dof_semantics_guard.py --selftest
    python3 chi2_dof_semantics_guard.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
from pathlib import Path

CORPUS = Path("/home/user/workspace/corpus/trinity")
TABLE = CORPUS / "data/zeta/zeta_figure1_chi2.csv"
OUT = Path(__file__).resolve().parent / "chi2_dof_semantics_guard.json"


def inspect(path: Path = TABLE) -> dict:
    """Проверить, предъявлены ли χ² и dof раздельно в наблюдаемой таблице."""
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    fields = list(rows[0]) if rows else []
    has_chi2 = any(name.lower() in {"chi2", "χ²", "chi_squared"}
                   for name in fields)
    has_dof = any(name.lower() in {"dof", "degrees_of_freedom", "степени_свободы"}
                  for name in fields)
    ratios = []
    if rows and "chi2_dof" in rows[0]:
        for number, row in enumerate(rows, 1):
            try:
                value = float(row["chi2_dof"])
            except (TypeError, ValueError) as exc:
                raise ValueError("строка %d содержит нечисловое отношение χ²/dof"
                                 % number) from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError("строка %d содержит недопустимое отношение χ²/dof"
                                 % number)
            ratios.append(value)
    separate = has_chi2 and has_dof
    return {
        "статус": "verified-in-scope" if separate else "not-evaluated",
        "источник_наблюдения": str(path),
        "столбцы": fields,
        "строк": len(rows),
        "отношение_наблюдено": bool(ratios),
        "chi2_наблюдено_отдельно": has_chi2,
        "dof_наблюдено_отдельно": has_dof,
        "причина": (
            "исходные χ² и dof предъявлены раздельно"
            if separate else
            "таблица содержит только готовое отношение χ²/dof; число степеней "
            "свободы не предъявлено, поэтому научная интерпретация "
            "χ²/dof остаётся not-evaluated"
        ),
        "ограничение": "сторож не оценивает научную пригодность и не выводит dof",
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

    with tempfile.TemporaryDirectory(prefix="chi2-dof-semantics-") as tmp:
        root = Path(tmp)
        ratio = root / "ratio.csv"
        ratio.write_text("T_mid,chi2_dof\n1,2.0\n", encoding="utf-8")
        report = inspect(ratio)
        check("готовое отношение без исходных полей не закрывает dof",
              report["статус"] == "not-evaluated"
              and report["dof_наблюдено_отдельно"] is False)

        separate = root / "separate.csv"
        separate.write_text("T_mid,chi2,dof\n1,4.0,2\n", encoding="utf-8")
        report = inspect(separate)
        check("раздельные χ² и dof распознаются",
              report["статус"] == "verified-in-scope"
              and report["chi2_наблюдено_отдельно"]
              and report["dof_наблюдено_отдельно"])

        ratio.write_text("T_mid,chi2_dof\n1,nan\n", encoding="utf-8")
        try:
            inspect(ratio)
        except ValueError:
            check("нефинитное отношение отвергается", True)
        else:
            check("нефинитное отношение отвергается", False)

    print("самопроверка сторожа смысла χ²/dof: %d пройдено, %d провалено"
          % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    report = inspect()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож смысла χ²/dof: %s; %s" %
          (report["статус"], report["причина"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
