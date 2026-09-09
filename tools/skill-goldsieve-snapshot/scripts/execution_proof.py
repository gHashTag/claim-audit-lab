#!/usr/bin/env python3
"""Execution-proof: анализатор обязан оставить машинный след на РЕАЛЬНОМ маршруте.

Проверка отвечает на вопрос, который молчание проверки не закрывает: работал ли
анализатор происхождения вообще, когда сито выносило вердикт. Прежде «нет
тождественности» и «анализатор не запускался» выглядели одинаково — оба давали
False. Теперь маршрут CLI выгружает след (`GOLDSIEVE_PROOF`), и пустой граф при
НЕПУСТОМ кейсе объявляется аварией CI, а не тихим отрицательным ответом.

Запуск идёт ОТДЕЛЬНЫМ процессом через `python3 -m goldsieve run …` — то есть тем
же путём, которым инструмент реально применяется, а не искусственным вызовом
функции из теста.

Код возврата: 0 — след есть и он непустой; 1 — авария.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
# Кейс выбран потому, что его наблюдения ПО ПОСТРОЕНИЮ требуют разбора
# происхождения (глобальное состояние, межмодульная цепочка): если след на нём
# пуст, значит анализатор не вызывался.
CASE = os.path.join("cases", "identity_honest_controls_20260814.py")

# Закрытый список причин отказа. Импортируется из модуля, а не дублируется:
# расхождение двух списков само было бы источником тихого расхождения.
sys.path.insert(0, ROOT)
from goldsieve.proof import REASONS  # noqa: E402


def _load(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _nontrivial(rec: dict) -> bool:
    c = rec.get("counters", {})
    return bool(c.get("files_parsed", 0)) or bool(c.get("functions_seen", 0))


def check_trace(records: list[dict]) -> list[str]:
    """Претензии к следу. Пустой список — след годен."""
    bad: list[str] = []
    if not records:
        bad.append("след пуст: анализатор не оставил ни одной записи")
        return bad
    if not any(_nontrivial(r) for r in records):
        bad.append("все следы тривиальны: пустой граф при непустом кейсе")
    for r in records:
        for u in r.get("unsupported", []):
            reason = u.get("reason") if isinstance(u, dict) else u
            if reason not in REASONS:
                bad.append("причина вне закрытого списка: %r" % (reason,))
    return bad


def main() -> int:
    ok = fail = 0

    def check(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ок      %s" % name)
        else:
            fail += 1
            print("  ПРОВАЛ  %s %s" % (name, note))

    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "proof.jsonl")
        env = dict(os.environ, GOLDSIEVE_PROOF=dst)
        proc = subprocess.run(
            [sys.executable, "-m", "goldsieve", "run", CASE],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", timeout=900)
        records = _load(dst)
        check("маршрут CLI завершился", proc.returncode in (0, 1, 2),
              "код %s" % proc.returncode)
        check("след выгружен реальным маршрутом", bool(records),
              "записей 0")
        claims = check_trace(records)
        check("след годен", not claims, "; ".join(claims))
        total = {}
        for r in records:
            for k, v in r.get("counters", {}).items():
                total[k] = total.get(k, 0) + v
        print("  записей следа: %d; сумма счётчиков: %s"
              % (len(records), json.dumps(total, ensure_ascii=False,
                                          sort_keys=True)))

    # ПОДСТАВКА: сама проверка обязана падать на тривиальном следе и на
    # причине вне закрытого списка. Без этого «ок» ничего не значит.
    check("подставка: пустой след — авария",
          check_trace([]) != [])
    check("подставка: тривиальный след — авария",
          check_trace([{"counters": {"files_parsed": 0, "functions_seen": 0},
                        "unsupported": []}]) != [])
    check("подставка: чужая причина — авария",
          check_trace([{"counters": {"files_parsed": 1},
                        "unsupported": [{"reason": "выдуманная"}]}]) != [])

    print("execution-proof: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
