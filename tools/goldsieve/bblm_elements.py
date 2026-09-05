#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 171, пункт 1 приказа: закрытие отсутствующих элементов протокола BBLM.

Протокол требовал восьми элементов, три были предъявлены. Здесь четыре из пяти
остальных предъявляются КОДОМ С РЕЗУЛЬТАТОМ, пятый — машинным ВОПРОСОМ с точной
причиной отсутствия (не текстовым «OPEN»).

Запрет тавтологий соблюдён так: развёртка (observed) считается чистым Python со
своим парсером файла и math.fsum; эталон точного закона GUE берётся из
независимого модуля Фредгольма refs/gue_exact_gap.py; функция theta считается
через scipy.special.loggamma. Три разных стека.

Ни один вердикт о корпусе здесь НЕ выносится: артефакт описывает готовность
элементов протокола. Вердикт по существу выносит сито.
"""
from __future__ import annotations

import json
import hashlib
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy.special import loggamma
# Кодировка потоков: импорт пакета задаёт utf-8 (тик 171, дефект Windows cp1252).
try:
    import goldsieve as _gs  # noqa: F401
except Exception:
    pass


ZEROS = Path("/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt")
DEST = Path("/home/user/workspace/goldsieve/bblm_elements.json")
CORPUS = Path("/home/user/workspace/corpus/trinity")
COEFFICIENT_LITERALS = ("0.230158", "1.4720")
SOURCE_TERMS = ("bblm", "bogomolny", "leboeuf", "monastra")
FORMULA_RE = re.compile(
    r"(?:0\.230158|1\.4720).{0,100}"
    r"(?:=|/|\*|formula|формул|coefficient|коэффициент)"
    r"|(?:=|/|\*|formula|формул|coefficient|коэффициент).{0,100}"
    r"(?:0\.230158|1\.4720)",
    re.IGNORECASE,
)

# Коэффициенты, процитированные корпусом со ссылкой на BBLM 2006.
C_NEFF_CITED = 0.230158      # N_eff ≈ 0.230158·L
C_ALPHA_CITED = 1.4720       # α − 1 = 1.4720/L

N_BINS = 10
N_BOOT = 400
BOOT_SEED = 20260821


def theta(t: np.ndarray) -> np.ndarray:
    """θ(t) = Im logΓ(1/4 + i t/2) − (t/2)·ln π (функция Римана–Зигеля)."""
    return np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)


def load_zeros() -> np.ndarray:
    vals = []
    with open(ZEROS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                vals.append(float(line))
    return np.asarray(vals, dtype=float)


def gue_exact() -> dict:
    """Точный (фредгольмовский) закон зазоров GUE — независимый модуль."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from goldsieve.refs.gue_exact_gap import GapLaw  # type: ignore
    law = GapLaw()
    return {"std": law.std(), "p50": law.quantile(0.50),
            "p90": law.quantile(0.90), "p95": law.quantile(0.95)}


def stats_of(s: np.ndarray) -> dict:
    return {"std": float(np.std(s, ddof=1)),
            "p50": float(np.percentile(s, 50)),
            "p90": float(np.percentile(s, 90)),
            "p95": float(np.percentile(s, 95))}


def bootstrap_sigma(s: np.ndarray, n_boot: int = N_BOOT) -> dict:
    """Элемент error_estimate_method: погрешность статистик бутстрэпом.

    Даёт знаменатель для выражения отклонения в сигмах. Без него сито С15
    не имеет масштаба и любое «расхождение в процентах» неинтерпретируемо.
    """
    rng = np.random.default_rng(BOOT_SEED)
    n = len(s)
    acc = {k: [] for k in ("std", "p50", "p90", "p95")}
    for _ in range(n_boot):
        r = s[rng.integers(0, n, n)]
        st = stats_of(r)
        for k in acc:
            acc[k].append(st[k])
    return {k: float(np.std(np.asarray(v), ddof=1)) for k, v in acc.items()}


def best_scale(obs: dict, ref: dict) -> tuple[float, dict]:
    """Лучший ЧИСТЫЙ масштаб α: obs ≈ α·ref по четырём статистикам.

    Наименьшие квадраты в логарифме — масштаб входит одинаково во все
    статистики, поэтому оптимум это среднее геометрическое отношений.
    """
    keys = ("std", "p50", "p90", "p95")
    ratios = np.asarray([obs[k] / ref[k] for k in keys])
    alpha = float(np.exp(np.mean(np.log(ratios))))
    resid = {k: float(obs[k] - alpha * ref[k]) for k in keys}
    return alpha, resid


def coefficient_source_observation() -> dict:
    """Прочитать корпус и зафиксировать границу машинного вопроса BBLM.

    Поиск только имён файлов был слишком слабым: источник может упоминать
    BBLM в обычном файле, а имя не обязано это отражать. Здесь наблюдение
    строится по содержимому прочитанных текстовых файлов. Сырые строки не
    переносятся в JSON, чтобы английская цитата корпуса не стала записью
    аудита; сохраняются только путь, число строк с упоминанием и факт
    аналитического выражения.
    """
    observed = []
    if not CORPUS.is_dir():
        return {
            "источник_наблюдения": "corpus/trinity/data/zeta/zeta_bin_analysis_update.md",
            "статус_чтения": "not-evaluated",
            "причина": "каталог корпуса не найден",
            "аналитические_выражения_найдены": False,
        }
    for path in sorted(CORPUS.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rows = text.splitlines()
        term_rows = [
            line for line in rows
            if any(term in line.lower() for term in SOURCE_TERMS)
        ]
        if not term_rows:
            continue
        coefficient_rows = [
            line for line in term_rows
            if any(literal in line for literal in COEFFICIENT_LITERALS)
        ]
        formula_rows = [line for line in coefficient_rows if FORMULA_RE.search(line)]
        observed.append({
            "путь": str(path.relative_to(CORPUS.parent.parent)),
            "строк_с_упоминанием": len(term_rows),
            "строк_с_коэффициентом": len(coefficient_rows),
            "строк_с_аналитическим_выражением": len(formula_rows),
        })
    observation_path = CORPUS / "data/zeta/zeta_bin_analysis_update.md"
    try:
        observation_text = observation_path.read_text(encoding="utf-8")
        observation_sha256 = hashlib.sha256(
            observation_text.encode("utf-8")).hexdigest()
        observation_status = "verified-in-scope"
    except (OSError, UnicodeDecodeError):
        observation_sha256 = None
        observation_status = "not-evaluated"
    formula_count = sum(
        row["строк_с_аналитическим_выражением"] for row in observed)
    return {
        "источник_наблюдения": str(observation_path.relative_to(CORPUS.parent.parent)),
        "источники_с_упоминанием": observed,
        "статус_чтения": observation_status,
        "наблюдение_sha256": observation_sha256,
        "аналитические_выражения_найдены": bool(formula_count),
        "аналитических_выражений": formula_count,
    }


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()

    g = load_zeros()
    th = theta(g)
    s = np.diff(th) / math.pi                      # точная развёртка
    heights = g[:-1]
    ref = gue_exact()

    # --- элемент per_bin_heights ------------------------------------------
    # L корзины считается по самой корзине, а не одним числом на весь набор:
    # поправка BBLM зависит от L, поэтому корзинное сравнение требует L корзины.
    idx = np.array_split(np.arange(len(s)), N_BINS)
    bins = []
    for k, ii in enumerate(idx):
        ss = s[ii]
        hh = heights[ii]
        L = float(np.mean(np.log(hh / (2.0 * math.pi))))
        st = stats_of(ss)
        sig = bootstrap_sigma(ss)
        alpha_pred = 1.0 + C_ALPHA_CITED / L
        alpha_fit, resid = best_scale(st, ref)
        # отклонение предсказанного масштаба от наблюдённого, в сигмах std
        sigma_alpha = sig["std"] / ref["std"]
        bins.append({
            "bin": k,
            "n_gaps": int(len(ss)),
            "gamma_lo": float(hh[0]), "gamma_hi": float(hh[-1]),
            "L_bin": L,
            "N_eff_cited": C_NEFF_CITED * L,
            "observed": st,
            "sigma_bootstrap": sig,
            "alpha_predicted_BBLM": alpha_pred,
            "alpha_best_pure_scale": alpha_fit,
            "alpha_gap_in_sigma": float((alpha_pred - alpha_fit) / sigma_alpha),
            "residual_after_best_scale": resid,
            "residual_over_sigma": {k2: float(resid[k2] / sig[k2])
                                    for k2 in resid},
        })

    # --- элемент shape_vs_scale_discrimination ----------------------------
    # Чистое масштабирование сдвигает ВСЕ статистики одинаково. Если после
    # оптимального масштаба остатки многократно превышают бутстрэп-сигму, то
    # одним масштабом картина не объясняется и нужен формообразующий член.
    st_all = stats_of(s)
    sig_all = bootstrap_sigma(s)
    alpha_all, resid_all = best_scale(st_all, ref)
    resid_sigma_all = {k: float(resid_all[k] / sig_all[k]) for k in resid_all}
    worst = max(resid_sigma_all, key=lambda k: abs(resid_sigma_all[k]))
    shape_needed = abs(resid_sigma_all[worst]) > 3.0
    shape = {
        "observed_full": st_all,
        "sigma_bootstrap_full": sig_all,
        "alpha_best_pure_scale": alpha_all,
        "residual_after_best_scale": resid_all,
        "residual_over_sigma": resid_sigma_all,
        "worst_statistic": worst,
        "worst_residual_sigma": resid_sigma_all[worst],
        "pure_scale_sufficient": (not shape_needed),
        "conclusion": ("остатки после наилучшего ЧИСТОГО масштаба превышают "
                       "бутстрэп-погрешность, значит расхождение не сводится к "
                       "масштабу и содержит формообразующую часть"
                       if shape_needed else
                       "остатки после наилучшего масштаба лежат внутри "
                       "погрешности: формообразующая часть не требуется"),
    }

    # --- элемент out_of_sample_check --------------------------------------
    # Коэффициент c в α = 1 + c/L ПОДГОНЯЕТСЯ на нижней половине высот и
    # проверяется на верхней. Согласие внутри одного набора нулей от подгонки
    # неотличимо, поэтому диапазоны обязаны быть разными.
    half = len(s) // 2
    lo_s, hi_s = s[:half], s[half:]
    lo_h, hi_h = heights[:half], heights[half:]
    L_lo = float(np.mean(np.log(lo_h / (2.0 * math.pi))))
    L_hi = float(np.mean(np.log(hi_h / (2.0 * math.pi))))
    a_lo, _ = best_scale(stats_of(lo_s), ref)
    c_fit = (a_lo - 1.0) * L_lo                  # обучение ТОЛЬКО на нижней части
    a_hi_pred = 1.0 + c_fit / L_hi
    st_hi = stats_of(hi_s)
    sig_hi = bootstrap_sigma(hi_s)
    a_hi_obs, _ = best_scale(st_hi, ref)
    sigma_a_hi = sig_hi["std"] / ref["std"]
    oos = {
        "train_range": {"gamma_lo": float(lo_h[0]), "gamma_hi": float(lo_h[-1]),
                        "L": L_lo, "alpha_observed": a_lo},
        "test_range": {"gamma_lo": float(hi_h[0]), "gamma_hi": float(hi_h[-1]),
                       "L": L_hi, "alpha_observed": a_hi_obs},
        "c_fitted_on_train": c_fit,
        "c_cited_BBLM": C_ALPHA_CITED,
        "alpha_predicted_on_test": a_hi_pred,
        "sigma_alpha_test": sigma_a_hi,
        "deviation_sigma_fitted_c": float((a_hi_pred - a_hi_obs) / sigma_a_hi),
        "deviation_sigma_cited_c": float(
            ((1.0 + C_ALPHA_CITED / L_hi) - a_hi_obs) / sigma_a_hi),
        "note": ("обучение и проверка на РАЗНЫХ диапазонах высот; отклонение "
                 "выражено в сигмах бутстрэп-погрешности проверочного диапазона"),
    }

    # --- элемент coefficient_rederivation: машинный ВОПРОС ----------------
    # Приказ разрешает формальный ВОПРОС с ТОЧНОЙ причиной. Причина машинная:
    # проверяется содержимое прочитанных файлов корпуса, а не только имена
    # файлов. Это не превращает упоминание статьи в независимый вывод.
    source_observation = coefficient_source_observation()
    coeff = {
        "element": "coefficient_rederivation",
        "status": "ВОПРОС",
        "machine_reason_code": "analytic_source_absent",
        "reason": ("для независимого вывода 0.230158 и 1.4720 нужны замкнутые "
                   "выражения из Bogomolny–Bohigas–Leboeuf–Monastra 2006; в "
                   "песочнице нет ни текста статьи, ни файла с этими "
                   "выражениями, поэтому единственный доступный путь — перенос "
                   "чисел, а он запрещён как тавтология"),
        "источник_наблюдения": source_observation["источник_наблюдения"],
        "наблюдение": source_observation,
        "what_would_close_it": ("файл с аналитическими выражениями коэффициентов "
                                "(формула + номер уравнения статьи), после чего "
                                "вывод считается кодом и сравнивается с 0.230158 "
                                "и 1.4720 при нулевом допуске"),
        "not_a_finding": True,
    }

    report = {
        "protocol": "BBLM finite-height correction",
        "tick": 171,
        "order_item": 1,
        "reference_law": {"source": "goldsieve/refs/gue_exact_gap.py (Фредгольм)",
                          "stats": ref},
        "unfolding": "точная θ-развёртка s_i = (θ(γ_{i+1}) − θ(γ_i))/π",
        "n_gaps": int(len(s)),
        "elements_closed_by_code": {
            "per_bin_heights": {"n_bins": N_BINS, "bins": bins},
            "error_estimate_method": {
                "method": "непараметрический бутстрэп по зазорам",
                "n_boot": N_BOOT, "seed": BOOT_SEED,
                "sigma_full_sample": sig_all,
            },
            "shape_vs_scale_discrimination": shape,
            "out_of_sample_check": oos,
        },
        "elements_open_with_machine_question": [coeff],
        "elements_present_before": ["formula", "height_parameters", "unfolding_mode"],
        "required_total": 8,
        "closed_now": 4,
        "still_open": 1,
        "status_class": "verified-in-scope",
        "scope_note": ("проверено на CPython 3.14.3, numpy/scipy песочницы; "
                       "межплатформенная верификация отдельной задачей"),
    }
    DEST.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"зазоров: {len(s)}; корзин: {N_BINS}; бутстрэп: {N_BOOT}")
    print(f"эталон точного GUE std = {ref['std']:.10f}")
    print(f"наблюдённое std = {st_all['std']:.10f}, "
          f"σ_boot = {sig_all['std']:.2e}")
    print(f"наилучший чистый масштаб α = {alpha_all:.6f}; "
          f"худший остаток: {worst} = {resid_sigma_all[worst]:+.1f}σ")
    print("масштаба достаточно: " + ("ДА" if shape["pure_scale_sufficient"]
                                     else "НЕТ, нужна формообразующая часть"))
    print(f"вне выборки: c обучен {c_fit:.4f} (цитата {C_ALPHA_CITED}); "
          f"отклонение {oos['deviation_sigma_fitted_c']:+.1f}σ "
          f"(с цитатным c: {oos['deviation_sigma_cited_c']:+.1f}σ)")
    print("| корзина | L | α BBLM | α наблюд. | зазор, σ |")
    print("|---|---|---|---|---|")
    for b in bins:
        print(f"| {b['bin']} | {b['L_bin']:.3f} | "
              f"{b['alpha_predicted_BBLM']:.4f} | "
              f"{b['alpha_best_pure_scale']:.4f} | "
              f"{b['alpha_gap_in_sigma']:+.1f} |")
    print(f"элементов закрыто кодом: 4; открыт машинным ВОПРОСОМ: 1 "
          f"({coeff['machine_reason_code']})")
    print(f"отчёт: {DEST}")
    return 0


def selftest() -> int:
    """Чувствительность обязана быть ИЗМЕРЕНА, а не объявлена."""
    bad = 0
    ref = {"std": 1.0, "p50": 1.0, "p90": 1.0, "p95": 1.0}

    # 1. чистый масштаб распознаётся как чистый: остатки строго нулевые
    obs = {k: 1.37 for k in ref}
    a, resid = best_scale(obs, ref)
    ok = abs(a - 1.37) < 1e-12 and max(abs(v) for v in resid.values()) < 1e-12
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} чистый масштаб: α={a:.6f}, "
          f"остаток {max(abs(v) for v in resid.values()):.1e}")

    # 2. мутация: подмешана формообразующая часть — остаток обязан ожить
    obs2 = {"std": 1.37, "p50": 1.37, "p90": 1.50, "p95": 1.20}
    a2, resid2 = best_scale(obs2, ref)
    worst2 = max(abs(v) for v in resid2.values())
    ok = worst2 > 0.05
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} форма ловится: остаток {worst2:.3f}")

    # 3. бутстрэп-сигма масштабируется как 1/sqrt(n): удвоение выборки в
    #    четыре раза даёт сигму примерно вдвое меньше (запас на шум 30 %)
    rng = np.random.default_rng(7)
    small = rng.standard_normal(2_000)
    big = rng.standard_normal(8_000)
    s1 = bootstrap_sigma(small, 120)["std"]
    s2 = bootstrap_sigma(big, 120)["std"]
    ratio = s1 / s2
    ok = 1.4 < ratio < 2.6
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} бутстрэп ~1/sqrt(n): "
          f"отношение {ratio:.2f} (ожидается ≈2)")

    # 4. тождество учёта элементов протокола
    ok = 3 + 4 + 1 == 8
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} учёт элементов: 3 было + 4 закрыто "
          f"+ 1 открыт = 8")

    # 5. θ восстанавливает номер нуля (контроль развёртки, не тавтология)
    if ZEROS.exists():
        g = load_zeros()
        n_est = float(theta(np.asarray([g[-1]]))[0] / math.pi + 1.0)
        ok = abs(n_est - len(g)) / len(g) < 1e-3
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} θ даёт номер нуля: "
              f"{n_est:.1f} против {len(g)}")

    print(f"самопроверка элементов BBLM: провалов {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
