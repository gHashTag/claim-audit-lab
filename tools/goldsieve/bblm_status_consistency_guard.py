#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож согласованности машинных статусов BBLM.

Протокол BBLM и отчёт расчёта имеют разные роли: первый перечисляет
обязательные элементы, второй предъявляет наблюдение и вычисленные детали.
Если один файл объявит коэффициенты закрытыми, а другой оставит их
``analytic_source_absent``, текстовый доклад может скрыть это расхождение.
Этот сторож сравнивает только машинные артефакты и сохраняет научный предел:
согласованность файлов не доказывает закон GUE и не закрывает аналитический
источник коэффициентов.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "bblm_protocol.json"
ELEMENTS = HERE / "bblm_elements.json"
ACCOUNTING = HERE / "bblm_accounting.json"
OUT = HERE / "bblm_status_consistency_guard.json"


def _load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, "не удалось прочитать %s: %s" % (path, exc)
    if not isinstance(value, dict):
        return None, "артефакт %s не является JSON-объектом" % path
    return value, None


def audit(
    protocol: dict[str, Any] | None,
    elements: dict[str, Any] | None,
    accounting: dict[str, Any] | None,
) -> dict[str, Any]:
    """Сверить форму трёх артефактов без восстановления пропущенных полей."""
    errors: list[str] = []
    if protocol is None or elements is None or accounting is None:
        errors.append("один или несколько артефактов BBLM отсутствуют или повреждены")
        return _result("unsupported", errors, {}, {})

    p_rows = protocol.get("elements")
    if not isinstance(p_rows, list):
        errors.append("bblm_protocol.json не содержит списка elements")
        p_rows = []
    p_by_name = {
        row.get("element"): row
        for row in p_rows
        if isinstance(row, dict) and isinstance(row.get("element"), str)
    }
    missing = {
        row["element"]
        for row in p_rows
        if isinstance(row, dict) and not row.get("present")
        and isinstance(row.get("element"), str)
    }
    open_accounting = accounting.get("open_with_machine_question")
    if not isinstance(open_accounting, list):
        errors.append("учёт BBLM не содержит списка open_with_machine_question")
        open_accounting = []
    open_accounting_set = {str(item) for item in open_accounting}

    if protocol.get("required_total") != len(p_rows):
        errors.append("required_total не совпадает с числом строк protocol.elements")
    if protocol.get("missing_count") != len(missing):
        errors.append("missing_count не совпадает с числом отсутствующих элементов")
    if protocol.get("present_count") != len(p_rows) - len(missing):
        errors.append("present_count не раскладывает protocol.elements")
    if missing != open_accounting_set:
        errors.append(
            "список открытых элементов расходится между protocol и accounting"
        )

    coeff = p_by_name.get("coefficient_rederivation")
    if "coefficient_rederivation" in missing:
        if not isinstance(coeff, dict) or coeff.get("код_вопроса") != "analytic_source_absent":
            errors.append(
                "отсутствующий coefficient_rederivation не имеет кода "
                "analytic_source_absent"
            )
    elif isinstance(coeff, dict) and coeff.get("код_вопроса") == "analytic_source_absent":
        errors.append(
            "coefficient_rederivation одновременно объявлен присутствующим "
            "и помечен analytic_source_absent"
        )

    elements_open = elements.get("elements_open_with_machine_question")
    if not isinstance(elements_open, list):
        errors.append("bblm_elements.json не содержит elements_open_with_machine_question")
        elements_open = []
    elements_open_set = {
        str(row.get("element"))
        for row in elements_open
        if isinstance(row, dict) and row.get("element")
    }
    if elements_open_set != missing:
        errors.append("открытые элементы bblm_elements расходятся с protocol")

    if "coefficient_rederivation" in missing:
        row = next(
            (
                row for row in elements_open
                if isinstance(row, dict)
                and row.get("element") == "coefficient_rederivation"
            ),
            None,
        )
        if not isinstance(row, dict) or row.get("machine_reason_code") != "analytic_source_absent":
            errors.append(
                "открытый коэффициент в bblm_elements не имеет кода "
                "analytic_source_absent"
            )

    status = "verified-in-scope" if not errors else "unsupported"
    summary = {
        "required_total": len(p_rows),
        "present_count": len(p_rows) - len(missing),
        "missing_count": len(missing),
        "missing_elements": sorted(missing),
        "protocol_verdict": protocol.get("verdict"),
        "protocol_status_class": protocol.get("status_class"),
        "elements_status_class": elements.get("status_class"),
        "accounting_divergence_count": accounting.get("divergence_count"),
    }
    return _result(status, errors, summary, {
        "ограничение": (
            "согласованность машинных статусов не является научным "
            "подтверждением zeta/GUE; analytic_source_absent сохраняется "
            "до предъявления аналитической формулы и номера уравнения"
        )
    })


def _result(
    status: str,
    errors: list[str],
    summary: dict[str, Any],
    extra: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "статус": status,
        "проверка": "согласованность машинных статусов BBLM",
        "ошибки": errors,
        "сводка": summary,
    }
    result.update(extra)
    return result


def _selftest() -> int:
    protocol, _ = _load(PROTOCOL)
    elements, _ = _load(ELEMENTS)
    accounting, _ = _load(ACCOUNTING)
    if protocol is None or elements is None or accounting is None:
        print("самопроверка статусов BBLM: ПРОВАЛ — нет текущих артефактов")
        return 1
    passed = failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print("  ок      " + label)
        else:
            failed += 1
            print("  ПРОВАЛ  " + label)

    good = audit(protocol, elements, accounting)
    check("согласованные текущие артефакты принимаются",
          good["статус"] == "verified-in-scope"
          and not good["ошибки"])
    check("открытый элемент сохранён в сводке",
          good["сводка"]["missing_elements"] == ["coefficient_rederivation"])
    check("научное ограничение предъявлено",
          "научным" in good["ограничение"])

    mutated_protocol = copy.deepcopy(protocol)
    rows = mutated_protocol["elements"]
    coeff = next(row for row in rows if row["element"] == "coefficient_rederivation")
    coeff["present"] = True
    mutated = audit(mutated_protocol, elements, accounting)
    check("мутация закрытия коэффициентов обнаруживается",
          mutated["статус"] == "unsupported")

    mutated_elements = copy.deepcopy(elements)
    mutated_elements["elements_open_with_machine_question"] = []
    mutated = audit(protocol, mutated_elements, accounting)
    check("исчезновение открытого элемента обнаруживается",
          mutated["статус"] == "unsupported")

    mutated_accounting = copy.deepcopy(accounting)
    mutated_accounting["open_with_machine_question"] = []
    mutated = audit(protocol, elements, mutated_accounting)
    check("расхождение учёта обнаруживается",
          mutated["статус"] == "unsupported")

    with tempfile.TemporaryDirectory(prefix="goldsieve-bblm-status-") as td:
        bad = Path(td) / "bad.json"
        bad.write_text("{\"broken\":", encoding="utf-8")
        loaded, error = _load(bad)
        check("повреждённый машинный артефакт не становится покрытием",
              loaded is None and error is not None)

    print("самопроверка согласованности статусов BBLM: "
          "%d пройдено, %d провалено" % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv not in ([], ["--scan"]):
        print("использование: bblm_status_consistency_guard.py [--selftest|--scan]")
        return 2
    protocol, p_error = _load(PROTOCOL)
    elements, e_error = _load(ELEMENTS)
    accounting, a_error = _load(ACCOUNTING)
    errors = [item for item in (p_error, e_error, a_error) if item]
    if errors:
        report = _result("unsupported", errors, {}, {
            "источник_наблюдения": str(PROTOCOL),
            "ограничение": "научный вердикт не выносится",
        })
    else:
        report = audit(protocol, elements, accounting)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож согласованности статусов BBLM: %s; ошибок %d"
          % (report["статус"], len(report["ошибки"])))
    print("JSON: %s" % OUT)
    return 0 if report["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
