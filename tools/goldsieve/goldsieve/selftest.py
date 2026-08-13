"""Самопроверка самого сита.

Сито — тоже инструмент, и на него распространяется то же правило, что и на всё
остальное: у инструмента обязан быть тест, включая тест на подставленный
неверный ответ. Здесь проверяется, что сито выдаёт нужный вердикт на четырёх
заведомо известных случаях, и что вырожденную проверку оно ловит.
"""

import math

import os

import numpy as np

from .sieve import (Claim, run, CONFIRMED, REFUTED, QUESTION, EMPTY, VOID,
                    PASS, OPEN, FAIL, rel_dev)

# Все пропуски обязаны быть объявлены (сито С13), иначе вердикт ВОПРОС.
SR = {"С%d" % i: "неприменимо к синтетическому случаю" for i in range(1, 19)}


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
        observed=lambda: {k: f(x) for k, f in stat.items()},
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
        external_target=lambda: {"value": 878.4, "uncertainty": 0.5},
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

    # подставка для С15: то же, но формула ушла на 20 сигм -> FAIL
    bad_pred = Claim(
        name="формула разошлась с измерением на 20 сигм",
        stated=888.4,
        reference=lambda: 888.4,
        wrong=lambda: 878.4,
        claim_kind="prediction",
        external_target=lambda: {"value": 878.4, "uncertainty": 0.5},
        skip_reasons=SR,
    )
    st15b = {x.sieve: x.status for x in run(bad_pred).results}["С15 внешняя цель"]
    if st15b == FAIL:
        ok += 1
        print("  ok   %-45s %s" % ("С15 ловит расхождение в 20 сигм", st15b))
    else:
        fail += 1
        print("  FAIL %-45s %s" % ("С15 ловит расхождение в 20 сигм", st15b))

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

    print("\n  модули-эталоны и служебные модули:")
    from . import stats as _stats
    from .coverage import selftest as _cov
    from .family import selftest as _fam
    mods = [("неопределённость", _stats.selftest, 6), ("покрытие", _cov, 3),
            ("семейство и множественность", _fam, 14)]
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
