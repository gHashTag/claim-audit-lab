#!/usr/bin/env python3
"""Очередь cross_platform_replay (пункт 3 приказа 2026-08-18).

Раньше недоступный локальный runner давал два плохих следствия:
  * тик считался СОРВАННЫМ (tick_aborted_other), хотя вся работа на Linux была
    сделана — статистика отказов накручивалась чужим офлайном;
  * задача межплатформенной проверки нигде не сохранялась, поэтому повтор
    «macOS platform-unverified» переставал быть информацией.

Теперь задача СТАВИТСЯ В ОЧЕРЕДЬ и ждёт живого runner. Тик при этом успешен.

Команды:
    python3 replay_queue.py enqueue --platform macos --task "полный каскад" \
        --reason device_offline
    python3 replay_queue.py list
    python3 replay_queue.py status                 краткая сводка
    python3 replay_queue.py claim --platform macos     взять задачи в работу
    python3 replay_queue.py complete --id <id> --result ok|fail --note "…"
    python3 replay_queue.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

QUEUE = Path(os.environ.get(
    "GOLDSIEVE_REPLAY_QUEUE",
    "/home/user/workspace/cron_tracking/8dff7aa3/cross-platform-replay.json"))

PLATFORMS = ("macos", "windows", "linux-other")
STATES = ("queued", "claimed", "done", "failed")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load() -> dict:
    if not QUEUE.exists():
        return {"items": []}
    try:
        return json.loads(QUEUE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": [], "note": "предыдущий файл очереди был битым"}


def _save(data: dict) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(QUEUE.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, QUEUE)


def _ident(platform: str, task: str) -> str:
    return hashlib.sha256(f"{platform}|{task}".encode()).hexdigest()[:12]


def enqueue(platform: str, task: str, reason: str) -> int:
    if platform not in PLATFORMS:
        print(f"неизвестная платформа: {platform}; известные: {', '.join(PLATFORMS)}")
        return 2
    data = _load()
    ident = _ident(platform, task)
    for it in data["items"]:
        if it["id"] == ident and it["state"] in ("queued", "claimed"):
            it["attempts"] = int(it.get("attempts", 0)) + 1
            it["last_seen"] = _now()
            _save(data)
            print(f"уже в очереди: {ident} (попыток поставить: {it['attempts']})")
            return 0
    data["items"].append({
        "id": ident, "platform": platform, "task": task, "reason": reason,
        "state": "queued", "created": _now(), "last_seen": _now(), "attempts": 1,
    })
    _save(data)
    print(f"поставлено в очередь: {ident} [{platform}] {task}")
    return 0


def claim(platform: str) -> int:
    data = _load()
    taken = []
    for it in data["items"]:
        if it["platform"] == platform and it["state"] == "queued":
            it["state"] = "claimed"
            it["claimed_at"] = _now()
            taken.append(it)
    _save(data)
    if not taken:
        print(f"для {platform} задач в очереди нет")
        return 0
    for it in taken:
        print(f"взято в работу: {it['id']} {it['task']}")
    return 0


def complete(ident: str, result: str, note: str) -> int:
    data = _load()
    for it in data["items"]:
        if it["id"] == ident:
            it["state"] = "done" if result == "ok" else "failed"
            it["finished_at"] = _now()
            it["result_note"] = note
            _save(data)
            print(f"закрыто: {ident} -> {it['state']}")
            return 0
    print(f"нет такой задачи: {ident}")
    return 2


def show(as_status: bool) -> int:
    data = _load()
    items = data["items"]
    if as_status:
        counts: dict[str, int] = {}
        for it in items:
            key = f"{it['platform']}/{it['state']}"
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            print("очередь пуста")
        for k in sorted(counts):
            print(f"  {k}: {counts[k]}")
        oldest = min((it for it in items if it["state"] == "queued"),
                     key=lambda i: i["created"], default=None)
        if oldest:
            print(f"  самая старая ожидающая: {oldest['id']} с {oldest['created']} "
                  f"(попыток: {oldest.get('attempts', 1)})")
        return 0
    for it in items:
        print(f"{it['id']}  {it['state']:8s} {it['platform']:12s} "
              f"попыток={it.get('attempts', 1):3d}  {it['task'][:60]}")
    if not items:
        print("очередь пуста")
    return 0


def selftest() -> int:
    global QUEUE
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok     " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    with tempfile.TemporaryDirectory() as td:
        saved, QUEUE = QUEUE, Path(td) / "q.json"
        try:
            check("неизвестная платформа отвергается",
                  enqueue("plan9", "t", "device_offline") == 2)
            check("файл не создан отказом", not QUEUE.exists())
            enqueue("macos", "полный каскад", "device_offline")
            check("одна задача в очереди", len(_load()["items"]) == 1)
            enqueue("macos", "полный каскад", "device_offline")
            items = _load()["items"]
            check("повтор НЕ создаёт дубль", len(items) == 1)
            check("повтор считает попытки", items[0]["attempts"] == 2)
            enqueue("windows", "полный каскад", "device_offline")
            check("разные платформы — разные задачи", len(_load()["items"]) == 2)
            claim("macos")
            st = {i["id"]: i["state"] for i in _load()["items"]}
            mac = _ident("macos", "полный каскад")
            win = _ident("windows", "полный каскад")
            check("claim берёт только свою платформу",
                  st[mac] == "claimed" and st[win] == "queued")
            check("complete на несуществующем id даёт код 2",
                  complete("нетти", "ok", "") == 2)
            complete(mac, "ok", "прогон на macOS 15")
            check("complete закрывает задачу",
                  [i for i in _load()["items"] if i["id"] == mac][0]["state"] == "done")
            # битый файл не должен ронять очередь
            QUEUE.write_text("{битый", encoding="utf-8")
            check("битый файл очереди не роняет разбор", _load()["items"] == [])
        finally:
            QUEUE = saved
    print(f"самопроверка очереди: пройдено {ok}, провалено {fail}")
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    ap = argparse.ArgumentParser(description="очередь межплатформенных прогонов")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enqueue")
    e.add_argument("--platform", required=True)
    e.add_argument("--task", required=True)
    e.add_argument("--reason", default="device_offline")
    sub.add_parser("list")
    sub.add_parser("status")
    c = sub.add_parser("claim")
    c.add_argument("--platform", required=True)
    d = sub.add_parser("complete")
    d.add_argument("--id", required=True)
    d.add_argument("--result", choices=("ok", "fail"), required=True)
    d.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.cmd == "enqueue":
        return enqueue(a.platform, a.task, a.reason)
    if a.cmd == "list":
        return show(False)
    if a.cmd == "status":
        return show(True)
    if a.cmd == "claim":
        return claim(a.platform)
    return complete(a.id, a.result, a.note)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
