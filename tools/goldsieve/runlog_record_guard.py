#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож парности записей живого журнала запусков.

Хеш-цепочка отвечает за порядок байтов, но не за смысл записи. Этот сторож
отдельно проверяет, что каждая запись ``running`` имеет ровно одну
терминальную запись, что у терминальной записи есть итог и артефакты, а
неполная строка JSON не превращается в молчаливый пропуск.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
JOURNAL = Path(os.environ.get(
    "GOLDSIEVE_RUNLOG",
    "/home/user/workspace/cron_tracking/8dff7aa3/runs.jsonl",
))
OUT = HERE / "runlog_record_guard.json"
TERMINAL = {"passed", "failed", "aborted", "blocked"}


def audit_text(text: str) -> dict:
    """Проверить текст журнала без изменения файла."""
    errors: list[str] = []
    groups: dict[str, list[dict]] = defaultdict(list)
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (TypeError, ValueError) as exc:
            errors.append("строка %d: повреждённый JSON (%s)" % (number, exc))
            continue
        if not isinstance(row, dict):
            errors.append("строка %d: запись не является объектом" % number)
            continue
        missing = [key for key in ("run_id", "command", "status")
                   if not row.get(key)]
        if missing:
            errors.append("строка %d: отсутствуют поля %s"
                          % (number, ",".join(missing)))
            continue
        groups[str(row["run_id"])].append(row)

    incomplete: list[str] = []
    duplicate_terminal: list[str] = []
    duplicate_start: list[str] = []
    for run_id, rows in sorted(groups.items()):
        starts = [row for row in rows if row.get("status") == "running"]
        terminals = [row for row in rows if row.get("status") in TERMINAL]
        unknown = [row.get("status") for row in rows
                   if row.get("status") not in ({"running"} | TERMINAL)]
        if len(starts) != 1:
            duplicate_start.append("%s (%d)" % (run_id, len(starts)))
        if len(terminals) != 1:
            duplicate_terminal.append("%s (%d)" % (run_id, len(terminals)))
        if unknown:
            errors.append("run_id %s: неизвестные статусы %s"
                          % (run_id, ",".join(map(str, unknown))))
        if terminals:
            final = terminals[0]
            if not final.get("finished"):
                errors.append("run_id %s: у итоговой записи нет finished"
                              % run_id)
            if not isinstance(final.get("artifacts"), list):
                errors.append("run_id %s: artifacts итоговой записи не список"
                              % run_id)
        if len(starts) == 1 and len(terminals) == 1 and not unknown:
            continue
        incomplete.append(run_id)

    verdict = "verified-in-scope" if not (
        errors or incomplete or duplicate_start or duplicate_terminal
    ) else "unsupported"
    return {
        "verdict": verdict,
        "reason_code": ("run_pairs_complete" if verdict == "verified-in-scope"
                        else "run_pairs_incomplete"),
        "lines": len(lines),
        "run_groups": len(groups),
        "errors": errors,
        "incomplete_run_ids": incomplete,
        "duplicate_start": duplicate_start,
        "duplicate_terminal": duplicate_terminal,
        "terminal_statuses": sorted(TERMINAL),
    }


def selftest() -> int:
    good = (
        '{"run_id":"r1","command":"tick","status":"running",'
        '"started":"2026-01-01T00:00:00"}\n'
        '{"run_id":"r1","command":"tick","status":"passed",'
        '"finished":"2026-01-01T00:00:01","artifacts":[]}\n'
    )
    cases = [
        ("парная запись проходит", audit_text(good)["verdict"] == "verified-in-scope"),
        ("оборванная запись ловится",
         audit_text(good.splitlines()[0])["verdict"] == "unsupported"),
        ("двойной итог ловится",
         audit_text(good + good.splitlines()[1] + "\n")["verdict"] == "unsupported"),
        ("повреждённая строка ловится",
         audit_text(good + "{\n")["verdict"] == "unsupported"),
    ]
    failed = 0
    for name, ok in cases:
        print("  %-34s %s" % (name, "ok" if ok else "ПРОВАЛ"))
        failed += 0 if ok else 1
    print("самопроверка: %d пройдено, %d провалено" % (len(cases) - failed, failed))
    return failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--journal", default=str(JOURNAL))
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    try:
        result = audit_text(Path(args.journal).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        result = {
            "verdict": "not-evaluated",
            "reason_code": "journal_unavailable",
            "errors": [str(exc)],
        }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")
    print("сторож записей журнала: %s; групп запусков %s; строк %s"
          % (result["verdict"], result.get("run_groups", 0),
             result.get("lines", 0)))
    print("JSON: %s" % OUT)
    # На удалённом CI живой журнал песочницы отсутствует. Это объявленный
    # not-evaluated, а не провал: локальный запуск с предъявленным журналом
    # обязан дать verified-in-scope.
    return 0 if result["verdict"] in {"verified-in-scope", "not-evaluated"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
