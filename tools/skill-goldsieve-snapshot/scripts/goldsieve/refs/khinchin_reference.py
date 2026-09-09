"""Эталон постоянной Хинчина с аналитическим хвостом.

Проблема, которую это закрывает: прямое произведение сходится как O(ln N / N),
и на N = 2·10^5 сито С6 честно показало разброс 6.1e-03 — эталон не сошёлся до
требуемой точности, то есть был непригоден.

Формула (Хинчин):  K = prod_{n>=1} n^{log2(1 + 1/(n(n+2)))},
откуда  ln K = (1/ln2) * sum_{n>=1} ln(n) * ln(1 + 1/(n(n+2))).

Слагаемое разложим: u_n = 1/(n(n+2)),  ln(1+u_n) = u_n - u_n^2/2 + O(n^-6),
u_n = n^-2 - 2 n^-3 + 4 n^-4 - ...,  поэтому
    ln n * ln(1+u_n) = ln n * (n^-2 - 2 n^-3 + 3.5 n^-4 + O(n^-5)).
Хвост считаем интегралами (Эйлер-Маклорен, ведущий член):
    sum_{n>N} ln n / n^2  ~= (ln N + 1)/N        + ln N/(2 N^2)
    sum_{n>N} ln n / n^3  ~= (ln N + 1/2)/(2N^2)
    sum_{n>N} ln n / n^4  ~= (ln N + 1/3)/(3N^3)
Достигнутая на практике устойчивость (измерено самопроверкой): разброс между
N = 2.5e5 и N = 1e6 составляет ~3e-10, то есть отброшенные члены разложения
ln(1+u) и поправки Эйлера-Маклорена дают порядок 1e-10, а не машинный нуль. Для
задач сита этого хватает с запасом в шесть порядков: требуемая точность 5e-4.
Число сравнивать с табличным значением 2.685452001... допустимо только как
перекрёстную проверку — эталоном служит вычисление, а не таблица.
"""

from __future__ import annotations

import math

import numpy as np


def khinchin(nmax: int = 1_000_000) -> float:
    n = np.arange(1, nmax + 1, dtype=float)
    u = 1.0 / (n * (n + 2.0))
    s = float(np.sum(np.log(n) * np.log1p(u)))
    N = float(nmax)
    lnN = math.log(N)
    tail2 = (lnN + 1.0) / N + lnN / (2.0 * N * N)
    tail3 = (lnN + 0.5) / (2.0 * N * N)
    tail4 = (lnN + 1.0 / 3.0) / (3.0 * N ** 3)
    s += tail2 - 2.0 * tail3 + 3.5 * tail4
    return math.exp(s / math.log(2.0))


def khinchin_quadrature(nmax: int = 20_000) -> float:
    """Второй путь: интеграл по мере Гаусса-Кузьмина, плотность 1/((1+x)ln2).

    a_1 = floor(1/x), поэтому ln K = int_0^1 ln(floor(1/x)) / ((1+x) ln2) dx.
    Интеграл берётся численно по каждому промежутку [1/(n+1), 1/n] — другой код и
    другой маршрут, но, честно говоря, алгебраически та же тождественность, так
    что это проверка реализации, а не независимое подтверждение теории.
    """
    from scipy.integrate import quad
    ln2 = math.log(2.0)
    total = 0.0
    for k in range(2, nmax + 1):
        val, _ = quad(lambda x: math.log(k) / ((1.0 + x) * ln2),
                      1.0 / (k + 1.0), 1.0 / k, epsabs=1e-15, epsrel=1e-13)
        total += val
    N = float(nmax)
    lnN = math.log(N)
    total += ((lnN + 1.0) / N + lnN / (2 * N * N)) / ln2 \
        - 2.0 * ((lnN + 0.5) / (2 * N * N)) / ln2
    return math.exp(total)


def selftest() -> int:
    fail = 0
    a = khinchin(250_000)
    b = khinchin(1_000_000)
    stab = abs(a - b) / b
    ok = stab < 1e-8
    print("  %s хвост стабилизирует эталон: K(2.5e5)=%.12f K(1e6)=%.12f, разброс %.1e"
          % ("ok  " if ok else "FAIL", a, b, stab))
    fail += 0 if ok else 1

    # без хвоста разброс обязан быть на порядки хуже — иначе поправка ничего не делает
    def naive(nmax):
        n = np.arange(1, nmax + 1, dtype=float)
        return math.exp(float(np.sum(np.log(n) * np.log1p(1.0 / (n * (n + 2.0)))))
                        / math.log(2.0))
    raw = abs(naive(250_000) - naive(1_000_000)) / b
    ok = raw > 1e-6 and raw / stab > 1e4
    print("  %s без хвоста разброс %.1e, то есть в %.0e раз хуже"
          % ("ok  " if ok else "FAIL", raw, raw / stab))
    fail += 0 if ok else 1

    c = khinchin_quadrature(20_000)
    dev = abs(c - b) / b
    ok = dev < 1e-6
    print("  %s квадратура сходится с произведением: %.12f, расхождение %.1e"
          % ("ok  " if ok else "FAIL", c, dev))
    fail += 0 if ok else 1
    return fail


if __name__ == "__main__":
    print("самопроверка эталона Хинчина:")
    raise SystemExit(1 if selftest() else 0)
