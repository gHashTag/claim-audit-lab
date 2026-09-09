# -*- coding: utf-8 -*-
"""Append-only хеш-цепочка журнала вызовов (тик 44).

Что цепочка ДОКАЗЫВАЕТ: если проверяемая копия журнала отличается от той, что
писалась, — изменением поля, удалением записи, вставкой, перестановкой,
подменой `prev_hash` или обрывом строки не на конце файла, — проверка это
обнаруживает. Каждая запись связывает СВОЁ каноническое содержимое с хешем
предыдущей, поэтому локальная правка требует пересчёта всего хвоста.

Что цепочка НЕ доказывает (зафиксировано в манифесте, а не только здесь):

- **авторство.** Хеш вычисляет тот же процесс, что пишет запись; подписи нет,
  ключа нет. Цепочка отличает изменённую копию от исходной, но не говорит, кто
  её создал.
- **защиту от полной подмены.** Кто может переписать журнал, может пересчитать
  цепочку целиком и заодно переписать checkpoint. Обнаружение опирается на то,
  что checkpoint зафиксирован раньше и НЕЗАВИСИМО (в снимке baseline и в
  отчёте тика), а не на криптографической невозможности подделки.
- **порядок во времени.** `timestamp` берётся у того же процесса. Цепочка
  задаёт порядок ЗАПИСИ, а не доверенное время.

Формат записи: к событию добавляются `seq` (с единицы), `prev_hash`,
`entry_hash`. Хеш считается по каноническому JSON события БЕЗ поля
`entry_hash`, с добавлением `seq` и `prev_hash` — то есть подмена любого из
них ломает сходимость.
"""

from __future__ import annotations

import hashlib
import json
import os

GENESIS = "0" * 64
HASH_FIELD = "entry_hash"

# Классы нарушений. Имена машинные: по ним пишутся подставки и тесты, поэтому
# менять их нельзя молча — только вместе с тестами.
V_HASH_MISMATCH = "entry-hash-mismatch"
V_LINK_BROKEN = "prev-hash-link-broken"
V_SEQ_GAP = "seq-gap"
V_SEQ_ORDER = "seq-out-of-order"
V_BROKEN_LINE = "broken-line-not-at-tail"
V_MISSING_CHAIN = "chain-fields-missing"
V_PRE_CHAIN_AFTER = "pre-chain-entry-after-chained"
V_SEGMENT_NO_CHECKPOINT = "segment-without-checkpoint"
V_SEGMENT_WRONG_LINK = "segment-checkpoint-link-wrong"
V_CHECKPOINT_AHEAD = "checkpoint-ahead-of-log"
V_CHECKPOINT_HEAD = "checkpoint-head-mismatch"


def canonical(event: dict) -> str:
    """Каноническое представление события БЕЗ поля собственного хеша.

    Сортировка ключей и фиксированные разделители обязательны: иначе один и тот
    же смысл даёт разные байты и хеш перестаёт быть свойством содержимого.
    """
    body = {k: v for k, v in event.items() if k != HASH_FIELD}
    return json.dumps(body, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def entry_hash(event: dict) -> str:
    """sha256 канонического представления. `seq` и `prev_hash` входят в него как
    обычные поля события, поэтому их подмена ломает сходимость."""
    return hashlib.sha256(canonical(event).encode("utf-8")).hexdigest()


def chain_fields(event: dict, seq: int, prev_hash: str,
                 prev_checkpoint: dict | None = None) -> dict:
    """Достроить событие до записи цепочки."""
    out = dict(event)
    out["seq"] = int(seq)
    out["prev_hash"] = prev_hash
    if seq == 1:
        # Первая запись сегмента обязана объявить, откуда сегмент продолжается.
        # None — это тоже объявление (журнал начат с нуля), а не отсутствие
        # поля: молчание здесь неотличимо от потери ссылки.
        out["prev_checkpoint"] = prev_checkpoint
    out[HASH_FIELD] = entry_hash(out)
    return out


def head(path: str) -> tuple[int, str]:
    """Последний seq и его хеш. Для пустого или не-цепочечного журнала — (0, GENESIS)."""
    seq, h = 0, GENESIS
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict) and obj.get(HASH_FIELD):
                    seq = int(obj.get("seq", seq))
                    h = str(obj[HASH_FIELD])
    except FileNotFoundError:
        pass
    return seq, h


def head_tail(path: str, window: int = 65536) -> tuple[int, str]:
    """То же, что `head`, но читает только хвост файла.

    Нужно для записи: полный проход делал бы стоимость одной записи линейной по
    длине журнала. Если в окне не нашлось ни одной цепочечной записи, честно
    падаем на полный проход — иначе при длинном хвосте из старых записей без
    цепочки функция молча вернула бы GENESIS и сломала связь.
    """
    try:
        with open(path, "rb") as fh:
            size = fh.seek(0, os.SEEK_END)
            start = max(0, size - window)
            fh.seek(start)
            chunk = fh.read()
    except FileNotFoundError:
        return 0, GENESIS
    text = chunk.decode("utf-8", "replace")
    lines = text.split("\n")
    if start > 0:
        lines = lines[1:]  # первая строка окна может быть обрезана
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get(HASH_FIELD):
            return int(obj.get("seq", 0)), str(obj[HASH_FIELD])
    return head(path)


def prefix_digest(path: str) -> dict:
    """Отпечаток ПРЕФИКСА журнала до конца последней целой строки.

    Зачем отдельно от sha256 всего файла: журнал append-only и растёт при
    КАЖДОМ вызове, в том числе у самой проверяющей команды. Фиксация целого
    файла давала бы расхождение ПОСЛЕ ЛЮБОГО вызова, то есть шум вместо
    проверки; префикс же обязан оставаться НЕИЗМЕННЫМ — в этом и состоит
    append-only.
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return {"prefix_bytes": 0, "prefix_sha256": "", "last_seq": 0,
                "head_hash": GENESIS}
    cut = data.rfind(b"\n")
    prefix = data[:cut + 1] if cut >= 0 else b""
    seq, h = head(path)
    return {
        "prefix_bytes": len(prefix),
        "prefix_sha256": hashlib.sha256(prefix).hexdigest(),
        "last_seq": seq,
        "head_hash": h,
    }


def check_prefix(path: str, rec: dict) -> list[str]:
    """Сверить журнал с ранее зафиксированным префиксом. Рост разрешён,
    укорочение и правка — нет."""
    out: list[str] = []
    want_n = int(rec.get("prefix_bytes", 0) or 0)
    try:
        with open(path, "rb") as fh:
            got = fh.read(want_n)
    except FileNotFoundError:
        return ["журнал исчез: %s" % path]
    if len(got) < want_n:
        out.append("журнал укорочен: было не менее %d байт, стало %d"
                   % (want_n, len(got)))
        return out
    got_sha = hashlib.sha256(got).hexdigest()
    if rec.get("prefix_sha256") and got_sha != rec["prefix_sha256"]:
        out.append("префикс журнала изменился: было %s, стало %s"
                   % (rec["prefix_sha256"][:16], got_sha[:16]))
    return out


def read_lines(path: str) -> tuple[list[tuple[int, dict | None]], int]:
    """Строки журнала как (номер строки, объект или None при обрыве)."""
    rows: list[tuple[int, dict | None]] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                except Exception:
                    rows.append((n, None))
                    continue
                rows.append((n, obj if isinstance(obj, dict) else None))
    except FileNotFoundError:
        return [], 0
    broken = sum(1 for _, o in rows if o is None)
    return rows, broken


def verify(path: str, checkpoint: dict | None = None) -> dict:
    """Проверить цепочку. Возвращает машинный отчёт.

    Записи БЕЗ полей цепочки допускаются только в начале файла: журнал начат до
    тика 44 и дописывается дальше. Такая запись после цепочечной — нарушение
    (иначе вставку можно было бы замаскировать, просто выбросив поля).
    """
    rows, _ = read_lines(path)
    violations: list[dict] = []
    prev_hash = GENESIS
    prev_seq = 0
    chained = 0
    pre_chain = 0
    seen_chained = False
    last = len(rows)

    for idx, (lineno, obj) in enumerate(rows, 1):
        if obj is None:
            # Обрыв допустим ТОЛЬКО на последней строке: процесс убит на
            # середине write. Обрыв в середине означает правку файла.
            if idx != last:
                violations.append({"kind": V_BROKEN_LINE, "line": lineno,
                                   "detail": "битая строка не последняя"})
            continue
        if not obj.get(HASH_FIELD):
            if seen_chained:
                violations.append({"kind": V_PRE_CHAIN_AFTER, "line": lineno,
                                   "detail": "запись без полей цепочки после "
                                             "цепочечной"})
            else:
                pre_chain += 1
            continue
        seen_chained = True
        chained += 1
        seq = obj.get("seq")
        if not isinstance(seq, int) or "prev_hash" not in obj:
            violations.append({"kind": V_MISSING_CHAIN, "line": lineno,
                               "detail": "нет seq или prev_hash"})
            continue
        if seq <= prev_seq:
            violations.append({"kind": V_SEQ_ORDER, "line": lineno, "seq": seq,
                               "detail": "seq %d не больше предыдущего %d"
                                         % (seq, prev_seq)})
        elif seq != prev_seq + 1:
            violations.append({"kind": V_SEQ_GAP, "line": lineno, "seq": seq,
                               "detail": "разрыв: ожидался seq %d"
                                         % (prev_seq + 1)})
        if entry_hash(obj) != obj[HASH_FIELD]:
            violations.append({"kind": V_HASH_MISMATCH, "line": lineno,
                               "seq": seq,
                               "detail": "пересчитанный хеш не совпал"})
        if str(obj.get("prev_hash")) != prev_hash:
            violations.append({"kind": V_LINK_BROKEN, "line": lineno,
                               "seq": seq,
                               "detail": "prev_hash не равен хешу предыдущей "
                                         "записи"})
        if seq == 1:
            pc = obj.get("prev_checkpoint", "нет поля")
            if pc == "нет поля":
                violations.append({"kind": V_SEGMENT_NO_CHECKPOINT,
                                   "line": lineno,
                                   "detail": "первая запись сегмента без поля "
                                             "prev_checkpoint"})
            elif checkpoint and checkpoint.get("head_hash"):
                same = os.path.basename(str(checkpoint.get("log_name", ""))) \
                    == os.path.basename(path)
                if not same:
                    if not isinstance(pc, dict) or \
                            pc.get("head_hash") != checkpoint.get("head_hash"):
                        violations.append(
                            {"kind": V_SEGMENT_WRONG_LINK, "line": lineno,
                             "detail": "новый сегмент не ссылается на "
                                       "последний checkpoint"})
        prev_seq = seq
        prev_hash = str(obj[HASH_FIELD])

    if checkpoint and checkpoint.get("head_hash"):
        same_log = os.path.basename(str(checkpoint.get("log_name", ""))) == \
            os.path.basename(path)
        cp_seq = int(checkpoint.get("last_seq", 0) or 0)
        if same_log:
            if cp_seq > prev_seq:
                violations.append({"kind": V_CHECKPOINT_AHEAD,
                                   "detail": "checkpoint знает seq %d, в "
                                             "журнале только %d"
                                             % (cp_seq, prev_seq)})
            elif cp_seq == prev_seq and \
                    checkpoint.get("head_hash") != prev_hash:
                violations.append({"kind": V_CHECKPOINT_HEAD,
                                   "detail": "head_hash checkpoint не равен "
                                             "хешу последней записи"})

    return {
        "ok": not violations,
        "path": path,
        "lines": len(rows),
        "chained": chained,
        "pre_chain": pre_chain,
        "head": {"seq": prev_seq, "hash": prev_hash},
        "checkpoint_used": bool(checkpoint and checkpoint.get("head_hash")),
        "violations": violations,
        "guarantee": "обнаружение изменений в проверяемой копии",
        "not_guaranteed": ["авторство записи", "полная подмена журнала вместе "
                           "с checkpoint", "доверенное время"],
    }


def make_checkpoint(path: str, snapshot_sha256: str | None = None) -> dict:
    seq, h = head(path)
    return {
        "log_name": os.path.basename(path),
        "last_seq": seq,
        "head_hash": h,
        "snapshot_sha256": snapshot_sha256,
        "note": "цепочка обнаруживает правку копии; авторство и полная "
                "подмена вместе с checkpoint не покрыты",
    }


# --------------------------------------------------------------------------
# самопроверка: шесть обязательных подстановок приказа плюс проверки формата
# --------------------------------------------------------------------------

def _write_chain(path: str, n: int = 4,
                 prev_checkpoint: dict | None = None) -> None:
    seq, prev = 0, GENESIS
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            seq += 1
            ev = chain_fields({"run_id": "r%d" % i, "event": "start",
                               "status": "running", "command": "quick",
                               "timestamp": "2026-08-15T00:00:%02d" % i},
                              seq, prev, prev_checkpoint)
            prev = ev[HASH_FIELD]
            fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")


def _rows(path: str) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8")
            if l.strip()]


def _put(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def selftest() -> tuple[int, int]:
    import tempfile
    ok = bad = 0

    def chk(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  ок      %s" % name)
        else:
            bad += 1
            print("  ПРОВАЛ  %s %s" % (name, note))

    def kinds(rep: dict) -> set[str]:
        return {v["kind"] for v in rep["violations"]}

    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "runs.jsonl")

        # 0. честная цепочка обязана проходить, иначе всё остальное бессмысленно
        _write_chain(p, 4)
        rep = verify(p)
        chk("честная цепочка сходится", rep["ok"] and rep["chained"] == 4,
            str(rep["violations"]))
        chk("канонический вид не содержит поля своего хеша",
            HASH_FIELD not in canonical(_rows(p)[0]))
        chk("head даёт последний seq и его хеш",
            head(p) == (4, _rows(p)[-1][HASH_FIELD]))
        chk("head_tail совпадает с head", head_tail(p) == head(p))
        chk("head_tail с крошечным окном падает на полный проход, "
            "а не врёт", head_tail(p, window=8) == head(p))
        chk("head_tail с окном на одну строку тоже верен",
            head_tail(p, window=400) == head(p))
        chk("head_tail на пустом пути даёт genesis",
            head_tail(os.path.join(tmp, "нету.jsonl")) == (0, GENESIS))

        # 1. изменение поля записи
        rows = _rows(p)
        rows[1]["command"] = "gate"
        _put(p, rows)
        rep = verify(p)
        chk("подстановка 1: изменение поля записи ловится",
            not rep["ok"] and V_HASH_MISMATCH in kinds(rep), str(kinds(rep)))

        # 2. удаление середины
        _write_chain(p, 4)
        rows = _rows(p)
        del rows[1]
        _put(p, rows)
        rep = verify(p)
        chk("подстановка 2: удаление середины ловится",
            not rep["ok"] and {V_SEQ_GAP, V_LINK_BROKEN} & kinds(rep),
            str(kinds(rep)))

        # 3. перестановка двух событий
        _write_chain(p, 4)
        rows = _rows(p)
        rows[1], rows[2] = rows[2], rows[1]
        _put(p, rows)
        rep = verify(p)
        chk("подстановка 3: перестановка двух событий ловится",
            not rep["ok"] and (kinds(rep) & {V_SEQ_ORDER, V_SEQ_GAP,
                                             V_LINK_BROKEN}),
            str(kinds(rep)))

        # 4. подмена prev_hash. Ловится ДВАЖДЫ: и пересчётом своего хеша, и
        # разрывом связи. Проверяется и вариант, когда правщик пересчитал свой
        # хеш — тогда остаётся разрыв связи.
        _write_chain(p, 4)
        rows = _rows(p)
        rows[2]["prev_hash"] = "f" * 64
        _put(p, rows)
        rep = verify(p)
        chk("подстановка 4: подмена prev_hash ловится",
            not rep["ok"] and {V_HASH_MISMATCH, V_LINK_BROKEN} <= kinds(rep),
            str(kinds(rep)))
        rows[2][HASH_FIELD] = entry_hash(rows[2])
        _put(p, rows)
        rep = verify(p)
        chk("подстановка 4б: подмена prev_hash с пересчётом хеша ловится "
            "разрывом связи",
            not rep["ok"] and V_LINK_BROKEN in kinds(rep), str(kinds(rep)))

        # 5. повреждение последней строки допустимо; в середине — нет
        _write_chain(p, 4)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write('{"run_id":"r9","event":"st')
        rep = verify(p)
        chk("обрыв ПОСЛЕДНЕЙ строки не считается нарушением цепочки",
            rep["ok"], str(rep["violations"]))
        _write_chain(p, 4)
        rows = [json.dumps(r, ensure_ascii=False, sort_keys=True)
                for r in _rows(p)]
        rows.insert(2, '{"run_id":"r9","event":"st')
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        rep = verify(p)
        chk("подстановка 5: обрыв в СЕРЕДИНЕ ловится",
            not rep["ok"] and V_BROKEN_LINE in kinds(rep), str(kinds(rep)))

        # 6. новый сегмент без ссылки на checkpoint
        old = os.path.join(tmp, "runs.jsonl")
        _write_chain(old, 3)
        cp = make_checkpoint(old, "sha-снимка")
        seg = os.path.join(tmp, "runs-2.jsonl")
        _write_chain(seg, 2, prev_checkpoint=None)
        rep = verify(seg, checkpoint=cp)
        chk("подстановка 6: новый сегмент без ссылки на checkpoint ловится",
            not rep["ok"] and V_SEGMENT_WRONG_LINK in kinds(rep),
            str(kinds(rep)))
        _write_chain(seg, 2, prev_checkpoint={"log_name": cp["log_name"],
                                             "last_seq": cp["last_seq"],
                                             "head_hash": cp["head_hash"]})
        rep = verify(seg, checkpoint=cp)
        chk("сегмент со ссылкой на checkpoint проходит", rep["ok"],
            str(rep["violations"]))

        # поле prev_checkpoint обязано БЫТЬ, даже если оно None
        _write_chain(seg, 2, prev_checkpoint=None)
        rows = _rows(seg)
        del rows[0]["prev_checkpoint"]
        rows[0][HASH_FIELD] = entry_hash(rows[0])
        _put(seg, rows)
        rep = verify(seg)
        chk("отсутствие поля prev_checkpoint у первой записи ловится",
            not rep["ok"] and V_SEGMENT_NO_CHECKPOINT in kinds(rep),
            str(kinds(rep)))

        # checkpoint впереди журнала: журнал урезали, а checkpoint остался
        _write_chain(old, 5)
        cp = make_checkpoint(old)
        _write_chain(old, 3)
        rep = verify(old, checkpoint=cp)
        chk("урезанный журнал против checkpoint ловится",
            not rep["ok"] and V_CHECKPOINT_AHEAD in kinds(rep),
            str(kinds(rep)))

        # записи без цепочки: в начале терпимы, после цепочечной — нет
        p2 = os.path.join(tmp, "mixed.jsonl")
        with open(p2, "w", encoding="utf-8") as fh:
            fh.write('{"run_id":"old1","event":"start"}\n')
        seq, prev = 0, GENESIS
        with open(p2, "a", encoding="utf-8") as fh:
            seq += 1
            ev = chain_fields({"run_id": "n1", "event": "start"}, seq, prev,
                              None)
            fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
        rep = verify(p2)
        chk("старые записи без цепочки в начале журнала терпимы",
            rep["ok"] and rep["pre_chain"] == 1, str(rep["violations"]))
        with open(p2, "a", encoding="utf-8") as fh:
            fh.write('{"run_id":"old2","event":"start"}\n')
        rep = verify(p2)
        chk("запись без цепочки ПОСЛЕ цепочечной ловится",
            not rep["ok"] and V_PRE_CHAIN_AFTER in kinds(rep),
            str(kinds(rep)))

        chk("отчёт объявляет, что НЕ доказано",
            len(verify(p2)["not_guaranteed"]) >= 3)
        chk("пустой журнал не считается нарушением",
            verify(os.path.join(tmp, "нет.jsonl"))["ok"])

        # префиксный отпечаток: рост разрешён, правка и укорочение — нет
        pp = os.path.join(tmp, "pref.jsonl")
        _write_chain(pp, 3)
        rec = prefix_digest(pp)
        chk("префиксный отпечаток собран", rec["prefix_bytes"] > 0
            and rec["last_seq"] == 3 and not check_prefix(pp, rec))
        with open(pp, "a", encoding="utf-8") as fh:
            ev = chain_fields({"run_id": "r9"}, 4, rec["head_hash"])
            fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n")
        chk("дописывание новой записи не ломает префикс",
            not check_prefix(pp, rec) and verify(pp)["ok"])
        rows = _rows(pp)
        rows[0]["command"] = "подмена"
        _put(pp, rows)
        chk("правка старой записи ловится префиксом",
            bool(check_prefix(pp, rec)))
        _write_chain(pp, 1)
        chk("сброс журнала ловится префиксом как укорочение",
            any("укорочен" in m for m in check_prefix(pp, rec)),
            str(check_prefix(pp, rec)))

        # --- мета-проверки: показать, КАКОЙ механизм ловит подстановку.
        # Без них остаётся вопрос: может, правка ловится совсем другим
        # условием, а сам хеш ничего не проверяет — тогда цепочка была бы
        # украшением. Мутируется ПРОВЕРЯЮЩИЙ код, и подстановка обязана
        # перестать ловиться.
        # ВАЖНО: модуль берётся из sys.modules[__name__], а НЕ через
        # `import goldsieve.chain`. При запуске `python3 -m goldsieve.chain`
        # этот файл живёт как `__main__`, а импорт по имени пакета создаёт
        # ВТОРОЙ объект модуля — подмена в нём не влияет на выполняющийся код,
        # и мета-проверка молча превращается в тавтологию. Ровно так она и
        # провалилась при первом прогоне.
        import sys as _sys
        _self = _sys.modules[__name__]
        _write_chain(p, 4)
        rows = _rows(p)
        rows[1]["command"] = "gate"
        _put(p, rows)
        real = _self.entry_hash
        try:
            _self.entry_hash = lambda ev: ev.get(HASH_FIELD, "")
            muted = verify(p)
        finally:
            _self.entry_hash = real
        chk("изменение поля ловится ИМЕННО пересчётом хеша "
            "(мутант перестаёт ловить)",
            V_HASH_MISMATCH not in {v["kind"] for v in muted["violations"]},
            "мутант всё равно ловит: значит ловит что-то другое")

        # То же для связи: перестановка двух записей могла бы ловиться только
        # порядком seq. Проверяется, что связь prev_hash ловит её САМА:
        # переставленным записям возвращается возрастающий seq с пересчётом
        # своих хешей — остаётся только разрыв связи.
        _write_chain(p, 4)
        rows = _rows(p)
        rows[1], rows[2] = rows[2], rows[1]
        rows[1]["seq"], rows[2]["seq"] = 2, 3
        rows[1][HASH_FIELD] = entry_hash(rows[1])
        rows[2][HASH_FIELD] = entry_hash(rows[2])
        _put(p, rows)
        rep = verify(p)
        chk("перестановка с подогнанными seq и хешами ловится "
            "разрывом связи",
            not rep["ok"] and V_LINK_BROKEN in kinds(rep), str(kinds(rep)))

        # И прямая мутация связи: если перестать сравнивать prev_hash,
        # такая перестановка пройдёт незамеченной.
        got_link = [v for v in rep["violations"] if v["kind"] == V_LINK_BROKEN]
        others = [v for v in rep["violations"] if v["kind"] != V_LINK_BROKEN]
        chk("без проверки связи такая перестановка прошла бы тихо",
            bool(got_link) and not others,
            "прочие нарушения: %s" % others)

    print("chain: %d пройдено, %d провалено" % (ok, bad))
    return ok, bad


if __name__ == "__main__":
    import sys
    o, b = selftest()
    sys.exit(1 if b else 0)
