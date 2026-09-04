#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож парности записей живого журнала запусков.

Хеш-цепочка отвечает за порядок байтов, но не за смысл записи. Этот сторож
отдельно проверяет, что каждая запись ``running`` имеет ровно одну
терминальную запись, что у терминальной записи есть итог, артефакты и
согласованный код возврата, а неполная строка JSON не превращается в
молчаливый пропуск.
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
    terminal_result_mismatch: list[str] = []
    identity_mismatch: list[str] = []
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
            start = starts[0] if len(starts) == 1 else None
            # Один run_id и парная запись ещё не доказывают, что итог
            # относится к тому же вызову: повреждённый или вручную
            # склеенный журнал мог оставить команду/тик/процесс от другого
            # запуска. Сверяем только поля, которые предъявлены обеими
            # сторонами; отсутствие необязательного tick в старых записях
            # не превращаем в ложный провал.
            if start is not None:
                mismatched = []
                if (start.get("command") is not None
                        and final.get("command") != start.get("command")):
                    mismatched.append("command")
                for key in ("tick", "pid"):
                    if (start.get(key) is not None
                            and final.get(key) is not None
                            and final.get(key) != start.get(key)):
                        mismatched.append(key)
                if mismatched:
                    identity_mismatch.append(
                        "%s (%s)" % (run_id, ",".join(mismatched)))
                    errors.append(
                        "run_id %s: итог не относится к началу по полям %s"
                        % (run_id, ",".join(mismatched))
                    )
            if not final.get("finished"):
                errors.append("run_id %s: у итоговой записи нет finished"
                              % run_id)
            if not isinstance(final.get("artifacts"), list):
                errors.append("run_id %s: artifacts итоговой записи не список"
                              % run_id)
            exit_code = final.get("exit_code")
            status = final.get("status")
            result_ok = (
                isinstance(exit_code, int)
                and not isinstance(exit_code, bool)
                and ((status == "passed" and exit_code == 0)
                     or (status in {"failed", "aborted", "blocked"}
                         and exit_code != 0))
            )
            if not result_ok:
                terminal_result_mismatch.append(run_id)
                errors.append(
                    "run_id %s: status=%s не согласован с exit_code=%s"
                    % (run_id, status, exit_code)
                )
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
        "terminal_result_mismatch": terminal_result_mismatch,
        "identity_mismatch": identity_mismatch,
        "terminal_statuses": sorted(TERMINAL),
    }


def selftest() -> int:
    good = (
        '{"run_id":"r1","command":"tick","status":"running",'
        '"started":"2026-01-01T00:00:00"}\n'
        '{"run_id":"r1","command":"tick","status":"passed",'
        '"finished":"2026-01-01T00:00:01","exit_code":0,"artifacts":[]}\n'
    )
    cases = [
        ("парная запись проходит", audit_text(good)["verdict"] == "verified-in-scope"),
        ("оборванная запись ловится",
         audit_text(good.splitlines()[0])["verdict"] == "unsupported"),
        ("двойной итог ловится",
         audit_text(good + good.splitlines()[1] + "\n")["verdict"] == "unsupported"),
        ("повреждённая строка ловится",
         audit_text(good + "{\n")["verdict"] == "unsupported"),
        ("несогласованный код возврата ловится",
         audit_text(good.replace('"status":"passed"',
                                 '"status":"failed"'))["verdict"]
         == "unsupported"),
        ("итог чужой команды ловится",
         audit_text(good.replace('"command":"tick","status":"passed"',
                                 '"command":"другая-команда","status":"passed"'))[
             "verdict"] == "unsupported"),
    ]
    failed = 0
    for name, ok in cases:
        print("  %-34s %s" % (name, "ok" if ok else "ПРОВАЛ"))
        failed += 0 if ok else 1
    print("самопроверка: %d пройдено, %d провалено" % (len(cases) - failed, failed))
    return failed


def identity_selftest() -> int:
    """Отдельно измерить чувствительность связи начала и итога запуска."""
    good = (
        '{"run_id":"r1","command":"tick","status":"running",'
        '"tick":336,"pid":17,"started":"2026-01-01T00:00:00"}\n'
        '{"run_id":"r1","command":"tick","status":"passed",'
        '"tick":336,"pid":17,"finished":"2026-01-01T00:00:01",'
        '"exit_code":0,"artifacts":[]}\n'
    )
    cases = [
        ("команда начала и итога совпадает",
         audit_text(good)["verdict"] == "verified-in-scope"),
        ("чужая команда ловится",
         audit_text(good.replace('"command":"tick","status":"passed"',
                                 '"command":"other","status":"passed"'))[
             "identity_mismatch"] == ["r1 (command)"]),
        ("чужой тик ловится",
         audit_text(good.replace('"tick":336,"pid":17,"finished"',
                                 '"tick":337,"pid":17,"finished"'))[
             "identity_mismatch"] == ["r1 (tick)"]),
        ("чужой PID ловится",
         audit_text(good.replace('"tick":336,"pid":17,"finished"',
                                 '"tick":336,"pid":18,"finished"'))[
             "identity_mismatch"] == ["r1 (pid)"]),
    ]
    failed = sum(not ok for _, ok in cases)
    for name, ok in cases:
        print("  %-34s %s" % (name, "ok" if ok else "ПРОВАЛ"))
    print("самопроверка связи начала и итога: %d пройдено, %d провалено"
          % (len(cases) - failed, failed))
    return failed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--identity-selftest", action="store_true")
    parser.add_argument("--journal", default=str(JOURNAL))
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if args.identity_selftest:
        return identity_selftest()
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
