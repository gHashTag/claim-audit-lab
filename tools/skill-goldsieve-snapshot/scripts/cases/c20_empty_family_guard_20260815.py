# -*- coding: utf-8 -*-
"""Инженерная проверка: пустое семейство С20 не является подтверждением.

Это не утверждение корпуса и не дешёвая арифметика. Кейс проверяет состояние
конвейера: когда эффективную кратность нельзя оценить, С20 обязан вернуть OPEN,
а свод обязан сохранить ВОПРОС. Загрузка сделана тем же module_from_spec без
регистрации, что и CLI: guard ниже не позволяет случайно тестировать другой
режим исполнения.
"""
import json
import sys

from goldsieve.sieve import (Claim, OPEN, PASS, sieve_effective_multiplicity,
                             sieve_numbers)

# Тихий отказ: реальный CLI не помещает модуль кейса в sys.modules.
if __name__ in sys.modules:
    raise RuntimeError("guard: кейс зарегистрирован в sys.modules")


def _empty_family():
    return {"values": [], "eps": 0.01, "sigma": 0.0, "search_size": 0}


def _reference():
    # Независимое определение ожидаемого состояния: пустое семейство не имеет
    # ни одного различимого члена, поэтому M_eff не оценивается.
    spec = _empty_family()
    empty = len(tuple(spec["values"])) == 0
    return {"status": "OPEN" if empty else "NOT-OPEN",
            "reason": "пустое семейство" if empty else "есть члены"}


def _observed():
    # Другой маршрут к тому же числу: суммирование пустой последовательности,
    # без вызова _reference и без чтения результата С20.
    return float(sum(tuple(_empty_family()["values"])))


def _reference_alt():
    # Принципиально иной маршрут: JSON-представление входа и проверка длины,
    # без вызова _reference и без вызова сита.
    payload = json.loads('{"values": []}')
    return float(len(payload["values"]))


def _wrong():
    return 1.0


# С1–С5, С12 и С20 исполняются; остальные пропуски названы точными номерами.
_SKIP = {"С%d" % n: "инженерный кейс проверяет только guard С20"
         for n in sieve_numbers() if n not in {1, 2, 3, 4, 5, 12, 20}}

CLAIMS = [Claim(
    name="Пустое семейство С20 сохраняет вопрос вместо подтверждения",
    source="goldsieve/cases/c20_empty_family_guard_20260815.py",
    stated=lambda: 0.0,
    reference=lambda: float(len(tuple(_empty_family()["values"]))),
    observed=_observed,
    meff=_empty_family,
    wrong=_wrong,
    null_model=_wrong,
    null_expect=1.0,
    null_kind="negative",
    reference_alt=lambda: float(sum([])),
    alt_tolerance=lambda: 1e-12,
    skip_reasons=_SKIP,
    claim_family="tooling_safety",
    observable="empty_family_guard",
    measurement_source="самопроверка goldsieve",
    uncertainty_type="none",
    novelty_key="tool:c20:empty-family-guard:v1",
    information_class="novelty",
    purpose="tool_selftest",
    models=["valid-family", "empty-family"],
    independent_of=["С20: пустое семейство"],
    notes="Ожидается OPEN внутри С20 и итоговый ВОПРОС с причиной meff_unstable.",
)]
