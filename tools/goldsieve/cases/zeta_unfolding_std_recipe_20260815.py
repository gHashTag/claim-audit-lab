"""Происхождение числа 0,4009: измерение из сырых нулей, а не арифметика таблицы.

Приказ пользователя (пункт 1) требует закрыть zeta-кейс: зафиксировать рецепт
развёртки и объяснить, откуда берётся 0,4009. Прежний кейс
`cases/zeta_std_gue_20260815.py` сравнивал напечатанное 0,4009 с ТЕОРИЕЙ
(surmise Вигнера) и получал ОПРОВЕРГНУТО — но корпус и сам объявляет это
отклонение открытым, то есть проверялось не то утверждение.

Здесь проверяется другое, ранее не проверявшееся утверждение: напечатанное
значение std получено из файла нулей заявленным рецептом развёртки.

Три пути к числу принципиально разные:
  reference     — точная развёртка приращением θ(γ)/π (scipy loggamma, numpy);
  observed      — развёртка корпуса (ведущий член плотности), ЧИСТЫЙ Python,
                  свой парсер файла, суммирование через math.fsum;
  reference_alt — та же θ-развёртка, но loggamma из mpmath на 30 знаках и
                  накопление моментов в Python (другая библиотека спецфункций,
                  другая арифметика).

Подставка — теоретическое значение 0,4220156929501: неверный ответ той же
формы, поставленный там, где он отличается от измерения на 5 %.
Отрицательный контроль — пуассоновская последовательность через тот же
конвейер: она обязана давать std около 1, а не эталон.
"""

import math
import re

import numpy as np
from scipy.special import loggamma

from goldsieve.sieve import Claim

ZEROS = ("/home/user/workspace/corpus/trinity/data/zeta/"
         "zeros_odlyzko_100k.txt")
DOC = ("/home/user/workspace/corpus/trinity/data/zeta/"
       "zeta_gue_analysis_results.md")

WIGNER_STD = math.sqrt(3.0 * math.pi / 8.0 - 1.0)   # 0,42201569295012265


# ------------------------------------------------------------- заявленное

def _stated():
    """Напечатанное значение std из таблицы Global Statistics."""
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()
    match = re.search(r"\| Std deviation \| ([0-9.]+) \| ([0-9.]+) \|", text)
    if not match:
        raise AssertionError("строка Std deviation не найдена")
    return {"std": float(match.group(1))}


# ---------------------------------------------- эталон: θ-развёртка (numpy)

def _zeros_numpy():
    return np.loadtxt(ZEROS)


def _reference():
    """Точная развёртка: s_i = (θ(γ_{i+1}) − θ(γ_i))/π, θ через scipy loggamma."""
    g = _zeros_numpy()
    th = np.imag(loggamma(0.25 + 0.5j * g)) - 0.5 * g * math.log(math.pi)
    s = np.diff(th) / math.pi
    return {"std": float(np.std(s, ddof=1))}


# ------------------------------- наблюдение: развёртка корпуса, чистый Python

def _zeros_python():
    """Свой парсер файла: без numpy, построчно."""
    out = []
    with open(ZEROS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(float(line))
    return out


def _observed():
    """Развёртка корпуса (ведущий член), std через math.fsum, без numpy."""
    g = _zeros_python()
    two_pi = 2.0 * math.pi
    s = [(g[i + 1] - g[i]) * math.log(g[i] / two_pi) / two_pi
         for i in range(len(g) - 1)]
    n = len(s)
    mean = math.fsum(s) / n
    var = math.fsum((x - mean) ** 2 for x in s) / (n - 1)
    return {"std": math.sqrt(var)}


# ------------------------------- второй эталон: mpmath 30 знаков, свой цикл

_ALT_CACHE = {}


def _reference_alt():
    """θ-развёртка на mpmath (30 знаков), накопление моментов в Python."""
    if "v" in _ALT_CACHE:
        return _ALT_CACHE["v"]
    import mpmath as mp
    g = _zeros_python()
    with mp.workdps(30):
        half = mp.mpf(1) / 2
        lnpi = mp.log(mp.pi)
        th = [mp.im(mp.loggamma(mp.mpf(1) / 4 + mp.mpc(0, 1) * mp.mpf(x) * half))
              - mp.mpf(x) * half * lnpi for x in g]
        s = [(th[i + 1] - th[i]) / mp.pi for i in range(len(th) - 1)]
        n = len(s)
        mean = mp.fsum(s) / n
        var = mp.fsum([(x - mean) ** 2 for x in s]) / (n - 1)
        _ALT_CACHE["v"] = {"std": float(mp.sqrt(var))}
        return _ALT_CACHE["v"]


def _alt_tolerance():
    """Терпимость ВЫВОДИТСЯ из измеренного расхождения двух реализаций."""
    delta = abs(_reference_alt()["std"] - _reference()["std"])
    return max(1.0e-12, 10.0 * delta)


# -------------------------------------------------- подставка и контроль

def _wrong():
    """Теоретическое значение surmise: отличается от измерения на 5 %."""
    return {"std": WIGNER_STD}


def _negative_control():
    """Пуассоновская последовательность через тот же конвейер: std ≈ 1."""
    g = _zeros_numpy()
    rng = np.random.default_rng(20260815)
    step = 2.0 * math.pi / math.log(g[len(g) // 2] / (2.0 * math.pi))
    t = g[0] + np.cumsum(rng.exponential(size=len(g)) * step)
    th = np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)
    s = np.diff(th) / math.pi
    s = s / np.mean(s)
    return {"std": float(np.std(s, ddof=1))}


# --------------------------------------------------- выборка и статистики

def _sample():
    """Сырые развёрнутые зазоры (θ-развёртка), 99 999 значений."""
    g = _zeros_numpy()
    th = np.imag(loggamma(0.25 + 0.5j * g)) - 0.5 * g * math.log(math.pi)
    return np.diff(th) / math.pi


def _std_stat(values):
    return float(np.std(np.asarray(values, dtype=float), ddof=1))


def _selfcheck():
    ref = _reference()["std"]
    obs = _observed()["std"]
    assert abs(_stated()["std"] - 0.4009) < 1.0e-12, "печатное значение изменилось"
    assert abs(ref - obs) < 5.0e-5, "две развёртки расходятся сильнее печатной точности"
    assert abs(_wrong()["std"] - ref) / ref > 0.04, "подставка неотличима от эталона"
    assert _negative_control()["std"] > 0.8, "отрицательный контроль похож на эталон"


_selfcheck()


CLAIMS = [
    Claim(
        name="Напечатанная std 0,4009 получена из файла 100 000 нулей заявленной развёрткой",
        source="data/zeta/zeta_gue_analysis_results.md:34",
        stated=_stated(),
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_negative_control,
        null_expect=1.0,
        null_kind="negative",
        # Терпимость ВЫВЕДЕНА из печатной точности заявленного числа:
        # напечатано четыре знака после запятой, значит половина последнего
        # разряда 5e-5 абсолютных, что при 0,4009 даёт 1,247e-4 относительных.
        tolerance=5.0e-5 / 0.4009,
        sample=_sample,
        statistics={"std": _std_stat},
        bootstrap_block=1,
        reference_alt=_reference_alt,
        alt_tolerance=_alt_tolerance,
        inputs=[ZEROS, DOC],
        claim_family="воспроизведение измеренной статистики из сырых данных",
        observable="стандартное отклонение развёрнутых расстояний между нулями",
        measurement_source="файл нулей Одлыжко (100 000 нулей, γ 14,13…74 920,83)",
        uncertainty_type="sampling",
        novelty_key="zeta:unfolding_recipe:raw_data_recompute:v1",
        information_class="novelty",
        purpose="audit",
        models=["точная развёртка θ(γ)/π (scipy loggamma, numpy)",
                "развёртка корпуса по ведущему члену плотности (чистый Python)",
                "θ-развёртка на mpmath, 30 знаков"],
        independent_of={},
        notes=(
            "Правило исключения краёв: корпус края НЕ исключает, используются все "
            "99 999 зазоров; оценка разброса — выборочная std с ddof=1. "
            "0,4220156929501 в кейсе выступает ПОДСТАВКОЙ, а не эталоном: это "
            "std surmise Вигнера, и от точного закона зазоров GUE (0,424258) она "
            "сама отличается на +0,53 %."
        ),
        skip_reasons={
            "С6": "сетки в рецепте нет: развёртка считается на всех зазорах без дискретизации",
            "С7": "проверяется одна статистика, смена оценки не заявлена утверждением",
            "С8": "погрешность нулей ~1e-9 при эффекте 1e-4 — на четыре порядка меньше",
            "С9": "конечный размер выборки учитывается ситом С10 через бутстрэп",
            "С11": "проверяется одна статистика: критерий «слишком хорошо» требует трёх и более",
            "С15": "утверждение не предсказательное: внешней измеренной цели нет",
            "С16": "перебора формул нет",
            "С17": "описательная статистика не является формулой-кандидатом",
            "С18": "границы семейства формул не заявлены",
            "С19": "второй эталон на 30 знаках и есть проверка достаточности арифметики",
            "С20": "эффективное число попыток неприменимо: перебора нет",
            "С21": "алгебраическая форма кандидата не заявлена",
        },
    )
]
