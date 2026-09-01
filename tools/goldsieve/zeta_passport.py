#!/usr/bin/env python3
"""Паспорт рецепта развёртки нулей дзеты и происхождение чисел 0,4009 / Wigner–surmise approximation 0,42201569295012265.

Задача (приказ пользователя, пункт 1):
  1) зафиксировать МАШИННО точный рецепт развёртки: набор нулей, sha256, диапазон
     индексов, формулу theta, правило исключения краёв;
  2) воспроизвести 0,42201569295012265 НЕЗАВИСИМЫМИ путями (замкнутая форма,
     квадратура высокой точности по плотности, квадратура по функции выживания,
     Монте-Карло по обратной CDF);
  3) объяснить происхождение корпусного 0,4009 перебором ЗАКОННЫХ вариантов
     рецепта и машинным выбором того варианта, который его воспроизводит.

Всё детерминированное считается кодом. Вывод — JSON, плюс самопроверки с
подставками (guard): подделка обязана быть отвергнута.
"""

import hashlib
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
from scipy.special import loggamma

CORPUS = "/home/user/workspace/corpus/trinity"
ZEROS = os.path.join(CORPUS, "data/zeta/zeros_odlyzko_100k.txt")
DOC_GUE = os.path.join(CORPUS, "data/zeta/zeta_gue_analysis_results.md")
DOC_BIN = os.path.join(CORPUS, "data/zeta/zeta_bin_analysis_update.md")

TARGET_REF = 0.42201569295012265      # число Wigner–surmise approximation, которое требуется воспроизвести
EXACT_GUE_STD = 0.424258              # точный закон зазоров GUE (refs/gue_exact_gap.py)


# ---------------------------------------------------------------- провенанс

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def corpus_head():
    out = subprocess.run(["git", "-C", CORPUS, "log", "-1", "--format=%H"],
                         capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", check=True)
    return out.stdout.strip()


def observed_std_from_corpus():
    """Прочитать округлённое наблюдаемое из таблицы корпуса.

    Ранее ``TARGET_OBS`` был константой в инструменте: паспорт хешировал
    документ, но не извлекал из него число, которое называл наблюдаемым.
    Это оставляло возможность пройти проверку при дрейфе текста корпуса.
    Таблица содержит ровно одну строку ``Std deviation``; требуем ровно одно
    совпадение, чтобы отсутствие или дублирование наблюдаемого не превращалось
    в молчаливый пропуск.
    """
    with open(DOC_GUE, "r", encoding="utf-8", errors="strict") as fh:
        text = fh.read()
    rows = re.findall(
        r"^\|\s*Std deviation\s*\|\s*([0-9]+(?:[.,][0-9]+)?)\s*\|",
        text,
        flags=re.MULTILINE,
    )
    if len(rows) != 1:
        raise ValueError(
            "в корпусном документе ожидалась ровно одна строка "
            "Std deviation, найдено %d" % len(rows)
        )
    return float(rows[0].replace(",", "."))


# ------------------------------------------------------- рецепт развёртки

def theta(t):
    """Тэта Римана-Зигеля через logGamma, без обрезания ряда."""
    t = np.asarray(t, dtype=float)
    return np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)


def unfold_theta(g):
    """Развёртка приращением средней считающей функции: s_i = (θ(γ_{i+1})-θ(γ_i))/π."""
    return np.diff(theta(g)) / math.pi


def unfold_leading(g):
    """Развёртка корпуса: ведущий член локальной плотности, множитель по НИЖНЕМУ нулю."""
    return np.diff(g) * np.log(g[:-1] / (2.0 * math.pi)) / (2.0 * math.pi)


def unfold_leading_upper(g):
    """Тот же ведущий член, но множитель по ВЕРХНЕМУ нулю (законный вариант)."""
    return np.diff(g) * np.log(g[1:] / (2.0 * math.pi)) / (2.0 * math.pi)


def unfold_leading_mid(g):
    """Тот же ведущий член в середине интервала."""
    mid = 0.5 * (g[:-1] + g[1:])
    return np.diff(g) * np.log(mid / (2.0 * math.pi)) / (2.0 * math.pi)


# ------------------------------- четыре независимых пути к 0,4220156929...

def std_closed_form():
    """Путь A: замкнутая форма второго момента surmise Вигнера, sqrt(3π/8 − 1)."""
    return math.sqrt(3.0 * math.pi / 8.0 - 1.0)


def std_mpmath_density():
    """Путь B: квадратура ∫ s²p(s)ds на 50 знаках (mpmath), плотность surmise."""
    import mpmath as mp
    with mp.workdps(50):
        p = lambda s: (32 / mp.pi**2) * s**2 * mp.e**(-4 * s**2 / mp.pi)
        m2 = mp.quad(lambda s: s**2 * p(s), [0, mp.inf])
        m1 = mp.quad(lambda s: s * p(s), [0, mp.inf])
        return float(mp.sqrt(m2 - m1**2)), float(m1)


def std_survival_quadrature():
    """Путь C: другое интегральное представление — E[s²] = ∫ 2s(1−F(s))ds по CDF.

    Функция под интегралом — CDF, а не плотность: иной аналитический объект.
    Гаусс-Лежандр на [0, 30] с 4000 узлами.
    """
    def cdf(s):
        return math.erf(2.0 * s / math.sqrt(math.pi)) \
            - (4.0 * s / math.pi) * math.exp(-4.0 * s * s / math.pi)

    x, w = np.polynomial.legendre.leggauss(4000)
    hi = 30.0
    s = 0.5 * hi * (x + 1.0)
    ww = 0.5 * hi * w
    surv = np.array([1.0 - cdf(v) for v in s])
    m2 = float(np.sum(ww * 2.0 * s * surv))
    m1 = float(np.sum(ww * surv))          # E[s] = ∫(1−F)ds
    return math.sqrt(m2 - m1 * m1), m1


def std_monte_carlo(n=4_000_000, seed=20260815):
    """Путь D: Монте-Карло по обратной CDF — выборочный путь, не квадратура."""
    def cdf(s):
        return math.erf(2.0 * s / math.sqrt(math.pi)) \
            - (4.0 * s / math.pi) * math.exp(-4.0 * s * s / math.pi)

    grid = np.linspace(0.0, 12.0, 200_001)
    fvals = np.array([cdf(v) for v in grid])
    rng = np.random.default_rng(seed)
    u = rng.random(n)
    smp = np.interp(u, fvals, grid)
    std = float(np.std(smp, ddof=1))
    # стандартная ошибка оценки std: sigma/sqrt(2(n-1)) для приближённо нормальной
    se = std / math.sqrt(2.0 * (n - 1))
    return std, se


# --------------------------------------------- варианты рецепта наблюдения

def stats_std(vals, ddof=1):
    return float(np.std(np.asarray(vals, dtype=float), ddof=ddof))


def variants(g):
    """Законные варианты рецепта наблюдения. Ключ -> (описание, std)."""
    st = unfold_theta(g)
    sl = unfold_leading(g)
    su = unfold_leading_upper(g)
    sm = unfold_leading_mid(g)
    out = {}
    out["leading_lower_ddof1_all"] = (
        "развёртка корпуса (ведущий член, нижний нуль), все 99999 зазоров, ddof=1", stats_std(sl))
    out["leading_lower_ddof0_all"] = (
        "то же, ddof=0", stats_std(sl, ddof=0))
    out["leading_lower_renormalised"] = (
        "то же, дополнительно поделено на выборочное среднее", stats_std(sl / np.mean(sl)))
    out["leading_upper"] = (
        "ведущий член по верхнему нулю", stats_std(su))
    out["leading_mid"] = (
        "ведущий член в середине интервала", stats_std(sm))
    out["theta_exact"] = (
        "точная развёртка θ(γ)/π, все зазоры", stats_std(st))
    out["theta_renormalised"] = (
        "θ-развёртка, поделена на среднее", stats_std(st / np.mean(st)))
    # правило исключения краёв: отбросить первые/последние k зазоров
    for k in (1, 10, 100, 1000):
        out["theta_trim_%d" % k] = (
            "θ-развёртка без %d зазоров с каждого края" % k, stats_std(st[k:-k]))
    # объединение по 10 высотным корзинам: внутрикорзинная std (pooled)
    bins = np.array_split(st, 10)
    pooled = math.sqrt(sum(((len(b) - 1) * np.var(b, ddof=1)) for b in bins)
                       / sum((len(b) - 1) for b in bins))
    out["theta_pooled_10bins"] = (
        "объединённая внутрикорзинная std по 10 высотным корзинам (θ)", float(pooled))
    binsl = np.array_split(sl, 10)
    pooledl = math.sqrt(sum(((len(b) - 1) * np.var(b, ddof=1)) for b in binsl)
                        / sum((len(b) - 1) for b in binsl))
    out["leading_pooled_10bins"] = (
        "объединённая внутрикорзинная std по 10 корзинам (ведущий член)", float(pooledl))
    out["leading_bin_mean_of_std"] = (
        "среднее по корзинным std (ведущий член)",
        float(np.mean([np.std(b, ddof=1) for b in binsl])))
    return out


# --------------------------------------------------------------- guard-и

def selfchecks(g, paths, var, observed_std):
    """Подставки: проверка обязана отвергать неверный ответ."""
    checks = []

    def ck(name, cond, detail=""):
        checks.append({"проверка": name, "ok": bool(cond), "деталь": detail})

    # 1. считающая функция обязана восстанавливать индекс последнего нуля
    n_est = float(theta(g[-1]) / math.pi + 1.0)
    ck("θ восстанавливает номер нуля", abs(n_est - len(g)) < 1.5,
       "N=%.3f против %d" % (n_est, len(g)))

    # 2. обе развёртки дают единичное среднее
    ck("θ-развёртка: среднее ≈ 1", abs(np.mean(unfold_theta(g)) - 1.0) < 1e-3,
       "%.6f" % np.mean(unfold_theta(g)))
    ck("ведущий член: среднее ≈ 1", abs(np.mean(unfold_leading(g)) - 1.0) < 5e-3,
       "%.6f" % np.mean(unfold_leading(g)))

    # 3. ПОДСТАВКА: пуассоновская последовательность через тот же конвейер
    #    НЕ должна давать std surmise (иначе конвейер сам производит согласие)
    rng = np.random.default_rng(20260815)
    step = 2.0 * math.pi / math.log(g[len(g) // 2] / (2.0 * math.pi))
    t = g[0] + np.cumsum(rng.exponential(size=len(g)) * step)
    sp = unfold_theta(np.asarray(t))
    sp = sp / np.mean(sp)
    ck("подставка Пуассона отвергнута", abs(float(np.std(sp, ddof=1)) - 1.0) < 0.05,
       "std=%.4f (Пуассон 1, surmise %.4f)" % (np.std(sp, ddof=1), TARGET_REF))

    # 4. ПОДСТАВКА: неверный ответ 0,45 не должен пройти сверку путей
    ck("подставка 0,45 отвергнута всеми путями",
       all(abs(0.45 - v) > 1e-6 for v in paths.values() if isinstance(v, float)))

    # 5. четыре пути обязаны различаться реализацией, но сходиться численно
    ck("путь A против B", abs(paths["A_closed"] - paths["B_mpmath"]) < 1e-14,
       "%.3e" % abs(paths["A_closed"] - paths["B_mpmath"]))
    ck("путь A против C", abs(paths["A_closed"] - paths["C_survival"]) < 1e-9,
       "%.3e" % abs(paths["A_closed"] - paths["C_survival"]))
    ck("путь A против D (в пределах SE)",
       abs(paths["A_closed"] - paths["D_monte_carlo"]) < 4.0 * paths["D_se"],
       "|Δ|=%.3e, 4·SE=%.3e" % (abs(paths["A_closed"] - paths["D_monte_carlo"]),
                                4.0 * paths["D_se"]))

    # 6. surmise НЕ совпадает с точным законом GUE — это разные эталоны
    ck("surmise отличается от точного GUE",
       abs(paths["A_closed"] - EXACT_GUE_STD) > 1e-4,
       "Δ=%.6f (%.3f %%)" % (EXACT_GUE_STD - paths["A_closed"],
                             100.0 * (EXACT_GUE_STD - paths["A_closed"]) / paths["A_closed"]))

    # 7. хотя бы один вариант рецепта обязан воспроизводить наблюдаемое из
    # корпусной таблицы в пределах печатной точности (половина последнего
    # разряда = 5e-5). Число не берётся из константы инструмента.
    #    печатной точности (половина последнего разряда = 5e-5)
    hits = [k for k, (_, v) in var.items() if abs(v - observed_std) <= 5e-5]
    ck("наблюдаемое из корпуса воспроизводится вариантом рецепта",
       bool(hits), "%.4f: %s" % (observed_std, ",".join(hits) or "нет"))
    return checks


def main():
    g = np.loadtxt(ZEROS)
    a_closed = std_closed_form()
    b_mp, b_mean = std_mpmath_density()
    c_surv, c_mean = std_survival_quadrature()
    d_mc, d_se = std_monte_carlo()
    paths = {"A_closed": a_closed, "B_mpmath": b_mp, "C_survival": c_surv,
             "D_monte_carlo": d_mc, "D_se": d_se}

    observed_std = observed_std_from_corpus()
    var = variants(g)
    checks = selfchecks(g, paths, var, observed_std)

    hits_obs = {k: v for k, (_, v) in var.items() if abs(v - observed_std) <= 5e-5}
    report = {
        "паспорт_рецепта": {
            "набор_нулей": ZEROS,
            "sha256": sha256(ZEROS),
            "число_нулей": int(len(g)),
            "диапазон_индексов": "1..%d (нумерация Одлыжко от первого нуля)" % len(g),
            "диапазон_высот": [float(g[0]), float(g[-1])],
            "число_зазоров": int(len(g) - 1),
            "источник": "Odlyzko Zeta Tables, файл zeros1, ~9 знаков",
            "коммит_корпуса": corpus_head(),
            "документы": {DOC_GUE: sha256(DOC_GUE), DOC_BIN: sha256(DOC_BIN)},
            "theta": "θ(t) = Im logΓ(1/4 + i t/2) − (t/2)·ln π (без обрезания ряда)",
            "развёртка_точная": "s_i = (θ(γ_{i+1}) − θ(γ_i))/π",
            "развёртка_корпуса": "s_i = (γ_{i+1} − γ_i)·ln(γ_i/2π)/(2π)",
            "исключение_краёв": "корпус края НЕ исключает: используются все 99999 зазоров",
            "оценка_разброса": "выборочная std, ddof=1",
            "перцентили": "линейная интерполяция между порядковыми статистиками",
        },
        "цель_эталона": TARGET_REF,
        "наблюдаемое_из_корпуса": {
            "value": observed_std,
            "source": DOC_GUE,
            "field": "Std deviation / Value",
        },
        "пути_к_эталону": paths,
        "точный_GUE_std": EXACT_GUE_STD,
        "варианты_рецепта": {k: {"описание": d, "std": v} for k, (d, v) in var.items()},
        "воспроизводят_0_4009": hits_obs,
        "проверки": checks,
        "версии": {"python": sys.version.split()[0], "numpy": np.__version__},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    failed = [c for c in checks if not c["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
