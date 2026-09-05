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
    chi2_field = next((name for name in fields
                       if name.lower() in {"chi2", "χ²", "chi_squared"}), None)
    dof_field = next((name for name in fields
                      if name.lower() in {"dof", "degrees_of_freedom",
                                          "степени_свободы"}), None)
    ratio_field = next((name for name in fields
                        if name.lower() == "chi2_dof"), None)
    has_chi2 = chi2_field is not None
    has_dof = dof_field is not None
    ratios = []
    if rows and ratio_field is not None:
        for number, row in enumerate(rows, 1):
            try:
                value = float(row[ratio_field])
            except (TypeError, ValueError) as exc:
                raise ValueError("строка %d содержит нечисловое отношение χ²/dof"
                                 % number) from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError("строка %d содержит недопустимое отношение χ²/dof"
                                 % number)
            ratios.append(value)
    # Заголовки сами по себе не являются наблюдением: пустая таблица с
    # колонками chi2 и dof не может закрыть долг происхождения чисел.
    has_rows = bool(rows)
    separate = has_rows and has_chi2 and has_dof
    ratio_consistent = None
    inconsistency = None
    if separate:
        ratio_consistent = True
        for number, row in enumerate(rows, 1):
            try:
                chi2 = float(row[chi2_field])
                dof = float(row[dof_field])
            except (TypeError, ValueError) as exc:
                raise ValueError("строка %d содержит нечисловые χ² или dof"
                                 % number) from exc
            if (not math.isfinite(chi2) or chi2 < 0
                    or not math.isfinite(dof) or dof <= 0
                    or not dof.is_integer()):
                raise ValueError("строка %d содержит недопустимые χ² или dof"
                                 % number)
            if ratio_field is not None:
                expected = chi2 / dof
                observed = float(row[ratio_field])
                if not math.isclose(observed, expected, rel_tol=1e-9,
                                    abs_tol=1e-12):
                    ratio_consistent = False
                    inconsistency = (
                        "строка %d: χ²/dof=%g, но χ²/dof из полей=%g"
                        % (number, observed, expected))
                    break
    if separate and ratio_consistent is False:
        status = "unsupported"
        reason = (
            "таблица предъявляет отдельные χ² и dof, но готовое отношение "
            "им противоречит: %s" % inconsistency
        )
    elif separate:
        status = "verified-in-scope"
        reason = "исходные χ² и dof предъявлены раздельно"
    elif not has_rows:
        status = "not-evaluated"
        reason = (
            "таблица не содержит строк наблюдения; одних заголовков χ² и dof "
            "недостаточно для реконструкции"
        )
    else:
        status = "not-evaluated"
        reason = (
            "таблица содержит только готовое отношение χ²/dof; число степеней "
            "свободы не предъявлено, поэтому научная интерпретация χ²/dof "
            "остаётся not-evaluated"
        )
    return {
        "статус": status,
        "источник_наблюдения": str(path),
        "столбцы": fields,
        "строк": len(rows),
        "отношение_наблюдено": bool(ratios),
        "chi2_наблюдено_отдельно": has_chi2,
        "dof_наблюдено_отдельно": has_dof,
        "отношение_согласовано_с_полями": ratio_consistent,
        "причина": reason,
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

        consistent = root / "consistent.csv"
        consistent.write_text("T_mid,chi2,dof,chi2_dof\n1,4.0,2,2.0\n",
                              encoding="utf-8")
        report = inspect(consistent)
        check("готовое отношение согласуется с раздельными полями",
              report["статус"] == "verified-in-scope"
              and report["отношение_согласовано_с_полями"] is True)

        inconsistent = root / "inconsistent.csv"
        inconsistent.write_text("T_mid,chi2,dof,chi2_dof\n1,4.0,2,3.0\n",
                                encoding="utf-8")
        report = inspect(inconsistent)
        check("противоречивое отношение не считается доказанным",
              report["статус"] == "unsupported"
              and report["отношение_согласовано_с_полями"] is False)

        ratio.write_text("T_mid,chi2_dof\n1,nan\n", encoding="utf-8")
        try:
            inspect(ratio)
        except ValueError:
            check("нефинитное отношение отвергается", True)
        else:
            check("нефинитное отношение отвергается", False)

        empty = root / "empty.csv"
        empty.write_text("T_mid,chi2,dof\n", encoding="utf-8")
        report = inspect(empty)
        check("пустая таблица с заголовками не закрывает наблюдение",
              report["статус"] == "not-evaluated"
              and report["строк"] == 0)

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
