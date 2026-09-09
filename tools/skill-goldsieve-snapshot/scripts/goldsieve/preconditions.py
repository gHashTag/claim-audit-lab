# -*- coding: utf-8 -*-
"""Семантические предпосылки утверждения: допущение обязано быть объявлено.

Найдено на тике 47. Утверждение «при 123 201 испытании порог Шидака равен
5,06 сигма» получило вердикт ПОДТВЕРЖДЕНО. Арифметика верна, но формула Šidák
выведена ИЗ НЕЗАВИСИМОСТИ испытаний, а независимость перебранных формул корпуса
не проверена — более того, члены семейства зависимы по построению (общие
множители). Значит слово ПОДТВЕРЖДЕНО здесь читается шире, чем доказано:
доказано тождество, а не его применимость.

Механика. Предпосылка объявляется В ПАСПОРТЕ ЦЕЛИ полем ``tests_independent``
со значениями ``true`` / ``false`` / ``unknown``. Дальше вердикт ПОДТВЕРЖДЕНО
понижается:

===================== ==================================================
объявлено             вердикт вместо ПОДТВЕРЖДЕНО
===================== ==================================================
true                  остаётся ПОДТВЕРЖДЕНО (предпосылка объявлена верной)
unknown               ДОПУЩЕНИЕ НЕ ПРОВЕРЕНО (assumption-unverified)
false                 НЕПРИМЕНИМО (not-applicable)
не объявлено, но
поправка на
множественность
используется          ДОПУЩЕНИЕ НЕ ПРОВЕРЕНО (independence_undeclared)
===================== ==================================================

Чего модуль НЕ делает: он не проверяет независимость и не оценивает её степень.
Это работа сита С20 (устойчивость вывода к замене m на эффективное m_eff). Здесь
только запрет на молчание: допущение либо объявлено, либо вердикт не может быть
безусловным.
"""

from __future__ import annotations

# статусы предпосылки
OK = "ok"
UNVERIFIED = "assumption-unverified"
VIOLATED = "not-applicable"
UNDECLARED = "independence-undeclared"
IRRELEVANT = "irrelevant"

# вердикты, которыми ПОДТВЕРЖДЕНО замещается
ASSUMPTION = "ДОПУЩЕНИЕ НЕ ПРОВЕРЕНО"
NOT_APPLICABLE = "НЕПРИМЕНИМО"

VALUES = ("true", "false", "unknown")

# ключевые слова: по ним видно, что утверждение опирается на поправку для
# множественных испытаний, а значит обязано объявить предпосылку
MULTIPLICITY_WORDS = ("шидак", "sidak", "šidák", "бонферрони", "bonferroni",
                      "множествен", "multiplicity", "испытан", "trials")


def normalize(value) -> str:
    """Приводит объявление к ``true`` / ``false`` / ``unknown``.

    Булев True/False принимается: писать в кейсе питонов литерал естественнее.
    Пустая строка и None означают «не объявлено» и дают ``""``.
    """
    if value is None or value == "":
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    s = str(value).strip().lower()
    if s in VALUES:
        return s
    raise ValueError(
        "tests_independent обязано быть одним из %s, получено %r"
        % (", ".join(VALUES), value))


def requires_declaration(claim) -> bool:
    """Обязано ли утверждение объявить предпосылку независимости.

    Обязано, если оно ОПИРАЕТСЯ на поправку для множественных испытаний: либо
    объявлен размер перебора, либо заявлена множественность или эффективное
    число попыток, либо предмет утверждения назван словами из
    :data:`MULTIPLICITY_WORDS`.
    """
    if getattr(claim, "search_size", None) is not None:
        return True
    for attr in ("multiplicity", "meff"):
        if getattr(claim, attr, None) is not None:
            return True
    text = " ".join(str(getattr(claim, a, "") or "") for a in
                    ("name", "claim_family", "observable", "novelty_key"))
    low = text.lower()
    return any(w in low for w in MULTIPLICITY_WORDS)


def evaluate(claim) -> dict:
    """Машинная сводка предпосылки: статус, объявление, обязательность."""
    declared = normalize(getattr(claim, "tests_independent", None))
    need = requires_declaration(claim)
    if declared == "true":
        status = OK
    elif declared == "unknown":
        status = UNVERIFIED
    elif declared == "false":
        status = VIOLATED
    elif need:
        status = UNDECLARED
    else:
        status = IRRELEVANT
    return {"declared": declared or "not-declared",
            "required": need,
            "status": status,
            "detail": DETAIL[status]}


DETAIL = {
    OK: "предпосылка независимости испытаний объявлена верной",
    UNVERIFIED: "независимость испытаний объявлена НЕ проверенной: вердикт "
                "относится к тождеству, а не к его применимости",
    VIOLATED: "независимость испытаний объявлена нарушенной: поправка Шидака к "
              "этому набору испытаний неприменима",
    UNDECLARED: "утверждение опирается на поправку для множественных "
                "испытаний, но предпосылка независимости не объявлена",
    IRRELEVANT: "предпосылка независимости к утверждению не относится",
}

# статус предпосылки -> вердикт, которым замещается ПОДТВЕРЖДЕНО
REPLACEMENT = {UNVERIFIED: ASSUMPTION, UNDECLARED: ASSUMPTION,
               VIOLATED: NOT_APPLICABLE}

# статус предпосылки -> подтип причины вердикта
REASON = {UNVERIFIED: "independence_unknown",
          UNDECLARED: "independence_undeclared",
          VIOLATED: "independence_violated"}

# статус предпосылки -> трёхуровневый статус области охвата
SCOPE = {OK: "verified-in-scope", IRRELEVANT: "verified-in-scope",
         UNVERIFIED: "not-evaluated", UNDECLARED: "not-evaluated",
         VIOLATED: "unsupported"}


def apply(claim, verdict: str, confirmed: str = "ПОДТВЕРЖДЕНО"):
    """Понижает ПОДТВЕРЖДЕНО, если предпосылка не объявлена верной.

    Возвращает пару (вердикт, сводка). Другие вердикты не трогает намеренно:
    ПУСТО, ВОПРОС и ОПРОВЕРГНУТО и без того не являются подтверждением, а
    подмена их на «неприменимо» скрыла бы найденное расхождение.
    """
    info = evaluate(claim)
    if verdict != confirmed:
        info["applied"] = False
        return verdict, info
    new = REPLACEMENT.get(info["status"])
    info["applied"] = new is not None
    return (new or verdict), info


# --------------------------------------------------------------------------
# самопроверка
# --------------------------------------------------------------------------

class _Claim:
    """Минимальная заглушка утверждения: только читаемые поля."""

    def __init__(self, **kw):
        self.name = kw.pop("name", "проверочное утверждение")
        self.search_size = kw.pop("search_size", None)
        self.multiplicity = kw.pop("multiplicity", None)
        self.meff = kw.pop("meff", None)
        self.claim_family = kw.pop("claim_family", "")
        self.observable = kw.pop("observable", "")
        self.novelty_key = kw.pop("novelty_key", "")
        self.tests_independent = kw.pop("tests_independent", None)
        if kw:
            raise TypeError("лишние поля: %r" % (list(kw),))


def selftest() -> int:
    """Возвращает число провалов. Проверок: 20."""
    import sys
    _self = sys.modules[__name__]
    fail = 0
    C = "ПОДТВЕРЖДЕНО"

    def ok(cond, msg):
        nonlocal fail
        if not cond:
            fail += 1
            print("    ПРОВАЛ: %s" % msg)

    # 1-4. нормализация
    ok(_self.normalize(True) == "true", "True обязано стать true")
    ok(_self.normalize(False) == "false", "False обязано стать false")
    ok(_self.normalize("UNKNOWN") == "unknown", "регистр обязан игнорироваться")
    ok(_self.normalize(None) == "", "None означает «не объявлено»")

    # 5. мусор обязан отвергаться, а не толковаться
    try:
        _self.normalize("maybe")
        ok(False, "недопустимое значение принято")
    except ValueError:
        pass

    # 6-8. ПОДСТАВКА: unknown НЕ имеет права дать ПОДТВЕРЖДЕНО
    v, info = _self.apply(_Claim(tests_independent="unknown",
                                 search_size=123201), C)
    ok(v == _self.ASSUMPTION, "unknown обязано понизить вердикт, получено %r" % v)
    ok(info["status"] == _self.UNVERIFIED, "статус обязан быть %s" % _self.UNVERIFIED)
    ok(info["applied"] is True, "понижение обязано быть отмечено")

    # 9-10. ПОДСТАВКА: false даёт неприменимо
    v, info = _self.apply(_Claim(tests_independent=False, search_size=100), C)
    ok(v == _self.NOT_APPLICABLE, "false обязано дать НЕПРИМЕНИМО, получено %r" % v)
    ok(_self.SCOPE[info["status"]] == "unsupported",
       "нарушенная предпосылка обязана давать unsupported")

    # 11. true оставляет вердикт
    v, _ = _self.apply(_Claim(tests_independent=True, search_size=100), C)
    ok(v == C, "true обязано оставить ПОДТВЕРЖДЕНО, получено %r" % v)

    # 12-13. ПОДСТАВКА: молчание не проходит там, где поправка используется
    v, info = _self.apply(_Claim(search_size=123201), C)
    ok(v == _self.ASSUMPTION,
       "необъявленная предпосылка обязана понизить вердикт, получено %r" % v)
    ok(info["status"] == _self.UNDECLARED, "статус обязан быть %s" % _self.UNDECLARED)

    # 14-15. поправка распознаётся и по названию, и по полю meff
    ok(_self.requires_declaration(
        _Claim(name="порог Шидака при 123 201 испытании")),
       "название с поправкой обязано требовать объявления")
    ok(_self.requires_declaration(_Claim(meff={"values": []})),
       "заявленное эффективное число попыток обязано требовать объявления")

    # 16. утверждение без множественности не обязано ничего объявлять
    v, info = _self.apply(_Claim(name="печатное значение phi^phi"), C)
    ok(v == C and info["status"] == _self.IRRELEVANT,
       "утверждение без множественности не должно понижаться: %r %r"
       % (v, info["status"]))

    # 17-19. ПОДСТАВКА: другие вердикты не подменяются
    for other in ("ПУСТО", "ВОПРОС", "ОПРОВЕРГНУТО"):
        v, info = _self.apply(_Claim(tests_independent="unknown",
                                     search_size=10), other)
        ok(v == other and info["applied"] is False,
           "вердикт %s не должен подменяться, получено %r" % (other, v))

    # 20. каждому статусу обязаны соответствовать текст и область охвата
    ok(all(s in _self.DETAIL and s in _self.SCOPE
           for s in (OK, UNVERIFIED, VIOLATED, UNDECLARED, IRRELEVANT)),
       "у статуса нет текста или области охвата")

    return fail


def main(argv=None) -> int:
    print("самопроверка предпосылок утверждения")
    fail = selftest()
    print("  итог: %d провалов" % fail)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
