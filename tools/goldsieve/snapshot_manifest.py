#!/usr/bin/env python3
"""Проверяемый снимок: SHA-256 входов, отчётов и журналов + перепроверка БЕЗ СЕТИ.

Зачем. `baseline/manifest.json` фиксировал только файлы инструмента. Отчёт,
ведомость и журналы прогонов в него не входили, поэтому фраза «отчёт
соответствует прогону» держалась на доверии. Здесь снимок покрывает три
класса входов: инструмент, документы (отчёты, ведомость, реестр, манифест
охвата, ожидающие задачи) и журналы прогонов, на которые ссылается отчёт.

Отдельное требование приказа тика 43 — перепроверка без сети. Она не
декларируется, а ДОКАЗЫВАЕТСЯ: на время проверки `socket.socket` подменяется
на класс, который бросает исключение при любой попытке создать сокет. Если
проверка прошла, значит сети она не касалась.

    python3 snapshot_manifest.py build     собрать снимок
    python3 snapshot_manifest.py verify    перепроверить (сеть запрещена)
    python3 snapshot_manifest.py selftest  самопроверка модуля
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import socket
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "baseline", "snapshot-manifest.json")
TRACK = "/home/user/workspace/cron_tracking/8dff7aa3"
WORK = "/home/user/workspace"


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _tool_files() -> list[str]:
    """Файлы инструмента берутся из baseline.py — один источник состава.

    Дублировать список нельзя: разошедшиеся списки давали бы «снимок сходится»
    при изменённом файле, который просто не попал во второй список."""
    sys.path.insert(0, ROOT)
    import baseline  # noqa: E402
    return sorted(baseline._tool_files())


def _docs() -> list[str]:
    out = []
    for pat in (os.path.join(WORK, "loop*", "report.md"),
                os.path.join(TRACK, "audit-ledger.md"),
                os.path.join(ROOT, "claims.yaml"),
                os.path.join(ROOT, "coverage_manifest.yaml"),
                os.path.join(ROOT, "pending", "*.yaml"),
                os.path.join(ROOT, "docs", "*.md")):
        out.extend(glob.glob(pat))
    return sorted(p for p in out if os.path.isfile(p))


def _logs(patterns: list[str] | None = None) -> list[str]:
    """Журналы прогонов. По умолчанию — журналы этой оболочки в /tmp.

    Журнал может исчезнуть (перезапуск песочницы), поэтому в снимке для
    каждого файла хранится ещё и размер: пропавший журнал отличим от
    подменённого."""
    pats = patterns or ["/tmp/tri-*.txt", "/tmp/g4*.txt", "/tmp/r4*.txt",
                        os.path.join(TRACK, "runs.jsonl")]
    out: list[str] = []
    for pat in pats:
        out.extend(glob.glob(pat))
    return sorted(p for p in out if os.path.isfile(p))


def build(out_path: str = OUT, root: str = ROOT) -> dict:
    groups = {
        "tool": [os.path.join(root, rel) for rel in _tool_files()],
        "docs": _docs(),
        "logs": _logs(),
    }
    body: dict = {"created": time.strftime("%Y-%m-%dT%H:%M:%S"), "groups": {}}
    for name, paths in groups.items():
        entries = {}
        for p in paths:
            rel = os.path.relpath(p, WORK)
            entries[rel] = {"sha256": sha256(p), "size": os.path.getsize(p)}
        body["groups"][name] = entries
    body["counts"] = {k: len(v) for k, v in body["groups"].items()}
    body["digest"] = hashlib.sha256(
        json.dumps(body["groups"], sort_keys=True,
                   ensure_ascii=False).encode()).hexdigest()[:16]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return body


class _NoNetwork:
    """Подмена сокета на время перепроверки: любая попытка — исключение."""

    def __init__(self, *a, **k):
        raise RuntimeError("перепроверка снимка не имеет права ходить в сеть")


def verify(path: str = OUT, allow_missing_logs: bool = True) -> tuple[int, list[str]]:
    """Перепроверка снимка. Возвращает (код, список расхождений).

    Пропавший журнал по умолчанию НЕ считается расхождением: журналы живут во
    временном каталоге. Пропавший файл инструмента или документа — считается
    всегда."""
    problems: list[str] = []
    try:
        with open(path, encoding="utf-8") as fh:
            body = json.load(fh)
    except Exception as exc:
        return 1, ["снимок не читается: %s" % exc]
    want = hashlib.sha256(
        json.dumps(body.get("groups", {}), sort_keys=True,
                   ensure_ascii=False).encode()).hexdigest()[:16]
    if want != body.get("digest"):
        problems.append("отпечаток снимка не сходится с его же составом: "
                        "%s против %s" % (want, body.get("digest")))
    real_socket = socket.socket
    socket.socket = _NoNetwork  # type: ignore[assignment]
    try:
        for group, entries in sorted(body.get("groups", {}).items()):
            for rel, rec in sorted(entries.items()):
                full = os.path.join(WORK, rel)
                if not os.path.isfile(full):
                    if group == "logs" and allow_missing_logs:
                        continue
                    problems.append("пропал файл (%s): %s" % (group, rel))
                    continue
                got = sha256(full)
                if got != rec["sha256"]:
                    problems.append(
                        "изменился файл (%s): %s\n    было %s\n    стало %s"
                        % (group, rel, rec["sha256"][:16], got[:16]))
    finally:
        socket.socket = real_socket
    return (1 if problems else 0), problems


def selftest() -> tuple[int, int]:
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
        # Снимок на игрушечном составе: проверяется механика, а не корпус.
        f1 = os.path.join(tmp, "a.txt")
        f2 = os.path.join(tmp, "b.log")
        open(f1, "w").write("раз")
        open(f2, "w").write("два")
        body = {"groups": {"tool": {}, "docs": {}, "logs": {}}}
        for grp, p in (("tool", f1), ("logs", f2)):
            body["groups"][grp][os.path.relpath(p, WORK)] = {
                "sha256": sha256(p), "size": os.path.getsize(p)}
        body["digest"] = hashlib.sha256(
            json.dumps(body["groups"], sort_keys=True,
                       ensure_ascii=False).encode()).hexdigest()[:16]
        man = os.path.join(tmp, "snap.json")
        json.dump(body, open(man, "w", encoding="utf-8"), ensure_ascii=False)
        rc, probs = verify(man)
        check("нетронутый снимок сходится", rc == 0 and not probs)
        open(f1, "w").write("раз-два")
        rc, probs = verify(man)
        check("подмена файла инструмента ловится",
              rc == 1 and any("изменился" in p for p in probs))
        open(f1, "w").write("раз")
        os.unlink(f2)
        rc, probs = verify(man)
        check("пропавший журнал не считается расхождением",
              rc == 0 and not probs)
        rc, probs = verify(man, allow_missing_logs=False)
        check("строгий режим ловит пропавший журнал",
              rc == 1 and any("пропал" in p for p in probs))
        # ПОДСТАВКА: правка состава без правки отпечатка обязана вскрыться.
        body["groups"]["docs"]["подделка"] = {"sha256": "0" * 64, "size": 0}
        json.dump(body, open(man, "w", encoding="utf-8"), ensure_ascii=False)
        rc, probs = verify(man)
        check("правка состава мимо отпечатка вскрывается",
              rc == 1 and any("отпечаток снимка" in p for p in probs))
        # Доказательство отсутствия сети: под подменой сокета обращение
        # обязано падать, а сама проверка — проходить.
        real = socket.socket
        socket.socket = _NoNetwork  # type: ignore[assignment]
        try:
            socket.socket()
            check("подмена сокета действительно запрещает сеть", False,
                  "сокет создался")
        except RuntimeError:
            check("подмена сокета действительно запрещает сеть", True)
        finally:
            socket.socket = real
        check("проверка возвращает сокет на место",
              socket.socket is real)
        bad = os.path.join(tmp, "нет.json")
        rc, probs = verify(bad)
        check("отсутствующий снимок даёт код 1, а не исключение", rc == 1)
    print("snapshot_manifest: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "verify"
    if cmd == "build":
        body = build()
        print("снимок собран: %s" % OUT)
        for k, v in sorted(body["counts"].items()):
            print("  %-6s %d файлов" % (k, v))
        print("  отпечаток снимка: %s" % body["digest"])
        return 0
    if cmd == "verify":
        rc, probs = verify()
        if rc == 0:
            print("снимок сходится (перепроверка без сети)")
        else:
            print("РАСХОЖДЕНИЯ: %d" % len(probs))
            for p in probs:
                print("  " + p)
        return rc
    if cmd == "selftest":
        return 1 if selftest()[1] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
