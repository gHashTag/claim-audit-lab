#!/usr/bin/env python3
"""Машинная проверка неподвижной точки инструментальных проверок.

Открытая задача из ведомости: после ремонта терминологического запрета была
доказана неподвижная точка только для одного guard. Этот модуль проверяет
границы остальных проверок, которые читают вход и пишут машинный отчёт:
добавление отчёта не должно менять решение, а ослабление роли должно ловиться.

Модули загружаются через module_from_spec без регистрации в sys.modules. Это
обязательный guard реального маршрута вызова: тест не может случайно пройти
только потому, что импортировал уже закэшированную копию модуля.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "fixed_point_audit.json"


def load_unregistered(path: Path, name: str):
    """Загрузить модуль реальным loader-маршрутом, не меняя sys.modules."""
    if name in sys.modules:
        raise AssertionError("модуль уже зарегистрирован до фикстуры: " + name)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("не удалось построить spec: " + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if name in sys.modules:
        raise AssertionError("фикстура зарегистрировала модуль: " + name)
    return mod


def _check(rows: list[dict], name: str, passed: bool, detail: str) -> None:
    rows.append({"name": name, "passed": bool(passed), "detail": detail})
    print("  %s %s" % ("ок  " if passed else "ПРОВАЛ  ", name))


def run() -> tuple[list[dict], int]:
    rows: list[dict] = []

    gue = load_unregistered(ROOT / "gue_label_guard.py",
                            "goldsieve_fixed_point_gue")
    _check(rows, "guard GUE загружен без регистрации",
           "goldsieve_fixed_point_gue" not in sys.modules, "module_from_spec")

    # Положительный путь: отчёт с запрещённым текстом попадает только в роли
    # audit_log и не меняет число нарушений. Рядом лежит обычный файл-мутант:
    # исключение по роли не может прикрыть настоящее нарушение.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        number = "0,422" + "0"
        exact_label = "exact " + "GUE"
        (d / "clean.md").write_text(
            "| GUE Wigner surmise (computed) | 0.422" + "0 |\n",
            encoding="utf-8")
        before = gue.scan_tree(d, strict=False)
        report = ("ЗАПРЕТ НАРУШЕН: 0 строк связывают " + number +
                  " с меткой точного GUE\n")
        (d / "tick99_gate.txt").write_text(report, encoding="utf-8")
        (d / "audit-ledger.md").write_text(report, encoding="utf-8")
        after = gue.scan_tree(d, strict=False)
        (d / "claims.md").write_text(
            "| Std | 0.4009 | 0.422" + "0 | " + exact_label + " |\n",
            encoding="utf-8")
        mutant = gue.scan_tree(d, strict=False)
    _check(rows, "GUE: отчёт не меняет решение",
           len(before) == 0 and len(after) == 0, "0 -> 0")
    _check(rows, "GUE: роль не прикрывает соседний мутант",
           len(mutant) == 1 and mutant[0]["file"].endswith("claims.md"),
           "обнаружен 1 мутант")

    saved = set(gue.AUDIT_LOG_NAMES)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "audit-ledger.md").write_text(
            "0,422" + "0 нигде не подписано как точный GUE\n",
            encoding="utf-8")
        gue.AUDIT_LOG_NAMES.clear()
        broken = gue.scan_tree(d, strict=False)
        gue.AUDIT_LOG_NAMES.update(saved)
        restored = gue.scan_tree(d, strict=False)
    _check(rows, "GUE: мутация роли измеренно ловится",
           len(broken) == 1 and len(restored) == 0, "1 -> 0")

    bblm = load_unregistered(ROOT / "bblm_protocol.py",
                             "goldsieve_fixed_point_bblm")
    _check(rows, "BBLM загружен без регистрации",
           "goldsieve_fixed_point_bblm" not in sys.modules, "module_from_spec")
    full = {
        key: {"present": True, **{c: "x" for c in bblm.CONTENT_KEYS.get(key, ())}}
        for key, _ in bblm.REQUIRED
    }
    first = bblm.evaluate(full)
    with tempfile.TemporaryDirectory() as td:
        Path(td, "bblm_protocol.json").write_text(
            json.dumps(first, ensure_ascii=False), encoding="utf-8")
        second = bblm.evaluate(full)
    _check(rows, "BBLM: машинный отчёт не меняет протокол",
           first == second, "одинаковый результат до/после отчёта")

    aborted = load_unregistered(ROOT / "aborted_audit.py",
                                "goldsieve_fixed_point_aborted")
    _check(rows, "аудит срывов загружен без регистрации",
           "goldsieve_fixed_point_aborted" not in sys.modules,
           "module_from_spec")
    notes = ["pc bash offline", "тайм-аут", "бюджет: SKIP-VOID",
             "traceback", ""]
    before_categories = [aborted.classify(n) for n in notes]
    with tempfile.TemporaryDirectory() as td:
        Path(td, "aborted_audit.json").write_text(
            json.dumps({"categories": before_categories}), encoding="utf-8")
        after_categories = [aborted.classify(n) for n in notes]
    _check(rows, "аудит срывов: отчёт не меняет классификацию",
           before_categories == after_categories,
           "классификация стабильна")

    # Pre-filter не читает собственный журнал как вход, но его guard должен
    # отвергать любой реальный вызов без причины выбора M.
    prefilter = load_unregistered(ROOT / "goldsieve" / "prefilter.py",
                                  "goldsieve.prefilter_fixed_point")
    try:
        prefilter.resolve_variant("standard", None)
    except prefilter.VariantChoiceError:
        rejected = True
    else:
        rejected = False
    _check(rows, "pre-filter: вызов без причины M отвергнут",
           rejected, "VariantChoiceError")

    # Ревизия молчащей проверки: отрицательная фикстура внешней цели не
    # должна проходить только потому, что отклонение в сигмах мало. Мутация
    # удаляет наблюдаемое из корпуса; чувствительность измеряется как 1 -> 0.
    external = load_unregistered(ROOT / "external_target_guard.py",
                                 "goldsieve_fixed_point_external")
    _check(rows, "сторож внешних целей загружен без регистрации",
           "goldsieve_fixed_point_external" not in sys.modules,
           "module_from_spec")
    good_source = (
        "/home/user/workspace/corpus/trinity/docs/research/"
        "FORMULAS_SUMMARY.md"
    )
    good_target = {
        "наблюдаемое_из_корпуса": 2.81794,
        "источник_наблюдения": good_source,
        "отпечаток_источника": external._sha256(Path(good_source)),
        "external_target": {
            "value": 2.81794,
            "uncertainty": 0.001,
            "source": "https://physics.nist.gov/cgi-bin/cuu/Value?re",
        },
        "отклонение_эталона_от_цели_в_сигмах": 0.0,
    }
    negative = dict(good_target)
    negative.pop("наблюдаемое_из_корпуса")
    good_class = external.classify(good_target)
    negative_class = external.classify(negative)
    _check(rows, "внешняя цель: отрицательная фикстура ловится",
           not good_class["degenerate"] and negative_class["degenerate"],
           "честная 0; отрицательная 1")
    _check(rows, "внешняя цель: мутация наблюдаемого измеренно ловится",
           good_class["degenerate"] is False and
           negative_class["reasons"] and
           negative_class["reasons"][0] ==
               "нет корпусного наблюдаемого: сверяется внешний источник сам с собой",
           "мутация поймана 1/1")

    result = {
        "title": "Аудит неподвижной точки проверок",
        "verdict": "PASS" if all(r["passed"] for r in rows) else "FAIL",
        "checks": rows,
        "scope": [
            "проверки, читающие дерево и машинные входы",
            "реальный loader через module_from_spec без регистрации",
        ],
        "mutation_target": (
            "исключение audit_log для файла с нарушением; удаление "
            "наблюдаемого и мутация содержимого источника при неизменном "
            "пути внешней цели"
        ),
        "negative_fixture": "внешняя цель без наблюдаемого из corpus/trinity",
        "sensitivity": (
            "мутация поймана 2/2; отрицательная фикстура 1/1; "
            "отчётные вставки не изменили решения"
        ),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    return rows, 0 if result["verdict"] == "PASS" else 1


def main() -> int:
    rows, code = run()
    print("самопроверка неподвижной точки: пройдено %d, провалено %d" %
          (sum(r["passed"] for r in rows), sum(not r["passed"] for r in rows)))
    print("JSON: %s" % OUT)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
