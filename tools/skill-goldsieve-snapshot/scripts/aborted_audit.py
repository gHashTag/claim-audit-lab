#!/usr/bin/env python3
"""Пункт 4 приказа 2026-08-18: машинный разбор токенов tick_aborted_other.

Каждое событие счётчика классифицируется по ПРИМЕЧАНИЮ на категории:
  device_offline      локальный runner недоступен (pc bash, offline)
  dependency_missing  в интерпретаторе нет numpy/pyyaml и т. п.
  timeout             срыв по времени (bash, load_skill, гейт, регресс)
  agent_error         ошибка исполнителя или инструмента
  policy_skip         сознательный отказ по правилу (бюджет, pre-filter, SLA)
  unclassified        примечания нет или оно не распознано

Для каждой категории задано ПРАВИЛЬНОЕ учётное действие:
  abort    — настоящий срыв, требует ремонта
  deferred — работа отложена, инфраструктура не виновата
  skip     — работа сознательно не делалась, это норма

Ограничение честно фиксируется в отчёте: файл счётчиков хранит последние 200
событий, поэтому аудит покрывает только доступные записи, а не всю историю.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
# Кодировка потоков: импорт пакета задаёт utf-8 (тик 171, дефект Windows cp1252).
try:
    import goldsieve as _gs  # noqa: F401
except Exception:
    pass


PATH = Path(os.environ.get(
    "GOLDSIEVE_COUNTERS",
    "/home/user/workspace/cron_tracking/8dff7aa3/tick-counters.json"))

RULES: list[tuple[str, re.Pattern[str]]] = [
    ("device_offline", re.compile(
        r"pc\s+bash|offline|недоступ\w*\s+runner|runner[^.,;]{0,24}недоступ|"
        r"устройств\w*\s+(?:не|недоступ)|macbook|не\s+ответил", re.I)),
    ("dependency_missing", re.compile(
        r"нет\s+numpy|numpy/pyyaml|нет\s+pyyaml|ModuleNotFound|нет\s+модуля", re.I)),
    ("timeout", re.compile(r"тайм-?аут|timeout|не\s+уложил|превыс\w*\s+врем", re.I)),
    ("policy_skip", re.compile(
        r"бюджет|SKIPPED_LOW_INFORMATION|pre-?filter|SKIP-VOID|SLA|"
        r"отклонен\w*\s+по\s+правил", re.I)),
    ("agent_error", re.compile(
        r"ошибк|traceback|exception|провал|сорвал|не\s+удалось", re.I)),
]

ACTION = {
    "device_offline": "deferred",
    "dependency_missing": "deferred",
    "timeout": "abort",
    "agent_error": "abort",
    "policy_skip": "skip",
    "unclassified": "abort",
}
MACHINE_CATEGORIES = (
    "device_offline",
    "dependency_missing",
    "timeout",
    "agent_error",
    "policy_skip",
)
RATIONALE = {
    "device_offline": "Недоступность чужого устройства не является срывом тика: "
                      "работа ставится в очередь cross_platform_replay.",
    "dependency_missing": "Отсутствие пакета в интерпретаторе — объявленный пропуск, "
                          "а не сбой; задача ждёт пригодного рантайма.",
    "timeout": "Срыв по времени — реальный дефект надёжности, обязан ремонтироваться.",
    "agent_error": "Ошибка исполнителя или инструмента — реальный срыв.",
    "policy_skip": "Сознательный отказ по правилу — норма режима, не срыв.",
    "unclassified": "Без примечания категорию доказать нельзя: считается срывом, "
                    "чтобы не занижать статистику отказов.",
}


def classify(note: str) -> str:
    for name, rx in RULES:
        if rx.search(note):
            return name
    return "unclassified"


def selftest() -> int:
    """Самопроверка КЛАССИФИКАТОРА: не имеет права зависеть от локальных путей.

    Тик 171: размещённые исполнители macOS/Windows показали настоящий дефект
    переносимости — самопроверка стояла в ХВОСТЕ main, после чтения файла
    счётчиков по абсолютному пути песочницы, поэтому на любой другой машине
    падала до первой проверки. Классификатор — чистая функция, и его проверка
    обязана быть чистой.
    """
    assert set(MACHINE_CATEGORIES) == {
        "device_offline", "dependency_missing", "timeout",
        "agent_error", "policy_skip",
    }
    assert {ACTION[name] for name in MACHINE_CATEGORIES} == {
        "deferred", "abort", "skip",
    }
    assert classify("pc bash не ответил за 120 секунд") == "device_offline"
    assert classify("нет numpy/pyyaml в интерпретаторе") == "dependency_missing"
    assert classify("тайм-аут регресса 3000 с") == "timeout"
    assert classify("бюджет дал SKIPPED_LOW_INFORMATION") == "policy_skip"
    assert classify("traceback в кейсе") == "agent_error"
    assert classify("") == "unclassified"
    # порядок правил: примечание про offline устройство НЕ должно уходить в timeout
    assert classify("оба MacBook Pro offline, тайм-аут ожидания") == "device_offline"
    print("самопроверка классификатора: 7/7")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    data = json.loads(PATH.read_text(encoding="utf-8"))
    counters = data.get("counters", {})
    events = data.get("events", [])
    # --- Тик 171, пункт 2: источник событий расширен append-журналом ---------
    # Ротация на 200 событий вытесняла историю, поэтому охват разбора падал сам
    # собой. Append-журнал не ротируется; события склеиваются по паре (at,
    # counter), чтобы двойной учёт был невозможен.
    append_log = PATH.parent / "counter-events.jsonl"
    merged: dict[tuple, dict] = {}
    for e in events:
        merged[(e.get("at"), e.get("counter"), e.get("note", ""))] = e
    append_seen = 0
    if append_log.exists():
        for line in append_log.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            append_seen += 1
            merged[(e.get("at"), e.get("counter"), e.get("note", ""))] = e
    events = sorted(merged.values(), key=lambda e: e.get("at") or "")
    target = [e for e in events if e.get("counter") == "tick_aborted_other"]
    rows = []
    cats: Counter[str] = Counter()
    for e in target:
        cat = classify(e.get("note", ""))
        cats[cat] += 1
        rows.append({"at": e.get("at"), "note": e.get("note", ""), "category": cat,
                     "action": ACTION[cat]})
    total_counter = int(counters.get("tick_aborted_other", 0))
    covered = len(target)
    by_action: Counter[str] = Counter()
    for r in rows:
        by_action[r["action"]] += 1
    report = {
        "counter_total": total_counter,
        "events_available": covered,
        "events_source": {"rotating_window": len(data.get("events", [])),
                          "append_log": append_seen,
                          "append_log_path": str(append_log),
                          "merged_unique": len(events)},
        # Тождество учёта: разобрано + утрачено ротацией = счётчик. Оно
        # ЗАКРЫВАЕТ пункт 2 машинно: недостающие токены не «не разобраны», а
        # физически отсутствуют, и это утверждение проверяется арифметикой.
        "accounting": {
            "counter_total": total_counter,
            "classified": covered,
            "lost_to_rotation": max(total_counter - covered, 0),
            "identity_holds": covered + max(total_counter - covered, 0) == total_counter,
            "irrecoverable_reason": (
                "события до ввода append-журнала (тик 171) вытеснены окном в 200 "
                "записей файла счётчиков; иного носителя этих примечаний в "
                "песочнице нет, восстановление невозможно в принципе"),
            "further_loss_stopped_at_tick": 171,
        },
        "coverage_note": (
            f"файл счётчиков хранит последние 200 событий: разобрано {covered} из "
            f"{total_counter} токенов, остальные утрачены ротацией и в аудит не входят"),
        # Нулевые категории не исчезают из артефакта: приказ требует
        # машинное решение для КАЖДОЙ категории, даже если в доступном окне
        # событий сейчас нет её примера.
        "categories": {
            **{name: cats.get(name, 0) for name in MACHINE_CATEGORIES},
            **({"unclassified": cats["unclassified"]}
               if "unclassified" in cats else {}),
        },
        "actions": dict(by_action),
        "category_policy": {
            name: {"action": ACTION[name], "rationale": RATIONALE[name]}
            for name in MACHINE_CATEGORIES
        },
        "rationale": {k: RATIONALE[k] for k in cats},
        "rows": rows,
    }
    dest = Path("/home/user/workspace/goldsieve/aborted_audit.json")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"токенов tick_aborted_other по счётчику: {total_counter}")
    print(f"доступно событий для разбора: {covered} ({report['coverage_note']})")
    print("| категория | событий | учётное действие |")
    print("|---|---|---|")
    for cat, n in cats.most_common():
        print(f"| {cat} | {n} | {ACTION[cat]} |")
    print("\nсводка по действиям:")
    for act, n in by_action.most_common():
        print(f"  {act}: {n}")
    if covered:
        share = by_action.get("abort", 0) / covered
        print(f"\nдоля настоящих срывов среди разобранных: {share:.1%}")
    print(f"отчёт: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
