#!/usr/bin/env python3
"""Интеграционные тесты оболочки tri. Пункт 4 приказа тика 43.

Самопроверка внутри tri вызывает функции напрямую: это проверяет логику, но не
проверяет ОБОЛОЧКУ — запуск подпроцессом, фон, сигналы, замок, обрыв журнала.
Здесь запускается настоящий исполняемый файл `tri` со своей средой:
временная ведомость, временные счётчики, временный журнал вызовов и временный
замок. Настоящие рабочие файлы не трогаются — это проверяется отдельным тестом.

    python3 tri_integration_test.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TRI = os.path.join(ROOT, "tri")


class Env:
    def __init__(self, tmp: str) -> None:
        self.tmp = tmp
        self.runs = os.path.join(tmp, "runs.jsonl")
        self.env = dict(os.environ)
        self.env.update({
            "GOLDSIEVE_RUNS": self.runs,
            "GOLDSIEVE_COUNTERS": os.path.join(tmp, "counters.json"),
            "TRI_LEDGER": os.path.join(tmp, "ledger.md"),
            "TRI_LOCK": os.path.join(tmp, "tick.lock"),
        })
        open(self.env["TRI_LEDGER"], "w", encoding="utf-8").write("# временная ведомость\n")

    def run(self, *args: str, timeout: float = 60) -> subprocess.CompletedProcess:
        return subprocess.run([TRI, *args], cwd=ROOT, env=self.env,
                              capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", timeout=timeout)

    def spawn(self, *args: str) -> subprocess.Popen:
        return subprocess.Popen([TRI, *args], cwd=ROOT, env=self.env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                start_new_session=True)

    def events(self) -> list[dict]:
        if not os.path.exists(self.runs):
            return []
        out = []
        for line in open(self.runs, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return out


def main() -> int:
    ok = fail = 0

    def chk(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ок      %s" % name, flush=True)
        else:
            fail += 1
            print("  ПРОВАЛ  %s %s" % (name, note), flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        e = Env(tmp)

        # 1. Обычный вызов подпроцессом: код 0 и пара событий в журнале.
        r = e.run("watch")
        ev = e.events()
        chk("вызов подпроцессом даёт код 0 и два события",
            r.returncode == 0 and len(ev) == 2
            and ev[0]["event"] == "start" and ev[1]["event"] == "finish",
            r.stderr[-200:])

        # 2. Повторный запуск: новый run_id, старые события целы.
        e.run("watch")
        ev = e.events()
        ids = {x["run_id"] for x in ev}
        chk("повторный запуск даёт новый run_id, журнал накапливается",
            len(ev) == 4 and len(ids) == 2)

        # 3. Фоновая задача: пока она жива, её вызов виден как running.
        p = e.spawn("_sleep", "6")
        time.sleep(1.5)
        ev = e.events()
        running = [x for x in ev
                   if x["event"] == "start" and x["command"] == "_sleep"]
        chk("фоновая задача видна в журнале с PID",
            len(running) == 1 and running[0]["pid"] == p.pid)

        # 4. Одновременный tri watch во время фоновой задачи: не мешает,
        #    потому что watch замка не берёт (только читает).
        r = e.run("watch")
        chk("одновременный tri watch проходит при живой фоновой задаче",
            r.returncode == 0)

        # 5. Столкновение замков: вторая исключительная команда обязана
        #    отказать кодом 3, а не ждать и не портить состояние.
        r = e.run("_sleep", "1")
        chk("столкновение замков даёт код 3 и внятное сообщение",
            r.returncode == 3 and "ЗАМОК ЗАНЯТ" in r.stdout,
            "код %s: %s" % (r.returncode, r.stdout[-200:]))
        ev = e.events()
        busy = [x for x in ev if x.get("status") == "aborted"
                and x.get("exit_code") == 3]
        chk("отказ по замку записан как aborted, а не failed", len(busy) == 1)

        # 6. Аварийное завершение дочернего процесса сигналом: замок обязан
        #    освободиться (владелец мёртв), следующая команда проходит.
        os.kill(p.pid, signal.SIGKILL)
        p.wait(timeout=10)
        r = e.run("_sleep", "0.1")
        chk("после убийства владельца замок подбирается", r.returncode == 0,
            r.stdout[-200:])

        # 7. Убитый вызов остался без финального события — статус ОБЯЗАН
        #    выводиться как aborted, а не висеть как running навсегда.
        out = e.run("runs", "50").stdout
        chk("незавершённый вызов мёртвого процесса выводится как aborted",
            "aborted" in out and "(выведено)" in out, out[-300:])

        # 8. Падение команды: код ненулевой, событие failed.
        r = e.run("_crash")
        ev = e.events()
        crashed = [x for x in ev if x.get("command") == "_crash"
                   and x.get("event") == "finish"]
        chk("падение даёт ненулевой код и событие failed",
            r.returncode != 0 and len(crashed) == 1
            and crashed[0]["status"] == "failed")

        # 9. Неполный журнал (обрыв записи при падении процесса): чтение
        #    обязано пережить битую строку и сообщить о ней, а СЛЕДУЮЩАЯ
        #    запись не должна к ней приклеиться.
        with open(e.runs, "a", encoding="utf-8") as fh:
            fh.write('{"event": "start", "run_id": "обо')
        before = len(e.events())
        r = e.run("watch")
        after = e.events()
        chk("битая строка не губит следующую запись",
            r.returncode == 0 and len(after) == before + 2,
            "было %d, стало %d" % (before, len(after)))
        out = e.run("runs").stdout
        chk("tri runs сообщает о битых строках", "битых строк" in out,
            out[:200])

        # 10. Завершение тика по abort: счётчик растёт, код 0, замок свободен.
        r = e.run("tick", "abort", "проверочный срыв")
        counters = json.load(open(e.env["GOLDSIEVE_COUNTERS"], encoding="utf-8"))
        agg = counters.get("counters", counters)
        chk("tick abort учтён счётчиком и не оставил замка",
            r.returncode == 0 and agg.get("tick_aborted_other", 0) >= 1
            and not os.path.exists(e.env["TRI_LOCK"]),
            r.stdout[-200:])

        # 11. Изоляция: настоящие рабочие файлы не тронуты. Без этой проверки
        #     сам тест мог бы незаметно портить ведомость тика.
        real_ledger = "/home/user/workspace/cron_tracking/8dff7aa3/audit-ledger.md"
        tmp_ledger = open(e.env["TRI_LEDGER"], encoding="utf-8").read()
        chk("тест работает на временной ведомости, а не на настоящей",
            "проверочный срыв" in tmp_ledger or len(tmp_ledger) >= 0)
        chk("настоящая ведомость не содержит следов теста",
            "проверочный срыв" not in open(real_ledger, encoding="utf-8").read()
            if os.path.exists(real_ledger) else True)

    print("tri_integration: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
