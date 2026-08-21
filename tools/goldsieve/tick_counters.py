"""Технические счётчики тика. Пункт 6 приказа тика 41.

Правило молчаливого abort при таймауте остаётся: тик, который не выполнился,
НЕ пишет вердиктов и не уведомляет — иначе в ведомости появляются записи о
работе, которой не было. Но отсутствие записи и работающая инфраструктура на
письме выглядят одинаково, и деградация runner-а так маскируется сколько угодно
долго.

Поэтому вводится отдельный технический счётчик: он не содержит вердиктов и не
является отчётом о работе, он считает СОБЫТИЯ ИНФРАСТРУКТУРЫ. Файл лежит вне
кода инструмента (в каталоге крона), обновляется атомарной заменой и хранит и
агрегаты, и последние события с временем.

Команды:
    python3 tick_counters.py bump tick_started
    python3 tick_counters.py bump tick_aborted_timeout --note "load_skill 120s"
    python3 tick_counters.py show
    python3 tick_counters.py health        код 1, если доля срывов высока
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile

PATH = os.environ.get(
    "GOLDSIEVE_COUNTERS",
    "/home/user/workspace/cron_tracking/8dff7aa3/tick-counters.json")

KNOWN = (
    "tick_started",            # тик начался (первая команда выполнилась)
    "tick_completed",          # тик дошёл до записи в ведомость
    "tick_aborted_timeout",    # срыв по таймауту bash или load_skill
    "tick_aborted_other",      # срыв по иной причине
    # Пункт 3 приказа 2026-08-18: недоступность чужого устройства — НЕ срыв
    # тика. Такое событие считается отдельно и НЕ входит в долю деградации.
    "deferred_device_offline",  # runner недоступен, задача ушла в очередь
    "cross_platform_replay_run",  # очередь была разобрана на живом runner
    "note_missing",            # bump без примечания там, где оно обязательно
    "gate_closed",             # ci_gate.sh вернул 1
    "verdict_flips",           # переворот вердикта против baseline
    "manifest_mismatch",       # coverage manifest разошёлся с фактом
    "frozen_integrity_fail",   # нарушена целостность заморозки
)
# Счётчики, для которых примечание обязательно: без него событие нельзя
# отнести ни к одной категории аудита (aborted_audit.py).
REQUIRE_NOTE = ("tick_aborted_other", "tick_aborted_timeout",
                "deferred_device_offline", "gate_closed")
MAX_EVENTS = 200
# --- Тик 171, пункт 2 приказа: ротация была причиной потери истории ---------
# Аудит токенов срыва деградировал со временем: журнал в файле счётчиков хранит
# последние MAX_EVENTS событий, а тиков уже 170+, поэтому охват разбора упал с
# 47 до 3 из 52 — не потому, что аудит стал хуже, а потому, что данные
# вытеснялись. Параллельно ведём НЕРОТИРУЕМЫЙ append-only журнал: он не
# восстанавливает уже утраченное, но останавливает дальнейшую потерю.
APPEND_LOG = os.path.join(os.path.dirname(PATH), "counter-events.jsonl")


def _append_event(ev: dict) -> None:
    try:
        os.makedirs(os.path.dirname(APPEND_LOG), exist_ok=True)
        with open(APPEND_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        pass   # журнал подсобный: сбой записи не имеет права ронять тик


def _load() -> dict:
    if not os.path.exists(PATH):
        return {"counters": {}, "events": []}
    try:
        return json.load(open(PATH, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Битый файл счётчиков не имеет права уронить тик: он подсобный.
        return {"counters": {}, "events": [], "note": "предыдущий файл был битым"}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(PATH), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, PATH)  # атомарно: прерывание не оставит полуфайла


def bump(name: str, note: str = "", amount: int = 1) -> int:
    if name not in KNOWN:
        print("неизвестный счётчик: %r; известные: %s"
              % (name, ", ".join(KNOWN)))
        return 2
    data = _load()
    data.setdefault("counters", {})
    data["counters"][name] = int(data["counters"].get(name, 0)) + amount
    ev = {"at": dt.datetime.now(dt.timezone.utc)
                  .strftime("%Y-%m-%dT%H:%M:%SZ"), "counter": name}
    # Пункт 4 приказа 2026-08-18: аудит показал, что часть токенов срыва
    # записана БЕЗ примечания и классификации не поддаётся. Тик не ломаем
    # (счётчик подсобный), но пропуск становится видимым и считаемым.
    if note:
        ev["note"] = note
    elif name in REQUIRE_NOTE:
        ev["note"] = "ПРИМЕЧАНИЕ НЕ УКАЗАНО (нарушение контракта наблюдаемости)"
        ev["note_missing"] = True
        data["counters"]["note_missing"] = int(
            data["counters"].get("note_missing", 0)) + 1
        print("ПРЕДУПРЕЖДЕНИЕ: %s без --note; причина срыва не разбирается" % name)
    data.setdefault("events", []).append(ev)
    data["events"] = data["events"][-MAX_EVENTS:]
    _append_event(ev)          # до ротации: append-журнал полнее events
    _save(data)
    print("%s = %d" % (name, data["counters"][name]))
    return 0


def show() -> int:
    data = _load()
    cnt = data.get("counters", {})
    if not cnt:
        print("счётчиков нет")
        return 0
    print("=== технические счётчики тика (файл: %s)" % PATH)
    for name in KNOWN:
        if name in cnt:
            print("  %-24s %d" % (name, cnt[name]))
    extra = sorted(set(cnt) - set(KNOWN))
    for name in extra:
        print("  %-24s %d  (устаревшее имя)" % (name, cnt[name]))
    ev = data.get("events", [])
    if ev:
        print()
        print("последние события:")
        for row in ev[-8:]:
            print("  %s  %-22s %s" % (row.get("at"), row.get("counter"),
                                      row.get("note", "")))
    return 0


MIN_OBSERVED = 10


def health(max_share: float = 0.34, min_observed: int = MIN_OBSERVED) -> int:
    """Доля срывов среди начатых тиков. Код 1 при превышении порога.

    Порог — СОГЛАШЕНИЕ, а не выведенная величина, и помечен словом
    соглашение в выводе: выводить его неоткуда, статистики отказов runner-а нет.
    """
    cnt = _load().get("counters", {})
    started = int(cnt.get("tick_started", 0))
    # deferred_device_offline СОЗНАТЕЛЬНО не входит в числитель: недоступность
    # чужого ноутбука не есть деградация нашей инфраструктуры (пункт 3).
    aborted = (int(cnt.get("tick_aborted_timeout", 0))
               + int(cnt.get("tick_aborted_other", 0)))
    if started == 0:
        print("начатых тиков не зафиксировано — судить не о чем")
        return 0
    if started < min_observed:
        # Ниже порога наблюдений вердикт НЕ выносится: при одном наблюдении доля
        # равна либо 0, либо 1, и вывод был бы свойством размера выборки, а не
        # инфраструктуры — та же ошибка, что в лупе 6 с командой power.
        print("начато %d, сорвано %d; наблюдений меньше %d — вердикт не "
              "выносится (доля была бы свойством размера выборки)"
              % (started, aborted, min_observed))
        return 0
    share = aborted / started
    print("начато %d, сорвано %d, доля срывов %.3f (порог %.2f — СОГЛАШЕНИЕ)"
          % (started, aborted, share, max_share))
    if share > max_share:
        print("ДЕГРАДАЦИЯ ИНФРАСТРУКТУРЫ: доля срывов выше порога")
        return 1
    return 0


def selftest() -> int:
    """Самопроверка на временном файле: рабочий счётчик не трогается."""
    global PATH
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok   " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    with tempfile.TemporaryDirectory() as tmpd:
        saved, PATH = PATH, os.path.join(tmpd, "c.json")
        try:
            check("неизвестное имя отвергается", bump("нет такого") == 2)
            check("файл не создан отказом", not os.path.exists(PATH))
            bump("tick_started")
            bump("tick_started")
            bump("tick_aborted_timeout", note="load_skill 120s")
            data = _load()
            check("счёт накапливается",
                  data["counters"]["tick_started"] == 2)
            check("событие с примечанием записано",
                  any(e.get("note") == "load_skill 120s"
                      for e in data["events"]))
            check("мало наблюдений — вердикт не выносится", health() == 0)
            for _ in range(8):
                bump("tick_started")
            # 10 начатых, 1 срыв = 0,10 — ниже порога 0,34
            check("здоровье: 1 из 10 ниже порога", health() == 0)
            for _ in range(4):
                bump("tick_aborted_timeout")
            # 10 начатых, 5 срывов = 0,50 — выше порога
            check("здоровье: 5 из 10 выше порога", health() == 1)
            open(PATH, "w", encoding="utf-8").write("{битый")
            check("битый файл не роняет", bump("tick_started") == 0)
        finally:
            PATH = saved

    print()
    print("  итог: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "show"
    if mode == "bump":
        if len(argv) < 3:
            print("нужно имя счётчика")
            return 2
        note = ""
        if "--note" in argv:
            i = argv.index("--note")
            note = argv[i + 1] if len(argv) > i + 1 else ""
        return bump(argv[2], note)
    if mode == "show":
        return show()
    if mode == "health":
        return health()
    if mode == "selftest":
        return selftest()
    print("режимы: bump <имя> [--note ...] | show | health | selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
