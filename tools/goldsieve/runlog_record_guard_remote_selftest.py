#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка явного статуса при отсутствии живого журнала в CI."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
GUARD = HERE / "runlog_record_guard.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="runlog-missing-") as tmp:
        env = os.environ.copy()
        env["GOLDSIEVE_RUNLOG"] = str(Path(tmp) / "no-such-journal.jsonl")
        proc = subprocess.run(
            [sys.executable, str(GUARD)],
            cwd=str(HERE),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        result_path = HERE / "runlog_record_guard.json"
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            print("ПРОВАЛ: результат сторожа не прочитан: %s" % exc)
            return 1
    ok = (
        proc.returncode == 0
        and result.get("verdict") == "not-evaluated"
        and result.get("reason_code") == "journal_unavailable"
    )
    print(
        "отсутствующий живой журнал: %s"
        % ("ok, not-evaluated/journal_unavailable" if ok else "ПРОВАЛ")
    )
    if not ok:
        print("код=%s, результат=%s" % (proc.returncode, result))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
