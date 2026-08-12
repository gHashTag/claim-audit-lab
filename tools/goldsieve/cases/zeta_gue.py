"""Задача: расстояния между нулями дзета-функции против GUE.

Показывает, что вся ручная работа предыдущих тиков выражается через сито и
воспроизводится одной командой. Ни одно число здесь не процитировано: эталон
считается детерминантом Фредгольма, наблюдение — из файла нулей, контроль —
пуассоновский процесс, прогнанный тем же конвейером.
"""

import math
import os
import sys

import numpy as np
from scipy.special import loggamma

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402
from goldsieve.refs.gue_exact_gap import GapLaw, surmise_quantile, SURMISE_STD  # noqa: E402

ZEROS = "/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt"

_cache = {}


def zeros():
    if "g" not in _cache:
        _cache["g"] = np.loadtxt(ZEROS)
    return _cache["g"]


def theta(t):
    t = np.asarray(t, dtype=float)
    return np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)


def unfolded(gamma=None):
    g = zeros() if gamma is None else gamma
    return np.diff(theta(g)) / math.pi


def stats(s):
    return {"std": float(np.std(s, ddof=1)),
            "p50": float(np.percentile(s, 50)),
            "p90": float(np.percentile(s, 90)),
            "p95": float(np.percentile(s, 95)),
            "p99": float(np.percentile(s, 99))}


def exact(n=100, h=2.0e-3):
    key = ("law", n, h)
    if key not in _cache:
        law = GapLaw(h=h, n=n)
        _cache[key] = {"std": law.std(), "p50": law.quantile(0.5),
                       "p90": law.quantile(0.9), "p95": law.quantile(0.95),
                       "p99": law.quantile(0.99)}
    return _cache[key]


def surmise():
    return {"std": SURMISE_STD, "p50": surmise_quantile(0.5),
            "p90": surmise_quantile(0.9), "p95": surmise_quantile(0.95),
            "p99": surmise_quantile(0.99)}


def poisson_control():
    """Пуассоновский процесс с той же плотностью, через ту же развёртку."""
    g = zeros()
    rng = np.random.default_rng(20260813)
    grid = np.linspace(g[0], g[-1] * 1.05, 400000)
    th = theta(grid) / math.pi
    u = th[0] + np.cumsum(rng.exponential(size=len(g)))
    u = u[u <= th[-1]]
    t = np.interp(u, th, grid)
    return stats(unfolded(np.asarray(t)))


def leading_unfold():
    g = zeros()
    return stats(np.diff(g) * np.log(g[:-1] / (2.0 * math.pi)) / (2.0 * math.pi))


def height_bins(nbins=10):
    """Корзины по высоте: x = 1/ln(gamma/2pi) -> 0 при бесконечной высоте."""
    g = zeros()
    s = unfolded()
    mid = g[:-1]
    edges = np.quantile(mid, np.linspace(0, 1, nbins + 1))
    out = []
    for i in range(nbins):
        m = (mid >= edges[i]) & (mid <= edges[i + 1])
        x = 1.0 / math.log(float(np.mean(mid[m])) / (2.0 * math.pi))
        out.append((x, stats(s[m])))
    return out


CLAIMS = [
    # 1. То, что стояло в документах: колонка «GUE Expected» 0.91 / 2.15 / 2.75.
    #    Эталон вычислим, значит вердикт может быть по существу.
    Claim(
        name="колонка «GUE Expected» = 0.91 / 2.15 / 2.75",
        source="data/zeta/zeta_gue_analysis_results.md (до правки)",
        stated={"p50": 0.91, "p95": 2.15, "p99": 2.75},
        reference=lambda: {k: exact()[k] for k in ("p50", "p95", "p99")},
        wrong=lambda: {k: surmise()[k] for k in ("p50", "p95", "p99")},
        tolerance=0.01,
        notes="wrong здесь — surmise Вигнера: он отличается от точного закона "
              "лишь на 0.3-0.5%, поэтому при терпимости 1% сито С4 обязано "
              "показать вырождение — и это правда: на этой терпимости surmise "
              "и точный закон неразличимы.",
    ),
    # 2. Surmise как эталон: он и есть тот же класс дефекта, только тоньше.
    Claim(
        name="surmise Вигнера годится как эталон на уровне 2%",
        source="src/sacred/zeta_spacing.zig (после правки wignerCDF)",
        stated=surmise,
        reference=lambda: exact(),
        wrong=lambda: {k: v * 1.05 for k, v in exact().items()},
        tolerance=0.002,
        resolutions=[(60, 4.0e-3), (100, 2.0e-3), (140, 1.0e-3)],
        resolve=lambda r: exact(n=r[0], h=r[1]),
    ),
    # 3. Само наблюдение: дефицит хвостов и дисперсии.
    Claim(
        name="наблюдённые расстояния совпадают с GUE в пределах 1%",
        source="data/zeta/zeros_odlyzko_100k.txt, 100000 нулей",
        stated=lambda: stats(unfolded()),
        observed=lambda: stats(unfolded()),
        reference=lambda: exact(),
        wrong=lambda: {k: v * 1.5 for k, v in exact().items()},
        null_model=poisson_control,
        null_expect={"std": 1.0, "p50": 0.6931, "p90": 2.3026,
                     "p95": 2.9957, "p99": 4.6052},
        tolerance=0.01,
        estimators={"развёртка тэта": lambda: stats(unfolded()),
                    "развёртка ведущим членом": leading_unfold},
        precision=1e-6,
        bins=height_bins,
        notes="Обе развёртки дают одно и то же (сито С7), значит расхождение "
              "не артефакт развёртки.",
    ),
]

CLAIMS[2].stated = stats(unfolded())
