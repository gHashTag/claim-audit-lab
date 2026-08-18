"""Паспорт развёртки дзета: независимое воспроизведение 0,42201569295012265.

Наблюдение берётся из строки отчёта, а не из эталона. Эталон Wigner—surmise
получается двумя разными интегральными путями. Отдельно тем же паспортом
вычисляются точная развёртка θ и развёртка по ведущей плотности для файла
нулей: обе дают 0,4009. Точный закон GUE считается третьим, более строгим
ориентиром и показывает, что 0,4220 — именно Wigner—surmise, а не точный GUE.
"""

import math
import re
import statistics

import numpy as np
from scipy.special import loggamma

from goldsieve.refs.gue_exact_gap import GapLaw
from goldsieve.sieve import Claim


ZEROS = (
    "/home/user/workspace/corpus/trinity/data/zeta/"
    "zeros_odlyzko_100k.txt"
)
REPORT = (
    "/home/user/workspace/corpus/trinity/data/zeta/"
    "zeta_gue_analysis_results.md"
)

_CACHE = {}


def _zeros():
    with open(ZEROS, encoding="utf-8") as handle:
        return [float(line.strip()) for line in handle if line.strip()]


def _stated():
    with open(REPORT, encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(
        r"\| Std deviation \| ([0-9.]+) \| ([0-9.]+) \|", text
    )
    if not match:
        raise AssertionError("строка Std deviation не найдена")
    return {"corpus_std": float(match.group(1)),
            "wigner_std": float(match.group(2))}


def _observed():
    """Другой парсер той же строки: разбирает таблицу по заголовку и колонкам."""
    with open(REPORT, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    header = next(
        i for i, line in enumerate(lines)
        if line.startswith("| Metric | Value | GUE (computed) |")
        or line.startswith("| Metric | Value | GUE Wigner surmise (computed) |")
    )
    columns = {}
    for line in lines[header + 1:]:
        if not line.startswith("| ") or line.startswith("|--------"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[0] == "Std deviation":
            columns["corpus_std"] = float(cells[1])
            columns["wigner_std"] = float(cells[2])
            return columns
    raise AssertionError("строка Std deviation не разобрана")


def _wigner_closed():
    return math.sqrt(3.0 * math.pi / 8.0 - 1.0)


def _wigner_density_quad():
    """Интеграл по плотности, mpmath 50 знаков."""
    import mpmath as mp

    with mp.workdps(50):
        density = lambda s: (32 / mp.pi**2) * s**2 * mp.e**(
            -4 * s**2 / mp.pi
        )
        m1 = mp.quad(lambda s: s * density(s), [0, mp.inf])
        m2 = mp.quad(lambda s: s**2 * density(s), [0, mp.inf])
        return float(mp.sqrt(m2 - m1**2))


def _wigner_survival_quad():
    """Тот же закон через функцию выживания, без интегрирования плотности."""
    def cdf(s):
        return (
            math.erf(2.0 * s / math.sqrt(math.pi))
            - (4.0 * s / math.pi) * math.exp(-4.0 * s * s / math.pi)
        )

    x, w = np.polynomial.legendre.leggauss(4000)
    s = 15.0 * (x + 1.0)
    weights = 15.0 * w
    survival = np.array([1.0 - cdf(v) for v in s])
    m1 = float(np.sum(weights * survival))
    m2 = float(np.sum(weights * 2.0 * s * survival))
    return math.sqrt(m2 - m1 * m1)


def _theta_std():
    if "theta" not in _CACHE:
        g = np.asarray(_zeros(), dtype=float)
        theta = np.imag(loggamma(0.25 + 0.5j * g))
        theta -= 0.5 * g * math.log(math.pi)
        _CACHE["theta"] = float(np.std(np.diff(theta) / math.pi, ddof=1))
    return _CACHE["theta"]


def _leading_std():
    g = _zeros()
    gaps = [
        (g[i + 1] - g[i]) * math.log(g[i] / (2.0 * math.pi))
        / (2.0 * math.pi)
        for i in range(len(g) - 1)
    ]
    return statistics.stdev(gaps)


def _exact_gue_std():
    if "exact_gue" not in _CACHE:
        _CACHE["exact_gue"] = GapLaw(h=2.0e-3, n=100).std()
    return _CACHE["exact_gue"]


def _reference():
    """Wigner reference plus raw-zero diagnostics, all computed."""
    return {
        "wigner_std": _wigner_density_quad(),
        "corpus_std": _theta_std(),
        "exact_gue_std": _exact_gue_std(),
    }


def _reference_alt():
    """Независимые пути: выживание Wigner и ведущий член плотности."""
    return {
        "wigner_std": _wigner_survival_quad(),
        "corpus_std": _leading_std(),
    }


def _wrong():
    return {"corpus_std": 0.5, "wigner_std": 0.5}


def _negative_control():
    return {"corpus_std": 1.0, "wigner_std": 1.0}


def _alt_tolerance():
    """Порог второго метода из напечатанной точности, не из его результата."""
    return 5.0e-5 / 0.4009


def _selfcheck():
    stated = _stated()
    observed = _observed()
    reference = _reference()
    alternate = _reference_alt()
    assert stated == {"corpus_std": 0.4009, "wigner_std": 0.4220}
    assert observed == stated
    assert abs(reference["wigner_std"] - 0.42201569295012265) < 1e-12
    assert abs(alternate["wigner_std"] - reference["wigner_std"]) < 1e-9
    assert abs(reference["corpus_std"] - 0.4009) < 5e-5
    assert abs(alternate["corpus_std"] - 0.4009) < 5e-5
    assert reference["exact_gue_std"] - reference["wigner_std"] > 1e-3
    assert _wrong() != reference
    assert _negative_control() != reference


_selfcheck()


CLAIMS = [
    Claim(
        name=(
            "Паспорт развёртки дзета воспроизводит std "
            "0,42201569295012265 и объясняет 0,4009"
        ),
        source="data/zeta/zeta_gue_analysis_results.md:34",
        stated=_stated(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_negative_control,
        null_expect={"corpus_std": 1.0, "wigner_std": 1.0},
        null_kind="negative",
        # Половина последнего напечатанного разряда для 0,4009:
        # 5e-5 / 0,4009 ≈ 1,247e-4 относительных.
        tolerance=1.25e-4,
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        inputs=[ZEROS, REPORT],
        claim_family="паспорт рецепта развёртки дзета",
        observable="std нормированных расстояний и источник нормировки",
        measurement_source="файл нулей Odlyzko zeros1 и отчёт Trinity",
        uncertainty_type="none",
        novelty_key="zeta:unfolding_std_passport:v1",
        information_class="novelty",
        purpose="internal_consistency",
        models=["Wigner—surmise", "точный закон GUE"],
        independent_of={"source": "сырой файл нулей", "observable": "рецепт развёртки"},
        notes=(
            "Машинный паспорт: 100000 нулей, индексы 1..100000, 99999 зазоров; "
            "θ(t)=Im logΓ(1/4+i t/2)−(t/2)lnπ, s_i=(θ(γ_{i+1})−θ(γ_i))/π, "
            "края не исключаются, std выборочная ddof=1. "
            "Два независимых пути дают 0,42201569295012265. "
            "Для 0,4009 точная θ-развёртка даёт 0,4009327315, а ведущий член "
            "плотности с множителем по нижнему нулю — 0,4009263778: это иная "
            "измерительная развёртка того же файла, не табличная арифметика. "
            "Точный Fredholm-GUE даёт около 0,424258, поэтому 0,4220 — Wigner "
            "surmise, а не точный GUE; причина расхождения зафиксирована кодом."
        ),
        skip_reasons={
            "С6": "рецепт не содержит дискретной сетки сходимости",
            "С7": "проверяется одна статистика развёртки",
            "С8": "погрешность исходных нулей отдельно не заявлена",
            "С9": "конечный ряд дан целиком, экстраполяция не заявлена",
            "С10": "в кейсе нет выборочного bootstrap ряда",
            "С11": "нет трёх статистик с оценённым разбросом",
            "С15": "внешней измеренной цели нет",
            "С16": "перебора формул нет",
            "С17": "проверяется рецепт, а не формула-кандидат",
            "С18": "границы семейства формул не заявлены",
            "С19": "арифметический бюджет не является частью утверждения",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма кандидата не заявлена",
        },
    )
]
