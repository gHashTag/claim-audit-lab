#!/usr/bin/env python3
"""Сторож риска: чистый масштаб не доказывает совпадение формы BBLM."""

from __future__ import annotations

import copy
import json
import os
import sys
from typing import Any


ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(ROOT, "bblm_elements.json")


def _audit(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"статус": "unsupported", "причина": "отчёт не является объектом"}
    closed = data.get("elements_closed_by_code")
    if not isinstance(closed, dict):
        return {"статус": "unsupported",
                "причина": "нет машинного перечня закрытых элементов"}
    shape = closed.get("shape_vs_scale_discrimination")
    if not isinstance(shape, dict):
        return {"статус": "not-evaluated",
                "причина": "раздел разделения формы и масштаба отсутствует"}
    required = (
        "alpha_best_pure_scale",
        "residual_after_best_scale",
        "residual_over_sigma",
        "worst_statistic",
        "worst_residual_sigma",
        "pure_scale_sufficient",
    )
    missing = [key for key in required if key not in shape]
    if missing:
        return {"статус": "not-evaluated",
                "причина": "не хватает полей: " + ", ".join(missing)}
    residual = shape.get("residual_over_sigma")
    if not isinstance(residual, dict) or not residual:
        return {"статус": "not-evaluated",
                "причина": "остатки после масштаба не предъявлены"}
    try:
        worst = float(shape["worst_residual_sigma"])
        sufficient = shape["pure_scale_sufficient"]
        if not isinstance(sufficient, bool) or worst < 0:
            raise ValueError
    except (TypeError, ValueError):
        return {"статус": "unsupported",
                "причина": "поля масштаба имеют недопустимый тип или знак"}
    if sufficient:
        return {
            "статус": "unsupported",
            "причина": "чистый масштаб ошибочно объявлен достаточным",
            "худший_остаток_сигма": worst,
        }
    return {
        "статус": "verified-in-scope",
        "причина": "отчёт не сводит формообразующее расхождение к масштабу",
        "худший_остаток_сигма": worst,
        "статистика": shape["worst_statistic"],
        "источник_отчёта": REPORT,
    }


def _selftest() -> int:
    checks = 0
    failures = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks, failures
        checks += 1
        if condition:
            print("  ок  " + name)
        else:
            failures += 1
            print("  ПРОВАЛ  " + name)

    good = {
        "elements_closed_by_code": {
            "shape_vs_scale_discrimination": {
                "alpha_best_pure_scale": 0.97,
                "residual_after_best_scale": {"p50": 0.02},
                "residual_over_sigma": {"p50": 10.0},
                "worst_statistic": "p50",
                "worst_residual_sigma": 10.0,
                "pure_scale_sufficient": False,
            }
        }
    }
    result = _audit(good)
    check("формообразующая часть не сводится к масштабу",
          result["статус"] == "verified-in-scope")

    missing = copy.deepcopy(good)
    del missing["elements_closed_by_code"][
        "shape_vs_scale_discrimination"]["worst_residual_sigma"]
    check("неполный отчёт остаётся not-evaluated",
          _audit(missing)["статус"] == "not-evaluated")

    malicious = copy.deepcopy(good)
    malicious["elements_closed_by_code"][
        "shape_vs_scale_discrimination"]["pure_scale_sufficient"] = True
    check("ложное объявление достаточного масштаба блокируется",
          _audit(malicious)["статус"] == "unsupported")

    malformed = copy.deepcopy(good)
    malformed["elements_closed_by_code"][
        "shape_vs_scale_discrimination"]["worst_residual_sigma"] = "много"
    check("нечисловой остаток блокируется",
          _audit(malformed)["статус"] == "unsupported")

    check("необъектный отчёт блокируется",
          _audit([])["статус"] == "unsupported")
    print("самопроверка сторожа формы и масштаба: %d пройдено, %d провалено"
          % (checks, failures))
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    try:
        with open(REPORT, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        print("сторож формы и масштаба: not-evaluated; отчёт не прочитан: %s"
              % exc)
        return 0
    result = _audit(data)
    print("сторож формы и масштаба: %s; %s"
          % (result["статус"], result["причина"]))
    if "худший_остаток_сигма" in result:
        print("  худший остаток: %.6g сигма (%s)"
              % (result["худший_остаток_сигма"], result["статистика"]))
    print("  источник отчёта: %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
