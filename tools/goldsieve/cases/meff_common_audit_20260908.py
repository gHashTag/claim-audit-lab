# -*- coding: utf-8 -*-
"""Машинный вопрос об общем M_eff для 12 архивов.

Архивы содержат несколько записей С20 из одного перебора. Отдельные M_eff
нельзя складывать, пока не предъявлены общий ансамбль и его идентификатор.
Кейс читает исходные архивы отдельно от сводного отчёта сторожа и не
превращает наличие прочитанных файлов в научное подтверждение.
"""

from __future__ import annotations

import json
from pathlib import Path

from goldsieve.sieve import Claim


КОРЕНЬ = Path(__file__).resolve().parent.parent
СВОДКА = КОРЕНЬ / "meff_common_guard.json"


def _архивы() -> list[Path]:
    """Взять 12 архивов, перечисленных в отдельной сводке, и перечитать их."""
    результат = []
    try:
        отчёт = json.loads(СВОДКА.read_text(encoding="utf-8"))
        строки = отчёт["наблюдения"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
        строки = []
    for строка in строки:
        if not isinstance(строка, dict):
            continue
        путь = Path(строка.get("источник_наблюдения", ""))
        if путь.is_file():
            результат.append(путь)
    return результат


АРХИВЫ = _архивы()
assert len(АРХИВЫ) == 12


def _извлечь(путь: Path) -> list[dict]:
    """Извлечь только конечные числа M и M_eff из одного архива."""
    документ = json.loads(путь.read_text(encoding="utf-8"))
    строки = []
    for элемент in документ:
        if not isinstance(элемент, dict):
            continue
        for результат in элемент.get("results", []):
            if not isinstance(результат, dict):
                continue
            if результат.get("sieve") != "С20 эффективное число попыток":
                continue
            числа = результат.get("numbers")
            if not isinstance(числа, dict):
                continue
            if isinstance(числа.get("M"), (int, float)) and isinstance(
                    числа.get("M_eff"), (int, float)):
                строки.append({
                    "M": float(числа["M"]),
                    "M_eff": float(числа["M_eff"]),
                    "общий_M_eff": числа.get("M_eff_общий"),
                    "идентификатор": числа.get("идентификатор_общего_ансамбля"),
                })
    return строки


def _наблюдаемое() -> dict:
    """Пересчитать число открытых архивов по самим архивам."""
    открытые = 0
    for путь in АРХИВЫ:
        строки = _извлечь(путь)
        общий_объявлен = all(
            isinstance(строка["общий_M_eff"], (int, float))
            and isinstance(строка["идентификатор"], str)
            and bool(строка["идентификатор"].strip())
            for строка in строки
        )
        if not общий_объявлен:
            открытые += 1
    return {
        "архивов": len(АРХИВЫ),
        "открытых_архивов": открытые,
    }


def _пропуски() -> dict[str, str]:
    return {
        "С%d" % номер: "этот кейс проверяет только предъявление общего M_eff "
        "и не заменяет недостающие статистические входы" for номер in range(1, 22)
    }


CLAIMS = [
    Claim(
        name="Общий M_eff для 12 архивов предъявлен однозначно",
        source="meff_common_guard.json и 12 архивов *_external_*.json",
        stated=None,
        reference=None,
        observed=_наблюдаемое,
        wrong=None,
        tolerance=0.0,
        inputs=[str(СВОДКА)] + [str(путь) for путь in АРХИВЫ],
        skip_reasons=_пропуски(),
        claim_family="zeta/GUE: общий ансамбль эффективного числа попыток",
        observable="число архивов с несколькими записями С20 и наличие общего M_eff",
        measurement_source="архивы результатов золотого сита",
        uncertainty_type="none",
        novelty_key="trinity:zeta:common-meff:20260908",
        information_class="общий M_eff",
        purpose="audit",
        models=["отдельные M_eff", "единый общий M_eff"],
        independent_of=["рецепт zeta", "BBLM", "внешние цели тиков 262-301"],
        reason_code_hint="meff_unstable",
        notes=(
            "Пересчитано 12 архивов: в каждом есть несколько записей С20, "
            "но общий M_eff и идентификатор общего ансамбля не предъявлены. "
            "Итог не является подтверждением или опровержением zeta/GUE: "
            "это машинный ВОПРОС с причиной meff_unstable."
        ),
    )
]
