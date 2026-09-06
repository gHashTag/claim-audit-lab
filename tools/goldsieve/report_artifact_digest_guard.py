#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож привязки содержимого артефакта к докладу.

Существующий путь и его граница не доказывают, что доклад ссылается на ту же
версию содержимого. Этот сторож принимает только явно предъявленный SHA-256
рядом с каждым путём. Отсутствующий дайджест оставляет запись
``not-evaluated``; несовпадающий дайджест получает ``unsupported``. Сторож
не делает научного вывода и не восстанавливает дайджест из соседних тиков.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path


TRACKING = Path("/home/user/workspace/cron_tracking/8dff7aa3")
OUT = Path(__file__).resolve().parent / "report_artifact_digest_guard.json"
PATH_RE = re.compile(r"/home/user/workspace/[A-Za-z0-9_./-]+")
HEX_RE = re.compile(r"(?i)\bsha256\s*[:=]?\s*([0-9a-f]{64})\b")
TRAILING = ".,;:)]}`\""


def latest_report(root: Path = TRACKING) -> Path:
    reports = sorted(root.glob("tick*-report.md"))
    if not reports:
        raise FileNotFoundError("доклад tickNNN-report.md не предъявлен")
    return reports[-1]


def extracted_paths(text: str) -> list[str]:
    values = {m.group(0).rstrip(TRAILING) for m in PATH_RE.finditer(text)}
    return sorted(values)


def _digest_for_path(lines: list[str], path: str) -> str | None:
    for number, line in enumerate(lines):
        if path not in line:
            continue
        for candidate in (line, *lines[number + 1:number + 3]):
            match = HEX_RE.search(candidate)
            if match:
                return match.group(1).lower()
    return None


def inspect_text(text: str, report: str) -> dict:
    lines = text.splitlines()
    paths = extracted_paths(text)
    observations = []
    missing = []
    mismatched = []
    for path in paths:
        declared = _digest_for_path(lines, path)
        actual = None
        if Path(path).is_file():
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        row = {
            "путь": path,
            "предъявленный_sha256": declared,
            "фактический_sha256": actual,
        }
        if declared is None:
            missing.append(path)
        elif actual is None or declared != actual:
            mismatched.append(path)
        observations.append(row)
    if mismatched:
        status = "unsupported"
        reason = "предъявленный SHA-256 не совпадает с прочитанным содержимым"
    elif not paths:
        status = "not-evaluated"
        reason = "в докладе не предъявлены пути артефактов"
    elif missing:
        status = "not-evaluated"
        reason = "для части путей не предъявлен SHA-256 содержимого"
    else:
        status = "verified-in-scope"
        reason = "каждый предъявленный путь связан с прочитанным SHA-256"
    return {
        "статус": status,
        "доклад": report,
        "путей": len(paths),
        "без_sha256": missing,
        "несовпадающих_sha256": mismatched,
        "наблюдения": observations,
        "причина": reason,
        "ограничение": (
            "дайджест связывает прочитанную копию с докладом, но не доказывает "
            "авторство файла или научную истинность утверждения"
        ),
    }


def inspect(report: Path) -> dict:
    result = inspect_text(report.read_text(encoding="utf-8"), str(report))
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return result


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            print("  ок  " + name)
            good += 1
        else:
            print("  ПРОВАЛ  " + name)
            bad += 1

    with tempfile.TemporaryDirectory(prefix="report-artifact-digest-"):
        # Фикстура использует настоящий путь разрешённого рабочего
        # пространства: извлечение путей из доклада намеренно ограничено
        # наблюдаемыми путями workspace.
        artifact = Path("/home/user/workspace/goldsieve/README.md")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        valid = f"артефакт {artifact} sha256: {digest}\n"
        result = inspect_text(valid, "фикстура-valid.md")
        check("совпадающий дайджест получает verified-in-scope",
              result["статус"] == "verified-in-scope")
        result = inspect_text(f"артефакт {artifact}\n", "фикстура-missing.md")
        check("отсутствующий дайджест получает not-evaluated",
              result["статус"] == "not-evaluated"
              and result["без_sha256"] == [str(artifact)])
        result = inspect_text(
            f"артефакт {artifact} sha256: {'0' * 64}\n",
            "фикстура-mismatch.md",
        )
        check("несовпадающий дайджест получает unsupported",
              result["статус"] == "unsupported"
              and result["несовпадающих_sha256"] == [str(artifact)])
        result = inspect_text("доклад без пути\n", "фикстура-empty.md")
        check("отсутствие пути не становится покрытием",
              result["статус"] == "not-evaluated")

    print("самопроверка дайджеста артефактов доклада: пройдено %d, провалено %d"
          % (good, bad))
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--selftest"]:
        return selftest()
    if args:
        print("использование: report_artifact_digest_guard.py [--selftest]")
        return 2
    try:
        result = inspect(latest_report())
    except (OSError, UnicodeError, ValueError) as exc:
        print("сторож дайджеста артефактов: not-evaluated; %s" % exc)
        return 0
    print("сторож дайджеста артефактов: %s; путей: %d; без SHA-256: %d; "
          "несовпадений: %d" % (
              result["статус"], result["путей"], len(result["без_sha256"]),
              len(result["несовпадающих_sha256"])))
    # Отсутствие доказательства наблюдаемо, но не является провалом гейта:
    # корпус не обязан ретроспективно содержать подписи старых докладов.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
