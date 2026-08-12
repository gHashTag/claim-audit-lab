"""Задача: константа Хинчина у частных цепной дроби нулей дзеты.

Вторая задача нужна для проверки переносимости сита: та же машинерия, другая
математика. Эталон считается по произведению Хинчина (не цитируется), контроль
— равномерные случайные числа, подставка — золотое сечение, у которого все
частные равны единице.
"""

import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402
from goldsieve.refs.khinchin_finite_sample import partial_quotients, geo_mean  # noqa: E402

ZEROS = "/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt"
TERMS = 30
SAMPLES = 500


def khinchin_reference(nmax=200000):
    """K = prod_{n>=1} (1 + 1/(n(n+2)))^{log2 n}. Считается, а не цитируется."""
    s = 0.0
    for n in range(1, nmax + 1):
        s += math.log2(n) * math.log1p(1.0 / (n * (n + 2.0)))
    return math.exp(s)


def zeros():
    return np.loadtxt(ZEROS)


def observed_pooled():
    """Пулированная оценка: геометрическое среднее по ВСЕМ частным разом."""
    g = zeros()[:SAMPLES]
    a = []
    for x in g:
        a += partial_quotients(float(x) - math.floor(float(x)), TERMS)
    return geo_mean(a)


def observed_binned():
    """По-корзинно: среднее геометрических средних отдельных разложений.

    Именно эта оценка давала «дефицит»: усреднение логарифмов внутри короткого
    разложения смещает оценку вниз.
    """
    g = zeros()[:SAMPLES]
    vals = [geo_mean(partial_quotients(float(x) - math.floor(float(x)), TERMS))
            for x in g]
    return float(np.mean(vals))


def control_uniform():
    rng = random.Random(20260813)
    a = []
    for _ in range(SAMPLES):
        a += partial_quotients(rng.random(), TERMS)
    return geo_mean(a)


def golden_ratio_answer():
    """Подставка: у phi все частные равны 1, геометрическое среднее 1."""
    phi = (1.0 + 5.0 ** 0.5) / 2.0
    return geo_mean(partial_quotients(phi, TERMS))


def by_terms():
    """Корзины по длине разложения: x = 1/TERMS -> 0 при бесконечном разложении."""
    g = zeros()[:SAMPLES]
    out = []
    for m in (10, 15, 20, 30, 45, 70):
        vals = [geo_mean(partial_quotients(float(x) - math.floor(float(x)), m))
                for x in g]
        out.append((1.0 / m, float(np.mean(vals))))
    return out


CLAIMS = [
    Claim(
        name="K по нулям дзеты = 2.620, систематически ниже 2.685",
        source="data/zeta/zeta_bin_analysis_update.md",
        stated=2.620,
        reference=khinchin_reference,
        observed=observed_binned,
        wrong=golden_ratio_answer,
        null_model=control_uniform,
        null_expect=None,
        null_kind="positive",   # равномерные вещественные по теореме Хинчина
                                # генерические: контроль ОБЯЗАН дать K
        tolerance=0.005,
        estimators={"по-корзинно": observed_binned, "пулированно": observed_pooled},
        bins=by_terms,
        precision=1e-9,
        resolutions=[2000, 20000, 200000],
        resolve=khinchin_reference,
    ),
]
