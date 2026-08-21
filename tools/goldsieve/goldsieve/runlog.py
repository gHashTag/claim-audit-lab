"""Журнал вызовов оболочки аудита: run_id, статусы, целостность.

Зачем. До тика 43 связь «команда → доказательство» держалась на памяти и на
именах временных файлов. Отчёт мог сослаться на артефакт, а какой именно вызов
его породил, на каком коммите корпуса и с каким отпечатком baseline — нигде не
фиксировалось. Здесь каждый вызов оставляет событие в JSONL: run_id, номер
тика, коммит корпуса, отпечаток baseline, команда, PID (в том числе фоновой
задачи), время старта и завершения, код возврата и список артефактов.

Формат намеренно построчный: дописывание строки в конец файла атомарно в
пределах одной записи, поэтому падение процесса портит МАКСИМУМ последнюю
строку, а не весь журнал. Чтение обязано это переживать — см. `read_events`.

Статусы задач разделены и проверяются кодом: набор `STATUSES` закрыт, чужое
слово в статусе — ошибка, а не свободный текст.
"""
from __future__ import annotations

import fcntl
import json
import os
import secrets
import subprocess
import tempfile
import time

from . import chain

# Закрытый набор статусов. `pending` и `not-evaluated` — не «почти сделано»:
# первый обязан иметь владельца, бюджет и критерии приёмки (проверяет
# coverage_manifest.py), второй означает отсутствие эксперимента.
STATUSES = ("running", "passed", "failed", "aborted", "pending",
            "not-evaluated")

# Статусы, при которых вызов ещё не завершён.
OPEN_STATUSES = ("running", "pending")

TRACK_DEFAULT = "/home/user/workspace/cron_tracking/8dff7aa3"


def runs_path() -> str:
    """Путь к журналу. Переопределяется через GOLDSIEVE_RUNS — на этом держатся
    и самопроверка, и интеграционные тесты (настоящий журнал они не трогают)."""
    env = os.environ.get("GOLDSIEVE_RUNS")
    if env:
        return env
    return os.path.join(TRACK_DEFAULT, "runs.jsonl")


def valid_status(status: str) -> bool:
    return status in STATUSES


def new_run_id() -> str:
    """run_id читаем глазом и уникален: время, PID, случайный хвост.

    Время в начале даёт лексикографический порядок, PID отделяет параллельные
    вызовы, случайный хвост закрывает случай двух запусков в одну секунду из
    одного PID (бывает при быстрых обёртках)."""
    return "%s-%d-%s" % (time.strftime("%Y%m%dT%H%M%S"), os.getpid(),
                         secrets.token_hex(3))


def corpus_commit(corpus: str = "/home/user/workspace/corpus/trinity") -> str:
    try:
        out = subprocess.run(["git", "-C", corpus, "rev-parse", "--short",
                              "HEAD"], capture_output=True, text=True, encoding="utf-8", errors="backslashreplace",
                             timeout=30)
        return out.stdout.strip() or "неизвестен"
    except Exception:
        return "неизвестен"


def baseline_fingerprint(root: str | None = None) -> str:
    """Отпечаток файлов инструмента из снимка baseline. Отсутствие снимка — не
    исключение: пишем «нет», иначе журнал перестанет вестись из-за побочного
    файла."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "baseline", "manifest.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return "нет"
    for key in ("files_fingerprint", "отпечаток_файлов", "fingerprint_files"):
        if key in data:
            return str(data[key])
    return str(data.get("fingerprint", "нет"))


def _tail_byte(path: str) -> bytes:
    try:
        with open(path, "rb") as fh:
            size = fh.seek(0, os.SEEK_END)
            if size == 0:
                return b"\n"
            fh.seek(-1, os.SEEK_END)
            return fh.read(1)
    except OSError:
        return b"\n"


def checkpoint_path() -> str:
    """Где живёт последний checkpoint журнала."""
    return os.environ.get(
        "GOLDSIEVE_LOG_CHECKPOINT",
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "baseline", "log-checkpoint.json"))


def read_checkpoint() -> dict | None:
    try:
        with open(os.path.normpath(checkpoint_path()), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) and data.get("head_hash") \
            else None
    except (OSError, ValueError):
        return None


def write_checkpoint(path: str | None = None,
                     snapshot_sha256: str | None = None) -> dict:
    """Зафиксировать checkpoint текущего журнала."""
    cp = chain.make_checkpoint(path or runs_path(), snapshot_sha256)
    dst = os.path.normpath(checkpoint_path())
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(cp, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return cp


def _append(event: dict, path: str | None = None) -> None:
    """Дописать событие строкой.

    Найдено самопроверкой тика 43: если предыдущая запись обрвалась БЕЗ
    перевода строки (процесс убит на середине write), то следующая запись
    приклеивается к обрывку и гибнет ВТОРАЯ запись, а не только первая. Поэтому
    перед дописыванием проверяется последний байт файла, и при обрыве сначала
    закрывается строка. Событие получает признак `after_truncated_write`, чтобы
    обрыв был виден в журнале, а не заглажен."""
    path = path or runs_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # Цепочка (тик 44): чтение головы и дозапись обязаны быть одним
    # критическим участком: два процесса, прочитав одну и ту же голову,
    # выдали бы две записи с одинаковым seq и разорвали связь. Поэтому
    # flock на самом файле журнала, а не общий замок команд: журнал пишут и
    # незамоченные команды.
    with open(path, "a+", encoding="utf-8") as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass
        prefix = ""
        if _tail_byte(path) not in (b"\n", b""):
            prefix = "\n"
            event = dict(event, after_truncated_write=True)
        if os.environ.get("GOLDSIEVE_CHAIN") == "0":
            # Только для ИЗМЕРЕНИЯ стоимости цепочки: путь «до» без связи
            # записей. Сравнивать с прежней версией кода было бы хуже:
            # различался бы не только журнал. В работе переменная НЕ
            # выставляется, а гейт проверяет целостность живого журнала,
            # поэтому постоянное отключение было бы заметно как нарушение.
            line = json.dumps(event, ensure_ascii=False, sort_keys=True)
            fh.write(prefix + line + "\n")
            fh.flush()
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            return
        seq, prev = chain.head_tail(path)
        prev_cp = None
        if seq == 0:
            cp = read_checkpoint()
            if cp and os.path.basename(str(cp.get("log_name", ""))) != \
                    os.path.basename(path):
                prev_cp = {"log_name": cp.get("log_name"),
                           "last_seq": cp.get("last_seq"),
                           "head_hash": cp.get("head_hash")}
        event = chain.chain_fields(event, seq + 1, prev, prev_cp)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        fh.write(prefix + line + "\n")
        fh.flush()
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass


def start(command: str, argv: list[str] | None = None,
          tick: int | None = None, path: str | None = None,
          pid: int | None = None) -> dict:
    """Событие начала вызова. Возвращает запись — из неё берётся run_id."""
    event = {
        "run_id": new_run_id(),
        "event": "start",
        "status": "running",
        "command": command,
        "argv": list(argv or []),
        "tick": tick,
        "pid": pid if pid is not None else os.getpid(),
        "corpus_commit": corpus_commit(),
        "baseline_fingerprint": baseline_fingerprint(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "started_unix": round(time.time(), 3),
    }
    _append(event, path)
    return event


def finish(run: dict, exit_code: int, artifacts: list[str] | None = None,
           status: str | None = None, path: str | None = None,
           child_pid: int | None = None) -> dict:
    """Событие завершения. Статус выводится из кода возврата, если не задан.

    Код 124 — таймаут из `timeout(1)`, это прерывание, а не провал проверки:
    смешивать их нельзя, иначе «упавшее по времени» попадёт в статистику
    провалов сита."""
    if status is None:
        status = "passed" if exit_code == 0 else (
            "aborted" if exit_code in (124, 130, 137, 143) else "failed")
    if not valid_status(status):
        raise ValueError("недопустимый статус: %s" % status)
    event = {
        "run_id": run["run_id"],
        "event": "finish",
        "status": status,
        "command": run.get("command"),
        "tick": run.get("tick"),
        "pid": run.get("pid"),
        "child_pid": child_pid,
        "exit_code": exit_code,
        "artifacts": list(artifacts or []),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duration_s": round(time.time() - float(run.get("started_unix", 0)), 3)
        if run.get("started_unix") else None,
    }
    _append(event, path)
    return event


def read_events(path: str | None = None) -> tuple[list[dict], int]:
    """Читает журнал, терпя обрыв последней строки.

    Возвращает (события, число битых строк). Битая строка НЕ игнорируется
    молча: число возвращается наружу, и `tri runs` его печатает — иначе
    потерянная запись выглядит как отсутствие вызова."""
    path = path or runs_path()
    events: list[dict] = []
    broken = 0
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    broken += 1
                    continue
                if isinstance(obj, dict) and obj.get("run_id"):
                    events.append(obj)
                else:
                    broken += 1
    except FileNotFoundError:
        return [], 0
    return events, broken


def alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def runs(path: str | None = None) -> tuple[list[dict], int]:
    """Сводка по run_id: последний статус вызова.

    Незавершённый вызов с мёртвым PID получает статус `aborted` с пометкой
    `derived: true`. Это ВЫВОД, а не запись из журнала: процесс мог быть убит
    до записи финального события, и молчаливое `running` навсегда — худшее из
    возможных, потому что выглядит как работающая задача."""
    events, broken = read_events(path)
    order: list[str] = []
    agg: dict[str, dict] = {}
    for ev in events:
        rid = ev["run_id"]
        if rid not in agg:
            agg[rid] = {"run_id": rid, "derived": False}
            order.append(rid)
        rec = agg[rid]
        for key in ("command", "tick", "pid", "corpus_commit",
                    "baseline_fingerprint", "started", "argv"):
            if ev.get(key) is not None and key not in rec:
                rec[key] = ev[key]
        if ev.get("event") == "finish":
            rec.update({"status": ev.get("status"),
                        "exit_code": ev.get("exit_code"),
                        "artifacts": ev.get("artifacts", []),
                        "finished": ev.get("finished"),
                        "duration_s": ev.get("duration_s")})
        else:
            rec.setdefault("status", ev.get("status", "running"))
    for rec in agg.values():
        if rec.get("status") == "running" and not alive(rec.get("pid")):
            rec["status"] = "aborted"
            rec["derived"] = True
            rec["derived_reason"] = "нет финального события, PID не жив"
    return [agg[r] for r in order], broken


class LockBusy(RuntimeError):
    """Замок занят живым процессом."""


# Замки, взятые В ЭТОМ же процессе. Без этого списка проверка «жив ли
# владелец» считала СВОЙ же PID признаком брошенного замка и подбирала его:
# повторный вход в ту же критическую секцию проходил бесшумно.
_HELD: set[str] = set()


class Lock:
    """Замок на тик. Занятый живым процессом замок — ОШИБКА, а не ожидание:
    два одновременных тика писали бы в одну ведомость и один baseline.

    Замок мёртвого процесса подбирается (stale): иначе один убитый тик
    заблокировал бы работу навсегда, и снимать замок пришлось бы руками."""

    def __init__(self, path: str):
        self.path = path
        self.taken = False

    def acquire(self) -> "Lock":
        real = os.path.abspath(self.path)
        if real in _HELD:
            raise LockBusy("замок уже взят этим же процессом")
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.taken = True
                _HELD.add(real)
                return self
            except FileExistsError:
                try:
                    holder = int(open(self.path).read().strip() or 0)
                except Exception:
                    holder = 0
                if alive(holder) and holder != os.getpid():
                    raise LockBusy("замок занят процессом %d" % holder)
                os.unlink(self.path)
        raise LockBusy("замок не взят")

    def release(self) -> None:
        if self.taken and os.path.exists(self.path):
            os.unlink(self.path)
        _HELD.discard(os.path.abspath(self.path))
        self.taken = False

    def __enter__(self) -> "Lock":
        return self.acquire()

    def __exit__(self, *exc) -> None:
        self.release()


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

    check("набор статусов закрыт", len(STATUSES) == 6
          and "passed" in STATUSES and "not-evaluated" in STATUSES)
    check("чужой статус отвергается", not valid_status("зелёный"))
    ids = {new_run_id() for _ in range(200)}
    check("run_id не повторяется на 200 вызовах", len(ids) == 200)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "runs.jsonl")
        r1 = start("gate", ["--all"], tick=43, path=path)
        finish(r1, 0, artifacts=["/tmp/g43.txt"], path=path)
        r2 = start("regress", tick=43, path=path, pid=999_000_001)
        rows, broken = runs(path)
        check("два вызова различаются по run_id",
              len(rows) == 2 and rows[0]["run_id"] != rows[1]["run_id"])
        check("завершённый вызов имеет статус passed и артефакт",
              rows[0]["status"] == "passed"
              and rows[0]["artifacts"] == ["/tmp/g43.txt"])
        check("вызов хранит тик, коммит и отпечаток baseline",
              rows[0].get("tick") == 43 and rows[0].get("corpus_commit")
              and rows[0].get("baseline_fingerprint"))
        check("незавершённый вызов с мёртвым PID выводится как aborted",
              rows[1]["status"] == "aborted" and rows[1]["derived"] is True)
        check("битых строк нет", broken == 0)
        # Цепочка (тик 44): запись обязана быть цепочечной СРАЗУ, а не
        # только когда её проверяют отдельной командой.
        ev_chain, _ = read_events(path)
        check("записи получают seq, prev_hash и entry_hash",
              all(e.get("entry_hash") and "prev_hash" in e
                  and isinstance(e.get("seq"), int) for e in ev_chain),
              str(ev_chain[:1]))
        check("seq идёт подряд с единицы",
              [e["seq"] for e in ev_chain] == list(range(1, len(ev_chain) + 1)))
        check("все записи имеют timestamp",
              all(e.get("timestamp") for e in ev_chain))
        check("живой журнал проходит проверку цепочки",
              chain.verify(path)["ok"], str(chain.verify(path)["violations"]))
        # checkpoint темпорально: пишется в своё место и связывает голову.
        old_env = os.environ.get("GOLDSIEVE_LOG_CHECKPOINT")
        os.environ["GOLDSIEVE_LOG_CHECKPOINT"] = os.path.join(tmp, "cp.json")
        try:
            cp = write_checkpoint(path, snapshot_sha256="a" * 64)
            check("checkpoint знает имя журнала, seq, голову и sha снимка",
                  cp["log_name"] == "runs.jsonl"
                  and cp["last_seq"] == len(ev_chain)
                  and cp["head_hash"] == ev_chain[-1]["entry_hash"]
                  and cp["snapshot_sha256"] == "a" * 64)
            check("checkpoint читается обратно",
                  (read_checkpoint() or {}).get("head_hash")
                  == cp["head_hash"])
            # НОВЫЙ СЕГМЕНТ: другое имя журнала обязан продолжаться от
            # checkpoint, и ссылка ставится АВТОМАТИЧЕСКИ при записи.
            seg = os.path.join(tmp, "runs-2.jsonl")
            rs = start("quick", tick=44, path=seg)
            ev_seg, _ = read_events(seg)
            check("новый segment автоматически ссылается на checkpoint",
                  (ev_seg[0].get("prev_checkpoint") or {}).get("head_hash")
                  == cp["head_hash"], str(ev_seg[0].get("prev_checkpoint")))
            check("новый segment проходит проверку с checkpoint",
                  chain.verify(seg, checkpoint=cp)["ok"],
                  str(chain.verify(seg, checkpoint=cp)["violations"]))
            finish(rs, 0, path=seg)
        finally:
            if old_env is None:
                os.environ.pop("GOLDSIEVE_LOG_CHECKPOINT", None)
            else:
                os.environ["GOLDSIEVE_LOG_CHECKPOINT"] = old_env
        # ПОДСТАВКА: обрыв последней строки на середине.
        with open(path, "a", encoding="utf-8") as fh:
            fh.write('{"run_id": "обрыв", "event": "sta')
        rows2, broken2 = runs(path)
        check("обрыв последней строки не рушит чтение",
              broken2 == 1 and len(rows2) == 2)
        # ПОДСТАВКА к самой записи: следующая запись НЕ должна приклеиться к
        # обрывку, иначе гибнет вторая запись, а не только первая.
        r_after = start("manifest", tick=43, path=path)
        rows_after, broken_after = runs(path)
        check("запись после обрыва не склеивается с обрывком",
              broken_after == 1
              and any(r["run_id"] == r_after["run_id"] for r in rows_after))
        ev_after, _ = read_events(path)
        check("обрыв помечен признаком в событии",
              any(e.get("after_truncated_write") for e in ev_after))
        finish(r_after, 0, path=path)
        # Живой PID остаётся running: собственный процесс жив по определению.
        r3 = start("watch", tick=43, path=path)
        rows3, _ = runs(path)
        live = [r for r in rows3 if r["run_id"] == r3["run_id"]][0]
        check("вызов живого процесса остаётся running",
              live["status"] == "running" and live["derived"] is False)
        finish(r3, 124, path=path)
        rows4, _ = runs(path)
        tm = [r for r in rows4 if r["run_id"] == r3["run_id"]][0]
        check("таймаут даёт aborted, а не failed", tm["status"] == "aborted")
        r4 = start("mut", tick=43, path=path)
        finish(r4, 1, path=path)
        rows5, _ = runs(path)
        bad = [r for r in rows5 if r["run_id"] == r4["run_id"]][0]
        check("ненулевой код даёт failed", bad["status"] == "failed")
        try:
            finish(r4, 0, status="зелёный", path=path)
            check("недопустимый статус отвергается", False, "исключения нет")
        except ValueError:
            check("недопустимый статус отвергается", True)
        # Замок: занят живым процессом -> ошибка; замок мёртвого -> подбирается.
        lp = os.path.join(tmp, "tick.lock")
        with Lock(lp) as _l:
            try:
                Lock(lp).acquire()
                check("замок не берётся дважды", False, "второй взят")
            except LockBusy:
                check("замок не берётся дважды", True)
        check("замок освобождается", not os.path.exists(lp))
        open(lp, "w").write("999000002")
        got = Lock(lp).acquire()
        check("замок мёртвого процесса подбирается", got.taken)
        got.release()
        check("пустой журнал не исключение", runs(os.path.join(tmp, "нет"))
              == ([], 0))
    print("runlog: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


if __name__ == "__main__":
    import sys
    sys.exit(1 if selftest()[1] else 0)
