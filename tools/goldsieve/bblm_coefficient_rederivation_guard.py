#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точечный сторож незакрытого вывода коэффициентов BBLM.

Наличие формулы поправки не является независимым выводом численных
коэффициентов. Этот сторож проверяет именно машинный вопрос протокола:
аналитический источник с формулой и номером уравнения отсутствует, поэтому
элемент получает код ``analytic_source_absent`` и статус ``not-evaluated``.
Это не научный вердикт и не новая внешняя константа.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "bblm_protocol.json"
OUT = HERE / "bblm_coefficient_rederivation_guard.json"
ELEMENT = "coefficient_rederivation"
QUESTION_CODE = "analytic_source_absent"


def _load(path: Path) -> tuple[dict | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "файл протокола отсутствует"
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, "протокол нельзя прочитать: %s" % exc
    if not isinstance(value, dict):
        return None, "протокол не является объектом JSON"
    return value, None


def inspect(path: Path = PROTOCOL) -> dict:
    document, error = _load(path)
    if error:
        return {
            "статус": "not-evaluated",
            "код_вопроса": QUESTION_CODE,
            "причина": error,
            "источник_наблюдения": str(path),
        }

    elements = document.get("elements")
    if not isinstance(elements, list):
        return {
            "статус": "unsupported",
            "причина": "в протоколе отсутствует список элементов",
            "источник_наблюдения": str(path),
        }
    matches = [
        item for item in elements
        if isinstance(item, dict) and item.get("element") == ELEMENT
    ]
    if len(matches) != 1:
        return {
            "статус": "unsupported",
            "причина": (
                "элемент coefficient_rederivation предъявлен не ровно один раз"
            ),
            "число_элементов": len(matches),
            "источник_наблюдения": str(path),
        }
    item = matches[0]
    present = item.get("present")
    declared = item.get("declared_present")
    code = item.get("код_вопроса")
    needed = item.get("needed")
    if present is False and declared is False and code == QUESTION_CODE:
        return {
            "статус": "not-evaluated",
            "код_вопроса": QUESTION_CODE,
            "элемент": ELEMENT,
            "аналитический_источник": "отсутствует",
            "формула_и_номер_уравнения": "не предъявлены",
            "описание_долга": str(needed or ""),
            "источник_наблюдения": str(path),
            "ограничение": (
                "машинный вопрос не доказывает коэффициенты и не является "
                "научной находкой"
            ),
        }
    if present is True and declared is True and code in (None, ""):
        return {
            "статус": "unsupported",
            "причина": (
                "коэффициентный вывод объявлен предъявленным без "
                "аналитического источника и номера уравнения"
            ),
            "элемент": ELEMENT,
            "источник_наблюдения": str(path),
        }
    return {
        "статус": "unsupported",
        "причина": "форма статуса коэффициентного вывода противоречива",
        "элемент": ELEMENT,
        "значения": {
            "present": present,
            "declared_present": declared,
            "код_вопроса": code,
        },
        "источник_наблюдения": str(path),
    }


def selftest() -> int:
    passed = failed = 0

    def check(title: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print("  ок      %s" % title)
        else:
            failed += 1
            print("  ПРОВАЛ  %s" % title)

    with tempfile.TemporaryDirectory(prefix="goldsieve-bblm-coeff-") as directory:
        root = Path(directory)
        missing = root / "нет.json"
        result = inspect(missing)
        check("отсутствующий протокол оставляет машинный вопрос",
              result["статус"] == "not-evaluated"
              and result["код_вопроса"] == QUESTION_CODE)

        question = root / "вопрос.json"
        question.write_text(json.dumps({
            "elements": [{
                "element": ELEMENT,
                "present": False,
                "declared_present": False,
                "код_вопроса": QUESTION_CODE,
            }]
        }, ensure_ascii=False), encoding="utf-8")
        result = inspect(question)
        check("отсутствующий источник получает analytic_source_absent",
              result["статус"] == "not-evaluated"
              and result["код_вопроса"] == QUESTION_CODE)

        forged = root / "подмена.json"
        forged.write_text(json.dumps({
            "elements": [{
                "element": ELEMENT,
                "present": True,
                "declared_present": True,
            }]
        }, ensure_ascii=False), encoding="utf-8")
        result = inspect(forged)
        check("заявленный вывод без источника не считается доказанным",
              result["статус"] == "unsupported")

        duplicate = root / "дубль.json"
        duplicate.write_text(json.dumps({
            "elements": [
                {"element": ELEMENT, "present": False,
                 "declared_present": False, "код_вопроса": QUESTION_CODE},
                {"element": ELEMENT, "present": False,
                 "declared_present": False, "код_вопроса": QUESTION_CODE},
            ]
        }, ensure_ascii=False), encoding="utf-8")
        check("дублированный элемент отвергается",
              inspect(duplicate)["статус"] == "unsupported")

    print("самопроверка сторожа coefficient_rederivation: пройдено %d, "
          "провалено %d" % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--selftest"]:
        return selftest()
    if args:
        print("использование: bblm_coefficient_rederivation_guard.py [--selftest]")
        return 2
    result = inspect()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож coefficient_rederivation: %s; код: %s; источник: %s" % (
        result.get("статус"), result.get("код_вопроса", "нет"),
        result.get("источник_наблюдения", str(PROTOCOL))))
    return 0 if result["статус"] in {"not-evaluated", "verified-in-scope"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
