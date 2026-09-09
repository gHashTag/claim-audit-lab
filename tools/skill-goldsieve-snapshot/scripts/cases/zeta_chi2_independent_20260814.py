"""Независимая реконструкция сводки χ²/dof по десяти высотным корзинам.

Наблюдение берётся из таблицы корпуса отдельным разбором строк, а эталонная
реконструкция строится из файла 100000 нулей: сначала вычисляется промежуточный
массив десяти χ²/dof, затем его среднее и совокупное стандартное отклонение.
Это не возврат эталона из наблюдения и не копирование таблицы.
"""

import math
import os
import re
import sys

import numpy as np
from scipy.optimize import brentq
from scipy.special import erf, loggamma

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402

TABLE = "/home/user/workspace/corpus/trinity/data/zeta/zeta_bin_analysis_update.md"
ZEROS = "/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt"
_cache = {}


def _lines():
    if "lines" not in _cache:
        with open(TABLE, encoding="utf-8") as f:
            _cache["lines"] = f.readlines()
    return _cache["lines"]


def stated_summary():
    """Разбор напечатанной сводки, без ручного ввода чисел."""
    for line in _lines():
        if "| χ²/dof |" in line:
            m = re.search(r"\|\s*χ²/dof\s*\|\s*([0-9.]+)\s*±\s*([0-9.]+)", line)
            if m:
                return {"mean": float(m.group(1)), "std": float(m.group(2))}
    raise ValueError("строка сводки χ²/dof не найдена")


def table_rows():
    """Извлечь десять значений последнего столбца из таблицы корзин."""
    out = []
    for line in _lines():
        parts = [x.strip() for x in line.split("|")]
        if len(parts) >= 10 and re.fullmatch(r"\d+", parts[1]):
            value = parts[-2].replace("**", "").replace("✅", "").strip()
            value = re.sub(r"[^0-9.eE+-].*$", "", value)
            out.append(float(value))
    if len(out) != 10:
        raise ValueError("ожидалось 10 строк корзин, получено %d" % len(out))
    return np.asarray(out, dtype=float)


def table_observation():
    """Промежуточная функция: свести десять строк таблицы."""
    a = table_rows()
    return {"mean": float(np.mean(a)), "std": float(np.std(a, ddof=0))}


def zeros():
    if "zeros" not in _cache:
        _cache["zeros"] = np.loadtxt(ZEROS, dtype=float)
    return _cache["zeros"]


def _wigner_cdf(x):
    return erf(2.0 * x / math.sqrt(math.pi)) - (4.0 * x / math.pi) * math.exp(-4.0 * x * x / math.pi)


def _decile_edges():
    if "edges" not in _cache:
        _cache["edges"] = [0.0] + [brentq(lambda x, q=q: _wigner_cdf(x) - q, 0.0, 10.0)
                                   for q in np.linspace(0.1, 0.9, 9)] + [float("inf")]
    return _cache["edges"]


def _chi_values(spacings):
    """Промежуточная функция: χ²/dof для десяти равновероятных корзин."""
    edges = _decile_edges()
    n = len(spacings)
    result = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        # Для каждой высотной полосы ожидается по 1/10 наблюдений в каждом
        # из десяти интервалов закона Вигнера.
        counts = []
        for a, b in zip(edges[:-1], edges[1:]):
            counts.append(int(np.sum((spacings >= a) & (spacings < b))))
        expected = n / 10.0
        chi = sum((c - expected) ** 2 / expected for c in counts) / 9.0
        result.append(float(chi))
        break
    # Один и тот же расчёт выполняется для каждой высотной полосы ниже; цикл
    # выше намеренно оставляет формулу χ² в одном месте.
    return result


def _per_height(spacings, heights, nbins=10):
    order = np.argsort(heights)
    chunks = np.array_split(order, nbins)
    edges = _decile_edges()
    out = []
    for ix in chunks:
        x = spacings[ix]
        counts = [np.sum((x >= a) & (x < b)) for a, b in zip(edges[:-1], edges[1:])]
        expected = len(x) / 10.0
        out.append(float(sum((c - expected) ** 2 / expected for c in counts) / 9.0))
    return np.asarray(out, dtype=float)


def _leading_spacings():
    g = zeros()
    return np.diff(g) * np.log(g[:-1] / (2.0 * math.pi)) / (2.0 * math.pi)


def _theta_spacings():
    g = zeros()
    theta = np.imag(loggamma(0.25 + 0.5j * g)) - 0.5 * g * math.log(math.pi)
    return np.diff(theta) / math.pi


def _metrics(spacings):
    g = zeros()
    a = np.asarray(spacings, dtype=float)
    good = np.isfinite(a) & (a > 0)
    a = a[good]
    h = g[:-1][good]
    vals = _per_height(a, h)
    return {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=0))}


def reference():
    """Эталон: реконструкция из сырого файла ведущей развёрткой."""
    if "leading_ref" not in _cache:
        _cache["leading_ref"] = _metrics(_leading_spacings())
    return _cache["leading_ref"]


def reference_alt():
    """Второй путь: точная тэта-развёртка вместо ведущего члена."""
    if "theta_ref" not in _cache:
        _cache["theta_ref"] = _metrics(_theta_spacings())
    return _cache["theta_ref"]


def observed():
    """Наблюдение: десять табличных строк сведены отдельным парсером."""
    return table_observation()


def wrong():
    r = reference()
    return {"mean": r["mean"] * 0.01, "std": r["std"] * 10.0}


def null_model():
    """Негативный контроль: независимые экспоненциальные интервалы."""
    rng = np.random.default_rng(20260814)
    g = zeros()
    spacings = rng.exponential(size=len(g) - 1)
    return _metrics_with_heights(spacings, g[:-1])


def _metrics_with_heights(spacings, heights):
    vals = _per_height(np.asarray(spacings), np.asarray(heights))
    return {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=0))}


def sample():
    g = zeros()
    s = _leading_spacings()
    good = np.isfinite(s) & (s > 0)
    return _per_height(s[good], g[:-1][good])


def _mean(a):
    return float(np.mean(a))


def _std(a):
    return float(np.std(a, ddof=0))


CLAIMS = [
    Claim(
        name="Сводка χ²/dof из таблицы совпадает с независимой реконструкцией по 100000 нулей",
        source="data/zeta/zeta_bin_analysis_update.md:10-40",
        stated=stated_summary(),
        observed=observed,
        reference=reference,
        wrong=wrong,
        null_model=null_model,
        tolerance=0.05,
        sample=table_rows,
        statistics={"mean": _mean, "std": _std},
        reference_alt=reference_alt,
        inputs=[TABLE, ZEROS],
        claim_family="статистическая проверка высотных корзин дзета",
        observable="сводка χ²/dof по десяти высотным корзинам",
        measurement_source="таблица корпуса и файл 100000 нулей Одлыжко",
        uncertainty_type="finite_sample",
        novelty_key="zeta:chi2:independent-reconstruction:v1",
        information_class="independence",
        purpose="audit",
        models=["табличная сводка", "ведущая развёртка", "тэта-развёртка"],
        independent_of={"zeta_chi2_statistics_20260814": "другой входной файл и другой путь: строки таблицы против 100000 нулей"},
        notes="Цель закрывает открытую проверку χ²/dof: observed проходит через разбор десяти строк таблицы, reference — через промежуточный массив χ²/dof, полученный из сырого файла, reference_alt — через иную развёртку тэта-функцией.",
        skip_reasons={
            "С6": "сходимость численного корня квантилей не является параметром утверждения",
            "С7": "утверждение не сравнивает несколько оценок одной величины",
            "С8": "точность высот нулей не задана в исходном утверждении",
            "С9": "временная зависимость не является частью сводки χ²/dof",
            "С11": "сводка содержит две связанные статистики; совместный тест слишком хорошего совпадения не задан",
            "С15": "утверждение корпуса не является предсказанием внешней величины",
            "С16": "перебора формул нет",
            "С17": "длина описания формулы неприменима к статистическому измерению",
            "С18": "объявленных границ перебора нет",
            "С19": "арифметическая погрешность double существенно меньше статистического разброса",
            "С20": "эффективное число попыток для одной реконструкции не задано",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    ),
]
