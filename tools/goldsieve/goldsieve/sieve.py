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
import os
import re
import time
import traceback
import inspect
from dataclasses import dataclass, field, asdict
from typing import Callable, Iterable, Optional
from urllib.parse import urlsplit

from . import preconditions as _pre

PASS = "PASS"
FAIL = "FAIL"
OPEN = "OPEN"
VOID = "VOID"      # сито выродилось: прошло бы и на неверном ответе
SKIP = "SKIP"      # сито неприменимо к этому утверждению

CONFIRMED = "ПОДТВЕРЖДЕНО"
REFUTED = "ОПРОВЕРГНУТО"
QUESTION = "ВОПРОС"
EMPTY = "ПУСТО"

# Зарезервированные домены документации не являются независимым источником
# измерения. Раньше С15 принимало строку только по наличию ``https://`` и тем
# самым не различало рабочую ссылку и URL-заглушку.
_RESERVED_EXTERNAL_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "example.invalid",
}


@dataclass
class Result:
    """Результат одного сита."""

    sieve: str
    status: str
    detail: str = ""
    numbers: dict = field(default_factory=dict)
    seconds: float = 0.0
    # Машиночитаемая причина статуса. Нужна, чтобы «пропуск» и «провал» не
    # сливались в одну строку текста: свод вердикта читает код, а не текст.
    reason_code: str = ""
    # Пропуск, объявленный САМИМ ситом (а не автором задачи). С13 обязан
    # принимать такие пропуски: иначе честный отказ сита выглядит как
    # незаявленный skip и портит вердикт.
    auto_skip: bool = False

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
    sample: Optional[Callable[[], object]] = None      # сырые наблюдения
    statistics: Optional[dict] = None                  # имя -> f(массив) -> число
    reference_alt: Optional[Callable[[], object]] = None  # эталон другим методом
    alt_tolerance: Optional[Callable[[], float]] = None    # ВЫВОДИМАЯ погрешность
                                                          # второго метода
    inputs: Optional[list] = None                      # файлы данных для провенанса
    alpha: float = 0.05
    skip_reasons: Optional[dict] = None                # сито -> причина пропуска
    claim_kind: str = "value"          # value | prediction (формула про внешнюю величину)
    external_target: Optional[Callable[[], dict]] = None   # авторитетное измерение
    stated_target: Optional[Callable[[], float]] = None    # цель, как её пишет корпус
    # Единица измерения вычисляемой величины. Если она объявлена, С15
    # требует такую же единицу у внешней цели: численное совпадение в
    # смешанных единицах не является содержательной сверкой.
    measurement_unit: str = ""
    # Связь источника наблюдаемого с внешней целью. Пустая строка означает
    # независимый источник; значение same_as_observation обязано быть
    # объявлено ДО прогона, если внешний текст получен из того же наблюдаемого.
    # Нулевое отклонение при такой связи — вырожденная сверка, а не результат.
    external_source_relation: str = ""
    multiplicity: Optional[Callable[[], dict]] = None      # ожидаемые случайные попадания
    mdl: Optional[Callable[[], dict]] = None               # биты описания против бит совпадения
    declared_domain: Optional[Callable[[], list]] = None   # нарушения объявленных границ
    arithmetic: Optional[Callable[[], dict]] = None  # {"params":(n,k,m,p,q),
                                    # "rel_uncertainty": относит. погрешность}
                                    # для проверки достаточности арифметики
    meff: Optional[Callable[[], dict]] = None   # {"values": члены семейства,
                                    # "eps": полоса сравнения, "sigma":
                                    # наблюдённое отклонение в сигмах}
                                    # для С20: устойчив ли вывод к замене
                                    # числа попыток на ЭФФЕКТИВНОЕ
    algebraic: Optional[Callable[[], dict]] = None  # {"target","coeffs",
                                    # "has_pi","rel_deviation"} для С21
    search_size: Optional[int] = None  # сколько формул/гипотез реально перебрано;
                                       # из него ВЫВОДИТСЯ порог С15 по Шидаку
    # Длина блока для бутстрэпа зависимой выборки: None — i.i.d., "auto" —
    # вывести из автокорреляции, целое — задать вручную. Зависимость данных
    # обязана быть ИЗМЕРЕНА, а не предположена.
    bootstrap_block: object = None
    # ---- паспорт цели: заполняется ДО прогона и входит в отпечаток ----
    # Он существует, чтобы гейт полезности мог отказать в заведомо
    # неинформативной проверке ДО того, как она израсходует ресурс, и чтобы
    # отказ был воспроизводимым.
    claim_family: str = ""           # семейство утверждений (например formula_family)
    observable: str = ""             # что именно измеряется
    measurement_source: str = ""     # CODATA 2022, PDG 2024, корпус, …
    uncertainty_type: str = ""       # statistical | systematic | both | none
    expected_effect_sigma: Optional[float] = None   # ожидаемый эффект в сигмах
    resolution_sigma: Optional[float] = None        # разрешение метода в сигмах
    novelty_key: str = ""            # класс новизны: бюджет тратится на класс
    information_class: str = ""      # precision | novelty | discrimination |
                                     # independence
    purpose: str = ""                # tool_selftest | calibration | audit | …
    models: Optional[list] = None    # какие модели различает проверка
    independent_of: Optional[list] = None  # от каких прежних проверок независима
    precision_gain: Optional[float] = None  # во сколько раз точнее прежней
    out_of_sample: bool = False      # проверка на данных вне калибровки
    # Семантическая предпосылка (тик 48): независимы ли перебранные испытания.
    # true | false | unknown, пусто — не объявлено. Поправки Šidák и Бонферрони
    # опираются на РАЗНЫЕ предпосылки, и утверждение о пороге не имеет права
    # получить безусловное ПОДТВЕРЖДЕНО, пока предпосылка молчит: см.
    # goldsieve.preconditions.
    tests_independent: Optional[str] = None
    # Машинная причина для ВОПРОСА, когда проверка обнаружила отсутствие
    # обязательного рецепта сравнения. Значение вычисляется кейсом, а не
    # назначается по впечатлению после прогона.
    reason_code_hint: str = ""
    notes: str = ""

    def target(self):
        """Паспорт цели как объект гейта полезности.

        Импорт локальный: gate.py не должен зависеть от sieve.py, иначе
        гейт нельзя запускать до сборки каскада.
        """
        from .gate import Target
        return Target(
            name=self.name,
            claim_family=self.claim_family or "unspecified",
            observable=self.observable or self.name,
            measurement_source=self.measurement_source,
            uncertainty_type=self.uncertainty_type,
            expected_effect_sigma=self.expected_effect_sigma,
            resolution_sigma=self.resolution_sigma,
            novelty_key=self.novelty_key,
            information_class=self.information_class,
            purpose=self.purpose or "external_prediction",
            models=tuple(self.models or ()),
            independent_of=dict(self.independent_of or {}),
            precision_gain=self.precision_gain,
            tests_independent=(_pre.normalize(self.tests_independent)
                               or "not-declared"),
            external_source_relation=self.external_source_relation,
        )


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


def printed_tolerance(value) -> float:
    """Относительная терпимость, вытекающая из ЧИСЛА НАПЕЧАТАННЫХ ЦИФР.

    Корпус печатает число с конечным числом значащих цифр, значит истинное
    значение известно лишь с точностью до половины последнего разряда.
    Расхождение мельче этой величины не может быть находкой: оно
    ненаблюдаемо в тех данных, на которые ссылается утверждение.

    Возвращает наибольшую печатную терпимость по всем ключам: сравнение
    обязано быть не строже, чем самое грубо напечатанное число.
    """
    worst_tol = 0.0
    for v in _as_dict(value).values():
        if v == 0 or not math.isfinite(v):
            continue
        a = abs(v)
        # repr даёт кратчайшую запись, воспроизводящую double; для чисел,
        # выписанных из корпуса, она совпадает с напечатанной.
        txt = repr(float(v)).lstrip("-")
        if "e" in txt or "E" in txt:
            mant = txt.split("e")[0].split("E")[0]
        else:
            mant = txt
        digits = len(mant.replace(".", "").lstrip("0")) or 1
        # половина последнего значащего разряда, отнесённая к величине
        worst_tol = max(worst_tol, 0.5 * 10.0 ** (-(digits - 1)) *
                        10.0 ** (math.floor(math.log10(a))) / a)
    return worst_tol


def sieve_observation(c: Claim) -> Result:
    """С3. Измерение из данных против вычисленного эталона.

    Ремонт: терпимость больше не может быть строже печатной точности
    заявленного числа. Прежде задача с tolerance = 1e-12 против выписанного из
    корпуса «0.91» давала FAIL всегда — опровергалось не утверждение, а
    округление. Действующий порог берётся как максимум из объявленной
    терпимости и печатной, и сообщается в тексте.
    """
    if c.reference is None or c.observed is None:
        return Result("С3 данные=эталон", SKIP)
    dev = rel_dev(c.observed(), c.reference())
    # ВЫРОЖДЕНИЕ: наблюдение тождественно эталону ПО ПОСТРОЕНИЮ (тик 37:
    # observed возвращал reference()). Признак берётся из кода: равенство
    # ЗНАЧЕНИЙ бит в бит законно для целых величин и простых констант.
    if _is_same_computation(c.observed, c.reference):
        return Result("С3 данные=эталон", VOID,
                      "наблюдение целиком производно от эталона: сравнения "
                      "нет, проверка прошла бы при любых данных"
                      + _identity_explanation(c.observed, c.reference),
                      numbers=dev, reason_code="observation_is_reference")
    k, w = worst(dev)
    tol = c.tolerance
    note = ""
    if c.stated is not None:
        ptol = printed_tolerance(c.stated)
        if ptol > tol:
            tol = ptol
            note = (" | порог поднят до печатной точности заявленного числа "
                    "%.3g" % ptol)
    st = PASS if abs(w) <= tol else FAIL
    return Result("С3 данные=эталон", st, fmt_dev(dev) + note, numbers=dev)


def _is_same_computation(fn, ref) -> bool:
    """Функция ТОЖДЕСТВЕННА эталону по построению, а не по значению.

    Признак ищется в КОДЕ, а не в числах. Первая версия (луп 11) объявляла
    вырождением ровное нулевое расхождение значений — и перепрогон реестра
    немедленно показал ошибку: у целочисленных величин (число комбинаций
    20 412) и у простых констант (3^phi) независимый путь высокой точности
    ЗАКОННО совпадает с эталоном до последнего бита. Бит-в-бит равенство не
    доказывает тождества вычислений.

    Детектируется ровно то, что было в тике 37: наблюдение — тот же объект, что
    эталон, либо его тело состоит из единственного вызова эталона.
    """
    if fn is None or ref is None:
        return False
    if fn is ref:
        return True
    name = getattr(ref, "__name__", None)
    if not name:
        return False
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return False
    skip = ('"' * 3, "'" * 3, "def ", "@")
    body = []
    for line in src.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith(skip):
            continue
        body.append(line)
    # быстрый путь: тело из одного возврата вызова эталона
    if (len(body) == 1 and body[0].startswith("return")
            and (name + "(") in body[0]):
        return True
    # КОСВЕННАЯ тавтология: observed -> посредник -> ... -> reference.
    # Строчный признак её не видит, поэтому разбирается граф вызовов модуля.
    from . import proof
    from .identity import derives_from
    # Execution-proof (пункт 4 приказа тика 42): реальный маршрут сита обязан
    # оставлять машинный след. След НЕ влияет на вердикт: инструмент, у
    # которого измерение меняет результат, нельзя ни калибровать, ни сравнивать
    # с baseline.
    with proof.scope("След тавтологии: %s" % getattr(fn, "__name__", "?")) as pr:
        same, _ = derives_from(fn, ref)
    proof.record(pr)
    return same


def _identity_explanation(fn, ref) -> str:
    """Текст, по которому вырождение можно проверить руками."""
    from .identity import derives_from
    same, chain = derives_from(fn, ref)
    return (" | " + chain) if (same and chain) else ""


def sieve_discriminates(c: Claim) -> Result:
    """С4. Подставка: на заведомо неверном значении проверка обязана упасть.

    Сито против «проверок», которые проходят всегда. Поддерживается СПИСОК
    подставок: одна вручную придуманная мутация проверяет меньше, чем набор
    (перенято из мутационного тестирования). Различаются две причины провала,
    которые раньше сливались в один статус: плоха сама подставка (она
    неотличима от эталона при этой терпимости) — или вырождена проверка.
    """
    if c.reference is None or c.wrong is None:
        return Result("С4 подставка ловится", SKIP)
    wrongs = c.wrong if isinstance(c.wrong, (list, tuple)) else [c.wrong]
    ref = c.reference()
    bad, good = [], []
    for i, fn in enumerate(wrongs, 1):
        dev = rel_dev(fn(), ref)
        k, w = worst(dev)
        if abs(w) <= c.tolerance:
            bad.append("подставка %d неотличима от эталона (%s %+.2f%%) при "
                       "терпимости %.2f%%: неверный ответ проходит"
                       % (i, k, 100.0 * w, 100.0 * c.tolerance))
        else:
            good.append("подставка %d отклонена: %s %+.2f%%" % (i, k, 100.0 * w))
    if bad:
        return Result("С4 подставка ловится", VOID, "; ".join(bad + good))
    return Result("С4 подставка ловится", PASS, "; ".join(good))


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


def _z_table(c: Claim):
    """Отклонения наблюдения от эталона в единицах полуширины бутстрэп-интервала."""
    from . import stats as S
    x = c.sample()
    ref = _as_dict(c.reference())
    m = len(c.statistics)
    alpha = S.sidak_alpha(c.alpha, m)
    rows = {}
    for name, f in c.statistics.items():
        if name not in ref:
            continue
        point, lo, hi, rel = S.bootstrap_ci(x, f, alpha=alpha,
                                            block=c.bootstrap_block)
        half = (hi - lo) / 2.0
        rows[name] = {"point": point, "lo": lo, "hi": hi, "half": half,
                      "ref": ref[name], "rel": rel,
                      "z": S.z_of_deviation(point, ref[name], half)}
    return rows


def sieve_uncertainty(c: Claim) -> Result:
    """С10. Неопределённость измерения: значимо ли расхождение вообще.

    Терпимость больше не назначается рукой: ширина бутстрэп-интервала с
    поправкой Шидака на число сравниваемых статистик и есть масштаб, в котором
    измеряется расхождение. |z| <= 1 означает «данные совместимы с эталоном».
    """
    if c.sample is None or c.statistics is None or c.reference is None:
        return Result("С10 неопределённость", SKIP)
    rows = _z_table(c)
    # Найденный дефект: если ни одно имя статистики не совпало с ключами
    # эталона, таблица пуста и сито падало с ValueError на max(). Падение
    # маскировалось общим перехватом и превращалось в FAIL, то есть в
    # обвинение утверждению за ошибку инструмента. Теперь это OPEN с прямым
    # указанием несопоставленных имён.
    if not rows:
        ref_keys = ", ".join(sorted(_as_dict(c.reference()))) or "нет"
        stat_keys = ", ".join(sorted(c.statistics)) or "нет"
        return Result("С10 неопределённость", OPEN,
                      "имена статистик не сопоставлены с эталоном: "
                      "статистики [%s], эталон [%s]" % (stat_keys, ref_keys))
    details = []
    for k, v in rows.items():
        if v["ref"] == 0:
            # Нулевой эталон — валидная статистика, а не отсутствие
            # сравнения. Процентное отклонение от нуля не определено, поэтому
            # сообщаем абсолютную разность и сохраняем z-бал.
            details.append(
                "%s абсолютная разность %+.6g (полуширина %.6g, z %+.1f)"
                % (k, v["point"] - v["ref"], v["half"], v["z"])
            )
        else:
            details.append(
                "%s %+.2f%% (полуширина %.2f%%, z %+.1f)"
                % (k, 100.0 * (v["point"] - v["ref"]) / v["ref"],
                   100.0 * v["half"] / abs(v["point"]), v["z"])
            )
    det = "; ".join(details)
    # Вырожденная выборка: полуширина бутстрэп-интервала равна нулю, потому что
    # наблюдение детерминированное (одно значение, константа). Тогда z не
    # определён — прежняя версия выдавала z = +inf и FAIL, то есть обвиняла
    # утверждение в том, что разброс не определён В ПРИНЦИПЕ. Это дефект
    # инструмента: значимость здесь не проверяема, и правильный ответ —
    # объявленный пропуск с машинной причиной, а не провал.
    live = {k: v for k, v in rows.items()
            if v["half"] > 0 and math.isfinite(v["z"])}
    if not live:
        return Result("С10 неопределённость", SKIP,
                      "значимость не проверяема: выборка детерминированная, "
                      "полуширина интервала равна нулю (" + det + ")",
                      numbers={k: v["z"] for k, v in rows.items()},
                      reason_code="significance_untestable", auto_skip=True)
    rows = live
    zmax = max(abs(v["z"]) for v in rows.values())
    st = FAIL if zmax > 1.0 else PASS
    nums = {k: v["z"] for k, v in rows.items()}
    # Свод вердиктов имеет право смягчить опровержение по С10 только если С10
    # сравнивал ЗАЯВЛЕННУЮ величину. Признак выставляется здесь, потому что
    # только здесь известно, какие именно имена сопоставились: если ни одно из
    # них не встречается среди ключей заявленного, выборка относится к другой
    # величине, и смягчать опровержение ею нельзя.
    stated_keys = set(_as_dict(c.stated)) if c.stated is not None else set()
    nums["сопоставлено_с_заявленным"] = 1 if (
        not stated_keys or (set(rows) & stated_keys)) else 0
    return Result("С10 неопределённость", st, det, numbers=nums)


def sieve_too_good(c: Claim) -> Result:
    """С11. Слишком хорошо: согласие точнее, чем позволяет выборочный шум.

    Если измерение садится на теорию заметно точнее случайной погрешности сразу
    по нескольким статистикам, вероятнее, что число списано из теории, а не
    измерено. Возвращается верхняя граница подозрительности при независимости
    статистик; настоящие статистики скоррелированы, поэтому истинная
    вероятность БОЛЬШЕ приведённой — это ограничение, не оценка.
    """
    if c.sample is None or c.statistics is None or c.reference is None:
        return Result("С11 слишком хорошо", SKIP)
    rows = {k: v for k, v in _z_table(c).items()
            if v["half"] > 0 and math.isfinite(v["z"])}
    # Вырожденные строки исключаются по той же причине, что и в С10: у них z не
    # определён, а произведение с ними давало бы «подозрительно точное
    # согласие» из ничего.
    if len(rows) < 3:
        return Result("С11 слишком хорошо", SKIP,
                      "меньше трёх статистик с определённым разбросом")
    zs = [abs(v["z"]) for v in rows.values()]
    # z нормирован на полуширину 95%-интервала, то есть на 1.96 сигма
    p = 1.0
    for z in zs:
        p *= math.erf(1.96 * z / math.sqrt(2.0)) or 1e-16
    det = "медианное |z| %.2f, верхняя граница вероятности при независимости %.1e" \
          % (sorted(zs)[len(zs) // 2], p)
    if p < 1e-3:
        return Result("С11 слишком хорошо", FAIL,
                      "согласие подозрительно точное: " + det, numbers={"p": p})
    return Result("С11 слишком хорошо", PASS, det, numbers={"p": p})


def sieve_independent_method(c: Claim) -> Result:
    """С12. Эталон подтверждён вторым, независимым методом.

    С6 проверяет только сетку внутри одного алгоритма: ошибка в самой формуле
    пройдёт при любом разрешении. Здесь та же величина считается другим путём.
    """
    if c.reference is None or c.reference_alt is None:
        return Result("С12 независимый метод", SKIP)
    dev = rel_dev(c.reference_alt(), c.reference())
    # ВЫРОЖДЕНИЕ: «второй метод» — тот же вызов эталона. Проверяется КОД, а не
    # значение.
    if _is_same_computation(c.reference_alt, c.reference):
        return Result("С12 независимый метод", VOID,
                      "второй метод целиком производен от эталона: это тот же "
                      "путь, а не независимый"
                      + _identity_explanation(c.reference_alt, c.reference),
                      numbers=dev, reason_code="no_second_method")
    k, w = worst(dev)
    # Масштаб сравнения — собственная погрешность второго метода, а не
    # терпимость утверждения: у метода Монте-Карло она своя и её надо ВЫВЕСТИ.
    if c.alt_tolerance is not None:
        tol = c.alt_tolerance()
        note = " (порог %.2f%% — измеренный разброс второго метода)" % (100 * tol)
    else:
        tol = max(c.tolerance, 0.01)
        note = " (порог %.2f%% — терпимость утверждения; погрешность второго " \
               "метода не объявлена)" % (100 * tol)
    st = PASS if abs(w) <= tol else FAIL
    return Result("С12 независимый метод", st, fmt_dev(dev) + note, numbers=dev)


def declared_skips_check(claim: Claim, results: list) -> Result:
    """С13 гигиена: молчаливый пропуск сита не допускается.

    Пустое поле даёт skip, и контроль слабеет незаметно — так со временем умирает
    любая проверка. Каждый skip обязан быть объявлен в claim.skip_reasons.
    """
    reasons = claim.skip_reasons or {}
    # Пропуск, объявленный САМИМ ситом (auto_skip), уже несёт машинную
    # причину и не считается молчаливым: требовать от автора задачи объяснять
    # честный отказ инструмента значило бы наказывать за прозрачность.
    skipped = [r.sieve for r in results
               if r.status == SKIP and not getattr(r, "auto_skip", False)]
    auto = [r.sieve for r in results
            if r.status == SKIP and getattr(r, "auto_skip", False)]
    # ключ обязан точно совпадать с номером сита ("С10"), а не быть общей
    # отпиской "С", закрывающей все пропуски сразу
    keys = {k.strip() for k in reasons}
    undeclared = [s for s in skipped if s.split()[0] not in keys]
    if not skipped:
        return Result("С13 объявленные пропуски", PASS,
                      "пропусков нет" if not auto else
                      "все %d пропуска объявлены ситом: %s"
                      % (len(auto), ", ".join(auto)))
    if undeclared:
        return Result("С13 объявленные пропуски", FAIL,
                      "не объявлены причины пропуска: " + ", ".join(undeclared))
    return Result("С13 объявленные пропуски", PASS,
                  "все %d пропуска объявлены" % len(skipped))


def end_to_end_mutation(claim: Claim, base_sieves) -> Result:
    """С14 сквозная подставка: подменяем измерение неверным и требуем срыва.

    С4 лишь мерит расстояние между неверным ответом и эталоном. Здесь неверный
    ответ прогоняется через ВЕСЬ каскад: если вердикт остаётся ПОДТВЕРЖДЕНО,
    конвейер не различает измерение от подделки.
    """
    if claim.wrong is None or (claim.observed is None and claim.stated is None):
        return Result("С14 сквозная подставка", SKIP)
    import copy as _copy
    ws = claim.wrong if isinstance(claim.wrong, (list, tuple)) else [claim.wrong]
    outcomes = []
    for i, wrong_fn in enumerate(ws, 1):
        # С4 уже поддерживает несколько подставок; С14 должен прогонять через
        # весь каскад каждую из них, а не молча брать только первую.
        mut = _copy.copy(claim)
        w = wrong_fn()
        mut.stated = w
        if claim.observed is not None:
            mut.observed = lambda w=w: w
        mut.sample = None          # выборка не соответствует подделке, честно снимаем
        mut.statistics = None
        mut.bins = None
        mut.estimators = None
        mut.skip_reasons = {"С%d" % i: "мутационный прогон" for i in range(1, 19)}
        sub = [s(mut) for s in base_sieves]
        v = verdict_of(sub)
        outcomes.append("подставка %d: %s" % (i, v))
        if v == CONFIRMED:
            return Result("С14 сквозная подставка", VOID,
                          "подделка получила вердикт ПОДТВЕРЖДЕНО — каскад не различает; "
                          + "; ".join(outcomes))
    return Result("С14 сквозная подставка", PASS,
                  "; ".join(outcomes))


def sidak_local_alpha(alpha: float, m: int) -> float:
    """Локальный уровень по Шидаку: 1-(1-alpha)^(1/m).

    Доказанное тождество, а не эвристика: если m тестов независимы, то
    вероятность хотя бы одной ложной тревоги равна 1-(1-alpha_loc)^m, и
    приравнивание её к alpha даёт эту формулу. Для больших m она мягче
    Бонферрони (alpha/m), но остаётся консервативной при положительной
    зависимости тестов.
    """
    if m <= 1:
        return alpha
    return 1.0 - (1.0 - alpha) ** (1.0 / m)


def sigma_threshold(c: Claim):
    """Порог С15 в сигмах, ВЫВЕДЕННЫЙ из размера перебора.

    Порог «3 сигма» — соглашение, а не вывод, и это была честно записанная
    слабость версии 3. Правильный порог зависит от того, сколько гипотез
    перебрано: при переборе m формул локальный уровень надо ужать по Шидаку, и
    двусторонний порог в сигмах равен обратной функции нормального
    распределения от 1-alpha_loc/2.

    Если размер перебора не объявлен, порог остаётся 3 сигма, но в тексте
    результата это помечено как соглашение — чтобы вердикт нельзя было принять
    за выведенный.
    """
    m = c.search_size
    if m is None:
        return 3.0, "порог 3 сигма (СОГЛАШЕНИЕ: размер перебора не объявлен)"
    if int(m) < 1:
        raise ValueError("размер перебора не может быть меньше единицы")
    a_loc = sidak_local_alpha(c.alpha, int(m))
    try:
        from scipy.stats import norm
        z = float(norm.isf(a_loc / 2.0))
    except Exception:
        z = _isf_normal(a_loc / 2.0)
    return z, ("порог %.3g сигма ВЫВЕДЕН: перебор %d, alpha=%.3g, "
               "локальный alpha=%.3g по Шидаку" % (z, int(m), c.alpha, a_loc))


def _isf_normal(p: float) -> float:
    """Обратная функция хвоста нормального распределения без scipy.

    Двоичный поиск по erfc: p = erfc(z/sqrt(2))/2. Нужен только как запасной
    путь, поэтому важна не скорость, а то, что он не врёт: точность проверяется
    в самопроверке против scipy.
    """
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 0.5 * math.erfc(mid / math.sqrt(2.0)) > p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sieve_external_target(c: Claim) -> Result:
    """С15. Внешняя цель: проверка не должна быть тавтологией.

    Если утверждение по смыслу предсказательное («формула даёт величину X»),
    то сравнивать вычисление формулы с напечатанным рядом числом бессмысленно:
    такая проверка проходит при ЛЮБОМ значении формулы, потому что и то и другое
    получено из одного выражения. Содержательное сравнение — только с внешним
    измерением и его погрешностью.

    Сито делает две вещи: (1) требует внешнюю цель для предсказательных
    утверждений, иначе объявляет конвейер вырожденным; (2) меряет отклонение в
    единицах погрешности внешней величины, а не в процентах от неё.
    """
    name = "С15 внешняя цель"
    if c.claim_kind != "prediction":
        return Result(name, SKIP, "утверждение о самом числе, не о внешней величине")
    if c.external_target is None:
        return Result(name, VOID,
                      "предсказательное утверждение без внешнего измерения: "
                      "сверка формулы с напечатанным числом прошла бы при любом "
                      "значении формулы")
    tgt = c.external_target()
    # Защита от нового класса риска: нечисловая/нефинитная цель или цель без
    # проверяемого URL раньше могла пройти дальше как обычная цель. В частности,
    # float("nan") делал worst_sigma равным нулю и мог ложно дать PASS.
    if not isinstance(tgt, dict):
        return Result(name, VOID, "внешняя цель не является записью")
    missing = [key for key in ("value", "uncertainty", "source")
               if key not in tgt]
    if missing:
        return Result(name, VOID,
                      "внешняя цель неполна: нет " + ", ".join(missing))
    expected_unit = str(c.measurement_unit or "").strip()
    target_unit = str(tgt.get("unit") or "").strip()
    if expected_unit or target_unit:
        if not expected_unit or not target_unit:
            return Result(
                name,
                VOID,
                "единица измерения внешней цели не зафиксирована с обеих сторон",
                reason_code="external_unit_missing",
            )
        if expected_unit != target_unit:
            return Result(
                name,
                VOID,
                "единицы измерения не совпадают: %s против %s"
                % (expected_unit, target_unit),
                reason_code="external_unit_mismatch",
            )
    source = str(tgt["source"])
    if not (source.startswith("https://") or source.startswith("http://")
            or " https://" in source or " http://" in source):
        return Result(name, VOID,
                      "внешняя цель без URL независимого источника")
    # Наличие маркера URL ещё не означает наличие проверяемого источника:
    # example.* — зарезервированные домены документации. Поддерживаем
    # исторический формат «Название, https://...», извлекая все URL и
    # проверяя hostname.
    urls = re.findall(r"https?://[^\s]+", source)
    hosts = []
    for raw_url in urls:
        parsed = urlsplit(raw_url.rstrip(".,;:)]}"))
        if parsed.hostname:
            hosts.append(parsed.hostname.lower())
    if not hosts or all(host in _RESERVED_EXTERNAL_HOSTS for host in hosts):
        return Result(
            name,
            VOID,
            "URL внешней цели указывает на заглушку или не имеет проверяемого "
            "источника",
            reason_code="external_source_unverifiable",
        )
    try:
        value = float(tgt["value"])
        unc = float(tgt["uncertainty"])
    except (TypeError, ValueError, OverflowError):
        return Result(name, VOID,
                      "значение или погрешность внешней цели нечисловы")
    if not (math.isfinite(value) and math.isfinite(unc)):
        return Result(name, VOID,
                      "значение или погрешность внешней цели не конечны")
    if unc <= 0:
        return Result(name, VOID, "погрешность внешней величины не задана")
    nums = {}
    worst_sigma = 0.0
    if c.reference is not None:
        f = float(_as_dict(c.reference())["value"]) if isinstance(c.reference(), dict) \
            else float(c.reference())
        nums["формула"] = f
        nums["сигм_формула"] = (f - value) / unc
        worst_sigma = max(worst_sigma, abs(nums["сигм_формула"]))
    if c.stated_target is not None:
        s = float(c.stated_target())
        nums["цель_в_корпусе"] = s
        nums["сигм_цель"] = (s - value) / unc
        worst_sigma = max(worst_sigma, abs(nums["сигм_цель"]))
    nums["внешнее"] = value
    nums["погрешность"] = unc
    det = "внешнее %.6g +- %.3g; " % (value, unc) + "; ".join(
        "%s %.4g" % (k, v) for k, v in nums.items() if k.startswith("сигм"))
    # Нулевое отклонение — действительное согласие, а не отсутствие
    # сравнения. Проверять нужно наличие ключей, иначе точное попадание
    # ошибочно превращается в OPEN.
    if "сигм_формула" not in nums and "сигм_цель" not in nums:
        return Result(name, OPEN, "нечего сравнивать с внешней величиной")
    # Если корпусное наблюдаемое и внешняя цель объявлены одним источником,
    # точное совпадение не измеряет предсказательную силу: оно прошло бы при
    # любом значении формулы. Отдельный reason-code не позволяет смешать этот
    # дефект выбора цели с обычным совпадением или с отсутствием URL.
    if (c.external_source_relation == "same_as_observation"
            and nums.get("сигм_цель") == 0.0):
        return Result(
            name,
            VOID,
            det + " | корпусное наблюдаемое и внешняя цель имеют один источник",
            numbers=nums,
            reason_code="external_source_degenerate",
        )
    thr, thr_note = sigma_threshold(c)
    nums["порог_сигм"] = thr
    st = PASS if worst_sigma <= thr else FAIL
    return Result(name, st, det + " | " + thr_note, numbers=nums)


def sieve_multiplicity(c: Claim) -> Result:
    """С16. Подгонка под ответ: сколько попаданий даёт СЛУЧАЙ.

    Если формулу выбирают перебором из M кандидатов, то попадание в цель с
    точностью eps ожидается случайно с вероятностью p_glob = 1-(1-p_loc)^M.
    При ожидаемом числе попаданий E[h] >= 1 совпадение перестаёт быть
    свидетельством: контроль показывает, что так же хорошо накрывается и
    произвольная цель. Это эффект look-elsewhere, перенесённый на перебор
    формул.
    """
    name = "С16 подгонка под ответ"
    if c.multiplicity is None:
        return Result(name, SKIP)
    m = c.multiplicity()
    exp_hits = float(m["expected_hits"])
    p_glob = float(m.get("p_global", float("nan")))
    frac = m.get("fraction_random_targets_hit")
    nums = {"ожидаемых_попаданий": exp_hits, "p_глоб": p_glob}
    if frac is not None:
        nums["доля_случайных_целей_с_попаданием"] = float(frac)
    # Молчаливый nan в выводе — след необъявленного ключа в задаче, и он
    # читается как настоящее число. Отсутствие величины называется отсутствием.
    det = ("ожидаемых случайных попаданий %.3g; p_глоб %s"
           % (exp_hits, ("%.3g" % p_glob) if p_glob == p_glob
              else "НЕ ЗАДАН (ключ p_global отсутствует)"))
    if frac is not None:
        det += "; случайная цель накрывается в %.1f%% случаев" % (100.0 * float(frac))
    if exp_hits >= 1.0 or (frac is not None and float(frac) >= 0.5):
        return Result(name, VOID, det + " | попадание ожидается случайно",
                      numbers=nums)
    if p_glob == p_glob and p_glob > c.alpha:
        return Result(name, FAIL, det + " | не проходит порог alpha=%.3g" % c.alpha,
                      numbers=nums)
    return Result(name, PASS, det, numbers=nums)


def sieve_description_length(c: Claim) -> Result:
    """С17. Описание короче данных: критерий содержательности по MDL.

    Совпадение с точностью eps несёт log2(1/(2 eps)) бит, но не больше, чем
    позволяет собственная погрешность цели. Указание одного члена семейства из M
    стоит log2(M) бит. Если описание стоит дороже, чем объясняет, никакого
    сжатия не произошло — «закон» не короче самого числа (Rissanen, MDL).
    """
    name = "С17 описание короче данных"
    if c.mdl is None:
        return Result(name, SKIP)
    m = c.mdl()
    db = float(m["description_bits"])
    mb = float(m["match_bits"])
    nums = {"бит_описания": db, "бит_совпадения": mb, "выигрыш": mb - db}
    det = "описание %.2f бит против совпадения %.2f бит (выигрыш %.2f)" % (
        db, mb, mb - db)
    if mb <= db:
        return Result(name, FAIL, det + " | сжатия нет", numbers=nums)
    return Result(name, PASS, det, numbers=nums)


def sieve_declared_domain(c: Claim) -> Result:
    """С18. Объявленная область: перебор шире, чем признано.

    Если фактически использованные параметры выходят за объявленные границы
    перебора, то заявленный размер пространства занижен, а вместе с ним занижена
    и поправка на множественность. Сито ловит расхождение между объявленным и
    использованным.
    """
    name = "С18 объявленная область"
    if c.declared_domain is None:
        return Result(name, SKIP)
    bad = c.declared_domain()
    if not bad:
        return Result(name, PASS, "все параметры внутри объявленных границ")
    head = "; ".join("%s" % (b,) for b in bad[:4])
    return Result(name, FAIL, "выход за объявленные границы: %s%s" % (
        head, " ..." if len(bad) > 4 else ""), numbers={"нарушений": len(bad)})


def sieve_arithmetic(c: Claim) -> Result:
    """С19. Достаточность арифметики: не подменяет ли округление вывод.

    Вердикт, полученный на double, законен лишь тогда, когда ошибка машинной
    арифметики на порядки меньше погрешности, с которой сравнивается результат.
    Сито не верит в это, а проверяет: то же значение пересчитывается на 50
    знаках, и разность сопоставляется с погрешностью сравнения.

    FAIL означает не «формула неверна», а «вердикт по этому утверждению
    выносить нельзя, пока не поднята точность» — поэтому он ведёт к ВОПРОСУ, а
    не к опровержению.
    """
    name = "С19 достаточность арифметики"
    if c.arithmetic is None:
        return Result(name, SKIP)
    spec = c.arithmetic()
    params = tuple(spec["params"])
    unc = float(spec["rel_uncertainty"])
    try:
        from .exact import arithmetic_is_sufficient
        ok, err, limit = arithmetic_is_sufficient(params, unc)
    except RuntimeError as e:
        return Result(name, OPEN, "проверить нечем: %s" % e)
    det = ("ошибка арифметики %.2e; предел %.2e (сотая доля погрешности "
           "сравнения %.2e)" % (err, limit, unc))
    nums = {"ошибка_арифметики": err, "предел": limit, "погрешность": unc}
    if ok:
        return Result(name, PASS, det, numbers=nums)
    return Result(name, FAIL, det + " | точности не хватает для вывода",
                  numbers=nums)


def sieve_effective_multiplicity(c: Claim) -> Result:
    """С20. Эффективное число попыток: устойчив ли вывод к зависимости членов.

    Поправка Шидака до сих пор считалась при ПРЕДПОЛОЖЕНИИ независимости
    перебранных формул. Предположение неверно: члены семейства лежат на
    логарифмической решётке, и два члена, отстоящие меньше чем на полосу
    сравнения, дают один и тот же вердикт — то есть один тест, а не два.

    Сито не заменяет один порог другим «правильным», а проверяет УСТОЙЧИВОСТЬ:
    если вывод (превышает ли отклонение порог) одинаков и при полном числе
    попыток, и при эффективном, ось множественности вывод не определяет. Если
    вывод меняется — он держится на предположении о независимости, и это
    ВОПРОС, а не находка. Логика та же, что у С7 для выбора оценки.

    M_eff считается двумя независимыми путями (goldsieve/meff.py): разрешающая
    кластеризация в духе trials factor Гросса-Витальса и собственные значения
    корреляционной матрицы по Ли-Цзи 2005.
    """
    name = "С20 эффективное число попыток"
    if c.meff is None:
        return Result(name, SKIP)
    spec = c.meff()
    try:
        from .meff import meff_from_family, sidak_sigma
    except Exception as e:  # noqa: BLE001
        return Result(name, OPEN, "проверить нечем: %r" % (e,))
    values = list(spec["values"])
    eps = float(spec["eps"])
    sigma = abs(float(spec["sigma"]))
    m_full = int(spec.get("search_size") or c.search_size or len(values))
    info = meff_from_family(values, eps)
    ratio = info["independence_ratio"]
    if ratio <= 0.0:
        return Result(name, OPEN, "эффективное число попыток не оценивается: "
                                  "пустое семейство")
    m_eff = max(1.0, ratio * m_full)
    thr_full = sidak_sigma(m_full, c.alpha)
    thr_eff = sidak_sigma(m_eff, c.alpha)
    nums = {"M": float(m_full), "M_eff": m_eff,
            "доля_независимых": ratio,
            "порог_M_сигма": thr_full, "порог_Meff_сигма": thr_eff,
            "отклонение_сигма": sigma}
    if info.get("M_eff_eigen") is not None:
        nums["M_eff_собств_подвыборка"] = info["M_eff_eigen"]
        nums["подвыборка"] = float(info["M_eff_eigen_of"])
    det = ("M=%d, M_eff=%.4g (доля независимых %.3g при полосе %.2g); "
           "порог %.3g сигма против %.3g сигма; отклонение %.3g сигма"
           % (m_full, m_eff, ratio, eps, thr_full, thr_eff, sigma))
    if (sigma > thr_full) == (sigma > thr_eff):
        return Result(name, PASS, det + " | вывод не зависит от того, считать "
                                        "попытки полными или эффективными",
                      numbers=nums)
    return Result(name, FAIL, det + " | вывод ДЕРЖИТСЯ на предположении о "
                                    "независимости членов семейства",
                  numbers=nums)


def sieve_algebraic_explanation(c: Claim) -> Result:
    """С21. Алгебраическая объяснимость: не бесплатно ли совпадение по теории.

    Близость члена семейства к цели — это малость линейной формы в логарифмах.
    Два инструмента:

    1. PSLQ (Фергюсон-Бейли-Арно): ищет целочисленное соотношение между
       логарифмом цели и логарифмами базиса. Если соотношение находится при
       МАЛЫХ коэффициентах, цель воспроизводится семейством почти точно, и
       совпадение получено бесплатно — VOID, то есть ПУСТО.
    2. Граница бейкеровского типа (Бейкер-Вюстхольц, усиление Матвеева 2000):
       теоретический потолок случайной близости.

    Область применимости объявляется, а не замалчивается: log pi не является
    логарифмом алгебраического числа, и оценок бейкеровского типа для форм с
    log pi не доказано. При m != 0 сито даёт OPEN с этой причиной. Ожидаемый и
    честный результат для остальных случаев: граница астрономически слаба и
    наблюдаемую близость НЕ запрещает — значит третья ось не заменяет ось
    перебора, а дополняет её.
    """
    name = "С21 алгебраическая объяснимость"
    if c.algebraic is None:
        return Result(name, SKIP)
    spec = c.algebraic()
    try:
        from .algebraic import analyse
    except Exception as e:  # noqa: BLE001
        return Result(name, OPEN, "проверить нечем: %r" % (e,))
    res = analyse(spec["target"], spec.get("coeffs", (1,)),
                  bool(spec.get("has_pi", True)),
                  float(spec["rel_deviation"]),
                  max_coeff=int(spec.get("max_coeff", 12)))
    limit = int(spec.get("free_coeff_limit", 6))
    nums = {}
    if res.get("pslq_max_coeff"):
        nums["макс_коэффициент"] = float(res["pslq_max_coeff"])
    if res.get("log_bound") is not None:
        nums["log_граница"] = res["log_bound"]
        nums["log_наблюдение"] = res["log_observed"]
    rel = res.get("pslq_relation")
    if rel and res.get("pslq_max_coeff", 999) <= limit:
        return Result(name, VOID,
                      "цель воспроизводится семейством при коэффициентах не "
                      "больше %d (%s): совпадение получено бесплатно"
                      % (limit, rel), numbers=nums)
    if not res.get("bound_applicable", False):
        return Result(name, OPEN, res.get("bound_reason", "граница неприменима"),
                      numbers=nums)
    if res.get("bound_binding"):
        return Result(name, FAIL,
                      "наблюдённая близость меньше теоретического минимума "
                      "(log %.3g против границы %.3g): либо цель лежит в "
                      "семействе точно, либо не хватает точности"
                      % (res["log_observed"], res["log_bound"]), numbers=nums)
    return Result(name, PASS,
                  "алгебраического объяснения нет: соотношение при малых "
                  "коэффициентах не найдено, граница бейкеровского типа "
                  "(log %.3g) слабее наблюдения (log %.3g) и близость не "
                  "запрещает" % (res["log_bound"], res["log_observed"]),
                  numbers=nums)


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
    sieve_uncertainty,
    sieve_too_good,
    sieve_independent_method,
    sieve_external_target,
    sieve_multiplicity,
    sieve_description_length,
    sieve_declared_domain,
    sieve_arithmetic,
    sieve_effective_multiplicity,
    sieve_algebraic_explanation,
]

def sieve_numbers() -> list:
    """Номера всех сит, взятые из ИХ ЖЕ вердиктов, а не из счётчика.

    Первая попытка исправления брала len(ALL_SIEVES) = 17, но номера сит идут
    до 19 (нумерация не непрерывна: С13 и С14 — мета-сита, стоящие отдельно), и
    С18 с С19 снова остались необъявленными. Счётчик длины — тот же класс
    ошибки, что и константа: он предполагает, что номера плотно заполняют
    диапазон. Поэтому номера собираются с пустого прогона.
    """
    empty = Claim(name="calibration")
    nums = []
    for s in ALL_SIEVES:
        try:
            title = s(empty).sieve
        except Exception:
            continue
        head = title.split()[0]
        if head.startswith("С") and head[1:].isdigit():
            nums.append(int(head[1:]))
    return sorted(set(nums))


N_SIEVES = len(ALL_SIEVES)     # оставлено для совместимости, НЕ использовать
                               # для перечисления номеров сит


# --------------------------------------------------------------------------
# прогон и вердикт
# --------------------------------------------------------------------------

def provenance(claim: Claim) -> dict:
    """Провенанс: чем именно получен вердикт. Без этого он невоспроизводим."""
    import hashlib
    import platform
    import subprocess
    d = {"python": platform.python_version()}
    try:
        import numpy
        d["numpy"] = numpy.__version__
    except Exception:  # noqa: BLE001
        pass
    try:
        import scipy
        d["scipy"] = scipy.__version__
    except Exception:  # noqa: BLE001
        pass
    files = {}
    for path in (claim.inputs or []):
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            files[path] = h.hexdigest()[:16]
            try:
                out = subprocess.run(["git", "-C", os.path.dirname(path) or ".",
                                      "rev-parse", "--short", "HEAD"],
                                     capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", timeout=10)
                if out.returncode == 0:
                    files[path + " @commit"] = out.stdout.strip()
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            files[path] = "недоступен: %r" % (e,)
    if files:
        d["inputs"] = files
    # Отпечаток рецепта: если терпимость, подставку или эталон подкрутили после
    # того, как результат стал известен, отпечаток изменится. Машинный аналог
    # пре-регистрации (перенято из Registered Reports).
    import inspect
    parts = ["tol=%r" % claim.tolerance, "alpha=%r" % claim.alpha]
    fns = [(nm, getattr(claim, nm, None)) for nm in
           ("reference", "reference_alt", "observed", "null_model", "alt_tolerance")]
    ws = claim.wrong if isinstance(claim.wrong, (list, tuple)) else [claim.wrong]
    fns += [("wrong", f) for f in ws]
    for nm, fn in fns:
        if callable(fn):
            try:
                parts.append(nm + ":" + inspect.getsource(fn))
            except (OSError, TypeError):
                parts.append(nm + ":<источник недоступен>")
    d["отпечаток рецепта"] = hashlib.sha256(
        "\n".join(parts).encode("utf-8")).hexdigest()[:16]
    d["alpha"] = claim.alpha
    d["tolerance"] = claim.tolerance
    # Паспорт цели входит в провенанс: порог гейта, бюджет и ключ новизны
    # меняют решение о том, стоит ли вообще запускать проверку, а значит
    # обязаны быть зафиксированы до того, как результат стал известен.
    if claim.novelty_key or claim.claim_family:
        try:
            d["паспорт цели"] = claim.target().hash()
            d["ключ новизны"] = claim.novelty_key
        except Exception:  # noqa: BLE001
            pass
    return d


@dataclass
class Report:
    claim: str
    source: str
    verdict: str
    results: list
    notes: str = ""
    prov: dict = field(default_factory=dict)
    reason_code: str = ""
    action: str = ""
    aggregatable: bool = True

    def text(self) -> str:
        out = ["утверждение: %s" % self.claim]
        if self.source:
            out.append("источник:    %s" % self.source)
        out += [r.line() for r in self.results]
        out.append("вердикт:     %s" % self.verdict)
        if self.reason_code:
            out.append("подтип:      %s" % self.reason_code)
        if self.action:
            out.append("действие:    %s" % self.action)
        if not self.aggregatable:
            out.append("свод:        не агрегируется в итоговый счётчик")
        if self.prov:
            flat = []
            for k, v in self.prov.items():
                if isinstance(v, dict):
                    flat += ["%s=%s" % (kk, vv) for kk, vv in v.items()]
                else:
                    flat.append("%s=%s" % (k, v))
            out.append("провенанс:   " + "; ".join(flat))
        if self.notes:
            out.append("примечание:  %s" % self.notes)
        return "\n".join(out)

    def to_json(self) -> str:
        d = {"claim": self.claim, "source": self.source, "verdict": self.verdict,
             "notes": self.notes, "provenance": self.prov,
             "results": [asdict(r) for r in self.results]}
        return json.dumps(d, ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------
# машиночитаемая причина вердикта и предписанное действие
# --------------------------------------------------------------------------

ACTION = {
    "independence_unknown":
        "доказано тождество, не его применимость: измерить зависимость "
        "испытаний (m_eff) либо перейти на поправку, не требующую "
        "независимости (Бонферрони)",
    "independence_undeclared":
        "объявить в паспорте цели поле tests_independent: молчание о "
        "предпосылке не считается её выполнением",
    "independence_violated":
        "поправка Šidák неприменима к зависимым испытаниям: использовать "
        "Бонферрони или порог по эффективному числу испытаний",
    "observation_is_reference":
        "переписать наблюдение так, чтобы оно получалось иным путём, чем "
        "эталон; сравнение величины с собой вердикта не даёт",
    "resolution_limited":
        "не запускать похожие цели до появления более точных данных",
    "multiplicity_limited":
        "требовать предрегистрацию пространства поиска либо выигрыш по MDL",
    "model_nonidentifiable":
        "требовать альтернативные модели и независимые наблюдаемые",
    "systematics_unmodeled":
        "не агрегировать в итоговый счётчик: учтена только случайная "
        "неопределённость",
    "significance_untestable":
        "усилить выборку либо объявить внешнюю погрешность: разброс не определён",
    "out_of_sample":
        "отметить как предсказательный успех: проверка шла на данных, не "
        "участвовавших в калибровке",
    "no_computable_reference":
        "восстановить рецепт эталона: сравнивать пока не с чем",
    "metrics_incommensurable":
        "зафиксировать общую шкалу, токенизацию, усреднение и стадию: "
        "текущие метрики несопоставимы",
    "external_source_unverifiable":
        "заменить URL-заглушку или недействительный адрес на проверяемый "
        "первичный источник внешнего измерения",
    "external_source_degenerate":
        "развести источник корпусного наблюдаемого и внешней цели; нулевое "
        "отклонение одного источника не является измерением",
    "external_unit_missing":
        "зафиксировать единицу вычисляемой величины и внешней цели до "
        "сравнения",
    "external_unit_mismatch":
        "привести формулу и внешнее измерение к одной единице либо остановить "
        "сверку",
    "estimator_dependent":
        "зафиксировать выбор оценки или сетки до прогона",
    "arithmetic_insufficient":
        "повысить разрядность вычисления до запаса 100x",
    "algebraically_explainable":
        "совпадение объясняется алгебраически: требовать цели вне решётки",
    "observation_mismatch":
        "расхождение с вычисляемым эталоном: исправить корпус",
    "external_mismatch":
        "формула противоречит внешнему измерению: исправить корпус",
    "domain_understated":
        "занижен размер перебора: пересчитать поправку на множественность",
    "too_good":
        "согласие точнее шума: проверить, не списано ли число из теории",
    "no_second_method":
        "подтвердить эталон принципиально иным путём",
    "no_compression":
        "формула не сжимает данные: требовать выигрыш по MDL",
    "meff_unstable":
        "вывод держится на числе попыток: пересчитать эффективное число",
    "pipeline_broken":
        "починить конвейер: контроль не воспроизводит эталон",
    "control_broken":
        "сломан КОНТРОЛЬ, а не утверждение: починить позитивный контроль и "
        "перепрогнать (урок лупов 5 и 10)",
    "input_precision_limited":
        "заявленный эффект не превышает погрешность входа: уточнить входные "
        "данные или переопределить эффект",
    "confirmed":
        "записать в реестр как подтверждённое",
    "unclassified":
        "подтип не определён: разобрать вручную и добавить правило",
}

# Подтипы, которые НЕЛЬЗЯ складывать в общий счётчик находок: вердикт получен
# при неполной модели неопределённости либо при вырожденной проверке.
# Подтипы, при которых вердикт НЕ идёт в счётчик находок: он говорит о
# состоянии проверки, а не об утверждении.
NON_AGGREGATABLE = (
    # Необъявленная или непроверенная предпосылка: такой вердикт не имеет
    # права попасть в сводный счётчик подтверждённых.
    "independence_unknown",
    "independence_undeclared",
    "independence_violated",
    "observation_is_reference",
    "systematics_unmodeled",
    "significance_untestable",
    "unclassified",
    "control_broken",
    "input_precision_limited",
    "metrics_incommensurable",
    "external_source_unverifiable",
    "external_source_degenerate",
    "external_unit_missing",
    "external_unit_mismatch",
)


def reason_of(results: list, verdict: str, claim: Optional[Claim] = None) -> str:
    """Машиночитаемый подтип причины вердикта. Порядок правил важен."""
    st = {r.sieve: r.status for r in results}
    by = {r.sieve: r for r in results}

    if verdict == EMPTY:
        # Избыток степеней свободы семейства: совпадение куплено перебором.
        if st.get("С16 подгонка под ответ") == VOID:
            return "multiplicity_limited"
        if st.get("С21 алгебраическая объяснимость") == VOID:
            return "algebraically_explainable"
        # Контроль или сквозная подставка не различает модель от шума.
        if st.get("С5 контроль") == VOID or st.get("С14 сквозная подставка") == VOID:
            return "model_nonidentifiable"
        # Подставка неотличима от эталона, или внешняя цель слишком груба:
        # это про разрешение, а не про множественность.
        if st.get("С4 подставка ловится") == VOID or \
                st.get("С15 внешняя цель") == VOID:
            external = by.get("С15 внешняя цель")
            if external is not None and external.reason_code:
                return external.reason_code
            return "resolution_limited"
        # Сломанный позитивный контроль — дефект ПРОВЕРКИ, не утверждения.
        if st.get("С5 контроль") == FAIL:
            return "control_broken"
        # Заявленный эффект утонул в погрешности входа.
        if st.get("С8 бюджет точности") == VOID:
            return "input_precision_limited"
        # Сравнение величины с самой собой: наблюдение тождественно эталону
        # либо «второй метод» — та же арифметика. Дефект ПОСТРОЕНИЯ проверки,
        # а не утверждения. Введено после разбора тика 37 (луп 11).
        if st.get("С3 данные=эталон") == VOID:
            return "observation_is_reference"
        if st.get("С12 независимый метод") == VOID:
            return "no_second_method"
        return "unclassified"

    if verdict == REFUTED:
        if st.get("С15 внешняя цель") == FAIL:
            return "external_mismatch"
        if st.get("С18 объявленная область") == FAIL:
            return "domain_understated"
        return "observation_mismatch"

    if verdict == QUESTION:
        if claim is not None and claim.reason_code_hint in ACTION:
            return claim.reason_code_hint
        if st.get("С1 регенерируемость") in (OPEN, FAIL):
            return "no_computable_reference"
        if st.get("С5 контроль") == FAIL:
            return "pipeline_broken"
        if st.get("С19 достаточность арифметики") == FAIL:
            return "arithmetic_insufficient"
        if st.get("С17 описание короче данных") == FAIL:
            return "no_compression"
        if st.get("С20 эффективное число попыток") == FAIL:
            return "meff_unstable"
        if st.get("С20 эффективное число попыток") == OPEN:
            return "meff_unstable"
        if st.get("С12 независимый метод") == FAIL:
            return "no_second_method"
        if st.get("С11 слишком хорошо") == FAIL:
            return "too_good"
        if (st.get("С7 выбор оценки") == OPEN or st.get("С6 сходимость") == OPEN
                or st.get("С9 конечный размер") == OPEN):
            return "estimator_dependent"
        c10 = by.get("С10 неопределённость")
        if c10 is not None and c10.reason_code == "significance_untestable":
            return "significance_untestable"
        if claim is not None and claim.claim_kind == "prediction" and \
                claim.uncertainty_type == "statistical":
            return "systematics_unmodeled"
        return "unclassified"

    # ПОДТВЕРЖДЕНО: предсказательный успех вне калибровки сильнее обычного.
    if claim is not None and getattr(claim, "out_of_sample", False):
        return "out_of_sample"
    return "confirmed"


def verdict_of(results: list) -> str:
    """Свод вердикта. Порядок правил важен и не переставляется."""
    st = {r.sieve: r.status for r in results}
    # 1. Вырожденная проверка бьёт всё: если подставка проходит или шум похож
    #    на сигнал, ни подтверждать, ни опровергать нечего.
    #
    # Исключение НАЙДЕНО ПЕРЕПРОГОНОМ (луп 11). Вырождение С3 или С12 означает
    # ровно одно: сравнение с эталоном ВНУТРИ корпуса ничего не даёт. Оно не
    # касается опровержения по ВНЕШНЕЙ цели (С15) или по заниженной области
    # перебора (С18): там масштаб задан погрешностью внешнего измерения либо
    # прямым подсчётом, а не сравнением величины с собой. Без исключения
    # опровержение формулы m_p/m_e с промахом 6,3e7 сигм понижалось до ПУСТО
    # из-за того, что в том же кейсе observed вызывал reference().
    #
    # Исключение НЕ распространяется на С16: там вырождение говорит, что
    # попадание объясняется перебором, и это относится к сути вывода.
    voids = {k for k, v in st.items() if v == VOID}
    if voids:
        internal_only = voids <= {"С3 данные=эталон", "С12 независимый метод"}
        external_refutation = (st.get("С15 внешняя цель") == FAIL
                               or st.get("С18 объявленная область") == FAIL)
        if not (internal_only and external_refutation):
            return EMPTY
    # 2. Нет вычисляемого эталона — вопрос, а не находка.
    if st.get("С1 регенерируемость") in (OPEN, FAIL):
        return QUESTION
    # 3. Вывод зависит от выбора оценки или не сошёлся по сетке — вопрос.
    if (st.get("С7 выбор оценки") == OPEN or st.get("С6 сходимость") == OPEN
            or st.get("С9 конечный размер") == OPEN):
        return QUESTION
    # 4. Эталон не подтверждён вторым методом — вопрос, а не опровержение.
    if st.get("С12 независимый метод") == FAIL:
        return QUESTION
    # 5. Подозрительно точное согласие — отдельный флаг, не подтверждение.
    if st.get("С11 слишком хорошо") == FAIL:
        return QUESTION
    # 6. Расхождение по существу при живых контролях — опровержение, но только
    #    если оно значимо на фоне выборочного шума (С10). Если шум объясняет —
    #    вопрос: расхождения могло и не быть.
    # 5b. Формула не сжимает данные — «закон» не короче числа, это не находка.
    if st.get("С17 описание короче данных") == FAIL:
        return QUESTION
    # 5в. Точности арифметики не хватает: вердикт по существу выносить нельзя,
    # это вопрос к вычислению, а не опровержение утверждения. Проверка стоит
    # ПЕРЕД опровержениями намеренно — иначе опровержение могло бы оказаться
    # артефактом округления.
    if st.get("С19 достаточность арифметики") == FAIL:
        return QUESTION
    # 5г. Вывод меняется при законной замене числа попыток на эффективное, или
    # близость упирается в теоретический потолок: и то и другое означает, что
    # вердикт держится на допущении, а не на данных. Вопрос, не опровержение.
    if st.get("С20 эффективное число попыток") == FAIL:
        return QUESTION
    # OPEN у С20 означает, что семейство пусто или иначе не позволяет оценить
    # эффективную кратность. Это не PASS: без оценки множественности нельзя
    # читать итог как подтверждение. Ранее такой OPEN выпадал из свода и
    # инженерный кейс пустого семейства получал ПОДТВЕРЖДЕНО до того, как С14
    # случайно обнаруживала вырождение.
    if st.get("С20 эффективное число попыток") == OPEN:
        return QUESTION
    if st.get("С21 алгебраическая объяснимость") == FAIL:
        return QUESTION
    if (st.get("С2 заявленное=эталон") == FAIL or st.get("С3 данные=эталон") == FAIL
            or st.get("С15 внешняя цель") == FAIL
            or st.get("С18 объявленная область") == FAIL):
        # С10 смягчает опровержение до вопроса ТОЛЬКО если он сравнивал
        # заявленную величину. Прежде любой PASS у С10 понижал опровержение —
        # включая случай, когда С10 сравнивал эталон сам с собой (выборка
        # относилась к другой величине) или когда имена статистик вовсе не
        # сопоставились. Это был путь тихо погасить опровержение, подложив
        # безобидную выборку. Теперь смягчение требует, чтобы С10 действительно
        # сопоставил хотя бы одну статистику с эталоном.
        c10 = next((r for r in results
                    if r.sieve == "С10 неопределённость"), None)
        # Если значимость НЕ ПРОВЕРЯЕМА (выборка детерминированная), то
        # расхождение ИЗ ДАННЫХ нельзя объявить опровержением: неизвестно,
        # больше оно шума или нет.
        #
        # Правило намеренно узкое. Первая версия понижала и расхождение по С2
        # (заявленное против вычисляемого эталона) — и перепрогон реестра сразу
        # показал ошибку: пять арифметических опровержений вида «в каталоге
        # написано 182,8 против пересчитанного 182,78» превратились в ВОПРОС.
        # Там нет и не может быть выборочного шума: сравниваются два числа,
        # оба вычислимы. Выборочная значимость относится только к величине,
        # ИЗМЕРЕННОЙ из данных, то есть к С3. Для С15 и С18 правило не
        # действует — там масштаб задан погрешностью внешнего измерения либо
        # прямым подсчётом.
        sample_based = (st.get("С3 данные=эталон") == FAIL
                        and st.get("С2 заявленное=эталон") != FAIL
                        and st.get("С15 внешняя цель") != FAIL
                        and st.get("С18 объявленная область") != FAIL)
        if sample_based and c10 is not None and \
                c10.reason_code == "significance_untestable":
            return QUESTION
        if c10 is not None and c10.status == PASS and \
                "не сопоставлены" not in (c10.detail or "") and \
                c10.numbers.get("сопоставлено_с_заявленным", 1):
            return QUESTION
        return REFUTED
    if any(v == FAIL for v in st.values()):
        return QUESTION
    return CONFIRMED


def run(claim: Claim, sieves=None, meta: bool = True) -> Report:
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
    if meta:
        results.append(declared_skips_check(claim, results))
        t0 = time.time()
        try:
            r = end_to_end_mutation(claim, sieves)
        except Exception as e:  # noqa: BLE001
            r = Result("С14 сквозная подставка", FAIL, "мутационный прогон упал: %r" % (e,))
        r.seconds = time.time() - t0
        results.append(r)
    verdict = verdict_of(results)
    code = reason_of(results, verdict, claim)
    # Предпосылка применяется ПОСЛЕ свода: она не отменяет ни одного сита, а
    # только запрещает читать ПОДТВЕРЖДЕНО как безусловное, если допущение о
    # независимости испытаний не объявлено верным.
    verdict, pre = _pre.apply(claim, verdict, CONFIRMED)
    if pre.get("applied"):
        code = _pre.REASON[pre["status"]]
    prov = provenance(claim)
    prov["предпосылка независимости"] = pre["declared"]
    prov["статус предпосылки"] = pre["status"]
    return Report(claim.name, claim.source, verdict, results, claim.notes,
                  prov, reason_code=code,
                  action=ACTION.get(code, ""),
                  aggregatable=code not in NON_AGGREGATABLE)


def run_all(claims: Iterable[Claim]) -> list:
    return [run(c) for c in claims]
