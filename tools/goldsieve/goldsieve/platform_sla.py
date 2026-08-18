"""Машинный SLA матрицы ОС.

Правило приказа: два последовательных результата not-evaluated не могут
оставаться бесконечным обещанием. При доступном runner задача возвращается в
очередь, иначе охват получает platform-unverified. В обоих случаях
verified-in-scope запрещён до успешного прогона.
"""

from __future__ import annotations

import os
import sys
from typing import Iterable

import yaml

from .scope import (NOT_EVALUATED, PLATFORM_UNVERIFIED, VERIFIED)

THRESHOLD = 2
PENDING = "pending"


def decide(history: Iterable[str], *, runner_available: bool = False) -> dict:
    """Вернуть решение SLA по истории статусов одной платформы."""
    rows = list(history)
    consecutive = 0
    for item in reversed(rows):
        if item == NOT_EVALUATED:
            consecutive += 1
        else:
            break
    if consecutive >= THRESHOLD:
        if runner_available:
            return {
                "action": "queue",
                "scope_status": NOT_EVALUATED,
                "consecutive": consecutive,
                "reason": "два последовательных пропуска: задача поставлена "
                          "в очередь на доступный runner",
            }
        return {
            "action": "platform-unverified",
            "scope_status": PLATFORM_UNVERIFIED,
            "consecutive": consecutive,
            "reason": "два последовательных пропуска без доступного runner",
        }
    return {
        "action": "wait",
        "scope_status": NOT_EVALUATED,
        "consecutive": consecutive,
        "reason": "порог двух последовательных пропусков ещё не достигнут",
    }


def validate_task(task: dict) -> tuple[bool, str]:
    """Проверить YAML-задачу очереди и запрет расширенного охвата."""
    sla = task.get("sla") or {}
    history = [row.get("scope_status") for row in sla.get("history") or []]
    if any(item not in (NOT_EVALUATED, VERIFIED, PLATFORM_UNVERIFIED)
           for item in history):
        return False, "история SLA содержит неизвестный статус"
    expected = decide(history,
                      runner_available=bool(sla.get("runner_available")))
    actual = task.get("scope_status")
    if actual != expected["scope_status"]:
        return (False, "scope_status %r не совпадает с решением SLA %r"
                % (actual, expected["scope_status"]))
    if actual == VERIFIED and expected["consecutive"] >= THRESHOLD:
        return False, "verified-in-scope запрещён после двух пропусков"
    if expected["action"] == "platform-unverified" and \
            task.get("status") == "passed":
        return False, "platform-unverified не может быть статусом успешной задачи"
    return True, expected["reason"]


def selftest() -> int:
    ok = fail = 0

    def check(name: str, condition: bool) -> None:
        nonlocal ok, fail
        if condition:
            ok += 1
            print("  ok   " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    one = decide([NOT_EVALUATED])
    check("один пропуск остаётся not-evaluated",
          one["scope_status"] == NOT_EVALUATED and one["action"] == "wait")
    two = decide([NOT_EVALUATED, NOT_EVALUATED])
    check("два пропуска дают platform-unverified без runner",
          two["scope_status"] == PLATFORM_UNVERIFIED and
          two["action"] == "platform-unverified")
    queued = decide([NOT_EVALUATED, NOT_EVALUATED],
                    runner_available=True)
    check("два пропуска ставят задачу в очередь при runner",
          queued["scope_status"] == NOT_EVALUATED and
          queued["action"] == "queue")
    reset = decide([NOT_EVALUATED, NOT_EVALUATED, VERIFIED])
    check("успешный прогон сбрасывает последовательность",
          reset["consecutive"] == 0 and reset["scope_status"] == NOT_EVALUATED)
    task = {
        "status": "pending",
        "scope_status": PLATFORM_UNVERIFIED,
        "sla": {
            "runner_available": False,
            "history": [
                {"tick": 57, "scope_status": NOT_EVALUATED},
                {"tick": 60, "scope_status": NOT_EVALUATED},
            ],
        },
    }
    check("YAML-задача принимает машинное решение SLA",
          validate_task(task)[0])
    task["scope_status"] = VERIFIED
    check("SLA отклоняет расширение до verified-in-scope",
          not validate_task(task)[0])
    print()
    print("  итог: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


def check_file(path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        task = yaml.safe_load(fh) or {}
    good, message = validate_task(task)
    print("SLA ОС: %s" % ("принят" if good else "ПРОВАЛ"))
    print("  задача: %s" % task.get("id", os.path.basename(path)))
    print("  scope_status: %s" % task.get("scope_status"))
    print("  %s" % message)
    return 0 if good else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--selftest":
        sys.exit(check_file(sys.argv[1]))
    sys.exit(selftest())
