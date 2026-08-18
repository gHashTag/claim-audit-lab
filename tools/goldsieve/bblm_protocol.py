#!/usr/bin/env python3
"""Пункт 2 приказа 2026-08-18: BBLM как ПРОТОКОЛ, а не текстовое «OPEN».

Задача. Конечновысотная поправка Bogomolny-Bohigas-Leboeuf-Monastra много тиков
числилась строкой «OPEN» в ведомости. Строка в ведомости не проверяема: она не
говорит, ЧЕГО именно не хватает, и не падает, когда чего-то не хватает.

Здесь протокол описан как машинный объект: список обязательных элементов, для
каждого — предикат присутствия и текст «что именно нужно». Вердикт выносится
кодом: пока хотя бы один обязательный элемент отсутствует, это ВОПРОС (не
находка и не опровержение), и JSON содержит точный перечень недостающего.

Команды:
    python3 bblm_protocol.py            вердикт + JSON
    python3 bblm_protocol.py --selftest самопроверка с негативной фикстурой
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # объявленный пропуск: интерпретатор без pyyaml
    yaml = None

HERE = Path(__file__).resolve().parent
SPEC = HERE / "bblm_spec.yaml"
OUT = HERE / "bblm_protocol.json"

# Обязательные элементы протокола. Порядок — порядок предъявления в отчёте.
REQUIRED = (
    ("formula", "формула поправки с явными выражениями"),
    ("coefficient_rederivation", "независимый вывод численных коэффициентов"),
    ("height_parameters", "параметры высоты выборки нулей"),
    ("per_bin_heights", "L по каждой корзине бинного анализа"),
    ("unfolding_mode", "режим развёртки с проверяемым паспортом"),
    ("error_estimate_method", "метод оценки погрешности предсказания"),
    ("out_of_sample_check", "проверка вне выборки"),
    ("shape_vs_scale_discrimination", "разделение масштаба и формы"),
)

# Дополнительные условия присутствия: элемент не считается заполненным, если
# нет проверяемого содержимого. Это защита от «present: true» без содержания.
CONTENT_KEYS = {
    "formula": ("expression_n_eff", "expression_alpha_minus_1", "variable",
                "source_url"),
    "unfolding_mode": ("mode", "verifier"),
    "coefficient_rederivation": ("method",),
    "height_parameters": ("t_min", "t_max", "n_zeros", "verifier"),
    "per_bin_heights": ("bins",),
    "error_estimate_method": ("method",),
    "out_of_sample_check": ("fit_range", "test_range", "result"),
    "shape_vs_scale_discrimination": ("scale_part", "shape_part"),
}


def evaluate(spec: dict) -> dict:
    elements = []
    for key, title in REQUIRED:
        node = spec.get(key) or {}
        declared = bool(node.get("present"))
        missing_content = [k for k in CONTENT_KEYS.get(key, ())
                           if not node.get(k)]
        present = declared and not missing_content
        row = {"element": key, "title": title, "present": present,
               "declared_present": declared}
        if not present:
            if declared and missing_content:
                row["needed"] = ("объявлено присутствующим, но нет полей: "
                                 + ", ".join(missing_content))
            else:
                row["needed"] = (node.get("needed")
                                 or "элемент не описан в спецификации")
        elements.append(row)
    missing = [e for e in elements if not e["present"]]
    verdict = "ВОПРОС" if missing else "ПРОТОКОЛ ПОЛОН"
    return {
        "protocol": "BBLM finite-height correction",
        "verdict": verdict,
        "verdict_basis": (
            "вердикт ВОПРОС вынесен кодом по числу отсутствующих обязательных "
            "элементов; это НЕ находка и НЕ опровержение"
            if missing else
            "все обязательные элементы заполнены проверяемым содержимым"),
        "required_total": len(REQUIRED),
        "present_count": len(elements) - len(missing),
        "missing_count": len(missing),
        "elements": elements,
        "status_class": "not-evaluated",
    }


def load_spec(path: Path = SPEC) -> dict:
    if yaml is None:
        raise RuntimeError("нет pyyaml: разбор спецификации невозможен "
                           "(объявленный пропуск)")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def selftest() -> int:
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok     " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    if yaml is None:
        print("ПРОПУСК самопроверки протокола: нет pyyaml в этом интерпретаторе")
        return 0
    spec = load_spec()
    rep = evaluate(spec)
    check("вердикт вынесен кодом", rep["verdict"] in ("ВОПРОС", "ПРОТОКОЛ ПОЛОН"))
    check("на текущей спецификации это ВОПРОС", rep["verdict"] == "ВОПРОС")
    check("перечень недостающего непуст", rep["missing_count"] >= 1)
    check("у каждого недостающего есть текст «что нужно»",
          all(e.get("needed") for e in rep["elements"] if not e["present"]))
    check("присутствующие элементы тоже есть", rep["present_count"] >= 1)

    # НЕГАТИВНАЯ ФИКСТУРА 1: полностью заполненный протокол обязан дать «полон».
    full = {k: {"present": True, **{c: "x" for c in CONTENT_KEYS.get(k, ())}}
            for k, _ in REQUIRED}
    check("полный протокол даёт ПРОТОКОЛ ПОЛОН",
          evaluate(full)["verdict"] == "ПРОТОКОЛ ПОЛОН")

    # МУТАЦИОННАЯ ЦЕЛЬ: снятие ОДНОГО элемента обязано быть замечено — иначе
    # проверка молчит и покрытием не является.
    caught = 0
    for key, _ in REQUIRED:
        mutant = {k: dict(v) for k, v in full.items()}
        mutant[key]["present"] = False
        if evaluate(mutant)["verdict"] == "ВОПРОС":
            caught += 1
    check("мутация каждого элемента ловится (%d/%d)" % (caught, len(REQUIRED)),
          caught == len(REQUIRED))

    # МУТАЦИОННАЯ ЦЕЛЬ 2: «present: true» без содержимого обязано быть отвергнуто.
    hollow = {k: dict(v) for k, v in full.items()}
    for c in CONTENT_KEYS["out_of_sample_check"]:
        hollow["out_of_sample_check"].pop(c, None)
    hollow_rep = evaluate(hollow)
    check("пустое «present: true» отвергается",
          hollow_rep["verdict"] == "ВОПРОС"
          and any("нет полей" in (e.get("needed") or "")
                  for e in hollow_rep["elements"]))
    print("самопроверка протокола BBLM: пройдено %d, провалено %d" % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if yaml is None:
        print("ПРОПУСК: нет pyyaml (объявленный пропуск)")
        return 0
    rep = evaluate(load_spec())
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("протокол BBLM: вердикт %s (заполнено %d из %d)"
          % (rep["verdict"], rep["present_count"], rep["required_total"]))
    for e in rep["elements"]:
        mark = "есть   " if e["present"] else "НЕТ    "
        print("  %s %-32s %s" % (mark, e["element"],
                                 "" if e["present"] else e["needed"][:96]))
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
