"""Execution-proof: машинный след работы анализатора (пункт 4 приказа тика 42).

Зачем модуль. Луп 12 нашёл дефект, при котором разбор графа молча НЕ выполнялся
ни на одном реальном прогоне: `inspect.getmodule()` возвращал None, и детектор
честно возвращал False. Внешне это выглядело как «вырождений нет». Тик 40 нашёл
тот же класс дефекта в другом месте: детектор молчал на lambda и partial, потому
что разбирал по `__name__`.

Общее у обоих: **отсутствие срабатывания не отличимо от отсутствия работы**.
Единственный способ различить — заставить анализатор оставлять след и требовать,
чтобы след был непустым там, где работа обязана была идти.

Что считается:

  * `files_parsed`    — сколько файлов реально разобрано в AST;
  * `functions_seen`  — сколько объектов функций сопоставлено с узлом AST;
  * `nodes_visited`   — сколько узлов-источников значения разобрано;
  * `edges_resolved`  — сколько имён разрешено (замыкание, globals, атрибут);
  * `chains_expanded` — сколько шагов рекурсии по цепочке происхождения;
  * `unsupported`     — перечень ЯВНЫХ отказов с причиной.

Правило пустого следа: если кейс непустой (у наблюдения есть код), а след
тривиален, это авария, а не вердикт. Проверять `is_trivial()`.

Асимметрия намеренная: счётчики НЕ влияют на вердикт. Инструмент, у которого
измерение меняет результат, нельзя ни калибровать, ни сравнивать с baseline.
"""

from __future__ import annotations

import json
import threading

COUNTERS = (
    "files_parsed",
    "functions_seen",
    "nodes_visited",
    "edges_resolved",
    "chains_expanded",
)

# Причины явного отказа. Список закрыт: новая причина добавляется здесь, иначе
# `note_unsupported` падает. Смысл — не дать отказу протечь безымянным.
REASONS = (
    "dynamic-import",          # importlib.import_module(переменная), __import__
    "star-import",             # from x import * — имена статически неизвестны
    "module-not-found",        # имя не разрешается в файл рядом с кейсом
    "external-module",         # разрешается, но вне корня анализа (stdlib, site-packages)
    "relative-beyond-root",    # from ... import вне корня
    "syntax-error",            # файл не разбирается
    "no-code-object",          # у объекта нет __code__ (C-функция, встроенный)
    "node-not-found",          # объект есть, узел AST не найден
    "depth-limit",             # достигнут предел рекурсии
    "conditional-import",      # импорт внутри функции или ветки — статически не разрешаем
)


class Proof:
    """Счётчики и отказы одного прогона анализатора."""

    __slots__ = ("counters", "unsupported", "label")

    def __init__(self, label: str = "") -> None:
        self.counters = dict.fromkeys(COUNTERS, 0)
        self.unsupported: list[tuple[str, str]] = []
        self.label = label

    # --- запись ------------------------------------------------------------

    def bump(self, name: str, delta: int = 1) -> None:
        if name not in self.counters:
            raise KeyError("неизвестный счётчик следа: %s" % name)
        self.counters[name] += delta

    def note_unsupported(self, reason: str, detail: str = "") -> None:
        if reason not in REASONS:
            raise KeyError("неизвестная причина отказа: %s" % reason)
        self.unsupported.append((reason, detail))

    # --- чтение ------------------------------------------------------------

    @property
    def total(self) -> int:
        return sum(self.counters.values())

    def is_trivial(self) -> bool:
        """След пуст: ни одного файла и ни одной функции не разобрано.

        Именно эта комбинация означает «анализатор не работал». Ноль узлов при
        разобранном файле — законно (функция без источников значения).
        """
        return (self.counters["files_parsed"] == 0
                and self.counters["functions_seen"] == 0)

    def reasons(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for reason, _detail in self.unsupported:
            out[reason] = out.get(reason, 0) + 1
        return out

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "counters": dict(self.counters),
            "unsupported": [{"reason": r, "detail": d}
                            for r, d in self.unsupported],
        }

    def render(self) -> str:
        parts = ["%s=%d" % (k, v) for k, v in self.counters.items()]
        line = "след: " + ", ".join(parts)
        if self.unsupported:
            rs = self.reasons()
            line += "; отказы: " + ", ".join(
                "%s×%d" % (k, v) for k, v in sorted(rs.items()))
        return line

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True)


# ---------------------------------------------------------------------------
# активный след: стек на поток
# ---------------------------------------------------------------------------

_LOCAL = threading.local()


def _stack() -> list[Proof]:
    st = getattr(_LOCAL, "stack", None)
    if st is None:
        st = []
        _LOCAL.stack = st
    return st


def active() -> Proof | None:
    st = _stack()
    return st[-1] if st else None


def bump(name: str, delta: int = 1) -> None:
    """Отметить событие в активном следе. Без активного следа — тихо ничего.

    Тишина здесь безопасна: она означает «никто не измеряет», а не «работы не
    было». Проверка тривиальности делается там, где след ЗАВЕДЁН явно.
    """
    p = active()
    if p is not None:
        p.bump(name, delta)


def note_unsupported(reason: str, detail: str = "") -> None:
    p = active()
    if p is not None:
        p.note_unsupported(reason, detail)


# ---------------------------------------------------------------------------
# последний след и его выгрузка на диск
# ---------------------------------------------------------------------------

LAST: Proof | None = None
ENV_PATH = "GOLDSIEVE_PROOF"


def record(p: Proof) -> None:
    """Запомнить след и дописать его в файл, если задан GOLDSIEVE_PROOF.

    Запись на диск нужна именно потому, что реальный маршрут CLI часто
    идёт в ОТДЕЛЬНОМ процессе: без выгрузки след был бы наблюдаем только
    в искусственном вызове из теста — то есть доказывал бы работу анализатора
    не там, где он реально применяется.
    """
    global LAST
    LAST = p
    import os
    path = os.environ.get(ENV_PATH)
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(p.to_json() + "\n")
    except OSError:
        pass


class scope:
    """Контекст сбора следа: `with proof.scope("кейс") as pr: ...`."""

    __slots__ = ("proof",)

    def __init__(self, label: str = "") -> None:
        self.proof = Proof(label)

    def __enter__(self) -> Proof:
        _stack().append(self.proof)
        return self.proof

    def __exit__(self, *exc) -> None:
        st = _stack()
        if st and st[-1] is self.proof:
            st.pop()
        return None


# ---------------------------------------------------------------------------
# самопроверка
# ---------------------------------------------------------------------------

def selftest() -> tuple[int, int]:
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    p = Proof("t")
    check("новый след тривиален", p.is_trivial())
    p.bump("files_parsed")
    check("после разбора файла след не тривиален", not p.is_trivial())

    p2 = Proof("t2")
    p2.bump("nodes_visited", 5)
    check("узлы без файла всё равно тривиальны (файл не разбирался)",
          p2.is_trivial())

    # ПОДСТАВКА: неизвестный счётчик обязан падать, а не создаваться молча.
    try:
        p.bump("выдуманный")
        check("неизвестный счётчик отвергнут", False)
    except KeyError:
        check("неизвестный счётчик отвергнут", True)

    # ПОДСТАВКА: причина отказа вне закрытого списка обязана падать.
    try:
        p.note_unsupported("что-то пошло не так")
        check("причина вне списка отвергнута", False)
    except KeyError:
        check("причина вне списка отвергнута", True)

    p.note_unsupported("dynamic-import", "importlib.import_module(name)")
    check("отказ записан", p.reasons() == {"dynamic-import": 1})
    check("отказ виден в render", "dynamic-import" in p.render())

    # активный след
    check("без scope активного следа нет", active() is None)
    with scope("внешний") as outer:
        bump("files_parsed")
        with scope("внутренний") as inner:
            bump("functions_seen", 3)
            note_unsupported("node-not-found", "lambda")
        check("вложенный след получил своё", inner.counters["functions_seen"] == 3)
        check("внешний след не получил чужого",
              outer.counters["functions_seen"] == 0)
        check("внешний получил своё", outer.counters["files_parsed"] == 1)
    check("после выхода активного следа нет", active() is None)

    # ПОДСТАВКА: bump без активного следа не должен падать (иначе инструмент
    # нельзя вызывать вне измерения).
    try:
        bump("files_parsed")
        check("bump без следа безопасен", True)
    except Exception:
        check("bump без следа безопасен", False)

    # сериализация обязана быть машиночитаемой
    d = json.loads(Proof("x").to_json())
    check("json содержит все счётчики",
          set(d["counters"]) == set(COUNTERS))

    # выгрузка на диск: след обязан быть машиночитаем из другого процесса
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as d2:
        dst = os.path.join(d2, "proof.jsonl")
        os.environ[ENV_PATH] = dst
        try:
            pw = Proof("выгрузка")
            pw.bump("files_parsed")
            record(pw)
        finally:
            os.environ.pop(ENV_PATH, None)
        got = [json.loads(line) for line in open(dst, encoding="utf-8")]
        check("след выгружен строкой JSON", len(got) == 1
              and got[0]["counters"]["files_parsed"] == 1)
    check("последний след запомнен", LAST is not None
          and LAST.label == "выгрузка")
    # ПОДСТАВКА: без переменной окружения запись не должна падать
    try:
        record(Proof("без файла"))
        check("запись без файла безопасна", True)
    except Exception:
        check("запись без файла безопасна", False)

    print("  proof: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


if __name__ == "__main__":
    import sys
    _ok, _fail = selftest()
    sys.exit(1 if _fail else 0)
