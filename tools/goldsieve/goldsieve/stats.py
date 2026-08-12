"""Неопределённость измерения: бутстрэп, выводимая терпимость, множественность.

Зачем: до этого модуля всё сито сравнивало точку с точкой, а терпимость
назначалась рукой. Это тот же класс дефекта, на который сито охотится, — число
без вывода. Здесь терпимость выводится из данных.

Опора (см. references/theory.md):
- Состоятельность бутстрэпа для выборочных квантилей при непрерывной плотности
  в точке квантиля (Bickel-Freedman 1981; Falk-Reiss 1989).
- Неравенство Дворецкого-Кифера-Вольфовица с постоянной Массара (1990):
  P(sup|F_n - F| > e) <= 2 exp(-2 n e^2) — даёт непараметрическую полосу для CDF
  без всякого бутстрэпа, годится как перекрёстная проверка ширины интервала.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np


def bootstrap_ci(sample: Sequence[float], stat: Callable[[np.ndarray], float],
                 b: int = 400, alpha: float = 0.05, seed: int = 20260813):
    """Процентильный бутстрэп: (оценка, низ, верх, полуширина/оценка)."""
    x = np.asarray(sample, dtype=float)
    n = len(x)
    rng = np.random.default_rng(seed)
    vals = np.empty(b)
    for i in range(b):
        vals[i] = stat(x[rng.integers(0, n, n)])
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    point = float(stat(x))
    half = (hi - lo) / 2.0
    return point, float(lo), float(hi), (half / abs(point) if point else float("inf"))


def dkw_band(n: int, alpha: float = 0.05) -> float:
    """Полоса ДКВ с постоянной Массара: sup|F_n - F| <= sqrt(ln(2/alpha)/(2n)).

    Верна для ЛЮБОГО непрерывного распределения и любого n, без асимптотики.
    """
    return math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


def quantile_ci_dkw(sample: Sequence[float], q: float, alpha: float = 0.05):
    """Интервал для квантиля через полосу ДКВ: непараметрический, без бутстрэпа.

    Инвертирование полосы: если |F_n - F| <= e всюду, то истинный q-квантиль
    лежит между выборочными квантилями уровней q-e и q+e.
    """
    x = np.sort(np.asarray(sample, dtype=float))
    n = len(x)
    e = dkw_band(n, alpha)
    lo_q, hi_q = max(0.0, q - e), min(1.0, q + e)
    return (float(np.quantile(x, lo_q)), float(np.quantile(x, hi_q)), e)


def sidak_alpha(alpha: float, m: int) -> float:
    """Поправка Шидака на m сравнений: 1-(1-alpha)^(1/m). Консервативнее не бывает
    без учёта зависимости, но честнее, чем брать худшее из m без поправки."""
    m = max(1, int(m))
    return 1.0 - (1.0 - alpha) ** (1.0 / m)


def z_of_deviation(point: float, ref: float, half_width: float) -> float:
    """Отклонение в единицах полуширины интервала. |z|<=1 — совместимо с эталоном."""
    if half_width == 0:
        return float("inf") if point != ref else 0.0
    return (point - ref) / half_width


def selftest() -> int:
    fail = 0
    rng = np.random.default_rng(7)

    # 1. Бутстрэп накрывает истинную дисперсию нормального образца
    x = rng.normal(size=20000)
    p, lo, hi, rel = bootstrap_ci(x, lambda a: a.std(ddof=1), b=200)
    ok = lo <= 1.0 <= hi
    print("  %s бутстрэп для std N(0,1): [%.4f, %.4f], +-%.2f%%"
          % ("ok  " if ok else "FAIL", lo, hi, 100 * rel))
    fail += 0 if ok else 1

    # 2. Подставка: бутстрэп НЕ должен накрывать заведомо неверное значение
    ok = not (lo <= 1.25 <= hi)
    print("  %s подставка std=1.25 вне интервала" % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    # 3. Ширина интервала падает как 1/sqrt(n)
    _, _, _, r1 = bootstrap_ci(rng.normal(size=2000), lambda a: a.std(ddof=1), b=200)
    _, _, _, r2 = bootstrap_ci(rng.normal(size=32000), lambda a: a.std(ddof=1), b=200)
    ratio = r1 / r2
    ok = 2.5 < ratio < 5.5           # ожидается 4 при 16-кратном росте n
    print("  %s ширина падает как 1/sqrt(n): отношение %.2f (ожидается ~4)"
          % ("ok  " if ok else "FAIL", ratio))
    fail += 0 if ok else 1

    # 4. Полоса ДКВ: эмпирическая CDF не выходит за неё (проверяем на 200 выборках)
    n, alpha = 2000, 0.05
    e = dkw_band(n, alpha)
    viol = 0
    for _ in range(200):
        y = np.sort(rng.random(n))
        emp = np.arange(1, n + 1) / n
        if np.max(np.abs(emp - y)) > e:
            viol += 1
    ok = viol <= 10                   # допустимо не более ~5% нарушений
    print("  %s полоса ДКВ e=%.4f нарушена в %d из 200 выборок"
          % ("ok  " if ok else "FAIL", e, viol))
    fail += 0 if ok else 1

    # 5. Подставка для ДКВ: заведомо маленькая полоса ОБЯЗАНА нарушаться часто
    viol = 0
    for _ in range(200):
        y = np.sort(rng.random(n))
        emp = np.arange(1, n + 1) / n
        if np.max(np.abs(emp - y)) > e / 4.0:
            viol += 1
    ok = viol > 100
    print("  %s урезанная полоса e/4 нарушена в %d из 200 выборок"
          % ("ok  " if ok else "FAIL", viol))
    fail += 0 if ok else 1

    # 6. Поправка Шидака монотонна и меньше alpha
    a = sidak_alpha(0.05, 5)
    ok = 0.0 < a < 0.05 and sidak_alpha(0.05, 20) < a
    print("  %s поправка Шидака: alpha_5 = %.5f" % ("ok  " if ok else "FAIL", a))
    fail += 0 if ok else 1

    return fail


if __name__ == "__main__":
    print("самопроверка модуля неопределённости:")
    raise SystemExit(1 if selftest() else 0)
