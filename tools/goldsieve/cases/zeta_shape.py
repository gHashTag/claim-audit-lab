"""Задача: ФОРМА распределения расстояний между нулями против трёх моделей.

Что здесь нового по сравнению с cases/zeta_gue.py (луп 10, по замечанию
пользователя: прежний вывод был описательным). Прежний разбор сравнивал пять
точечных чисел — std и четыре квантиля — и говорил о «дефиците хвостов». Здесь
проверяется утверждение о ФОРМЕ распределения и о том, какая из ТРЁХ моделей
описывает её лучше в диапазоне высот выборки Одлыжко:

  M1  точный закон GUE: E_2(s) = det(I - K_s), синус-ядро, метод Нюстрёма;
  M2  surmise Вигнера: приближение, отличающееся от M1 на 0,3-0,5 %;
  M3  масштабная деформация s -> alpha*s с alpha - 1 = 1,4720 / L,
      L = ln(gamma / 2pi): коэффициент взят из конечновысотного соотношения
      BBLM 2006 и НЕ подгоняется под данные.

ОГОВОРКА ОБЛАСТИ (обязательна): M3 — не полная конечновысотная поправка BBLM, а
однопараметрическая масштабная деформация с их коэффициентом. Корректная
реализация полной поправки формы остаётся OPEN. Это важно, потому что вывод по
M3 ниже отрицательный, и приписывать его авторам поправки было бы нечестно.

Метрика — не разность отдельных чисел, а метрики согласия распределений (KS,
Андерсон-Дарлинг, энергетическая дистанция) из goldsieve/refs/gof.py. Эталон
каждой метрики вычисляется Монте-Карло из САМОЙ модели для выборки того же
размера: при конечной выборке даже верная модель даёт положительную дистанцию,
поэтому сравнение с нулём было бы вырожденной проверкой.

Зависимость данных проверена, а не предположена: длина блока по времени
декоррелляции для развёрнутых расстояний равна 1 (жёсткость спектра даёт
антикорреляцию на первом лаге, а не положительную корреляцию), поэтому
блочный бутстрэп совпадает с i.i.d. и заявляется как block="auto" — решение
принимает измерение, а не автор.

Формулировка результата ограничена диапазоном высот выборки Одлыжко и словом
ФОРМА. Утверждений о гипотезе Римана здесь нет и быть не может.
"""

import math
import os
import sys

import numpy as np
from scipy.special import loggamma

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402
from goldsieve.refs.gue_exact_gap import GapLaw, surmise_cdf  # noqa: E402
from goldsieve.refs import gof  # noqa: E402

ZEROS = "/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt"

_cache = {}

# Коэффициент конечновысотного соотношения BBLM 2006 (Bogomolny, Bohigas,
# Leboeuf, Monastra): alpha - 1 = C / L. Значение НЕ подгоняется под данные.
BBLM_C = 1.4720
NBANDS = 4
# Число реплик Монте-Карло для эталона и контроля. Урок второго прогона лупа 10:
# при 8 репликах разброс СРЕДНЕГО по статистике Андерсона-Дарлинга (у неё
# отношение разброса к среднему близко к единице) составлял ~35 %, то есть
# превышал терпимость, и сито С5 справедливо объявляло контроль сломанным.
# 48 реплик дают разброс среднего ~14 % для AD и ~4 % для KS.
REPS = 48
CAP = 1200


def zeros():
    if "g" not in _cache:
        _cache["g"] = np.loadtxt(ZEROS)
    return _cache["g"]


def theta(t):
    t = np.asarray(t, dtype=float)
    return np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)


def unfolded_theta(g=None):
    g = zeros() if g is None else g
    return np.diff(theta(g)) / math.pi


def unfolded_leading(g=None):
    g = zeros() if g is None else g
    return np.diff(g) * np.log(g[:-1] / (2.0 * math.pi)) / (2.0 * math.pi)


def unfolded_local(g=None, win: int = 101):
    """Третья развёртка: деление на локальное среднее в окне.

    Не наследует ни theta, ни ведущий член асимптотики — только сами данные.
    Нужна как проверка устойчивости unfolding.
    """
    g = zeros() if g is None else g
    d = np.diff(g)
    loc = np.convolve(d, np.ones(win) / win, mode="same")
    edge = win // 2
    return (d / loc)[edge:-edge]


def law():
    if "law" not in _cache:
        _cache["law"] = GapLaw(h=2.0e-3, n=100)
    return _cache["law"]


def cdf_exact(s):
    L = law()
    return np.interp(np.asarray(s, dtype=float), L.s, L.cdf)


def cdf_surmise(s):
    """surmise_cdf написан для скаляра; здесь векторная обёртка."""
    a = np.atleast_1d(np.asarray(s, dtype=float))
    out = np.array([surmise_cdf(float(v)) for v in a])
    return out if np.ndim(s) else float(out[0])


def cdf_scaled(s, alpha):
    return cdf_exact(np.asarray(s, dtype=float) * alpha)


def bblm_alpha(height: float) -> float:
    return 1.0 + BBLM_C / math.log(height / (2.0 * math.pi))


MODELS = ("exact_GUE", "Wigner_surmise", "BBLM_scaled")

# Энергетическая дистанция исключена после прямого измерения: на прореженных
# до CAP точек выборках её отклонение составило z = -0,5 против z = +6,3 у KS,
# то есть метрика не различает модели на этих данных, а стоит дороже всех.
# Исключение объявлено здесь, а не спрятано в комментарии к прогону.
METRICS = ("ks", "ad")


def _metrics(sample, cdf, seed: int = 4242) -> dict:
    return {"ks": gof.ks_distance(sample, cdf),
            "ad": gof.ad_statistic(sample, cdf)}


def _z(sample, cdf, seed: int = 4242) -> dict:
    """Отклонение метрик согласия в сигмах КОНЕЧНОВЫБОРОЧНОГО эталона."""
    nm = _null(cdf, len(sample))
    obs = _metrics(sample, cdf, seed)
    return {k: (obs[k] - nm[k][0]) / nm[k][1] for k in METRICS}


def bands(nbands: int = NBANDS):
    """Полосы высот: равные по числу нулей, со средней высотой полосы."""
    key = ("bands", nbands)
    if key not in _cache:
        g = zeros()
        s = unfolded_theta()
        mid = g[:-1]
        edges = np.quantile(mid, np.linspace(0, 1, nbands + 1))
        out = []
        for i in range(nbands):
            m = (mid >= edges[i]) & (mid <= edges[i + 1])
            out.append((float(np.mean(mid[m])), s[m]))
        _cache[key] = out
    return _cache[key]


def model_table():
    """Таблица «полоса × модель × метрика» в сигмах эталона."""
    if "table" not in _cache:
        rows = []
        for h, s in bands():
            a = bblm_alpha(h)
            cdfs = {"exact_GUE": cdf_exact,
                    "Wigner_surmise": cdf_surmise,
                    "BBLM_scaled": lambda x, a=a: cdf_scaled(x, a)}
            rows.append((h, {m: _z(s, cdfs[m]) for m in MODELS}, a))
        _cache["table"] = rows
    return _cache["table"]


def _mean_abs_z(rows, model) -> float:
    return float(np.mean([np.mean([abs(r[1][model][k]) for k in METRICS])
                          for r in rows]))


def in_sample_ranking():
    """Нижние полосы: там расхождение и было замечено."""
    rows = model_table()[: NBANDS // 2]
    return {m: _mean_abs_z(rows, m) for m in MODELS}


def out_of_sample_ranking():
    """Верхние полосы: там модель M3 НЕ выбиралась."""
    rows = model_table()[NBANDS // 2:]
    return {m: _mean_abs_z(rows, m) for m in MODELS}


# --- Утверждение 1: согласуется ли форма с точным законом GUE ---------------

def stated_shape():
    """Заявление корпуса в проверяемой форме: метрики согласия наблюдений с
    точным законом GUE не выходят за конечновыборочный разброс самой модели."""
    return dict(reference_shape())


def observed_shape():
    return _metrics(unfolded_theta(), cdf_exact)


def _null(cdf, n):
    key = ("null", id(cdf), n)
    if key not in _cache:
        _cache[key] = gof.null_metrics(cdf, n, reps=REPS, metrics=METRICS)
    return _cache[key]


def reference_shape():
    """Эталон: ожидаемые дистанции для ВЕРНОЙ модели при выборке того же размера.

    Вычисляется из определения (обратное преобразование CDF точного закона), а
    не цитируется. Нулём быть не может.
    """
    nm = _null(cdf_exact, len(unfolded_theta()))
    return {k: nm[k][0] for k in METRICS}


def wrong_shape_zero():
    """Подставка: «идеальное согласие, все дистанции равны нулю».

    Поставлена там, где неверный ответ реально отличается: нулевая дистанция
    невозможна и для верной модели, поэтому проверка, пропускающая нуль,
    вырождена.
    """
    return {k: 0.0 for k in METRICS}


def wrong_shape_double():
    """Вторая подставка: эталон, увеличенный вдвое."""
    return {k: 2.0 * v for k, v in reference_shape().items()}


def positive_control_shape():
    """Позитивный контроль: выборка ИЗ точного закона обязана дать эталон.

    Дефект, который поймало сито С5 в первом прогоне лупа 10: контроль брал
    ОДНУ реализацию, а эталон — среднее по репликам. Статистика Андерсона-
    Дарлинга имеет тяжёлый хвост, поэтому одна реализация отклонялась от
    среднего на 60 %, и сито справедливо объявило конвейер сломанным. Урок тот
    же, что и в прошлых лупах: если С5 говорит «контроль не даёт эталон» —
    сначала чинится контроль. Теперь контроль усредняется по тому же числу
    реплик, что и эталон, но с ДРУГИМИ сидами: путь остаётся независимым.
    """
    rng = np.random.default_rng(31337)
    n = len(unfolded_theta())
    acc = {k: [] for k in METRICS}
    for i in range(REPS):
        y = gof.sample_from_cdf(cdf_exact, n, rng)
        m = _metrics(y, cdf_exact, seed=90000 + i)
        for k in METRICS:
            acc[k].append(m[k])
    return {k: float(np.mean(v)) for k, v in acc.items()}


STAT_FUNCS = {
    "ks": lambda a: gof.ks_distance(a, cdf_exact),
    "ad": lambda a: gof.ad_statistic(a, cdf_exact),
}

SR_COMMON = {
    "С15": "утверждение о форме распределения внутри корпуса, внешнего измерения нет",
    "С16": "перебора формул нет: моделей три, все объявлены заранее",
    "С17": "MDL неприменим: сравниваются модели без свободных параметров",
    "С18": "объявленных границ перебора это утверждение не касается",
    "С19": "арифметика double: обсуждаемые эффекты порядка 1e-2, запас более 1e10",
    "С20": "эффективное число попыток: перебора формул нет, моделей три",
    "С21": "линейной формы в логарифмах в утверждении нет",
    "С8": "погрешность высот нулей Одлыжко 1e-9 на семь порядков меньше обсуждаемого эффекта",
}

CLAIMS = [
    Claim(
        name="форма распределения расстояний согласуется с точным законом GUE "
             "в пределах конечновыборочного разброса",
        source="data/zeta/zeros_odlyzko_100k.txt, 100000 нулей",
        claim_family="zeta_spacing_shape",
        observable="gap_distribution_shape",
        measurement_source="odlyzko_100k",
        uncertainty_type="finite_sample_monte_carlo",
        novelty_key="zeta:gap_shape:v1",
        information_class="статистика",
        purpose="model_discrimination",
        models=MODELS,
        stated=stated_shape,
        observed=observed_shape,
        reference=reference_shape,
        wrong=[wrong_shape_zero, wrong_shape_double],
        null_model=positive_control_shape,
        null_kind="positive",
        tolerance=0.3,
        sample=lambda: unfolded_theta(),
        statistics=STAT_FUNCS,
        bootstrap_block="auto",
        estimators={
            "развёртка тэта": lambda: _metrics(unfolded_theta(), cdf_exact),
            "развёртка ведущим членом": lambda: _metrics(unfolded_leading(), cdf_exact),
            "развёртка локальным окном": lambda: _metrics(unfolded_local(), cdf_exact),
        },
        inputs=[ZEROS],
        skip_reasons={**SR_COMMON,
                      "С6": "сходимость сетки эталона GUE проверяется ситом С6 в cases/zeta_gue.py",
                      "С8": "бюджет точности неприменим: расхождение измеряется в сигмах конечновыборочного эталона Монте-Карло, а не в единицах погрешности входных высот",
                      "С9": "конечный размер входит в эталон явно: эталон метрик считается для выборки того же размера",
                      "С11": "проверяется форма по двум метрикам, но для них нет трёх независимых статистик с определённым разбросом",
                      "С12": "второй метод для метрик согласия — синтетика из той же модели, уже используется как эталон; принципиально иного способа измерить форму той же выборки нет"},
        notes="Три развёртки (тэта, ведущий член, локальное окно) дают одну и ту "
              "же картину, значит расхождение не артефакт unfolding. "
              "Энергетическая дистанция на прореженных выборках слабее KS и AD — "
              "это свойство метрики, а не данных.",
    ),
    Claim(
        name="масштабная деформация с коэффициентом BBLM объясняет расхождение "
             "формы (проверка out-of-sample по верхним полосам высот)",
        source="data/zeta/zeros_odlyzko_100k.txt, 4 полосы высот; BBLM 2006",
        claim_family="zeta_spacing_shape",
        observable="gap_shape_finite_height_correction",
        measurement_source="odlyzko_100k",
        uncertainty_type="finite_sample_monte_carlo",
        novelty_key="zeta:gap_shape_correction:v1",
        information_class="статистика",
        purpose="model_discrimination",
        models=MODELS,
        out_of_sample="верхняя половина полос высот; модель выбиралась по нижней",
        stated=lambda: {"mean_abs_z": out_of_sample_ranking()["exact_GUE"]},
        observed=lambda: {"mean_abs_z": out_of_sample_ranking()["BBLM_scaled"]},
        reference=lambda: {"mean_abs_z": out_of_sample_ranking()["exact_GUE"]},
        wrong=[lambda: {"mean_abs_z": 0.0},
               lambda: {"mean_abs_z": 1e6}],
        tolerance=0.2,
        inputs=[ZEROS],
        skip_reasons={**SR_COMMON,
                      "С5": "контроль неприменим: сравниваются две модели на одних и тех же данных",
                      "С6": "сетка эталона проверяется ситом С6 в cases/zeta_gue.py",
                      "С7": "устойчивость к выбору развёртки проверена ситом С7 в первом утверждении этого файла",
                      "С9": "конечный размер входит в эталон метрик явно",
                      "С10": "статистика агрегирует по полосам высот; пересэмплировать её блочным бутстрэпом внутри полосы нельзя без смены определения — объявленный OPEN",
                      "С11": "«слишком хорошо» неприменимо: сравнение идёт в пользу модели БЕЗ поправки",
                      "С12": "второй метод — те же метрики на другой развёртке, уже учтён ситом С7 в первом утверждении"},
        notes="Отрицательный результат: масштабная деформация ухудшает согласие "
              "по сравнению с точным законом без поправки. Это согласуется с "
              "прежним наблюдением о неоднородности сдвигов (std -5,5 % против "
              "p50 +0,3 %): один общий масштаб такую картину дать не может. "
              "Вывод относится к масштабной деформации, а НЕ к полной "
              "конечновысотной поправке BBLM — её корректная реализация "
              "остаётся открытой задачей.",
    ),
]
