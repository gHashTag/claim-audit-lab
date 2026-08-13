# -*- coding: utf-8 -*-
"""Порог разрешающей способности семейства формул n*3^k*pi^m*phi^p*e^q.

Вопрос, на который отвечает расчёт: при какой относительной точности eps
совпадение с целью перестаёт быть ожидаемым по случаю? Это та точка, где
ожидаемое число случайных попаданий E[h](eps) = 1. Ниже порога совпадение
несёт информацию, выше — не несёт вообще ничего.

Оценка делается двумя независимыми путями (аналитика и Монте-Карло) и
сравнивается — расхождение выше 25 % считается провалом расчёта.
"""
import json
import math
import sys

sys.path.insert(0, "/home/user/workspace/goldsieve")
from goldsieve import family

DECADES = (-1, 4)
RANGES = {
    "объявленные (20 412)": family.STANDARD_RANGES,
    "фактические (123 201)": {"n": range(1, 10), "k": range(-6, 7),
                              "m": range(-4, 5), "p": range(-6, 7),
                              "q": range(-4, 5)},
}


def expected_hits_analytic(eps, ranges):
    """E[h] = M * (плотность членов семейства в полосе шириной 2*eps).

    Семейство приблизительно логарифмически равномерно, поэтому доля членов,
    попадающих в относительную полосу +-eps вокруг случайной цели, равна
    ширине полосы в log10 делённой на размах порядков, занятый семейством
    внутри диапазона целей.
    """
    values = family.enumerate_family(ranges)
    lo, hi = DECADES
    inside = [v for v in values if 10.0 ** lo <= v <= 10.0 ** hi]
    band = 2.0 * eps / math.log(10.0)      # ширина полосы в декадах
    return len(inside) * band / (hi - lo)


def crossover(ranges, empirical=False, trials=400):
    """Двоичный поиск eps, при котором E[h] = 1."""
    lo, hi = 1e-9, 1e-1
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        if empirical:
            _, e = family.empirical_multiplicity(DECADES, mid, ranges=ranges,
                                                 trials=trials, seed=5)
        else:
            e = expected_hits_analytic(mid, ranges)
        if e < 1.0:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


out = {}
for label, ranges in RANGES.items():
    a = crossover(ranges, empirical=False)
    e = crossover(ranges, empirical=True)
    rel = abs(a - e) / e
    out[label] = {"аналитика": a, "монте_карло": e, "расхождение": rel}
    print("%-24s порог eps: аналитика %.3g, Монте-Карло %.3g, расхождение %.1f %%"
          % (label, a, e, 100 * rel))
    if rel > 0.25:
        print("  ПРОВАЛ РАСЧЁТА: два метода расходятся сильнее 25 %")

# Проверка: константы из корпуса против порога.
CONSTS = {
    "tau_n (PDG 2024)": (878.4, 0.5),
    "m_p/m_e (CODATA 2022)": (1836.152673426, 3.2e-8),
    "T_c КХД (HotQCD 2019)": (156.5, 1.5),
    "m_X17 (VNU)": (16.66, math.hypot(0.47, 0.35)),
    "alpha^-1 (CODATA)": (137.035999177, 2.1e-8),
}
thr = out["фактические (123 201)"]["монте_карло"]
print("\nпорог для фактического перебора: eps = %.3g" % thr)
print("%-24s %-12s %-12s %s" % ("величина", "eps опыта", "во сколько", "вывод"))
rows = {}
for name, (v, u) in CONSTS.items():
    eps = u / v
    ratio = eps / thr
    verdict = ("совпадение содержательно" if eps < thr
               else "совпадение ожидается случайно")
    rows[name] = {"eps": eps, "отношение_к_порогу": ratio, "вывод": verdict}
    print("%-24s %-12.3g %-12.3g %s" % (name, eps, ratio, verdict))

json.dump({"порог": out, "константы": rows}, open(
    "/home/user/workspace/loop4/threshold.json", "w"), ensure_ascii=False, indent=1)
print("\nсохранено: /home/user/workspace/loop4/threshold.json")
