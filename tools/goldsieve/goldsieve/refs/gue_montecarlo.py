"""Независимый эталон закона расстояний GUE: Монте-Карло по матрицам.

Зачем: refs/gue_exact_gap.py считает E2(s) = det(I - K_s) методом Нюстрёма. Если
ошибка сидит в самой постановке (ядро, нормировка, развёртка), то любое
уточнение сетки её не покажет — С6 пройдёт. Здесь та же величина получается
принципиально другим путём: диагонализуем случайные эрмитовы матрицы из
ансамбля GUE, разворачиваем спектр по полукруговому закону Вигнера и меряем
расстояния между соседями напрямую.

Ансамбль: H = (A + A^H)/2, A с независимыми комплексными гауссовыми элементами.

Развёртка сделана БЕЗ полукругового закона: расстояния в середине спектра
делятся на среднее по своему короткому окну (по умолчанию 60 подряд идущих
расстояний). Плотность на таком окне почти постоянна, поэтому окно снимает и
масштаб матрицы, и любую ошибку нормировки ансамбля — то есть Монте-Карло не
наследует ни одной константы из точного расчёта. Первая версия этого файла
делила на полукруговую плотность и дала промах -25% по всем статистикам:
нормировка ансамбля не совпадала с радиусом 2. Ошибка поймана этой же
самопроверкой, а не рассуждением.

Берётся только середина спектра (|x| < 1 после деления на sqrt(n)), где
плотность гладкая, а краевой режим Трейси-Видома не мешает.
"""

from __future__ import annotations

import numpy as np


def gue_spacings(n: int = 600, reps: int = 30, bulk: float = 1.0,
                 window: int = 60, seed: int = 20260813) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        a = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) / np.sqrt(2.0)
        h = (a + a.conj().T) / 2.0
        ev = np.linalg.eigvalsh(h) / np.sqrt(n)
        mid = ev[np.abs(ev) < bulk]
        d = np.diff(mid)
        k = (len(d) // window) * window
        if k == 0:
            continue
        blocks = d[:k].reshape(-1, window)
        out.append((blocks / blocks.mean(axis=1, keepdims=True)).ravel())
    return np.concatenate(out)


def mc_summary(n: int = 600, reps: int = 30, seed: int = 20260813) -> dict:
    s = gue_spacings(n=n, reps=reps, seed=seed)
    return {"std": float(s.std(ddof=1)),
            "p50": float(np.percentile(s, 50)),
            "p90": float(np.percentile(s, 90)),
            "p95": float(np.percentile(s, 95)),
            "p99": float(np.percentile(s, 99)),
            "n": int(s.size)}


def selftest() -> int:
    from .gue_exact_gap import GapLaw
    fail = 0
    law = GapLaw()
    mc = mc_summary(n=400, reps=12, seed=5)
    exact = {"std": law.std(), "p50": law.quantile(0.50),
             "p90": law.quantile(0.90), "p95": law.quantile(0.95)}
    for k in ("std", "p50", "p90", "p95"):
        dev = (mc[k] - exact[k]) / exact[k]
        ok = abs(dev) < 0.02
        print("  %s %s: Монте-Карло %.6f, детерминант %.6f, расхождение %+.2f%%"
              % ("ok  " if ok else "FAIL", k, mc[k], exact[k], 100 * dev))
        fail += 0 if ok else 1

    # Подставка: пуассоновский поток обязан РАЗОЙТИСЬ с законом GUE, иначе
    # сравнение ничего не проверяет
    rng = np.random.default_rng(3)
    poisson = rng.exponential(size=mc["n"])
    dev = (poisson.std(ddof=1) - exact["std"]) / exact["std"]
    ok = abs(dev) > 0.5
    print("  %s подставка (пуассон) отклонена: %+.1f%% по std"
          % ("ok  " if ok else "FAIL", 100 * dev))
    fail += 0 if ok else 1
    return fail


if __name__ == "__main__":
    print("самопроверка независимого эталона GUE (Монте-Карло):")
    raise SystemExit(1 if selftest() else 0)
