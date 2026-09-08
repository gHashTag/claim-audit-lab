# -*- coding: utf-8 -*-
"""Машинный вопрос о предпосылке независимости перебранных формул.

Сторож ``independence_assumption_guard.py`` проверяет тот же контракт, но этот
кейс получает наблюдаемое другим маршрутом: самостоятельно разбирает AST
файлов cases/ и не читает JSON-отчёт сторожа. Отсутствие декларации или
декларация ``unknown`` не превращаются в независимость. У кейса нет
вычислимого научного эталона для самой предпосылки, поэтому итог обязан быть
ВОПРОС с машинной причиной ``independence_undeclared``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from goldsieve.sieve import Claim


КОРЕНЬ = Path(__file__).resolve().parent.parent
КЕЙСЫ = КОРЕНЬ / "cases"


def _это_claim(узел: ast.Call) -> bool:
    функция = узел.func
    return ((isinstance(функция, ast.Name) and функция.id == "Claim")
            or (isinstance(функция, ast.Attribute)
                and функция.attr == "Claim"))


def _литерал(узел: ast.AST):
    if isinstance(узел, ast.Constant):
        return узел.value
    return None


def _наблюдаемое() -> dict:
    """Независимо пересчитать статусы деклараций в AST всех кейсов."""
    сводка = {
        "verified-in-scope": 0,
        "not-evaluated": 0,
        "unsupported": 0,
        "platform-unverified": 0,
    }
    причин: dict[str, int] = {}
    утверждений = 0
    ошибки = 0

    for путь in sorted(КЕЙСЫ.glob("*.py")):
        try:
            дерево = ast.parse(путь.read_text(encoding="utf-8"),
                               filename=str(путь))
        except (OSError, UnicodeError, SyntaxError):
            ошибки += 1
            сводка["unsupported"] += 1
            причин["case_ast_unreadable"] = (
                причин.get("case_ast_unreadable", 0) + 1)
            continue
        for узел in ast.walk(дерево):
            if not isinstance(узел, ast.Call) or not _это_claim(узел):
                continue
            утверждений += 1
            поле = next((ключ for ключ in узел.keywords
                         if ключ.arg == "tests_independent"), None)
            значение = None if поле is None else _литерал(поле.value)
            if значение in (False, "false"):
                статус = "unsupported"
                причина = "tests_declared_not_independent"
            elif значение in (True, "true"):
                статус = "not-evaluated"
                причина = "independence_assumption_declared_true_unverified"
            elif значение in ("unknown", "not-declared", None):
                статус = "not-evaluated"
                причина = ("independence_assumption_absent"
                           if поле is None
                           else "independence_assumption_unknown")
            else:
                статус = "unsupported"
                причина = "independence_assumption_nonliteral"
            сводка[статус] += 1
            причин[причина] = причин.get(причина, 0) + 1

    return {
        "утверждений": утверждений,
        "сводка": сводка,
        "причины": причин,
        "ошибки_разбора": ошибки,
    }


def _ложное_наблюдаемое() -> dict:
    """Контроль формы: намеренно не совпадает с настоящим счётчиком."""
    результат = _наблюдаемое()
    результат["утверждений"] += 1
    return результат


_ПРОПУСКИ = {
    "С1": "для предпосылки нет независимого вычислимого эталона",
    "С2": "декларация в паспорте не является доказательством независимости",
    "С3": "AST-сканирование не измеряет корреляции испытаний",
    "С4": "молчание не считается независимостью",
    "С5": "unknown не выбирает допустимость поправки Шидака",
    "С6": "true без измерения остаётся непроверенным",
    "С7": "false — ограничение применимости, а не научный эталон",
    "С8": "число Claim не является размером независимой выборки",
    "С9": "число файлов cases не является числом испытаний",
    "С10": "разбор синтаксиса не оценивает зависимость данных",
    "С11": "порог множественности не вычисляется этим кейсом",
    "С12": "второй метод для независимости не предъявлен",
    "С13": "все пропуски объявлены явно",
    "С14": "сквозная подстановка не заменяет измерение зависимости",
    "С15": "внешняя цель не относится к предпосылке независимости",
    "С16": "число формул не является доказательством независимости",
    "С17": "описание кейса не выбирает статус испытаний",
    "С18": "область AST ограничена файлами cases/*.py",
    "С19": "точность синтаксического разбора не даёт статистического вывода",
    "С20": "M_eff остаётся отдельным научным долгом",
    "С21": "алгебраическая форма не предъявляет корреляционную матрицу",
}


assert _наблюдаемое()["утверждений"] > 0
assert _ложное_наблюдаемое()["утверждений"] != _наблюдаемое()["утверждений"]


CLAIMS = [
    Claim(
        name="Предпосылка независимости перебранных формул доказана",
        source="cases/*.py: AST-вызовы Claim с полем tests_independent",
        stated=None,
        reference=None,
        observed=_наблюдаемое,
        wrong=_ложное_наблюдаемое,
        tolerance=0.0,
        inputs=[str(путь) for путь in sorted(КЕЙСЫ.glob("*.py"))],
        skip_reasons=_ПРОПУСКИ,
        claim_family="zeta/GUE: применимость предпосылки независимости",
        observable="статусы деклараций tests_independent в AST кейсов",
        measurement_source="самостоятельный AST-разбор корпуса кейсов",
        uncertainty_type="none",
        novelty_key="trinity:zeta:independence-assumption:20260908",
        information_class="independence",
        purpose="audit",
        models=["декларация независимости", "измеренная независимость"],
        independent_of={
            "source": "независимый AST-маршрут, не JSON сторожа",
            "claims": "рецепт zeta, общий M_eff и BBLM",
        },
        tests_independent="unknown",
        reason_code_hint="independence_undeclared",
        notes=(
            "Кейс самостоятельно разбирает AST файлов cases/*.py. "
            "Отсутствующие и неизвестные декларации не считаются независимостью; "
            "без измеренной зависимости и вычислимого эталона результатом "
            "остаётся машинный ВОПРОС, а не научное утверждение о zeta/GUE."
        ),
    )
]
