"""Три независимых уровня статуса и линтер слова «подтверждено».

Пункты 2 и 3 приказа тика 41.

Зачем это отдельный модуль. Тик 39 отчитался: «Три честных формы наблюдения
(глобальное изменяемое состояние, functools.partial, lambda) получили
ПОДТВЕРЖДЕНО». Формально каждое отдельное слово в той фразе верно — вердикт
действительно был ПОДТВЕРЖДЕНО. Неверен смысл: читатель понимает её как
«детектор эти формы РАЗБИРАЕТ», тогда как измерение тика 40 дало чувствительность
0,1852 [5/27]. Вердикт «утверждение не является тавтологией» и утверждение
«детектор умеет находить тавтологию такого вида» — РАЗНЫЕ вещи, и молчание
детектора первое не обосновывает.

Отсюда три уровня, которые нельзя смешивать:

* **verified-in-scope** — проверено в объявленном охвате. Требует: класс
  конструкций, присутствующий в coverage manifest с положительными,
  негативными фикстурами и мутационными целями, И версию рантайма, на которой
  прогон состоялся.
* **not-evaluated** — не проверялось. Причина обязательна. Отсутствие
  результата не есть отрицательный результат (сюда попадает и молчаливый abort
  по таймауту, и недоступная ОС).
* **unsupported** — заявлено, что конструкция НЕ разбирается, с причиной. Это
  сильнее, чем not-evaluated: здесь есть фикстура, которая обязана давать
  отрицательный ответ, и её внезапный положительный ответ — расхождение.

Линтер `lint_text` требует, чтобы рядом со словом «подтверждено» стояли и класс
конструкций, и версия рантайма вида 3.14.3. Ограничение линтера: он проверяет
СОСЕДСТВО, а не смысл — обойти его, приписав версию рантайма к пустому
заявлению, можно. Он ловит забывчивость, а не умысел, и это его объявленный
охват.
"""

from __future__ import annotations

import re
import sys

VERIFIED = "verified-in-scope"
NOT_EVALUATED = "not-evaluated"
UNSUPPORTED = "unsupported"
LEVELS = (VERIFIED, NOT_EVALUATED, UNSUPPORTED)

# Версия рантайма: ровно три числа через точку. «CPython 3.14» не годится —
# патч-версия влияет на поведение разбора AST, что и надо фиксировать.
RUNTIME_RE = re.compile(r"\b\d+\.\d+\.\d+\b")
CONFIRM_RE = re.compile(r"подтвержден", re.IGNORECASE)

# Отсылка к классу конструкций: либо явное слово, либо имя класса из манифеста.
CLASS_WORDS = ("класс конструкц", "классы конструкц", "конструкт",
               "coverage manifest", "объявленн", "в охвате", "охват")


class ScopeError(ValueError):
    """Статус построен неверно: смысл уровней смешан."""


def status(level: str, *, construct_class: str | None = None,
           runtime: str | None = None, reason: str | None = None) -> dict:
    """Собрать статус, отказавшись собирать заведомо бессмысленный.

    verified-in-scope без класса конструкций или без версии рантайма — ровно та
    ошибка тика 39, и она обязана быть невозможной по построению, а не
    отлавливаться вниманием читателя.
    """
    if level not in LEVELS:
        raise ScopeError("неизвестный уровень: %r" % (level,))
    if level == VERIFIED:
        if not construct_class:
            raise ScopeError("verified-in-scope без класса конструкций")
        if not runtime or not RUNTIME_RE.search(runtime):
            raise ScopeError("verified-in-scope без версии рантайма вида "
                             "3.14.3: %r" % (runtime,))
    else:
        if not reason:
            raise ScopeError("%s без причины" % level)
    out = {"level": level}
    for key, val in (("construct_class", construct_class),
                     ("runtime", runtime), ("reason", reason)):
        if val:
            out[key] = val
    return out


def render(st: dict) -> str:
    """Однострочная запись статуса для ведомости и отчёта."""
    lvl = st["level"]
    if lvl == VERIFIED:
        return ("%s (класс конструкций: %s; рантайм: %s)"
                % (lvl, st["construct_class"], st["runtime"]))
    return "%s (причина: %s)" % (lvl, st.get("reason", "не указана"))


def lint_text(text: str) -> list[tuple[int, str, str]]:
    """Проверить текст: слово «подтверждено» без покрытия и версии рантайма.

    Возвращает список (номер строки, строка, чего не хватает). Пусто — чисто.
    Окно проверки — сама строка и строка таблицы: соседство ищется в пределах
    одной строки, потому что именно строкой читается таблица ведомости.
    """
    bad: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        if not CONFIRM_RE.search(line):
            continue
        low = line.lower()
        missing = []
        if not RUNTIME_RE.search(line):
            missing.append("версия рантайма")
        if not any(w in low for w in CLASS_WORDS):
            missing.append("класс конструкций")
        if missing:
            bad.append((i, line.strip()[:120], " и ".join(missing)))
    return bad


def selftest() -> int:
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok   " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    # --- построение статуса --------------------------------------------------
    st = status(VERIFIED, construct_class="descriptor", runtime="CPython 3.14.3")
    check("verified-in-scope собирается", st["level"] == VERIFIED)
    check("рендер содержит класс и рантайм",
          "descriptor" in render(st) and "3.14.3" in render(st))
    for bad_kwargs, why in (
        (dict(construct_class="descriptor"), "без рантайма"),
        (dict(runtime="3.14.3"), "без класса конструкций"),
        (dict(construct_class="descriptor", runtime="CPython 3.14"),
         "рантайм без патч-версии"),
    ):
        try:
            status(VERIFIED, **bad_kwargs)
            check("отказ %s" % why, False)
        except ScopeError:
            check("отказ %s" % why, True)
    try:
        status(NOT_EVALUATED)
        check("отказ not-evaluated без причины", False)
    except ScopeError:
        check("отказ not-evaluated без причины", True)
    check("not-evaluated с причиной собирается",
          status(NOT_EVALUATED, reason="устройство не ответило")["level"]
          == NOT_EVALUATED)
    check("unsupported с причиной собирается",
          status(UNSUPPORTED, reason="имя поля известно только в рантайме")
          ["level"] == UNSUPPORTED)

    # --- линтер: исторический текст тика 39 обязан быть поймай --------------
    t39 = ("- Три честных формы наблюдения (глобальное изменяемое состояние, "
           "`functools.partial`, `lambda`) получили ПОДТВЕРЖДЕНО; независимые "
           "пути, подставка и контроль прошли обязательные сита.")
    found = lint_text(t39)
    check("линтер ловит формулировку тика 39", len(found) == 1)
    check("линтер называет, чего не хватает",
          bool(found) and "версия рантайма" in found[0][2]
          and "класс конструкций" in found[0][2])

    good = ("- Класс конструкций descriptor: verified-in-scope, подтверждено "
            "на CPython 3.14.3, 6 позитивных и 5 негативных фикстур.")
    check("линтер молчит на правильной формулировке", lint_text(good) == [])

    half = "- Подтверждено на CPython 3.14.3."
    check("линтер ловит рантайм без класса конструкций",
          len(lint_text(half)) == 1
          and lint_text(half)[0][2] == "класс конструкций")

    check("линтер молчит на тексте без слова",
          lint_text("- Вердикт ВОПРОС: С10 не сопоставил статистику.") == [])

    print()
    print("  итог: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(selftest())
