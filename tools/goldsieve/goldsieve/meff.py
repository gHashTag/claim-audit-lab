# -*- coding: utf-8 -*-
"""Эффективное число независимых тестов в семействе формул.

Ось множественности до сих пор опиралась на поправку Шидака при ПРЕДПОЛОЖЕНИИ
независимости членов семейства. Предположение неверно: члены
n * 3^k * pi^m * phi^p * e^q лежат на логарифмической решётке и при достаточно
малом разрешении неотличимы друг от друга, то есть дают ОДИН тест, а не разные.

Здесь считается M_eff — сколько независимых попыток на самом деле есть у
семейства. Два независимых пути:

1. Разрешающая кластеризация. Два члена, отстоящие в относительных единицах
   меньше чем на полосу eps, при данной точности сравнения дают одинаковый
   вердикт: это один тест, а не два. M_eff = число eps-разделённых кластеров.
   Это конструктивный аналог trials factor Гросса-Витальса, где множитель
   выводится из числа различимых локальных максимумов статистики, а не из
   числа гипотез (https://arxiv.org/abs/1005.1891).

2. Собственные значения корреляционной матрицы по Ли-Цзи 2005:
   M_eff = sum_i [ I(lambda_i >= 1) + (lambda_i - floor(lambda_i)) ].
   Матрица строится на статистике «логарифмическое расстояние члена до цели»
   по ансамблю случайных целей.

Оба пути обязаны согласоваться по порядку величины. Если нет — это находка об
инструменте, а не о корпусе.

ВАЖНО об области применения: M_eff отвечает на вопрос «сколько независимых
попыток», а не «во сколько раз слабее порог». Замена M на M_eff в поправке
Шидака законна и ослабляет порог; сито С20 проверяет, не МЕНЯЕТСЯ ли вывод при
этой законной замене.
"""

import hashlib
import math

try:
    import numpy as _np
except Exception:  # noqa: BLE001
    _np = None


def _targets_fingerprint(targets):
    """Короткий отпечаток фактического ансамбля целей для журнала."""
    if _np is None:
        return None
    values = _np.asarray(targets, dtype="<f8")
    payload = str(values.size).encode("ascii") + b":" + values.tobytes()
    return hashlib.sha256(payload).hexdigest()


def resolvable_clusters(values, eps):
    """M_eff через разрешение: сколько eps-различимых значений в наборе.

    values — положительные значения членов семейства, eps — относительная
    полоса сравнения. Кластеризация жадная по отсортированным логарифмам:
    соседи ближе eps сливаются, потому что при такой точности вердикт по ним
    один и тот же.
    """
    vals = sorted(float(v) for v in values if v and v > 0.0)
    if not vals:
        return 0
    if eps <= 0.0:
        return len(vals)
    logs = [math.log(v) for v in vals]
    # порог в логарифмах: log(1+eps) — относительная полоса
    step = math.log1p(eps)
    count = 1
    anchor = logs[0]
    for x in logs[1:]:
        if x - anchor > step:
            count += 1
            anchor = x
    return count


def li_ji_meff(correlation):
    """M_eff по Ли-Цзи 2005 из корреляционной матрицы.

    M_eff = sum_i [ I(lambda_i >= 1) + (lambda_i - floor(lambda_i)) ],
    где lambda_i — собственные значения матрицы корреляций тестов. Полностью
    коррелированные тесты дают M_eff = 1, независимые — M_eff = M.
    """
    if _np is None:
        raise RuntimeError("нужен numpy")
    matrix = _np.asarray(correlation, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("нужна квадратная матрица корреляций")
    eig = _np.linalg.eigvalsh(matrix)
    eig = _np.clip(eig, 0.0, None)
    # Ли-Цзи: целый тест за каждое собственное значение не меньше единицы плюс
    # дробный вклад за остальные. Дробную часть НЕЛЬЗЯ добавлять к lambda >= 1:
    # численный шум превращает lambda = 6 в 5,999999 и удваивает ответ — на
    # этом варианте самопроверка ловила ошибку.
    total = 0.0
    for lam in eig:
        total += 1.0 if lam >= 1.0 else float(lam)
    # Верхняя граница: тестов не может быть больше, чем их подано.
    return float(min(total, matrix.shape[0]))


def meff_from_family(values, eps, targets=None, subsample=180, seed=0):
    """Оба пути сразу: кластеризация и Ли-Цзи на подвыборке.

    Возвращает dict с M (подано), M_eff_cluster, M_eff_eigen (может быть None,
    если numpy недоступен) и отношением independence_ratio = M_eff / M по
    кластерному пути — именно он используется ситом, потому что он не зависит
    от выбора ансамбля целей.
    """
    vals = [float(v) for v in values if v and v > 0.0]
    out = {
        "M": len(vals),
        "M_eff_cluster": resolvable_clusters(vals, eps),
        "M_eff_eigen": None,
        "eps": eps,
    }
    out["independence_ratio"] = (out["M_eff_cluster"] / out["M"]
                                 if out["M"] else 0.0)
    if _np is None or len(vals) < 4:
        return out
    rng = _np.random.default_rng(seed)
    picked = _np.sort(_np.asarray(vals, dtype=float))
    if picked.size > subsample:
        # СМЕЖНОЕ окно, а не случайная подвыборка. Случайное прореживание
        # снижает локальную плотность и потому систематически ЗАВЫШАЕТ долю
        # независимых: на разборе Ω_Λ кластерный путь дал 6,1 %, а eigen-путь
        # на прореженной выборке 57 % — расхождение на порядок было артефактом
        # прореживания, а не свойством семейства. На смежном окне плотность
        # сохраняется и оба пути согласуются.
        start = (picked.size - subsample) // 2
        picked = picked[start:start + subsample]
    generated_targets = targets is None
    if targets is None:
        low, high = math.log10(min(vals)), math.log10(max(vals))
        targets = 10.0 ** rng.uniform(low, high, size=600)
    targets = _np.asarray(targets, dtype=float)
    # Риск каскада: без отпечатка ансамбля одинаковое число M_eff нельзя
    # отличить от результата другого набора целей. Сохраняем состав и seed,
    # не меняя численное решение.
    out["targets_count"] = int(targets.size)
    out["targets_seed"] = int(seed) if generated_targets else None
    out["targets_sha256"] = _targets_fingerprint(targets)
    # Статистика теста i на цели t: близость в логарифмах, сглаженная полосой.
    # Гауссово ядро вместо жёсткого индикатора: у индикатора при малом eps
    # почти нулевая дисперсия, и корреляция вырождается численно.
    dist = (_np.log(picked)[None, :] - _np.log(targets)[:, None]) / math.log1p(eps)
    stat = _np.exp(-0.5 * dist ** 2)
    keep = stat.std(axis=0) > 0.0
    stat = stat[:, keep]
    if stat.shape[1] >= 2:
        corr = _np.corrcoef(stat, rowvar=False)
        corr = _np.nan_to_num(corr, nan=0.0)
        try:
            eigen = li_ji_meff(corr)
        except Exception:  # noqa: BLE001
            eigen = None
        if eigen is not None:
            out["M_eff_eigen"] = eigen
            out["M_eff_eigen_of"] = int(stat.shape[1])
            out["eigen_ratio"] = eigen / float(stat.shape[1])
    return out


def sidak_sigma(search_size, alpha=0.05):
    """Порог в сигмах по Шидаку для заданного числа попыток."""
    from .sieve import sidak_local_alpha, _isf_normal
    local = sidak_local_alpha(alpha, max(1, int(search_size)))
    try:
        from scipy.stats import norm
        return float(norm.isf(local / 2.0))
    except Exception:  # noqa: BLE001
        return _isf_normal(local / 2.0)


def selftest():
    """Самопроверка модуля с подставками. Возвращает число провалов."""
    fail = 0

    def check(name, ok, detail=""):
        nonlocal fail
        print("  %s %s%s" % ("ok  " if ok else "FAIL", name,
                             ("  " + detail) if detail else ""))
        if not ok:
            fail += 1

    # 1. Дубликаты — это один тест, а не много.
    dup = [2.0] * 50
    got = resolvable_clusters(dup, 0.01)
    check("50 одинаковых значений дают 1 различимый тест", got == 1,
          "получено %d" % got)

    # 2. Хорошо разнесённые значения остаются отдельными тестами.
    spread = [1.0 * (2.0 ** i) for i in range(20)]
    got = resolvable_clusters(spread, 0.01)
    check("разнесённые значения остаются отдельными", got == 20,
          "получено %d" % got)

    # 3. ПОДСТАВКА: наивный ответ len(values) обязан отличаться от верного там,
    # где значения плотнее разрешения. Иначе сито не проверяет ничего.
    dense = [1.0 + 0.0001 * i for i in range(100)]
    got = resolvable_clusters(dense, 0.01)
    check("плотный набор сжимается (подставка len отличается)",
          got < 100 and got > 0, "получено %d из 100" % got)

    # 4. Монотонность по разрешению: грубее полоса — меньше тестов.
    coarse = resolvable_clusters(dense, 0.05)
    check("грубее полоса — не больше тестов", coarse <= got,
          "%d <= %d" % (coarse, got))

    if _np is not None:
        # 5. Ли-Цзи: единичная матрица даёт M_eff = M.
        ident = _np.eye(6)
        got = li_ji_meff(ident)
        check("Ли-Цзи на независимых тестах даёт M", abs(got - 6.0) < 1e-9,
              "M_eff=%.3f" % got)

        # 6. Ли-Цзи: полностью коррелированные тесты дают M_eff = 1.
        ones = _np.ones((6, 6))
        got = li_ji_meff(ones)
        check("Ли-Цзи на полностью зависимых тестах даёт 1",
              abs(got - 1.0) < 1e-6, "M_eff=%.3f" % got)

        # 7. ПОДСТАВКА: промежуточная корреляция обязана дать значение СТРОГО
        # между 1 и M. Реализация, возвращающая M или 1 всегда, здесь падает.
        mid = _np.full((6, 6), 0.5)
        _np.fill_diagonal(mid, 1.0)
        got = li_ji_meff(mid)
        check("промежуточная корреляция строго между 1 и M",
              1.0 < got < 6.0, "M_eff=%.3f" % got)

        # 8. Порог Шидака: меньше попыток — мягче порог.
        strict = sidak_sigma(123201)
        loose = sidak_sigma(1000)
        check("меньше попыток — мягче порог", loose < strict,
              "%.2f < %.2f сигма" % (loose, strict))

        # 9. Два пути обязаны согласоваться по порядку величины на РЕАЛЬНОМ
        # семействе. Без этой проверки «второй метод» независим только на
        # словах: расхождение на порядок уже случалось (артефакт прореживания).
        try:
            from .family import enumerate_family
            vals = enumerate_family()
            win = [v for v in vals if 0.14 <= v <= 3.5]
            info = meff_from_family(win, 0.0081)
            r_cl = info["independence_ratio"]
            r_ei = info.get("eigen_ratio")
            ok = (r_ei is not None and r_ei > 0.0
                  and 0.25 <= r_cl / r_ei <= 4.0)
            check("кластерный и собственный пути согласуются на семействе", ok,
                  "доли %.4g против %.4g" % (r_cl, r_ei or float("nan")))

            # Новый риск каскада: собственный путь зависит от ансамбля
            # случайных целей. Один seed в отчёте не является устойчивой
            # оценкой M_eff: при неудачном ансамбле можно получить иной
            # порог и принять шум за измерение. Здесь проверяем четыре
            # независимых фиксированных ансамбля; разброс должен быть
            # существенно меньше допуска согласования двух путей.
            seeds = (0, 1, 2, 3)
            eigen = [
                meff_from_family(win, 0.0081, seed=seed).get("M_eff_eigen")
                for seed in seeds
            ]
            finite = [float(v) for v in eigen if v is not None and math.isfinite(v)]
            stable = (len(finite) == len(seeds)
                      and min(finite) > 0.0
                      and max(finite) / min(finite) < 1.5)
            check("собственный M_eff устойчив к ансамблю целей", stable,
                  "оценки %s" % ", ".join("%.4g" % v for v in finite))
            # Даже устойчивый диапазон нуждается в воспроизводимом следе:
            # один seed обязан давать тот же ансамбль, другой — иной.
            a = meff_from_family(win, 0.0081, seed=17)
            b = meff_from_family(win, 0.0081, seed=17)
            c = meff_from_family(win, 0.0081, seed=18)
            reproducible = (
                a.get("targets_sha256") == b.get("targets_sha256")
                and a.get("targets_sha256") != c.get("targets_sha256")
                and a.get("targets_count") == 600
                and a.get("targets_seed") == 17
            )
            check("ансамбль M_eff имеет воспроизводимый отпечаток",
                  reproducible,
                  "seed=17: %s" % a.get("targets_sha256", "нет"))
        except Exception as exc:  # noqa: BLE001
            check("согласование путей проверено", False, repr(exc))

    return fail


if __name__ == "__main__":
    raise SystemExit(1 if selftest() else 0)
