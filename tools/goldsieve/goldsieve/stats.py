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


def acf_block_length(sample: Sequence[float], max_lag: int = 200) -> int:
    """Длина блока из автокорреляции: 2*tau по правилу Соколя.

    Обычный бутстрэп предполагает независимость наблюдений. Для зависимой
    выборки он занижает разброс, а значит ЗАВЫШАЕТ значимость расхождения —
    ровно та ошибка, против которой стоит сито С10. Длина блока не назначается
    рукой, а ВЫВОДИТСЯ из интегрального времени автокорреляции: tau = 1 + 2*sum
    rho_k по первым лагам до первого неположительного значения.
    """
    x = np.asarray(sample, dtype=float)
    n = len(x)
    if n < 50:
        return 1
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom <= 0:
        return 1
    tau = 1.0
    for k in range(1, min(max_lag, n - 1) + 1):
        rho = float(np.dot(x[:-k], x[k:])) / denom
        if rho <= 0.0:
            break
        tau += 2.0 * rho
    return int(max(1, min(round(2.0 * tau), n // 20)))


def _moving_block_indices(n: int, block: int, rng) -> np.ndarray:
    """Индексы бутстрэпа скользящими блоками (Kunsch 1989)."""
    if block <= 1:
        return rng.integers(0, n, n)
    starts = rng.integers(0, n - block + 1, int(np.ceil(n / block)))
    idx = (starts[:, None] + np.arange(block)[None, :]).ravel()
    return idx[:n]


def bootstrap_ci(sample: Sequence[float], stat: Callable[[np.ndarray], float],
                 b: int = 400, alpha: float = 0.05, seed: int = 20260813,
                 block=None):
    """Процентильный бутстрэп: (оценка, низ, верх, полуширина/оценка).

    block: None — независимые наблюдения; "auto" — длина блока выводится из
    автокорреляции; целое — задана вручную. Для зависимых данных блочный
    бутстрэп даёт ШИРЕ интервал, то есть более осторожный вывод.
    """
    x = np.asarray(sample, dtype=float)
    n = len(x)
    if block == "auto":
        block = acf_block_length(x)
    block = int(block or 1)
    rng = np.random.default_rng(seed)
    vals = np.empty(b)
    for i in range(b):
        vals[i] = stat(x[_moving_block_indices(n, block, rng)])
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


def _selftest_block(rng) -> int:
    """Блочный бутстрэп обязан быть ШИРЕ независимого на зависимой выборке.

    Подставка стоит там, где неверный ответ отличается: на белом шуме блочный
    интервал НЕ должен раздуваться, иначе метод просто портит все оценки.
    """
    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    n = 20000
    e = rng.normal(size=n)
    ar = np.empty(n)
    ar[0] = e[0]
    for i in range(1, n):
        ar[i] = 0.8 * ar[i - 1] + e[i]
    f = lambda a: float(a.mean())
    _, lo_i, hi_i, _ = bootstrap_ci(ar, f)
    _, lo_b, hi_b, _ = bootstrap_ci(ar, f, block="auto")
    check("блочный интервал шире независимого на AR(1): %.2f против %.2f"
          % (100 * (hi_b - lo_b), 100 * (hi_i - lo_i)),
          (hi_b - lo_b) > 1.5 * (hi_i - lo_i))

    w = rng.normal(size=n)
    _, lo_i, hi_i, _ = bootstrap_ci(w, f)
    _, lo_b, hi_b, _ = bootstrap_ci(w, f, block="auto")
    check("на белом шуме блочный интервал не раздувается",
          (hi_b - lo_b) < 1.6 * (hi_i - lo_i))

    k_ar, k_w = acf_block_length(ar), acf_block_length(w)
    check("длина блока у AR(1) больше, чем у шума: %d против %d" % (k_ar, k_w),
          k_ar > k_w)
    return fail


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

    fail += _selftest_block(rng)
    return fail


if __name__ == "__main__":
    print("самопроверка модуля неопределённости:")
    raise SystemExit(1 if selftest() else 0)
