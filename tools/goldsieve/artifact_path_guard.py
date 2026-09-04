#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож границы путей артефактов в журнале запусков.

Журнал обязан связывать итог запуска с артефактами, но строка ``artifacts``
сама по себе не ограничивает, куда может указывать путь. Относительный путь,
переход ``..`` или символическая ссылка наружу делает происхождение
артефакта неоднозначным. Этот сторож не утверждает содержимое файла: он
проверяет только наблюдаемую границу пути и явно оставляет старые непутевые
значения ``not-evaluated``.

Команды:
    python3 artifact_path_guard.py
    python3 artifact_path_guard.py --selftest
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LOG = Path("/home/user/workspace/cron_tracking/8dff7aa3/runs.jsonl")
OUT = HERE / "artifact_path_guard.json"
ALLOWED_ROOTS = (
    HERE,
    Path("/home/user/workspace/cron_tracking"),
    Path("/tmp"),
)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def inspect_artifact(raw: object) -> dict:
    if not isinstance(raw, str) or not raw:
        return {"status": "not-evaluated", "reason": "артефакт не является непустой строкой"}
    if "\x00" in raw:
        return {"status": "unsupported", "reason": "путь содержит нулевой байт", "raw": raw}
    # Старые записи об исключениях лежат в artifacts, но не являются путями.
    # Не угадываем их происхождение и не превращаем молчание в покрытие.
    if not (raw.startswith(("/", "./", "../")) or "/" in raw or "\\" in raw):
        return {"status": "not-evaluated", "reason": "значение не распознано как путь", "raw": raw}
    if "\\" in raw:
        return {"status": "unsupported", "reason": "обратная косая черта не допускается", "raw": raw}
    candidate = Path(raw)
    if not candidate.is_absolute():
        return {"status": "not-evaluated", "reason": "относительный путь не имеет однозначного происхождения", "raw": raw}
    resolved = candidate.resolve(strict=False)
    if not any(_inside(resolved, root.resolve()) for root in ALLOWED_ROOTS):
        return {
            "status": "unsupported",
            "reason": "разрешённый корень не предъявлен",
            "raw": raw,
            "resolved": str(resolved),
        }
    return {"status": "verified-in-scope", "raw": raw, "resolved": str(resolved)}


def scan(path: Path = DEFAULT_LOG) -> dict:
    if not path.exists():
        return {
            "status": "not-evaluated",
            "reason": "журнал запусков отсутствует",
            "journal": str(path),
            "read": 0,
            "paths": 0,
            "issues": [],
        }
    rows = []
    malformed = 0
    container_issues = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(record, dict):
            malformed += 1
            continue
        artifacts = record.get("artifacts", [])
        if artifacts is not None and not isinstance(artifacts, list):
            # Строка раньше молча перебиралась посимвольно. Это не проверка
            # границы путей: форма контейнера должна быть предъявлена явно.
            container_issues.append({
                "line": number,
                "status": "unsupported",
                "reason": "поле artifacts не является списком",
            })
            continue
        for raw in artifacts or []:
            rows.append((number, inspect_artifact(raw)))
    issues = [
        {"line": line, **result}
        for line, result in rows
        if result["status"] == "unsupported"
    ]
    nonpaths = sum(result["status"] == "not-evaluated" for _, result in rows)
    verified = sum(result["status"] == "verified-in-scope" for _, result in rows)
    status = (
        "unsupported"
        if issues or container_issues
        else ("not-evaluated" if malformed or nonpaths else "verified-in-scope")
    )
    return {
        "status": status,
        "journal": str(path),
        "read": len(path.read_text(encoding="utf-8").splitlines()),
        "artifacts": len(rows),
        "verified_paths": verified,
        "not_evaluated": nonpaths + malformed,
        "issues": issues + container_issues,
        "container_issues": container_issues,
    }


def selftest() -> int:
    fixtures = [
        (str(HERE / "ci_gate.sh"), "verified-in-scope"),
        ("/etc/passwd", "unsupported"),
        ("/tmp/../etc/passwd", "unsupported"),
        ("../../secret.txt", "not-evaluated"),
        ("FileNotFoundError", "not-evaluated"),
        ("/tmp/путь.txt", "verified-in-scope"),
    ]
    ok = fail = 0
    for raw, expected in fixtures:
        actual = inspect_artifact(raw)["status"]
        if actual == expected:
            ok += 1
            print("  ok   %s" % raw)
        else:
            fail += 1
            print("  ПРОВАЛ %s: ожидалось %s, получено %s" % (raw, expected, actual))
    # Отдельно проверяем симлинк, если файловая система его поддерживает.
    link = HERE / ".artifact-path-guard-link"
    try:
        link.unlink(missing_ok=True)
        link.symlink_to("/etc/passwd")
        actual = inspect_artifact(str(link))["status"]
        if actual == "unsupported":
            ok += 1
            print("  ok   символическая ссылка наружу")
        else:
            fail += 1
            print("  ПРОВАЛ символическая ссылка наружу: %s" % actual)
    finally:
        link.unlink(missing_ok=True)
    # Неверный контейнер не должен превращаться в перебор символов и
    # ошибочно получать not-evaluated вместо явного unsupported.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="goldsieve-artifact-log-") as td:
        log = Path(td) / "runs.jsonl"
        log.write_text('{"artifacts": "tick341-gate.log"}\n', encoding="utf-8")
        result = scan(log)
        if result["status"] == "unsupported" and result["container_issues"]:
            ok += 1
            print("  ok   неверная форма контейнера artifacts")
        else:
            fail += 1
            print("  ПРОВАЛ неверная форма контейнера artifacts")
    print("самопроверка границы путей артефактов: пройдено %d, провалено %d" % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("сторож путей артефактов: %s; прочитано артефактов %d; "
          "путей в области %d; not-evaluated %d; нарушений %d"
          % (report["status"], report["artifacts"], report["verified_paths"],
             report["not_evaluated"], len(report["issues"])))
    print("журнал: %s" % report["journal"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
