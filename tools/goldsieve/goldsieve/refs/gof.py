"""Согласие ФОРМЫ распределения: KS, Андерсон-Дарлинг, энергетическая дистанция.

Зачем отдельный модуль. До лупа 10 разбор расстояний между нулями дзета-функции
опирался на пять точечных статистик (std и четыре квантиля). Такой набор
отвечает на вопрос «совпадают ли отдельные числа», но не на вопрос «та же ли это
форма распределения». Пользователь указал на это прямо: график и вывод были
описательными.

Здесь три метрики согласия, каждая со своим эталоном, вычисляемым из ТОЙ ЖЕ
модели методом Монте-Карло. Эталон для метрики согласия не равен нулю: при
конечной выборке даже верная модель даёт положительную дистанцию. Поэтому
сравнивать наблюдённую дистанцию с нулём нельзя — сравнивается с ожидаемой
дистанцией для выборки того же размера из самой модели.

Опоры:
- Kolmogorov-Smirnov: sup|F_n - F|.
- Anderson-Darling: A^2 = -n - (1/n) sum (2i-1)[ln u_i + ln(1-u_{n+1-i})],
  взвешивает хвосты сильнее KS (Anderson & Darling 1954).
- Энергетическая дистанция между выборками (Szekely & Rizzo 2013):
  E = 2*E|X-Y| - E|X-X'| - E|Y-Y'|; неотрицательна и равна нулю только при
  совпадении распределений.
"""

from __future__ import annotations

import numpy as np


def ks_distance(x, cdf) -> float:
    """sup|F_n - F| по значениям выборки."""
    xs = np.sort(np.asarray(x, dtype=float))
    n = len(xs)
    u = np.clip(np.asarray(cdf(xs), dtype=float), 0.0, 1.0)
    emp_hi = np.arange(1, n + 1) / n
    emp_lo = np.arange(0, n) / n
    return float(max(np.max(emp_hi - u), np.max(u - emp_lo)))


def ad_statistic(x, cdf) -> float:
    """Статистика Андерсона-Дарлинга A^2 (полностью заданная модель)."""
    xs = np.sort(np.asarray(x, dtype=float))
    n = len(xs)
    u = np.clip(np.asarray(cdf(xs), dtype=float), 1e-12, 1.0 - 1e-12)
    i = np.arange(1, n + 1)
    a2 = -n - float(np.sum((2 * i - 1) * (np.log(u) + np.log(1.0 - u[::-1])))) / n
    return a2


def energy_distance(x, y, cap: int = 4000, seed: int = 20260814) -> float:
    """Энергетическая дистанция между двумя выборками.

    Полная формула квадратична по размеру выборки, поэтому обе выборки
    прореживаются до cap точек СЛУЧАЙНО и с фиксированным сидом: прореживание
    входит в отпечаток рецепта и не зависит от порядка данных.
    """
    rng = np.random.default_rng(seed)
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if len(a) > cap:
        a = a[rng.choice(len(a), cap, replace=False)]
    if len(b) > cap:
        b = b[rng.choice(len(b), cap, replace=False)]

    def mean_abs(p, q):
        return float(np.mean(np.abs(p[:, None] - q[None, :])))

    return 2.0 * mean_abs(a, b) - mean_abs(a, a) - mean_abs(b, b)


def sample_from_cdf(cdf, n: int, rng, lo: float = 0.0, hi: float = 8.0,
                    grid: int = 4001) -> np.ndarray:
    """Выборка из модели обратным преобразованием по сетке CDF."""
    s = np.linspace(lo, hi, grid)
    u = np.clip(np.asarray(cdf(s), dtype=float), 0.0, 1.0)
    u = np.maximum.accumulate(u)
    return np.interp(rng.random(n), u, s)


def null_metrics(cdf, n: int, reps: int = 40, seed: int = 20260814,
                 metrics=("ks", "ad", "energy")) -> dict:
    """Ожидаемые дистанции для ВЕРНОЙ модели при выборке размера n.

    Возвращает словарь «метрика -> (среднее, стандартное отклонение)».
    Это и есть вычисляемый эталон: не нуль, а конечновыборочное ожидание.
    """
    rng = np.random.default_rng(seed)
    ks, ad, en = [], [], []
    ref = sample_from_cdf(cdf, min(n, 1200), rng) if "energy" in metrics else None
    for _ in range(reps):
        y = sample_from_cdf(cdf, n, rng)
        if "ks" in metrics:
            ks.append(ks_distance(y, cdf))
        if "ad" in metrics:
            ad.append(ad_statistic(y, cdf))
        if "energy" in metrics:
            en.append(energy_distance(y, ref, cap=1200))
    out = {}
    for name, vals in (("ks", ks), ("ad", ad), ("energy", en)):
        if name not in metrics:
            continue
        v = np.asarray(vals, dtype=float)
        out[name] = (float(v.mean()), float(v.std(ddof=1)))
    return out


def selftest() -> int:
    """Самопроверка с подставкой: у каждого модуля-эталона своя.

    Подставка стоит там, где неверный ответ реально отличается: метрики
    считаются для выборки из ПРАВИЛЬНОЙ модели и для выборки из смещённой
    (сдвиг масштаба 8%). Если метрика не различает эти два случая, она не годится
    для разговора о форме распределения.
    """
    fail = 0
    rng = np.random.default_rng(3)

    # Модель: экспоненциальное распределение (аналитическая CDF).
    cdf = lambda s: 1.0 - np.exp(-np.asarray(s, dtype=float))
    n = 4000
    good = rng.exponential(size=n)
    bad = rng.exponential(size=n) * 1.08

    ks_g, ks_b = ks_distance(good, cdf), ks_distance(bad, cdf)
    ok = ks_b > 2.0 * ks_g
    print("  %s KS различает верную и смещённую модель: %.4f против %.4f"
          % ("ok  " if ok else "FAIL", ks_b, ks_g))
    fail += 0 if ok else 1

    ad_g, ad_b = ad_statistic(good, cdf), ad_statistic(bad, cdf)
    ok = ad_b > 3.0 * ad_g and ad_g > 0
    print("  %s AD различает верную и смещённую модель: %.3f против %.3f"
          % ("ok  " if ok else "FAIL", ad_b, ad_g))
    fail += 0 if ok else 1

    ref = sample_from_cdf(cdf, 3000, np.random.default_rng(9))
    en_g, en_b = energy_distance(good, ref), energy_distance(bad, ref)
    ok = en_b > 3.0 * en_g and en_g >= 0
    print("  %s энергетическая дистанция различает модели: %.5f против %.5f"
          % ("ok  " if ok else "FAIL", en_b, en_g))
    fail += 0 if ok else 1

    # Обратное преобразование обязано воспроизводить саму модель: средняя
    # выборки из экспоненты равна 1, а KS остаётся на уровне шума.
    y = sample_from_cdf(cdf, 20000, np.random.default_rng(5))
    ok = abs(float(y.mean()) - 1.0) < 0.05 and ks_distance(y, cdf) < 0.02
    print("  %s обратное преобразование воспроизводит модель: mean %.4f, KS %.4f"
          % ("ok  " if ok else "FAIL", float(y.mean()), ks_distance(y, cdf)))
    fail += 0 if ok else 1

    # Эталон конечной выборки: наблюдённая KS верной модели лежит в пределах
    # трёх сигм от ожидания, а смещённой — выходит далеко за них.
    # Размер выборки здесь БОЛЬШЕ, чем в тестах различимости выше, и это не
    # подгонка порога: шум KS убывает как 1/sqrt(n), а систематическое смещение
    # модели не убывает вовсе, поэтому требование z > 6 выполняется за счёт
    # выборки, а не за счёт ослабления требования. При n = 4000 то же смещение
    # даёт z = 4,8 — тест ловил бы смещение, но не с заявленным запасом.
    n2 = 16000
    rng2 = np.random.default_rng(11)
    good2 = rng2.exponential(size=n2)
    bad2 = rng2.exponential(size=n2) * 1.08
    nm = null_metrics(cdf, n2, reps=20)
    mu, sd = nm["ks"]
    z_g = (ks_distance(good2, cdf) - mu) / sd
    z_b = (ks_distance(bad2, cdf) - mu) / sd
    ok = abs(z_g) < 3.5 and z_b > 6.0
    print("  %s эталон конечной выборки: z верной %.2f, z смещённой %.2f"
          % ("ok  " if ok else "FAIL", z_g, z_b))
    fail += 0 if ok else 1

    # Подставка на сам эталон: разброс обязан быть положительным, иначе
    # деление на него дало бы бесконечные сигмы и ложную значимость.
    ok = all(v[1] > 0 for v in nm.values())
    print("  %s разброс эталона положителен по всем трём метрикам"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    return fail


if __name__ == "__main__":
    print("самопроверка метрик согласия формы:")
    raise SystemExit(1 if selftest() else 0)
