# -*- coding: utf-8 -*-
"""Машинный вопрос об идентифицируемости общего M_eff.

Кейс самостоятельно находит архивы с несколькими записями сита С20 и читает
их содержимое. Отчёт сторожа не используется как наблюдение. Одинаковое M
в этих архивах не предъявляет общий ансамбль: нужны общий M_eff и
идентификатор набора. Пока их нет, вопрос о поправке множественности
остаётся not-evaluated.
"""

from __future__ import annotations

import json
from pathlib import Path

from goldsieve.sieve import Claim


if __name__ in __import__("sys").modules:
    raise RuntimeError(
        "кейс должен загружаться через module_from_spec без регистрации"
    )


КОРЕНЬ = Path(__file__).resolve().parent.parent
ОЖИДАЕМЫЕ_АРХИВЫ = 12
ОЖИДАЕМЫЙ_M = 123201.0


def _архивы() -> list[Path]:
    """Найти архивы, где действительно предъявлены записи С20."""
    найденные = []
    for путь in sorted(КОРЕНЬ.glob("*_external_*.json")):
        try:
            документ = json.loads(путь.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        записи = []
        for элемент in документ if isinstance(документ, list) else []:
            if not isinstance(элемент, dict):
                continue
            for результат in элемент.get("results", []):
                if (
                    isinstance(результат, dict)
                    and результат.get("sieve")
                    == "С20 эффективное число попыток"
                ):
                    числа = результат.get("numbers")
                    if (
                        isinstance(числа, dict)
                        and isinstance(числа.get("M"), (int, float))
                        and isinstance(числа.get("M_eff"), (int, float))
                    ):
                        записи.append(результат)
        if len(записи) > 1:
            найденные.append(путь)
    return найденные


АРХИВЫ = _архивы()
assert len(АРХИВЫ) == ОЖИДАЕМЫЕ_АРХИВЫ


def _записи(путь: Path) -> list[dict]:
    документ = json.loads(путь.read_text(encoding="utf-8"))
    записи = []
    for элемент in документ:
        if not isinstance(элемент, dict):
            continue
        for результат in элемент.get("results", []):
            if (
                not isinstance(результат, dict)
                or результат.get("sieve") != "С20 эффективное число попыток"
            ):
                continue
            числа = результат.get("numbers")
            if not isinstance(числа, dict):
                continue
            if not isinstance(числа.get("M"), (int, float)):
                continue
            if not isinstance(числа.get("M_eff"), (int, float)):
                continue
            записи.append(
                {
                    "M": float(числа["M"]),
                    "M_eff": float(числа["M_eff"]),
                    "общий_M_eff": числа.get("M_eff_общий"),
                    "идентификатор": числа.get(
                        "идентификатор_общего_ансамбля"
                    ),
                }
            )
    return записи


def _наблюдаемое() -> dict:
    """Извлечь общий размер, разброс M_eff и предъявление общего ансамбля."""
    все = []
    по_архивам = {}
    for путь in АРХИВЫ:
        записи = _записи(путь)
        по_архивам[путь.name] = len(записи)
        все.extend(записи)
    значения_m = sorted({запись["M"] for запись in все})
    значения_meff = sorted({запись["M_eff"] for запись in все})
    общие = [
        запись
        for запись in все
        if isinstance(запись["общий_M_eff"], (int, float))
        and isinstance(запись["идентификатор"], str)
        and bool(запись["идентификатор"].strip())
    ]
    return {
        "статус_входа": "verified-in-scope",
        "научный_статус": "not-evaluated",
        "архивов": len(АРХИВЫ),
        "записей_С20": len(все),
        "значения_M": значения_m,
        "ожидаемый_M_во_всех_записях": (
            len(значения_m) == 1 and значения_m[0] == ОЖИДАЕМЫЙ_M
        ),
        "различных_M_eff": len(значения_meff),
        "минимальный_M_eff": min(значения_meff),
        "максимальный_M_eff": max(значения_meff),
        "записей_с_общим_M_eff_и_идентификатором": len(общие),
        "записей_по_архивам": по_архивам,
        "код_вопроса": "meff_unstable",
    }


def _ложное_наблюдаемое() -> dict:
    результат = _наблюдаемое()
    результат["записей_с_общим_M_eff_и_идентификатором"] = 1
    return результат


def _контроль_формы() -> float:
    return float(_наблюдаемое()["архивов"])


ПРОПУСКИ = {
    "С%d" % номер: (
        "кейс устанавливает состав M_eff, но не предъявляет независимый "
        "эталон зависимости испытаний"
    )
    for номер in range(1, 22)
}


Наблюдение = _наблюдаемое()
assert Наблюдение["архивов"] == ОЖИДАЕМЫЕ_АРХИВЫ
assert Наблюдение["записей_С20"] > Наблюдение["архивов"]
assert Наблюдение["ожидаемый_M_во_всех_записях"]
assert Наблюдение["записей_с_общим_M_eff_и_идентификатором"] == 0
assert _ложное_наблюдаемое()[
    "записей_с_общим_M_eff_и_идентификатором"
] != Наблюдение["записей_с_общим_M_eff_и_идентификатором"]


CLAIMS = [
    Claim(
        name="Общий M_eff для записей С20 предъявлен и идентифицируем",
        source="12 архивов *_external_*.json с несколькими записями С20",
        stated=None,
        reference=None,
        observed=_наблюдаемое,
        wrong=_ложное_наблюдаемое,
        null_model=_контроль_формы,
        null_expect=float(ОЖИДАЕМЫЕ_АРХИВЫ),
        null_kind="negative",
        tolerance=0.0,
        inputs=[str(путь) for путь in АРХИВЫ],
        skip_reasons=ПРОПУСКИ,
        claim_family="zeta/GUE: общий ансамбль и эффективное число попыток",
        observable=(
            "число записей С20, разброс M_eff и наличие общего "
            "идентификатора ансамбля"
        ),
        measurement_source="самостоятельное чтение JSON-архивов корпуса",
        uncertainty_type="none",
        novelty_key="trinity:zeta:meff-ensemble-identifiability:20260909",
        information_class="идентифицируемость поправки множественности",
        purpose="audit",
        models=["отдельные M_eff", "единый общий M_eff"],
        independent_of=[
            "рецепт развёртки zeta",
            "предпосылка независимости",
            "аналитический источник BBLM",
        ],
        out_of_sample=False,
        tests_independent="unknown",
        reason_code_hint="meff_unstable",
        notes=(
            "Во всех найденных записях M одинаково, но M_eff различается, "
            "а общий M_eff и идентификатор ансамбля отсутствуют. Это "
            "оставляет научный статус not-evaluated и не даёт складывать "
            "записи как независимые испытания."
        ),
    )
]
