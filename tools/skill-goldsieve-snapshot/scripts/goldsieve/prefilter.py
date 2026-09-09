"""Строгий pre-filter целей. Пункт 7 приказа тика 41.

Задача. Полный каскад по одной цели стоит минуты. При этом часть целей заведомо
НЕ способна дать различающий результат, и это видно заранее, дешёвой арифметикой:

* если локальный порог разрешающей способности семейства грубее, чем точность,
  с которой известна цель, то любое «совпадение» бесплатно — семейство накрывает
  окрестность цели своей плотностью;
* если ожидаемое число случайных попаданий при фактическом переборе >= 1, то
  попадание ожидается по случаю и содержательным быть не может;
* если относительная погрешность внешнего измерения хуже локального порога, то
  различить верную формулу от произвольной нечем.

Решение RUN / SKIP-VOID выносится ДО дорогого сита. SKIP-VOID — это не вердикт
об утверждении: это заявление о том, что данная проверка была бы вырождена (тот
же смысл, что у сита С4), и оно записывается с причиной, а не молча.

Что pre-filter НЕ делает: он не заменяет каскад и не выносит ПОДТВЕРЖДЕНО. Он
только отсекает заведомо неразрешимое. Ошибка первого рода у него дорога (мы
пропустили бы годную цель), поэтому при любой неопределённости входа решение —
RUN: сомнение трактуется в пользу дорогой проверки.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys

from . import family, meff, threshold

RUN = "RUN"
SKIP_VOID = "SKIP-VOID"

# Пункт 5 приказа 2026-08-18. Урок лупа 7: величина расхождения зависит от того,
# какой вариант перебора взят, а вариант раньше выбирался молча — в аргументах
# вызова. Теперь варианты ИМЕНОВАНЫ, оба размера печатаются ВСЕГДА, а выбор без
# машинного аргумента физически невозможен: поднимается исключение.
VARIANTS = {
    "standard": ("STANDARD_RANGES", family.STANDARD_RANGES),
    "actual": ("ACTUAL_RANGES", threshold.ACTUAL_RANGES),
}
MIN_REASON_LEN = 12
DECISION_LOG = os.environ.get(
    "GOLDSIEVE_PREFILTER_LOG",
    "/home/user/workspace/cron_tracking/8dff7aa3/prefilter-decisions.jsonl")


class VariantChoiceError(ValueError):
    """Вариант перебора выбран без машинного аргумента выбора."""


def variant_sizes() -> dict:
    """Размеры ОБОИХ вариантов перебора. Считаются кодом, не берутся из текста."""
    return {name: family.declared_size(rng) for name, (_, rng) in VARIANTS.items()}


def resolve_variant(variant: str | None, variant_reason: str | None) -> tuple:
    """Разрешить имя варианта в диапазоны, требуя аргумент выбора.

    Отсутствие имени или причины — ОТКАЗ, а не подстановка значения по
    умолчанию: молчаливый выбор варианта уже давал неверную величину
    расхождения (луп 7), и повторить это некодовым путём нельзя.
    """
    if variant not in VARIANTS:
        raise VariantChoiceError(
            "вариант перебора обязан быть назван явно: %s; получено %r"
            % (", ".join(sorted(VARIANTS)), variant))
    if not variant_reason or len(variant_reason.strip()) < MIN_REASON_LEN:
        raise VariantChoiceError(
            "выбор варианта %r без машинного аргумента выбора запрещён "
            "(нужна строка не короче %d символов)" % (variant, MIN_REASON_LEN))
    label, rng = VARIANTS[variant]
    return label, rng


def log_decision(dec, path: str | None = None) -> str:
    """Дописать решение в журнал: паспорт варианта переживает сам прогон."""
    dest = path or DECISION_LOG
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    row = {"at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "verdict": dec.verdict, "reasons": dec.reasons,
           "numbers": {k: str(v) for k, v in dec.numbers.items()}}
    with open(dest, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dest


class Decision:
    """Решение pre-filter с полным набором причин, а не одним словом."""

    def __init__(self, verdict: str, reasons: list[str], numbers: dict):
        self.verdict = verdict
        self.reasons = reasons
        self.numbers = numbers

    @property
    def run(self) -> bool:
        return self.verdict == RUN

    def __repr__(self) -> str:
        return "<%s %s>" % (self.verdict, "; ".join(self.reasons) or "—")

    def render(self) -> str:
        out = ["решение pre-filter: %s" % self.verdict]
        for key in sorted(self.numbers):
            out.append("  %-26s %s" % (key, self.numbers[key]))
        for r in self.reasons:
            out.append("  причина: " + r)
        return "\n".join(out)


def decide(target: float, *, uncertainty: float | None = None,
           search_size: int | None = None,
           ranges: dict | None = None,
           values: list[float] | None = None,
           variant: str | None = None,
           variant_reason: str | None = None) -> Decision:
    """Решить, способна ли цель дать различающий результат.

    target        — значение цели (внешнее измерение или величина корпуса);
    uncertainty   — АБСОЛЮТНАЯ погрешность цели; None означает «неизвестна», и
                    тогда отсечение по точности не применяется (сомнение -> RUN);
    search_size   — фактический размер перебора формул;
    ranges        — диапазоны показателей семейства; None = корпусные;
    values        — уже перечисленные значения семейства (кеш для скорости).
    """
    reasons: list[str] = []
    numbers: dict = {"цель": "%.12g" % target}
    # ПАСПОРТ ВАРИАНТА (пункт 5). Оба размера перебора печатаются ВСЕГДА, даже
    # когда используется только один: читатель отчёта обязан видеть, из чего
    # был выбор, а не только результат выбора.
    sizes = variant_sizes()
    numbers["M вариант standard"] = sizes["standard"]
    numbers["M вариант actual"] = sizes["actual"]
    # Паспорт обязателен ВСЕГДА: плотность семейства и множественность зависят
    # от варианта в любом вызове, поэтому «вызов без варианта» — это молчаливый
    # выбор, а именно он запрещён приказом.
    label, rng_chosen = resolve_variant(variant, variant_reason)
    if ranges is not None and ranges != rng_chosen:
        raise VariantChoiceError(
            "переданные диапазоны не совпадают с названным вариантом %r: "
            "паспорт варианта был бы ложным" % variant)
    ranges = rng_chosen
    numbers["выбранный вариант"] = "%s (%s)" % (variant, label)
    numbers["аргумент выбора"] = variant_reason.strip()

    if not math.isfinite(target) or target == 0:
        # Локальная плотность определена вокруг конечного ненулевого значения.
        return Decision(RUN, ["цель не конечна или равна нулю: отсечение "
                              "неприменимо, решение в пользу дорогой проверки"],
                        numbers)

    rng = ranges or family.STANDARD_RANGES
    # ОДНОРОДНОСТЬ ПАРЫ (урок лупа 7). Размер перебора и диапазоны обязаны
    # относиться к ОДНОМУ варианту. Пара «M от расширенного перебора, плотность
    # от стандартного» даёт верный знак и неверную величину — на этом уже
    # ошибались, и здесь это отказ, а не предупреждение.
    if search_size:
        declared = family.declared_size(rng)
        if search_size != declared:
            numbers["размер перебора M"] = search_size
            numbers["размер по диапазонам"] = declared
            return Decision(RUN, [
                "ПАРА НЕОДНОРОДНА: заявлен перебор %d, а переданные диапазоны "
                "дают %d. Плотность и множественность обязаны считаться на "
                "одном варианте; решение RUN, потому что отсекать по "
                "несогласованным входам нельзя" % (search_size, declared)],
                numbers)
    if values is None:
        values = [v for v in family.enumerate_family(rng)
                  if math.isfinite(v) and v > 0]
    numbers["членов семейства"] = len(values)

    eps = threshold.local_threshold(abs(target), rng, values=values)
    numbers["локальный порог eps_loc"] = "%.3g" % eps

    if uncertainty is not None and uncertainty > 0:
        rel = abs(uncertainty / target)
        numbers["отн. погрешность цели"] = "%.3g" % rel
        numbers["запас точности"] = "%.3g" % (rel / eps) if eps else "—"
        if rel > eps:
            reasons.append(
                "погрешность цели (%.3g отн.) ГРУБЕЕ локального порога "
                "семейства (%.3g): семейство накрывает окрестность цели своей "
                "плотностью, совпадение бесплатно" % (rel, eps))
    else:
        numbers["отн. погрешность цели"] = "неизвестна"

    if search_size:
        numbers["размер перебора M"] = search_size
        try:
            sigma = meff.sidak_sigma(search_size)
            numbers["порог по Шидаку"] = "%.2f сигма" % sigma
        except Exception:
            pass
        # Ожидаемое число случайных попаданий в окно порога при переборе M.
        # Окно двустороннее, поэтому ширина 2*eps.
        # expected_hits_analytic сам считает двустороннюю полосу +-eps по
        # фактически перечисленному семейству, поэтому eps передаётся как есть.
        hits = threshold.expected_hits_analytic(eps, rng)
        if hits is not None:
            numbers["ожидаемых попаданий"] = "%.3g" % hits
            if hits >= 1.0:
                reasons.append(
                    "ожидаемых случайных попаданий %.3g >= 1 при переборе %d: "
                    "попадание ожидается по случаю" % (hits, search_size))

    verdict = SKIP_VOID if reasons else RUN
    if verdict == RUN:
        reasons.append("различающий результат возможен: дорогое сито оправдано")
    return Decision(verdict, reasons, numbers)


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

    rng = family.STANDARD_RANGES
    vals = [v for v in family.enumerate_family(rng)
            if math.isfinite(v) and v > 0]
    check("семейство непусто", len(vals) > 1000)

    # --- цель, известная грубо: отсечение обязано сработать ------------------
    # X17: 16,66 +- 0,59 МэВ, относительная погрешность 3,5e-2 против локального
    # порога порядка 1e-4 — на четыре порядка грубее.
    d = decide(16.66, uncertainty=0.59, search_size=len(vals), values=vals,
               variant="standard", variant_reason="корпус объявляет этот перебор")
    check("грубая цель отсекается", d.verdict == SKIP_VOID)
    check("причина названа числами",
          any("ГРУБЕЕ" in r for r in d.reasons))

    # --- цель, известная точно: отсечения по точности быть не должно ---------
    # m_p/m_e = 1836,152673426(32): относительная погрешность 1,7e-11.
    d2 = decide(1836.152673426, uncertainty=3.2e-8, search_size=len(vals),
                values=vals, variant="standard", variant_reason="корпус объявляет этот перебор")
    check("точная цель не отсекается по точности",
          not any("ГРУБЕЕ" in r for r in d2.reasons))

    # --- неизвестная погрешность: сомнение в пользу дорогой проверки ---------
    d3 = decide(1836.152673426, uncertainty=None, values=vals,
                variant="standard", variant_reason="корпус объявляет этот перебор")
    check("без погрешности решение RUN", d3.verdict == RUN)
    check("отмечено, что погрешность неизвестна",
          d3.numbers["отн. погрешность цели"] == "неизвестна")

    # --- вырожденные входы ---------------------------------------------------
    check("нулевая цель даёт RUN",
          decide(0.0, values=vals, variant="standard", variant_reason="корпус объявляет этот перебор").verdict == RUN)
    check("нечисло даёт RUN",
          decide(float("nan"), values=vals, variant="standard", variant_reason="корпус объявляет этот перебор").verdict == RUN)

    # --- ПОДСТАВКА: порог, не зависящий от цели, обязан быть замечен ---------
    # Если локальный порог перестанет зависеть от значения цели, pre-filter
    # выродится в постоянную. Проверяем, что порог у далёких целей РАЗНЫЙ.
    e1 = threshold.local_threshold(16.66, rng, values=vals)
    e2 = threshold.local_threshold(1836.152673426, rng, values=vals)
    check("локальный порог зависит от цели", abs(e1 - e2) > 1e-12)

    # --- монотонность: чем точнее цель, тем меньше поводов отсекать ----------
    coarse = decide(16.66, uncertainty=0.59, values=vals, variant="standard", variant_reason="корпус объявляет этот перебор")
    fine = decide(16.66, uncertainty=1e-9, values=vals, variant="standard", variant_reason="корпус объявляет этот перебор")
    check("уточнение цели снимает отсечение",
          coarse.verdict == SKIP_VOID and fine.verdict == RUN)

    # --- ПОДСТАВКА: неоднородная пара обязана быть отвергнута ---------------
    mix = decide(878.4, uncertainty=0.5, search_size=123201, ranges=rng,
                 values=vals, variant="standard", variant_reason="корпус объявляет этот перебор")
    check("неоднородная пара отвергается",
          any("НЕОДНОРОДНА" in r for r in mix.reasons))
    # А согласованная пара на фактических диапазонах считается.
    from . import threshold as _t
    av = [v for v in family.enumerate_family(_t.ACTUAL_RANGES)
          if math.isfinite(v) and v > 0]
    homo = decide(878.4, uncertainty=0.5,
                  search_size=family.declared_size(_t.ACTUAL_RANGES),
                  ranges=_t.ACTUAL_RANGES, values=av, variant="actual", variant_reason="границы дают фактический перебор")
    check("согласованная пара считается",
          not any("НЕОДНОРОДНА" in r for r in homo.reasons))
    check("на фактическом переборе tau_n отсекается",
          homo.verdict == SKIP_VOID)

    # --- ПУНКТ 5 ПРИКАЗА: паспорт варианта ---------------------------------
    def raises(fn) -> bool:
        try:
            fn()
        except VariantChoiceError:
            return True
        except Exception:
            return False
        return False

    check("вызов без варианта запрещён",
          raises(lambda: decide(16.66, uncertainty=0.59, values=vals)))
    check("неизвестное имя варианта запрещено",
          raises(lambda: decide(16.66, values=vals, variant="выдуманный",
                                variant_reason="какая-то длинная причина")))
    check("пустая причина выбора запрещена",
          raises(lambda: decide(16.66, values=vals, variant="standard",
                                variant_reason="")))
    check("короткая причина выбора запрещена",
          raises(lambda: decide(16.66, values=vals, variant="standard",
                                variant_reason="так")))
    check("диапазоны против имени варианта запрещены",
          raises(lambda: decide(16.66, values=vals, ranges=_t.ACTUAL_RANGES,
                                variant="standard",
                                variant_reason="намеренно ложный паспорт")))
    sizes = variant_sizes()
    check("размер standard = 20412", sizes["standard"] == 20412)
    check("размер actual = 123201", sizes["actual"] == 123201)
    check("оба размера в паспорте решения",
          d.numbers["M вариант standard"] == 20412
          and d.numbers["M вариант actual"] == 123201)
    check("аргумент выбора попадает в паспорт",
          "корпус объявляет" in d.numbers["аргумент выбора"])
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        dest = os.path.join(td, "d.jsonl")
        log_decision(d, dest)
        log_decision(homo, dest)
        rows = [json.loads(x) for x in open(dest, encoding="utf-8")]
    check("журнал решений пишет обе записи", len(rows) == 2)
    check("в журнале сохранены оба размера и вариант",
          rows[1]["numbers"]["M вариант actual"] == "123201"
          and "actual" in rows[1]["numbers"]["выбранный вариант"])

    print()
    print("  итог: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(selftest())
