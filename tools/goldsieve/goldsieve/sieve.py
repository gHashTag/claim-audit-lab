"""Золотое сито — ядро.

Задача: не «проверить одно утверждение вручную», а прогнать любое численное
утверждение через фиксированный каскад сит и получить вердикт, который нельзя
получить случайно. Каждое сито — независимая причина НЕ поверить; утверждение
проходит только то, что прошло все применимые сита.

Вердикты (единственные допустимые):
  ПОДТВЕРЖДЕНО — все применимые сита PASS
  ОПРОВЕРГНУТО — есть сито, которое даёт FAIL по существу (расхождение с
                 вычисляемым эталоном при пройденных контролях)
  ВОПРОС       — не хватает данных/рецепта, чтобы решить (это НЕ находка)
  ПУСТО        — проверка вырождена: она прошла бы и на неверном ответе

Правило, ради которого всё написано: утверждение без вычисляемого эталона
никогда не становится ни ПОДТВЕРЖДЕНО, ни ОПРОВЕРГНУТО. Оно становится ВОПРОС.
"""

from __future__ import annotations

import json
import math
import time
import traceback
from dataclasses import dataclass, field, asdict
from typing import Callable, Iterable, Optional

PASS = "PASS"
FAIL = "FAIL"
OPEN = "OPEN"
VOID = "VOID"      # сито выродилось: прошло бы и на неверном ответе
SKIP = "SKIP"      # сито неприменимо к этому утверждению

CONFIRMED = "ПОДТВЕРЖДЕНО"
REFUTED = "ОПРОВЕРГНУТО"
QUESTION = "ВОПРОС"
EMPTY = "ПУСТО"


@dataclass
class Result:
    """Результат одного сита."""

    sieve: str
    status: str
    detail: str = ""
    numbers: dict = field(default_factory=dict)
    seconds: float = 0.0

    def line(self) -> str:
        mark = {PASS: "ok  ", FAIL: "FAIL", OPEN: "open", VOID: "VOID", SKIP: "skip"}[self.status]
        return "  %s %-28s %s" % (mark, self.sieve, self.detail)


@dataclass
class Claim:
    """Утверждение, поданное в сито.

    name       — как называется утверждение
    source     — откуда взято (файл:строка, документ, статья)
    stated     — заявленное значение (число или dict именованных чисел)
    reference  — callable() -> то же по форме, что stated. ВЫЧИСЛЯЕМЫЙ эталон.
                 None означает: эталона нет, рецепта нет. Тогда вердикт ВОПРОС.
    observed   — callable() -> измерение из данных (может быть None)
    tolerance  — относительная терпимость для сравнения (доля, не проценты)
    wrong      — callable() -> заведомо НЕВЕРНОЕ значение той же формы.
                 Нужно, чтобы проверить, что проверка вообще различает.
    null_model — callable() -> измерение на нулевой модели (шум, Пуассон,
                 перестановка). Сито требует, чтобы её отвергли.
    null_expect— что должна дать нулевая модель (форма как stated)
    resolutions— callable(param) -> значение; список параметров для сходимости
    estimators — dict имя -> callable(); разные оценки одной величины
    precision  — абсолютная погрешность входных данных (для бюджета точности)
    """

    name: str
    source: str = ""
    stated: object = None
    reference: Optional[Callable[[], object]] = None
    observed: Optional[Callable[[], object]] = None
    tolerance: float = 0.01
    wrong: Optional[Callable[[], object]] = None
    null_model: Optional[Callable[[], object]] = None
    null_expect: object = None
    null_kind: str = "negative"   # negative: контроль ОБЯЗАН отличаться от
                                  # эталона; positive: обязан его воспроизвести
    resolutions: Optional[Iterable] = None
    resolve: Optional[Callable[[object], object]] = None
    estimators: Optional[dict] = None
    precision: Optional[float] = None
    bins: Optional[Callable[[], list]] = None
    notes: str = ""


# --------------------------------------------------------------------------
# сравнение значений: скаляр или dict скаляров
# --------------------------------------------------------------------------

def _as_dict(v) -> dict:
    if isinstance(v, dict):
        return {k: float(x) for k, x in v.items()}
    return {"value": float(v)}


def rel_dev(a, b) -> dict:
    """Относительные отклонения a от b, по ключам."""
    da, db = _as_dict(a), _as_dict(b)
    out = {}
    for k in db:
        if k not in da:
            continue
        base = db[k]
        out[k] = (da[k] - base) / base if base != 0 else da[k] - base
    return out


def worst(dev: dict) -> tuple:
    if not dev:
        return ("", 0.0)
    k = max(dev, key=lambda k: abs(dev[k]))
    return (k, dev[k])


def fmt_dev(dev: dict) -> str:
    return ", ".join("%s %+.2f%%" % (k, 100.0 * v) for k, v in dev.items())


# --------------------------------------------------------------------------
# сита
# --------------------------------------------------------------------------

def sieve_regenerable(c: Claim) -> Result:
    """С1. Эталон вычисляем, а не процитирован.

    Единственное сито, которое может остановить всё остальное: если эталон —
    голое десятичное число из документа, сравнивать не с чем.
    """
    if c.reference is None:
        return Result("С1 регенерируемость", OPEN,
                      "эталон не вычисляем: рецепта нет, только значение")
    try:
        v = c.reference()
    except Exception as e:  # noqa: BLE001
        return Result("С1 регенерируемость", FAIL, "эталон падает: %r" % (e,))
    return Result("С1 регенерируемость", PASS, "эталон пересчитан",
                  numbers=_as_dict(v))


def sieve_agreement(c: Claim) -> Result:
    """С2. Заявленное совпадает с вычисленным эталоном."""
    if c.reference is None or c.stated is None:
        return Result("С2 заявленное=эталон", SKIP)
    dev = rel_dev(c.stated, c.reference())
    k, w = worst(dev)
    st = PASS if abs(w) <= c.tolerance else FAIL
    return Result("С2 заявленное=эталон", st, fmt_dev(dev), numbers=dev)


def sieve_observation(c: Claim) -> Result:
    """С3. Измерение из данных против вычисленного эталона."""
    if c.reference is None or c.observed is None:
        return Result("С3 данные=эталон", SKIP)
    dev = rel_dev(c.observed(), c.reference())
    k, w = worst(dev)
    st = PASS if abs(w) <= c.tolerance else FAIL
    return Result("С3 данные=эталон", st, fmt_dev(dev), numbers=dev)


def sieve_discriminates(c: Claim) -> Result:
    """С4. Подставка: на заведомо неверном значении проверка обязана упасть.

    Сито против «проверок», которые проходят всегда. Если неверное значение
    проходит с той же терпимостью — предыдущие сита ничего не значат.
    """
    if c.reference is None or c.wrong is None:
        return Result("С4 подставка ловится", SKIP)
    dev = rel_dev(c.wrong(), c.reference())
    k, w = worst(dev)
    if abs(w) <= c.tolerance:
        return Result("С4 подставка ловится", VOID,
                      "неверный ответ проходит: %s" % fmt_dev(dev), numbers=dev)
    return Result("С4 подставка ловится", PASS,
                  "неверный ответ отклонён: %s %+.2f%%" % (k, 100.0 * w))


def sieve_null_model(c: Claim) -> Result:
    """С5. Контроль прогоняется тем же конвейером.

    Два вида контроля, и вид обязан быть объявлен заранее:
      negative — модель без сигнала (шум, Пуассон, перестановка). Если она
                 воспроизводит эталон, проверка ничего не различает: VOID.
      positive — модель, которая ОБЯЗАНА дать эталон (генерическая по
                 построению). Если не даёт — сломан конвейер, а не данные: FAIL.
    """
    if c.null_model is None:
        return Result("С5 контроль", SKIP)
    got = c.null_model()
    if c.null_expect is not None:
        dev = rel_dev(got, c.null_expect)
        k, w = worst(dev)
        if abs(w) > max(0.1, 10.0 * c.tolerance):
            return Result("С5 контроль", FAIL,
                          "контроль сам не воспроизводится: %s" % fmt_dev(dev),
                          numbers=dev)
    if c.reference is None:
        return Result("С5 контроль", PASS, "контроль воспроизводится")
    dev = rel_dev(got, c.reference())
    k, w = worst(dev)
    if c.null_kind == "positive":
        if abs(w) <= max(c.tolerance, 0.01):
            return Result("С5 контроль", PASS,
                          "позитивный контроль даёт эталон: %s %+.2f%%" % (k, 100.0 * w))
        return Result("С5 контроль", FAIL,
                      "позитивный контроль НЕ даёт эталон, сломан конвейер: %s"
                      % fmt_dev(dev), numbers=dev)
    if abs(w) <= c.tolerance:
        return Result("С5 контроль", VOID,
                      "шум выглядит как сигнал: %s" % fmt_dev(dev), numbers=dev)
    return Result("С5 контроль", PASS,
                  "негативный контроль отличается от эталона: %s %+.2f%%" % (k, 100.0 * w))


def sieve_convergence(c: Claim) -> Result:
    """С6. Сходимость по разрешению: результат не должен зависеть от сетки."""
    if not c.resolutions or c.resolve is None:
        return Result("С6 сходимость", SKIP)
    vals = [( r, _as_dict(c.resolve(r)) ) for r in c.resolutions]
    keys = vals[0][1].keys()
    worst_swing = 0.0
    detail = []
    for k in keys:
        seq = [v[1][k] for v in vals]
        base = seq[-1]
        swing = max(abs(x - base) / (abs(base) or 1.0) for x in seq)
        worst_swing = max(worst_swing, swing)
        detail.append("%s разброс %.2e" % (k, swing))
    st = PASS if worst_swing <= c.tolerance / 10.0 else OPEN
    return Result("С6 сходимость", st, "; ".join(detail),
                  numbers={"swing": worst_swing})


def sieve_estimator_stability(c: Claim) -> Result:
    """С7. Устойчивость вывода к выбору оценки.

    Если разные законные оценки одной величины дают разные знаки вывода —
    утверждение не находка, а ВОПРОС. Ровно этим кончился дефицит Хинчина.
    """
    if not c.estimators or c.reference is None:
        return Result("С7 выбор оценки", SKIP)
    ref = c.reference()
    signs = set()
    detail = []
    for name, f in c.estimators.items():
        dev = rel_dev(f(), ref)
        k, w = worst(dev)
        detail.append("%s %+.2f%%" % (name, 100.0 * w))
        if abs(w) > c.tolerance:
            signs.add(1 if w > 0 else -1)
        else:
            signs.add(0)
    if len(signs) > 1:
        return Result("С7 выбор оценки", OPEN,
                      "вывод зависит от оценки: " + "; ".join(detail))
    return Result("С7 выбор оценки", PASS, "; ".join(detail))


def sieve_precision_budget(c: Claim) -> Result:
    """С8. Бюджет точности: заявленный эффект больше погрешности входа."""
    if c.precision is None or c.stated is None:
        return Result("С8 бюджет точности", SKIP)
    ref = c.reference() if c.reference is not None else None
    if ref is None:
        return Result("С8 бюджет точности", SKIP)
    dev = rel_dev(c.stated, ref)
    k, w = worst(dev)
    effect = abs(w)
    if effect <= c.precision:
        return Result("С8 бюджет точности", VOID,
                      "эффект %.2e не превышает погрешность входа %.2e"
                      % (effect, c.precision))
    return Result("С8 бюджет точности", PASS,
                  "эффект %.2e против погрешности %.2e" % (effect, c.precision))


def sieve_finite_size(c: Claim) -> Result:
    """С9. Конечный размер данных: известная систематика, а не эффект.

    Сито против обратной ошибки — объявить находкой то, что объясняется
    конечностью выборки. bins() возвращает [(x, значения)], где x -> 0 в
    пределе бесконечных данных (например 1/ln(gamma)). Линейная экстраполяция
    к x = 0 сравнивается с эталоном.

    Если экстраполяция садится на эталон хотя бы по части величин, но не по
    всем — статус OPEN: рычаг короткий, вывод не закрывается этими данными.
    """
    if c.bins is None or c.reference is None:
        return Result("С9 конечный размер", SKIP)
    pts = c.bins()
    if len(pts) < 3:
        return Result("С9 конечный размер", OPEN, "меньше трёх корзин")
    xs = [float(p[0]) for p in pts]
    ref = _as_dict(c.reference())
    lever = max(xs) / min(xs) if min(xs) > 0 else float("inf")
    agree, disagree, detail = [], [], []
    for k in ref:
        ys = [_as_dict(p[1])[k] for p in pts]
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        den = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
        y0 = my - slope * mx
        dev = (y0 - ref[k]) / ref[k] if ref[k] else y0 - ref[k]
        detail.append("%s -> %+.2f%%" % (k, 100.0 * dev))
        (agree if abs(dev) <= c.tolerance else disagree).append(k)
    msg = "экстраполяция к x=0 (рычаг %.1fx): %s" % (lever, "; ".join(detail))
    if agree and not disagree:
        return Result("С9 конечный размер", OPEN,
                      "расхождение объясняется конечным размером; " + msg)
    if agree and disagree:
        return Result("С9 конечный размер", OPEN,
                      "систематика объясняет %s, но не %s; "
                      % (",".join(agree), ",".join(disagree)) + msg)
    return Result("С9 конечный размер", PASS,
                  "конечным размером не объясняется; " + msg)


ALL_SIEVES = [
    sieve_regenerable,
    sieve_agreement,
    sieve_observation,
    sieve_discriminates,
    sieve_null_model,
    sieve_convergence,
    sieve_estimator_stability,
    sieve_precision_budget,
    sieve_finite_size,
]


# --------------------------------------------------------------------------
# прогон и вердикт
# --------------------------------------------------------------------------

@dataclass
class Report:
    claim: str
    source: str
    verdict: str
    results: list
    notes: str = ""

    def text(self) -> str:
        out = ["утверждение: %s" % self.claim]
        if self.source:
            out.append("источник:    %s" % self.source)
        out += [r.line() for r in self.results]
        out.append("вердикт:     %s" % self.verdict)
        if self.notes:
            out.append("примечание:  %s" % self.notes)
        return "\n".join(out)

    def to_json(self) -> str:
        d = {"claim": self.claim, "source": self.source, "verdict": self.verdict,
             "notes": self.notes, "results": [asdict(r) for r in self.results]}
        return json.dumps(d, ensure_ascii=False, indent=1)


def verdict_of(results: list) -> str:
    """Свод вердикта. Порядок правил важен и не переставляется."""
    st = {r.sieve: r.status for r in results}
    # 1. Вырожденная проверка бьёт всё: если подставка проходит или шум похож
    #    на сигнал, ни подтверждать, ни опровергать нечего.
    if any(v == VOID for v in st.values()):
        return EMPTY
    # 2. Нет вычисляемого эталона — вопрос, а не находка.
    if st.get("С1 регенерируемость") in (OPEN, FAIL):
        return QUESTION
    # 3. Вывод зависит от выбора оценки или не сошёлся по сетке — вопрос.
    if (st.get("С7 выбор оценки") == OPEN or st.get("С6 сходимость") == OPEN
            or st.get("С9 конечный размер") == OPEN):
        return QUESTION
    # 4. Расхождение по существу при живых контролях — опровержение.
    if st.get("С2 заявленное=эталон") == FAIL or st.get("С3 данные=эталон") == FAIL:
        return REFUTED
    if any(v == FAIL for v in st.values()):
        return QUESTION
    return CONFIRMED


def run(claim: Claim, sieves=None) -> Report:
    sieves = sieves or ALL_SIEVES
    results = []
    for s in sieves:
        t0 = time.time()
        try:
            r = s(claim)
        except Exception as e:  # noqa: BLE001
            r = Result(s.__name__, FAIL, "сито упало: %r" % (e,))
            r.detail += " | " + traceback.format_exc(limit=1).replace("\n", " ")
        r.seconds = time.time() - t0
        results.append(r)
    return Report(claim.name, claim.source, verdict_of(results), results, claim.notes)


def run_all(claims: Iterable[Claim]) -> list:
    return [run(c) for c in claims]
