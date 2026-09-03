"""Самопроверка самого сита.

Сито — тоже инструмент, и на него распространяется то же правило, что и на всё
остальное: у инструмента обязан быть тест, включая тест на подставленный
неверный ответ. Здесь проверяется, что сито выдаёт нужный вердикт на четырёх
заведомо известных случаях, и что вырожденную проверку оно ловит.
"""

import math

import os

import numpy as np

from . import sieve as sieve_module
from .sieve import (Claim, run, CONFIRMED, REFUTED, QUESTION, EMPTY, VOID,
                    PASS, OPEN, FAIL, rel_dev, reason_of, verdict_of,
                    ACTION, NON_AGGREGATABLE)

# Все пропуски обязаны быть объявлены (сито С13), иначе вердикт ВОПРОС.
SR = {"С%d" % i: "неприменимо к синтетическому случаю" for i in range(1, 22)}


def _cases():
    # 1. Верное утверждение с вычисляемым эталоном: sum 1/n^2 = pi^2/6
    def zeta2():
        return sum(1.0 / n ** 2 for n in range(1, 2_000_00))

    truth = Claim(
        name="сумма 1/n^2 равна pi^2/6",
        stated=math.pi ** 2 / 6.0,
        reference=zeta2,
        wrong=lambda: math.pi ** 2 / 5.0,
        tolerance=1e-4,
        skip_reasons=SR,
    )

    # 2. Ложное утверждение при живом эталоне: должно быть ОПРОВЕРГНУТО
    lie = Claim(
        name="сумма 1/n^2 равна 1.75 (заведомо неверно)",
        stated=1.75,
        reference=zeta2,
        wrong=lambda: 1.0,
        tolerance=1e-3,
        skip_reasons=SR,
    )

    # 3. Эталона нет, только цитата: должно быть ВОПРОС, а не находка
    nore = Claim(
        name="эталон 2.15 из документа без вывода",
        stated=2.15,
        reference=None,
        observed=lambda: 1.72,
        tolerance=0.01,
        skip_reasons=SR,
    )

    # 4. Вырожденная проверка: терпимость такая, что проходит и неверный ответ
    void = Claim(
        name="проверка с терпимостью, которая пропускает всё",
        stated=math.pi ** 2 / 6.0,
        reference=zeta2,
        wrong=lambda: 10.0 * math.pi ** 2 / 6.0,
        tolerance=100.0,
        skip_reasons=SR,
    )

    # 5. Вывод зависит от оценки: должно быть ВОПРОС (случай Хинчина)
    est = Claim(
        name="величина, у которой две законные оценки дают разные знаки",
        stated=2.62,
        reference=lambda: 2.6854520,
        estimators={"по-разложенчески": lambda: 2.755,
                    "пулированно": lambda: 2.668},
        tolerance=0.005,
        skip_reasons=SR,
    )
    # 6. Негативный контроль, который воспроизводит эталон: проверка вырождена
    noisy = Claim(
        name="шум даёт то же, что эталон (негативный контроль)",
        stated=1.0,
        reference=lambda: 1.0,
        null_model=lambda: 1.0,
        null_kind="negative",
        tolerance=0.01,
        skip_reasons=SR,
    )

    # 7. Позитивный контроль, который НЕ даёт эталон: сломан конвейер
    broken = Claim(
        name="позитивный контроль не даёт эталон",
        stated=1.0,
        reference=lambda: 1.0,
        null_model=lambda: 1.5,
        null_kind="positive",
        tolerance=0.01,
        skip_reasons=SR,
    )

    # 8. С9: расхождение с трендом по 1/N, экстраполяция садится на эталон
    trend = Claim(
        name="расхождение уходит при экстраполяции по 1/N",
        stated=0.95,
        reference=lambda: 1.0,
        observed=lambda: 0.95,
        wrong=lambda: 2.0,
        bins=lambda: [(0.10, 0.90), (0.05, 0.95), (0.02, 0.98), (0.01, 0.99)],
        tolerance=0.01,
        skip_reasons=SR,
    )

    # 9. С9: расхождение без тренда, конечным размером НЕ объясняется
    flat = Claim(
        name="расхождение без тренда по 1/N",
        stated=0.95,
        reference=lambda: 1.0,
        observed=lambda: 0.95,
        wrong=lambda: 2.0,
        bins=lambda: [(0.10, 0.95), (0.05, 0.951), (0.02, 0.949), (0.01, 0.95)],
        tolerance=0.01,
        skip_reasons=SR,
    )
    # 10. Незаявленный пропуск сита: гигиена обязана дать ВОПРОС
    silent = Claim(
        name="пропуски сит не объявлены",
        stated=1.0,
        reference=lambda: 1.0,
        wrong=lambda: 2.0,
        tolerance=0.01,
    )

    # 11. Расхождение в пределах выборочного шума: не опровержение, а вопрос
    rng = np.random.default_rng(11)
    x = rng.normal(loc=0.0, scale=1.0, size=3000)
    stat = {"std": lambda a: float(a.std(ddof=1)),
            "p50": lambda a: float(np.percentile(a, 50)),
            "p90": lambda a: float(np.percentile(a, 90))}
    noise = Claim(
        name="отклонение внутри шума",
        stated={"std": 1.0, "p50": 0.0 + 1e-9, "p90": 1.2816},
        reference=lambda: {"std": 1.0, "p50": 1e-9, "p90": 1.2816},
        observed=lambda: {k: f(x) for k, f in stat.items()},
        sample=lambda: x,
        statistics=stat,
        wrong=lambda: {"std": 2.0, "p50": 1.0, "p90": 3.0},
        tolerance=1e-4,          # заведомо жёстче шума
        skip_reasons=SR,
    )

    # 12. Слишком хорошо: эталон совпал с измерением точнее шума по трём статистикам
    toogood = Claim(
        name="согласие точнее выборочного шума",
        stated={k: f(x) for k, f in stat.items()},
        reference=lambda: {k: f(x) for k, f in stat.items()},
        # Наблюдение отличается на 1e-9 — не бит в бит. Так и должно быть: в
        # тождественном наблюдении С3 теперь видит вырождение (луп 11), а
        # проверяем мы здесь С11, «слишком точное согласие», а не тождество.
        observed=lambda: {k: f(x) * (1.0 + 1e-9) for k, f in stat.items()},
        sample=lambda: x,
        statistics=stat,
        wrong=lambda: {"std": 2.0, "p50": 1.0, "p90": 3.0},
        tolerance=0.01,
        skip_reasons=SR,
    )

    # 13. Второй метод не подтверждает эталон
    altbad = Claim(
        name="второй метод даёт другой эталон",
        stated=1.0,
        reference=lambda: 1.0,
        reference_alt=lambda: 1.2,
        wrong=lambda: 5.0,
        tolerance=0.01,
        skip_reasons=SR,
    )
    return (truth, lie, nore, void, est, noisy, broken, trend, flat,
            silent, noise, toogood, altbad)



def _regress_cause():
    """Перепрогон обязан отличать ужесточение сита от исправленного корпуса.

    Иначе принятая правка корпуса выглядит как регрессия инструмента, и
    наоборот: молчаливое ослабление сита прячется за «данные изменились».
    Возвращает число провалов, как остальные модульные самопроверки.
    """
    from .cli import _inputs_digest

    class _Rep:
        def __init__(self, prov):
            self.prov = prov

    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    a = _inputs_digest(_Rep({"inputs": {"f.md": "aaaa"}}))
    b = _inputs_digest(_Rep({"inputs": {"f.md": "bbbb"}}))
    check("отпечаток входов различает содержимое файла", a != b)
    a2 = _inputs_digest(_Rep({"inputs": {"f.md": "aaaa"}}))
    check("отпечаток входов устойчив при том же содержимом", a == a2)
    check("без входов отпечатка нет", _inputs_digest(_Rep({})) is None)
    x = _inputs_digest(_Rep({"inputs": {"a": "1", "b": "2"}}))
    y = _inputs_digest(_Rep({"inputs": {"a": "2", "b": "1"}}))
    check("перестановка хешей между файлами меняет отпечаток", x != y)
    return fail


def _gof_selftest() -> int:
    from .refs.gof import selftest as _g
    return _g()


def _identity_guards() -> int:
    """Вырождение по тождественности: наблюдение = эталон, второй метод = эталон.

    Найдено разбором тика 37: кейс сравнивал таблицу самой с собой (observed
    возвращал reference()), а «независимый метод» повторял ту же арифметику на
    Decimal. Оба сита давали PASS и складывались в ПОДТВЕРЖДЕНО.

    Признак берётся ИЗ КОДА. Первая версия ловила ровное нулевое расхождение
    ЗНАЧЕНИЙ — перепрогон реестра сразу перевернул 17 вердиктов, потому что у
    целых величин (20 412 комбинаций) и простых констант (3^phi) независимый
    путь законно совпадает с эталоном до последнего бита.
    """
    from .sieve import (Claim, sieve_observation, sieve_independent_method,
                        VOID, PASS, FAIL)
    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    def ref():
        return {"mean": 2.666, "std": 0.494938}

    def obs_is_ref():
        """Ровно случай тика 37."""
        return ref()

    def obs_real():
        return {"mean": 2.6661, "std": 0.494939}

    def obs_off():
        return {"mean": 3.5, "std": 0.494938}

    def alt_same_value():
        """Иной путь, дающий бит в бит то же: законно для простых величин."""
        total = 0.0
        for v in (2.666,):
            total += v
        return {"mean": total, "std": 0.494938}

    c = Claim(name="t", source="s", reference=ref, observed=obs_is_ref,
              tolerance=0.02)
    r = sieve_observation(c)
    check("С3 ловит наблюдение, вычисленное вызовом эталона",
          r.status == VOID and r.reason_code == "observation_is_reference")

    c1 = Claim(name="t", source="s", reference=ref, observed=ref,
               tolerance=0.02)
    check("С3 ловит наблюдение — тот же объект, что эталон",
          sieve_observation(c1).status == VOID)

    c2 = Claim(name="t", source="s", reference=ref, observed=obs_real,
               tolerance=0.02)
    check("С3 не путает живое измерение с тождеством",
          sieve_observation(c2).status == PASS)

    # ПОДСТАВКА, на которой упала первая версия: значения совпадают бит в бит,
    # но путь другой. Вырождением это НЕ является.
    c3 = Claim(name="t", source="s", reference=ref, observed=alt_same_value,
               tolerance=0.02)
    check("С3 не считает вырождением совпадение значений при ином пути",
          sieve_observation(c3).status == PASS)

    c4 = Claim(name="t", source="s", reference=ref, observed=obs_off,
               tolerance=0.02)
    check("С3 продолжает ловить расхождение",
          sieve_observation(c4).status == FAIL)

    def alt_is_ref():
        return ref()

    c5 = Claim(name="t", source="s", reference=ref, reference_alt=alt_is_ref,
               alt_tolerance=lambda: 1e-12, tolerance=0.02)
    r5 = sieve_independent_method(c5)
    check("С12 ловит второй метод, вычисленный вызовом эталона",
          r5.status == VOID and r5.reason_code == "no_second_method")

    c6 = Claim(name="t", source="s", reference=ref,
               reference_alt=alt_same_value, alt_tolerance=lambda: 1e-12,
               tolerance=0.02)
    check("С12 принимает иной путь, совпавший бит в бит",
          sieve_independent_method(c6).status == PASS)

    # Свод: вырождение С3/С12 не отменяет опровержение по ВНЕШНЕЙ цели.
    # Найдено перепрогоном: формула m_p/m_e с промахом 6,3e7 сигм понижалась
    # до ПУСТО из-за того, что в том же кейсе observed вызывал reference().
    from .sieve import Result, verdict_of, REFUTED, EMPTY
    ext = [Result("С3 данные=эталон", VOID, "вырождено"),
           Result("С15 внешняя цель", FAIL, "промах 6,3e7 сигм")]
    check("вырождение С3 не гасит опровержение по внешней цели",
          verdict_of(ext) == REFUTED)

    # ПОДСТАВКА: без внешнего опровержения вырождение по-прежнему даёт ПУСТО.
    only_void = [Result("С3 данные=эталон", VOID, "вырождено"),
                 Result("С2 заявленное=эталон", FAIL, "расхождение 5%")]
    check("вырождение С3 без внешней цели даёт ПУСТО",
          verdict_of(only_void) == EMPTY)

    # ПОДСТАВКА: вырождение по множественности (С16) гасит вывод и при
    # внешнем расхождении — оно относится к сути, а не к внутреннему сравнению.
    mult = [Result("С16 подгонка под ответ", VOID, "126 ожидаемых попаданий"),
            Result("С15 внешняя цель", FAIL, "промах")]
    check("вырождение С16 продолжает гасить вывод",
          verdict_of(mult) == EMPTY)
    return fail


def _identity_graph() -> int:
    """Детектор косвенной тавтологии по графу вызовов (модуль identity).

    У модуля своя самопроверка: 4 позитивных случая (прямой вызов, один и два
    посредника, чистая арифметика над эталоном), 6 негативных (чтение файла,
    общий парсер, свой источник рядом с эталоном, параметр функции, вызов чужой
    функции, возврат константы) и 3 guard'а на тихий отказ вне sys.modules.
    """
    from .identity import selftest as _identity_selftest
    return _identity_selftest()


def _reason_subtypes() -> int:
    """Подтипы причины вердикта: сломанный контроль и предел точности входа.

    Оба подтипа введены после лупа 10, где вердикт ПУСТО дважды означал дефект
    МОЕЙ проверки (контроль сравнивал одну реализацию со средним по репликам;
    С8 сравнивал ноль с погрешностью 1e-9), а не дефект утверждения. Без
    отдельного подтипа такой случай попадал в 'unclassified' и терялся.
    """
    from .sieve import (Result, Claim, reason_of, ACTION, NON_AGGREGATABLE,
                        sieve_external_target,
                        EMPTY, FAIL as _F, VOID as _V, PASS as _P2,
                        SKIP as _S2, OPEN as _O2)
    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    broken = [Result("С5 контроль", _F, "позитивный контроль не воспроизвёл эталон")]
    check("сломанный контроль опознан как control_broken",
          reason_of(broken, EMPTY) == "control_broken")
    check("для control_broken объявлено действие",
          "control_broken" in ACTION and
          "контроль" in ACTION["control_broken"].lower())

    prec = [Result("С5 контроль", _P2), Result("С8 бюджет точности", _V,
                                               "эффект 0 против погрешности 1e-9")]
    check("предел точности входа опознан как input_precision_limited",
          reason_of(prec, EMPTY) == "input_precision_limited")
    check("для input_precision_limited объявлено действие",
          "input_precision_limited" in ACTION and
          "погрешность" in ACTION["input_precision_limited"].lower())

    # Выборочная цель, скопированная из того же наблюдаемого, не становится
    # содержательной от наличия URL. Guard обязан сработать по объявленной
    # связи источников и точному нулю сигм.
    same_source = Claim(
        name="вырожденная внешняя цель",
        claim_kind="prediction",
        reference=lambda: 7.0,
        stated_target=lambda: 7.0,
        external_target=lambda: {
            "value": 7.0,
            "uncertainty": 1.0,
            "source": "https://pdg.lbl.gov/measurement",
        },
        external_source_relation="same_as_observation",
    )
    same_result = sieve_external_target(same_source)
    check("совпадение одного источника опознано как external_source_degenerate",
          same_result.status == _V and
          same_result.reason_code == "external_source_degenerate")
    check("вырожденная внешняя цель не агрегируется",
          reason_of([same_result], EMPTY) == "external_source_degenerate" and
          "external_source_degenerate" in NON_AGGREGATABLE and
          "external_source_degenerate" in ACTION)

    untraceable = Claim(
        name="внешняя цель без корпусного наблюдаемого",
        claim_kind="prediction",
        claim_family="new_external_family",
        reference=lambda: 7.0,
        external_target=lambda: {
            "value": 7.0,
            "uncertainty": 0.1,
            "source": "https://nist.gov/fixture",
        },
    )
    untraceable_result = sieve_external_target(untraceable)
    check("внешняя цель без файла корпуса опознана как external_observation_untraceable",
          untraceable_result.status == _V and
          untraceable_result.reason_code == "external_observation_untraceable")
    check("нетрассируемое наблюдаемое не агрегируется",
          reason_of([untraceable_result], EMPTY) ==
          "external_observation_untraceable" and
          "external_observation_untraceable" in NON_AGGREGATABLE)
    check("для нетрассируемого наблюдаемого объявлено действие",
          "external_observation_untraceable" in ACTION and
          "corpus/trinity" in ACTION["external_observation_untraceable"])

    # ПОРЯДОК ПРАВИЛ: множественность сильнее обоих новых подтипов. Иначе
    # совпадение, купленное перебором, объяснялось бы «сломанным контролем» и
    # уходило из-под правила о предрегистрации пространства поиска.
    both = [Result("С16 подгонка под ответ", _V, "1.5 ожидаемых попаданий"),
            Result("С5 контроль", _F), Result("С8 бюджет точности", _V)]
    check("множественность приоритетнее сломанного контроля",
          reason_of(both, EMPTY) == "multiplicity_limited")

    # Оба новых подтипа не агрегируются: вердикт получен при неисправной
    # проверке, складывать его в счётчик находок нельзя.
    # Правило свода: непроверяемая значимость понижает опровержение по С2/С3
    # до вопроса, но НЕ трогает опровержение по внешней цели.
    from .sieve import verdict_of, QUESTION as _Q, REFUTED as _R
    c10u = Result("С10 неопределённость", _S2, "значимость не проверяема",
                  reason_code="significance_untestable", auto_skip=True)
    # Расхождение ИЗ ДАННЫХ понижается: масштаб задаёт выборочный шум.
    base = [Result("С3 данные=эталон", _F, "расхождение 5%"), c10u]
    check("непроверяемая значимость понижает опровержение по С3 до вопроса",
          verdict_of(base) == _Q)
    # ПОДСТАВКА: арифметическое расхождение (С2) понижаться НЕ должно —
    # сравниваются два вычислимых числа, выборочного шума там нет. На этой
    # подставке первая версия правила и упала: перепрогон реестра перевернул
    # пять арифметических опровержений в ВОПРОС.
    arith = [Result("С2 заявленное=эталон", _F, "расхождение 0,01%"), c10u]
    check("арифметическое опровержение по С2 не понижается",
          verdict_of(arith) == _R)
    ext = [Result("С15 внешняя цель", _F, "промах 40 сигм"), c10u]
    check("опровержение по внешней цели не понижается",
          verdict_of(ext) == _R)

    # С20 может честно вернуть OPEN, когда семейство пусто. Это состояние
    # нельзя трактовать как PASS: до ремонта такой OPEN выпадал из свода, и
    # отсутствие оценки эффективной кратности превращалось в подтверждение.
    empty_meff = [Result("С20 эффективное число попыток", _O2,
                         "пустое семейство")]
    check("OPEN С20 понижает свод до вопроса",
          verdict_of(empty_meff) == _Q)
    check("OPEN С20 получает причину meff_unstable",
          reason_of(empty_meff, _Q) == "meff_unstable")

    check("оба подтипа исключены из агрегирования",
          "control_broken" in NON_AGGREGATABLE and
          "input_precision_limited" in NON_AGGREGATABLE)

    # Отсутствие общего рецепта метрик — отдельный класс риска, а не
    # арифметическое опровержение: машинная подсказка кейса обязана сохранять
    # вердикт ВОПРОС и отдельный reason-code.
    incomparable = Claim(name="несопоставимые метрики",
                         reason_code_hint="metrics_incommensurable")
    check("несопоставимость метрик получает отдельный reason-code",
          reason_of([], _Q, incomparable) == "metrics_incommensurable")
    check("несопоставимость метрик не агрегируется",
          "metrics_incommensurable" in NON_AGGREGATABLE and
          "metrics_incommensurable" in ACTION)
    check("очистка подсказки не маскирует несопоставимость метрик",
          reason_of([], _Q, Claim(name="без подсказки")) !=
          "metrics_incommensurable")
    return fail


def main() -> int:
    (truth, lie, nore, void, est, noisy, broken, trend, flat,
     silent, noise, toogood, altbad) = _cases()
    checks = [
        ("верное утверждение -> ПОДТВЕРЖДЕНО", run(truth).verdict, CONFIRMED),
        ("ложное утверждение -> ОПРОВЕРГНУТО", run(lie).verdict, REFUTED),
        ("нет вычисляемого эталона -> ВОПРОС", run(nore).verdict, QUESTION),
        ("вырожденная проверка -> ПУСТО", run(void).verdict, EMPTY),
        ("вывод зависит от оценки -> ВОПРОС", run(est).verdict, QUESTION),
        ("шум похож на сигнал -> ПУСТО", run(noisy).verdict, EMPTY),
        ("позитивный контроль сломан -> ВОПРОС", run(broken).verdict, QUESTION),
        ("тренд по 1/N -> ВОПРОС", run(trend).verdict, QUESTION),
        ("нет тренда по 1/N -> ОПРОВЕРГНУТО", run(flat).verdict, REFUTED),
        ("незаявленный пропуск -> ВОПРОС", run(silent).verdict, QUESTION),
        ("расхождение внутри шума -> ВОПРОС", run(noise).verdict, QUESTION),
        ("слишком точное согласие -> ВОПРОС", run(toogood).verdict, QUESTION),
        ("второй метод не сходится -> ВОПРОС", run(altbad).verdict, QUESTION),
    ]
    ok = fail = 0
    print("самопроверка сита:")
    for name, got, want in checks:
        if got == want:
            ok += 1
            print("  ok   %-45s %s" % (name, got))
        else:
            fail += 1
            print("  FAIL %-45s получено %s, ожидалось %s" % (name, got, want))

    # 6. Отдельно: сито С4 обязано помечать VOID именно вырожденный случай,
    #    а не просто выдавать общий вердикт.
    r = run(void)
    s4 = [x for x in r.results if x.sieve.startswith("С4")][0]
    if s4.status == VOID:
        ok += 1
        print("  ok   %-45s %s" % ("сито подставки помечает вырождение", s4.status))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("сито подставки помечает вырождение", s4.status))

    # Сквозная подставка обязана срывать каскад на верном утверждении
    r = run(truth)
    s14 = [x for x in r.results if x.sieve.startswith("С14")][0]
    if s14.status == PASS and "ПОДТВЕРЖДЕНО" not in s14.detail:
        ok += 1
        print("  ok   %-45s %s" % ("сквозная подставка срывает каскад", s14.detail))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("сквозная подставка срывает каскад", s14.detail))

    # Сито «слишком хорошо» обязано пометить именно тот случай
    s11 = [x for x in run(toogood).results if x.sieve.startswith("С11")][0]
    if s11.status == FAIL:
        ok += 1
        print("  ok   %-45s %s" % ("сито «слишком хорошо» срабатывает", s11.detail))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("сито «слишком хорошо» срабатывает", s11.status))

    # Набор подставок: плохая подставка обязана называться плохой подставкой,
    # а не «вырожденной проверкой»
    from .sieve import Claim as _C
    multi = _C(name="набор подставок", stated=1.0, reference=lambda: 1.0,
               wrong=[lambda: 2.0, lambda: 1.0009], tolerance=0.01,
               skip_reasons=SR)
    s4 = [x for x in run(multi).results if x.sieve.startswith("С4")][0]
    if s4.status == VOID and "неотличима" in s4.detail and "подставка 1 отклонена" in s4.detail:
        ok += 1
        print("  ok   %-45s %s" % ("плохая подставка отделена от вырождения", s4.detail[:60]))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("плохая подставка отделена от вырождения", s4.detail))

    # 7. rel_dev на dict должен считать по ключам, а не по порядку
    d = rel_dev({"a": 2.0, "b": 3.0}, {"b": 3.0, "a": 4.0})
    if abs(d["a"] + 0.5) < 1e-12 and abs(d["b"]) < 1e-12:
        ok += 1
        print("  ok   %-45s a %+.3f b %+.3f" % ("сравнение по именам", d["a"], d["b"]))
    else:
        fail += 1
        print("  FAIL %-45s %r" % ("сравнение по именам", d))


    print("\n  новые сита С15-С18:")

    # С15: предсказательное утверждение без внешней цели обязано дать ПУСТО
    taut = Claim(
        name="формула даёт напечатанное рядом число (тавтология)",
        stated=879.4,
        reference=lambda: 879.4,
        wrong=lambda: 900.0,
        claim_kind="prediction",
        skip_reasons=SR,
    )
    r = run(taut)
    if r.verdict == EMPTY:
        ok += 1
        print("  ok   %-45s %s" % ("С15 ловит тавтологию", r.verdict))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С15 ловит тавтологию", r.verdict))

    # С15 с внешней целью: согласие внутри погрешности -> не FAIL
    good_pred = Claim(
        name="формула согласуется с измерением внутри погрешности",
        stated=878.5,
        reference=lambda: 878.5,
        wrong=lambda: 950.0,
        claim_kind="prediction",
        external_target=lambda: {"value": 878.4, "uncertainty": 0.5,
                                 "source": "https://pdg.lbl.gov/2024/fixture"},
        stated_target=lambda: 878.4,
        skip_reasons=SR,
    )
    st15 = {x.sieve: x.status for x in run(good_pred).results}["С15 внешняя цель"]
    if st15 == PASS:
        ok += 1
        print("  ok   %-45s %s" % ("С15 пропускает согласие в 1 сигма", st15))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С15 пропускает согласие в 1 сигма", st15))

    # Нулевое отклонение — это точное согласие, а не отсутствие данных.
    exact_pred = Claim(
        name="формула точно совпала с внешним измерением",
        stated=878.4,
        reference=lambda: 878.4,
        wrong=lambda: 950.0,
        claim_kind="prediction",
        external_target=lambda: {"value": 878.4, "uncertainty": 0.5,
                                 "source": "https://pdg.lbl.gov/2024/fixture"},
        stated_target=lambda: 878.4,
        skip_reasons=SR,
    )
    st15_exact = {
        x.sieve: x.status for x in run(exact_pred).results
    }["С15 внешняя цель"]
    if st15_exact == PASS:
        print("  ok   %-45s %s" % ("С15 guard: нулевое отклонение", st15_exact))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С15 guard: нулевое отклонение", st15_exact))

    # подставка для С15: то же, но формула ушла на 20 сигм -> FAIL
    bad_pred = Claim(
        name="формула разошлась с измерением на 20 сигм",
        stated=888.4,
        reference=lambda: 888.4,
        wrong=lambda: 878.4,
        claim_kind="prediction",
        external_target=lambda: {"value": 878.4, "uncertainty": 0.5,
                                 "source": "https://pdg.lbl.gov/2024/fixture"},
        skip_reasons=SR,
    )
    st15b = {x.sieve: x.status for x in run(bad_pred).results}["С15 внешняя цель"]
    if st15b == FAIL:
        ok += 1
        print("  ok   %-45s %s" % ("С15 ловит расхождение в 20 сигм", st15b))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С15 ловит расхождение в 20 сигм", st15b))

    # Новый тип риска С15: повреждённая цель не должна превращаться в
    # согласие. Нефинитная погрешность и отсутствие URL проверяются отдельно.
    for label, target in (
        ("С15 ловит нефинитную цель",
         {"value": float("nan"), "uncertainty": 0.5,
          "source": "https://pdg.lbl.gov/2024/fixture"}),
        ("С15 требует URL цели",
         {"value": 878.4, "uncertainty": 0.5, "source": "архив без ссылки"}),
    ):
        malformed = Claim(
            name=label,
            stated=878.4,
            reference=lambda: 878.4,
            wrong=lambda: 950.0,
            claim_kind="prediction",
            external_target=lambda target=target: target,
            skip_reasons=SR,
        )
        malformed_status = {
            x.sieve: x.status for x in run(malformed).results
        }["С15 внешняя цель"]
        if malformed_status == VOID:
            ok += 1
            print("  ok   %-45s %s" % (label, malformed_status))
        else:
            fail += 1
            print("  FAIL %-45s %s" % (label, malformed_status))

    # Новый тип риска С15: численно правдоподобная сверка в смешанных
    # единицах не должна проходить. Проверяется как отсутствие единицы на
    # одной стороне, так и явное несовпадение; оба исхода неагрегируемы.
    unit_fixtures = (
        (
            "С15 требует единицу внешней цели",
            "МэВ",
            {"value": 1.2933, "uncertainty": 0.001,
             "source": "https://physics.nist.gov/fixture"},
            "external_unit_missing",
        ),
        (
            "С15 ловит несовпадение единиц",
            "МэВ",
            {"value": 1293.3, "uncertainty": 1.0, "unit": "кэВ",
             "source": "https://physics.nist.gov/fixture"},
            "external_unit_mismatch",
        ),
    )
    for label, unit, target, expected_reason in unit_fixtures:
        unit_claim = Claim(
            name=label,
            stated=1.2933,
            reference=lambda: 1.2933,
            wrong=lambda: 2.0,
            claim_kind="prediction",
            measurement_unit=unit,
            external_target=lambda target=target: target,
            skip_reasons=SR,
        )
        unit_report = run(unit_claim)
        unit_result = next(
            x for x in unit_report.results if x.sieve == "С15 внешняя цель"
        )
        unit_reason = reason_of(
            unit_report.results,
            verdict_of(unit_report.results),
            unit_claim,
        )
        if (unit_result.status == VOID
                and unit_result.reason_code == expected_reason
                and unit_reason == expected_reason
                and expected_reason in NON_AGGREGATABLE
                and expected_reason in ACTION):
            ok += 1
            print("  ok   %-45s %s" % (label, expected_reason))
        else:
            fail += 1
            print("  FAIL %-45s %s" % (label, unit_reason))

    # Новый тип риска С15: одинаковые числа и единицы не делают бюджеты
    # неопределённости сопоставимыми, если одна сторона сообщает только
    # статистическую, а другая — объединённую погрешность.
    uncertainty_fixtures = (
        (
            "С15 требует тип неопределённости внешней цели",
            "both",
            {"value": 1.2933, "uncertainty": 0.001,
             "source": "https://physics.nist.gov/fixture"},
            "external_uncertainty_type_missing",
        ),
        (
            "С15 ловит несовпадение типа неопределённости",
            "both",
            {"value": 1.2933, "uncertainty": 0.001,
             "uncertainty_type": "statistical",
             "source": "https://physics.nist.gov/fixture"},
            "external_uncertainty_type_mismatch",
        ),
    )
    for label, uncertainty_type, target, expected_reason in uncertainty_fixtures:
        uncertainty_claim = Claim(
            name=label,
            stated=1.2933,
            reference=lambda: 1.2933,
            wrong=lambda: 2.0,
            claim_kind="prediction",
            external_uncertainty_type=uncertainty_type,
            external_target=lambda target=target: target,
            skip_reasons=SR,
        )
        uncertainty_report = run(uncertainty_claim)
        uncertainty_result = next(
            x for x in uncertainty_report.results if x.sieve == "С15 внешняя цель"
        )
        uncertainty_reason = reason_of(
            uncertainty_report.results,
            verdict_of(uncertainty_report.results),
            uncertainty_claim,
        )
        if (uncertainty_result.status == VOID
                and uncertainty_result.reason_code == expected_reason
                and uncertainty_reason == expected_reason
                and expected_reason in NON_AGGREGATABLE
                and expected_reason in ACTION):
            ok += 1
            print("  ok   %-45s %s" % (label, expected_reason))
        else:
            fail += 1
            print("  FAIL %-45s %s" % (label, uncertainty_reason))

    # Отдельный риск происхождения: зарезервированный example.* не должен
    # считаться измерением лишь из-за наличия схемы https://. Причина обязана
    # сохраниться в своде как неагрегируемая, а не превратиться в обычное
    # ограничение разрешения.
    reserved_claim = Claim(
        name="URL-заглушка внешней цели",
        stated=878.4,
        reference=lambda: 878.4,
        wrong=lambda: 950.0,
        claim_kind="prediction",
        external_target=lambda: {
            "value": 878.4,
            "uncertainty": 0.5,
            "source": "https://example.invalid/measurement",
        },
        skip_reasons=SR,
    )
    reserved_report = run(reserved_claim)
    reserved_status = {
        x.sieve: x.status for x in reserved_report.results
    }["С15 внешняя цель"]
    reserved_reason = reason_of(
        reserved_report.results,
        verdict_of(reserved_report.results),
        reserved_claim,
    )
    if (reserved_status == VOID
            and reserved_reason == "external_source_unverifiable"):
        ok += 1
        print("  ok   %-45s %s" %
              ("С15 классифицирует URL-заглушку", reserved_reason))
    else:
        fail += 1
        print("  FAIL %-45s %s" %
              ("С15 классифицирует URL-заглушку", reserved_reason))

    # Мутационная цель: удаление содержательной проверки конечности не должно
    # выглядеть успешным. Подмена math.isfinite на всепропускающий мутант
    # обязана изменить решение нефинитной фикстуры.
    nan_target = {"value": float("nan"), "uncertainty": 0.5,
                  "source": "https://pdg.lbl.gov/2024/fixture"}
    nan_claim = Claim(
        name="мутация проверки конечности внешней цели",
        stated=878.4,
        reference=lambda: 878.4,
        wrong=lambda: 950.0,
        claim_kind="prediction",
        external_target=lambda: nan_target,
        skip_reasons=SR,
    )
    original_isfinite = sieve_module.math.isfinite
    try:
        sieve_module.math.isfinite = lambda _value: True
        mutant_status = {
            x.sieve: x.status for x in run(nan_claim).results
        }["С15 внешняя цель"]
    finally:
        sieve_module.math.isfinite = original_isfinite
    original_status = {
        x.sieve: x.status for x in run(nan_claim).results
    }["С15 внешняя цель"]
    if original_status == VOID and mutant_status != VOID:
        ok += 1
        print("  ok   %-45s %s -> %s" %
              ("мутация finite ловится", mutant_status, original_status))
    else:
        fail += 1
        print("  FAIL %-45s %s -> %s" %
              ("мутация finite ловится", mutant_status, original_status))

    # Новый тип риска С15: поставщик внешней цели может завершиться исключением.
    # Это не отсутствие расхождения и не пустая цель; причина обязана попасть
    # в машинный свод, чтобы сбой чтения нельзя было принять за согласие.
    def broken_target():
        raise RuntimeError("источник временно недоступен")

    broken_target_claim = Claim(
        name="поставщик внешней цели завершился ошибкой",
        stated=878.4,
        reference=lambda: 878.4,
        wrong=lambda: 950.0,
        claim_kind="prediction",
        external_target=broken_target,
        skip_reasons=SR,
    )
    broken_target_report = run(broken_target_claim)
    broken_target_result = next(
        x for x in broken_target_report.results if x.sieve == "С15 внешняя цель"
    )
    broken_target_reason = reason_of(
        broken_target_report.results,
        verdict_of(broken_target_report.results),
        broken_target_claim,
    )
    if (broken_target_result.status == VOID
            and broken_target_result.reason_code == "external_target_invalid"
            and broken_target_reason == "external_target_invalid"
            and "external_target_invalid" in NON_AGGREGATABLE
            and "external_target_invalid" in ACTION):
        ok += 1
        print("  ok   %-45s %s" %
              ("С15 классифицирует сбой поставщика", broken_target_reason))
    else:
        fail += 1
        print("  FAIL %-45s %s" %
              ("С15 классифицирует сбой поставщика", broken_target_reason))

    # С16: ожидаемых попаданий больше одного -> ПУСТО
    fitted = Claim(
        name="совпадение при переборе, ожидаемых попаданий 3",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        multiplicity=lambda: {"expected_hits": 3.0, "p_global": 0.95,
                              "fraction_random_targets_hit": 0.9},
        skip_reasons=SR,
    )
    if run(fitted).verdict == EMPTY:
        ok += 1
        print("  ok   %-45s %s" % ("С16 ловит подгонку под ответ", EMPTY))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С16 ловит подгонку под ответ", run(fitted).verdict))

    # подставка для С16: редкое попадание не должно объявляться подгонкой
    rare = Claim(
        name="редкое совпадение, ожидаемых попаданий 0.001",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        multiplicity=lambda: {"expected_hits": 1e-3, "p_global": 1e-3,
                              "fraction_random_targets_hit": 0.001},
        skip_reasons=SR,
    )
    st16 = {x.sieve: x.status for x in run(rare).results}["С16 подгонка под ответ"]
    if st16 == PASS:
        ok += 1
        print("  ok   %-45s %s" % ("С16 не срабатывает на редком попадании", st16))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С16 не срабатывает на редком попадании", st16))

    # С16: повреждённые числовые метрики не имеют права превращаться в PASS.
    # NaN раньше проходил сравнения «>=» и «>» как ложный, поэтому тихо
    # пропускал испорченную оценку множественности.
    for label, payload in (
            ("NaN в expected_hits",
             {"expected_hits": float("nan"), "p_global": 0.001}),
            ("NaN в p_global",
             {"expected_hits": 1e-3, "p_global": float("nan")}),
            ("доля вне диапазона",
             {"expected_hits": 1e-3, "p_global": 1e-3,
              "fraction_random_targets_hit": 1.1}),
            ("отсутствует p_global",
             {"expected_hits": 1e-3}),
    ):
        corrupt = Claim(
            name="повреждённая метрика С16: " + label,
            stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
            multiplicity=lambda payload=payload: payload,
            skip_reasons=SR,
        )
        rows = run(corrupt).results
        row = next(x for x in rows if x.sieve == "С16 подгонка под ответ")
        if row.status == FAIL and reason_of(rows, QUESTION) == "multiplicity_invalid":
            ok += 1
        else:
            fail += 1
            print("  FAIL повреждённая метрика С16: %s -> %s / %s"
                  % (label, row.status, reason_of(rows, QUESTION)))
    print("  ok   повреждённые метрики С16 отвергнуты (4/4)")

    # С17: описание дороже совпадения -> ВОПРОС, а не подтверждение
    nocompress = Claim(
        name="описание 14.3 бит против совпадения 5.6 бит",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        mdl=lambda: {"description_bits": 14.317, "match_bits": 5.64},
        skip_reasons=SR,
    )
    if run(nocompress).verdict == QUESTION:
        ok += 1
        print("  ok   %-45s %s" % ("С17 ловит отсутствие сжатия", QUESTION))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С17 ловит отсутствие сжатия",
                                   run(nocompress).verdict))

    # подставка для С17: реальное сжатие обязано пройти
    compress = Claim(
        name="описание 14.3 бит против совпадения 30 бит",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        mdl=lambda: {"description_bits": 14.317, "match_bits": 30.0},
        skip_reasons=SR,
    )
    st17 = {x.sieve: x.status for x in run(compress).results}["С17 описание короче данных"]
    if st17 == PASS:
        ok += 1
        print("  ok   %-45s %s" % ("С17 пропускает настоящее сжатие", st17))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С17 пропускает настоящее сжатие", st17))

    # С18: выход за объявленные границы -> ОПРОВЕРГНУТО
    outside = Claim(
        name="использованы показатели вне объявленного перебора",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        declared_domain=lambda: [("m", 4, (-3, 0))],
        skip_reasons=SR,
    )
    if run(outside).verdict == REFUTED:
        ok += 1
        print("  ok   %-45s %s" % ("С18 ловит выход за объявленный перебор", REFUTED))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С18 ловит выход за объявленный перебор",
                                   run(outside).verdict))

    # подставка для С18: законные параметры не должны давать нарушение
    inside = Claim(
        name="все показатели внутри объявленного перебора",
        stated=1.0, reference=lambda: 1.0, wrong=lambda: 2.0,
        declared_domain=lambda: [],
        skip_reasons=SR,
    )
    st18 = {x.sieve: x.status for x in run(inside).results}["С18 объявленная область"]
    if st18 == PASS:
        ok += 1
        print("  ok   %-45s %s" % ("С18 без ложных срабатываний", st18))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С18 без ложных срабатываний", st18))

    print("\n  калибровка прогона мощности:")
    import subprocess as _sp, os as _os, sys as _sys
    _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    # Прогон мощности на ОПРОВЕРГНУТОМ утверждении обязан сказать, что мощность
    # не определена, а НЕ жаловаться на калибровку: мутация сама устраняет
    # расхождение, поэтому претензия была бы не по адресу.
    _case = _os.path.join(_root, "cases", "master_catalog_msme_error.py")
    if _os.path.exists(_case):
        _out = _sp.run([_sys.executable, "-m", "goldsieve", "power", _case],
                       cwd=_root, capture_output=True, text=True,
                       encoding="utf-8", errors="backslashreplace",
                       timeout=600).stdout
        if "мощность в этой постановке не определена" in _out and \
                "КАЛИБРОВКА НЕ ПРОШЛА" not in _out:
            ok += 1
            print("  ok   на опровергнутом мощность объявлена неопределённой")
        else:
            fail += 1
            print("  FAIL на опровергнутом мощность объявлена неопределённой")
        # ПОДСТАВКА: команда обязана вообще не печатать число разрешения там,
        # где сканирования не было — иначе в ведомость снова попадёт значение
        # сетки, выданное за измерение.
        if "минимально различимое отклонение" not in _out:
            ok += 1
            print("  ok   без сканирования число разрешения не печатается")
        else:
            fail += 1
            print("  FAIL без сканирования число разрешения не печатается")

    print("\n  свод: смягчение опровержения по С10:")
    from .sieve import run as _run, Claim as _Cv, REFUTED as _R, QUESTION as _Q
    _sk = {"С%d" % i: "проверка свода" for i in
           (1, 4, 5, 6, 7, 8, 9, 11, 12, 15, 16, 17, 18, 19)}
    # С10 сравнивает ЧУЖУЮ величину: смягчать опровержение он не вправе
    c_alien = _Cv(name="чужая выборка", stated={"заявленное": 2.0},
                  reference=lambda: {"заявленное": 1.0, "другое": 5.0},
                  sample=lambda: [5.0, 5.01, 4.99],
                  statistics={"другое": lambda a: sum(a) / len(a)},
                  tolerance=0.01, skip_reasons=_sk)
    if _run(c_alien).verdict == _R:
        ok += 1
        print("  ok   С10 по чужой величине НЕ смягчает опровержение")
    else:
        fail += 1
        print("  FAIL С10 по чужой величине НЕ смягчает опровержение (%s)"
              % _run(c_alien).verdict)
    # ПОДСТАВКА: та же конструкция, но выборка относится к ЗАЯВЛЕННОЙ величине —
    # здесь смягчение законно, и вердикт обязан стать ВОПРОС. Без этой проверки
    # правило можно было бы «починить», запретив смягчение вообще.
    c_own = _Cv(name="своя выборка", stated={"заявленное": 2.0},
                reference=lambda: {"заявленное": 2.0},
                sample=lambda: [2.0, 2.01, 1.99],
                statistics={"заявленное": lambda a: sum(a) / len(a)},
                tolerance=0.0, skip_reasons=_sk)
    if _run(c_own).verdict == _Q:
        ok += 1
        print("  ok   С10 по заявленной величине смягчение сохраняет")
    else:
        fail += 1
        print("  FAIL С10 по заявленной величине смягчение сохраняет (%s)"
              % _run(c_own).verdict)

    print("\n  прогон мощности (power):")
    from .sieve import sieve_numbers as _sn, ALL_SIEVES as _AS
    _nums = _sn()
    if 18 in _nums and 19 in _nums:
        ok += 1
        print("  ok   номера сит собраны с прогона, С18 и С19 на месте")
    else:
        fail += 1
        print("  FAIL номера сит собраны с прогона, С18 и С19 на месте (%s)"
              % _nums)
    # ПОДСТАВКА: len(ALL_SIEVES) НЕ должен годиться как перечисление номеров —
    # именно эта подмена и дала 28 недействительных записей о разрешающей
    # способности. Проверка обязана падать, если кто-то вернёт счётчик длины.
    if max(_nums) > len(_AS):
        ok += 1
        print("  ok   счётчик длины списка не годится как перечисление номеров")
    else:
        fail += 1
        print("  FAIL счётчик длины списка не годится как перечисление номеров")

    print("\n  сито С10 при несопоставленных именах статистик:")
    from .sieve import (
        sieve_uncertainty,
        Claim as _C10,
        OPEN as _O,
        PASS as _P,
        SKIP as _S,
        FAIL as _FL,
    )
    c10 = _C10(name="x", reference=lambda: 1.0,
               sample=lambda: [1.0, 1.01, 0.99],
               statistics={"иное_имя": lambda a: sum(a) / len(a)})
    try:
        r10 = sieve_uncertainty(c10)
        if r10.status == _O and "не сопоставлены" in r10.detail:
            ok += 1
            print("  ok   С10 не падает и объясняет несопоставленные имена")
        else:
            fail += 1
            print("  FAIL С10 не падает и объясняет несопоставленные имена (%s)"
                  % r10.status)
    except Exception as e:
        fail += 1
        print("  FAIL С10 упало с %r" % (e,))
    # ПОДСТАВКА: при СОВПАДАЮЩЕМ имени сито обязано работать по существу, а не
    # уходить в тот же OPEN — иначе заглушка съела бы всю проверку.
    c10ok = _C10(name="x", reference=lambda: 1.0,
                 sample=lambda: [1.0, 1.01, 0.99],
                 statistics={"value": lambda a: sum(a) / len(a)})
    if sieve_uncertainty(c10ok).status != _O or "не сопоставлены" not in \
            sieve_uncertainty(c10ok).detail:
        ok += 1
        print("  ok   С10 при совпадающем имени работает по существу")
    else:
        fail += 1
        print("  FAIL С10 при совпадающем имени работает по существу")

    # Нулевой эталон — валидная статистика счётчика, а не отсутствие данных.
    # Процентная запись для нуля невозможна, поэтому С10 обязан сообщить
    # абсолютную разность и не падать с ZeroDivisionError.
    c10zero = _C10(
        name="нулевой эталон статистики",
        stated=0.0,
        reference=lambda: 0.0,
        observed=lambda: 0.0,
        # Выборка с ЖИВЫМ разбросом: иначе тест проверял бы сразу две вещи —
        # нулевой эталон и вырожденную выборку — и провал не различал бы их.
        sample=lambda: [-0.01, 0.0, 0.01, 0.005, -0.005],
        statistics={"value": lambda a: float(sum(a) / len(a))},
        skip_reasons=SR,
    )
    try:
        r10zero = sieve_uncertainty(c10zero)
        if r10zero.status == _P and "абсолютная разность" in r10zero.detail:
            ok += 1
            print("  ok   С10 обрабатывает нулевой эталон")
        else:
            fail += 1
            print("  FAIL С10 обрабатывает нулевой эталон (%s)" % r10zero.detail)
    except Exception as e:
        fail += 1
        print("  FAIL С10 обрабатывает нулевой эталон (%r)" % (e,))

    # Вырожденная выборка: разброса нет вовсе, значимость не проверяема. Это
    # ОБЪЯВЛЕННЫЙ пропуск с машинной причиной, а не провал утверждения. Прежде
    # здесь получалось z = +inf и FAIL — инструмент обвинял утверждение в своей
    # собственной неспособности измерить разброс.
    c10deg = _C10(name="вырожденная выборка", stated=1.0,
                  reference=lambda: 1.0, sample=lambda: [1.0, 1.0, 1.0, 1.0],
                  statistics={"value": lambda a: float(sum(a) / len(a))},
                  skip_reasons=SR)
    rdeg = sieve_uncertainty(c10deg)
    if rdeg.status == _S and rdeg.reason_code == "significance_untestable" \
            and rdeg.auto_skip:
        ok += 1
        print("  ok   С10 на вырожденной выборке объявляет пропуск")
    else:
        fail += 1
        print("  FAIL С10 на вырожденной выборке объявляет пропуск (%s/%s)"
              % (rdeg.status, rdeg.reason_code))

    # ПОДСТАВКА к предыдущему: вырожденность не должна проглатывать РЕАЛЬНОЕ
    # расхождение там, где разброс есть. Иначе «пропуск» стал бы способом
    # погасить любое опровержение.
    c10live = _C10(name="живой разброс", stated=1.0, reference=lambda: 1.0,
                   sample=lambda: [1.4, 1.5, 1.45, 1.55, 1.5],
                   statistics={"value": lambda a: float(sum(a) / len(a))},
                   skip_reasons=SR)
    rlive = sieve_uncertainty(c10live)
    if rlive.status == _FL:
        ok += 1
        print("  ok   С10 при живом разбросе ловит расхождение")
    else:
        fail += 1
        print("  FAIL С10 при живом разбросе ловит расхождение (%s)" % rlive.status)

    print("\n  сито С19 достаточность арифметики:")
    from .sieve import sieve_arithmetic, Claim as _C19, PASS as _P, FAIL as _F
    c_ok = _C19(name="x", arithmetic=lambda: {"params": (9, 4, 0, 4, -1),
                                              "rel_uncertainty": 1.7e-11})
    r_ok = sieve_arithmetic(c_ok)
    # ПОДСТАВКА: вымышленная погрешность точнее самой double обязана дать FAIL.
    c_bad = _C19(name="x", arithmetic=lambda: {"params": (9, 4, 0, 4, -1),
                                              "rel_uncertainty": 1e-16})
    r_bad = sieve_arithmetic(c_bad)
    if r_ok.status == _P and r_bad.status == _F:
        ok += 1
        print("  ok   С19 пропускает достаточную и ловит недостаточную точность")
    else:
        fail += 1
        print("  FAIL С19 пропускает достаточную и ловит недостаточную (%s/%s)"
              % (r_ok.status, r_bad.status))
    # без поля сито обязано молчать, а не выносить вердикт
    if sieve_arithmetic(_C19(name="x")).status not in (_P, _F):
        ok += 1
        print("  ok   С19 без данных не выносит вердикт")
    else:
        fail += 1
        print("  FAIL С19 без данных не выносит вердикт")

    print("\n  порог сита С15 (выведенный, не соглашение):")
    from .sieve import sidak_local_alpha, sigma_threshold, _isf_normal
    from .sieve import Claim as _C
    # 1. Порог растёт с размером перебора: 1 гипотеза -> 1,96 сигма (обычные
    # 95 %), 123 201 гипотеза -> около 5 сигм. Это ВЫВОД из поправки Шидака,
    # а не выбранное число.
    z1 = sigma_threshold(_C(name="x", search_size=1))[0]
    zM = sigma_threshold(_C(name="x", search_size=123201))[0]
    if abs(z1 - 1.96) < 0.01 and 4.9 < zM < 5.2:
        ok += 1
        print("  ok   порог выведен из перебора (%.2f -> %.2f сигма)" % (z1, zM))
    else:
        fail += 1
        print("  FAIL порог выведен из перебора (%.3f, %.3f)" % (z1, zM))
    # 2. Без объявленного перебора порог остаётся 3 сигма, но ОБЯЗАН быть
    # помечен словом СОГЛАШЕНИЕ — иначе его примут за выведенный.
    z0, note = sigma_threshold(_C(name="x"))
    if z0 == 3.0 and "СОГЛАШЕНИЕ" in note:
        ok += 1
        print("  ok   порог без перебора помечен как соглашение")
    else:
        fail += 1
        print("  FAIL порог без перебора помечен как соглашение")
    # 3. ПОДСТАВКА: Бонферрони alpha/m обязан отличаться от Шидака настолько,
    # чтобы проверка это видела при малом m (при большом m они сближаются, и
    # там подстановка прошла бы незамеченной).
    a_sid = sidak_local_alpha(0.05, 2)
    if abs(a_sid - 0.05 / 2) > 1e-4:
        ok += 1
        print("  ok   Шидак отличим от Бонферрони при m=2 (%.5f)" % a_sid)
    else:
        fail += 1
        print("  FAIL Шидак отличим от Бонферрони при m=2")
    # 4. Запасной обратный нормальный без scipy совпадает со scipy.
    try:
        from scipy.stats import norm
        d = max(abs(_isf_normal(p) - float(norm.isf(p)))
                for p in (0.025, 1e-4, 1e-7))
        if d < 1e-6:
            ok += 1
            print("  ok   запасной обратный нормальный совпал со scipy (%.1e)" % d)
        else:
            fail += 1
            print("  FAIL запасной обратный нормальный совпал со scipy (%.1e)" % d)
    except ImportError:
        ok += 1
        print("  ok   scipy отсутствует, запасной путь единственный")

    print("\n  модули-эталоны и служебные модули:")
    from . import stats as _stats
    from .coverage import selftest as _cov
    from .family import selftest as _fam
    from .threshold import selftest as _thr
    from .exact import selftest as _exa
    from .meff import selftest as _mef
    from .algebraic import selftest as _alg
    from .proof import selftest as _prf
    from .modgraph import selftest as _mgr
    # Тик 48: порог множественности двумя путями и семантическая предпосылка.
    from .sidak import selftest as _sid
    from .preconditions import selftest as _pre
    mods = [("неопределённость", _stats.selftest, 9), ("покрытие", _cov, 11),
            ("подтипы причины", _reason_subtypes, 14),
        ("вырождение по тождественности", _identity_guards, 10),
            ("граф вызовов: косвенная тавтология", _identity_graph, 18),
            ("метрики согласия формы", _gof_selftest, 6),
        ("причина переворота", _regress_cause, 4),
            ("семейство и множественность", _fam, 14),
            ("порог разрешающей способности", _thr, 9),
            ("достаточность арифметики", _exa, 5),
            ("эффективное число попыток", _mef, 11),
            ("алгебраическая объяснимость", _alg, 8),
            # Новые модули тика 42 возвращают пару (прошло, провалено),
            # поэтому берётся второй элемент — число провалов.
            ("машинный след анализатора", lambda: _prf()[1], 17),
            ("межмодульный граф", lambda: _mgr()[1], 17),
            ("порог множественности: два пути", _sid, 24),
            ("предпосылка независимости испытаний", _pre, 20)]
    if os.environ.get("GOLDSIEVE_FULL"):
        from .refs.khinchin_reference import selftest as _kh
        from .refs.gue_montecarlo import selftest as _mc
        mods += [("эталон Хинчина", _kh, 3), ("Монте-Карло GUE", _mc, 5)]
    for name, fn, n in mods:
        print("  -- %s" % name)
        f = fn()
        fail += f
        ok += n - f

    print("\n  итог: %d пройдено, %d провалено" % (ok, fail))
    return fail


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
