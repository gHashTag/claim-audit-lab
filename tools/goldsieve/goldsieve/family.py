"""Семейство перебираемых формул и множественность попаданий.

Модуль отвечает на один вопрос: если формулу выбирают перебором из M кандидатов,
сколько попаданий в произвольную цель с относительной точностью eps ожидается
СЛУЧАЙНО. Без этого числа «совпадение на 0,001%» не является свидетельством.

Опора: эффект look-elsewhere (Gross & Vitells 2010) и поправка на множественность.
Локальная вероятность p_loc относится к одной проверенной гипотезе; при переборе
M кандидатов вероятность увидеть хотя бы одно попадание есть
    p_glob = 1 - (1 - p_loc)^M,
а ожидаемое число попаданий E[h] = M * p_loc. При E[h] >= 1 попадание перестаёт
быть свидетельством в пользу конкретной формулы.

У модуля есть своя самопроверка с подставкой (см. selftest_family).
"""

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0
E = math.e
PI = math.pi

# Объявленный в корпусе «стандартный» перебор:
# n in [1,9], k in [-4,4], m in [-3,0], p in [-4,4], q in [-3,3] -> 9*9*4*9*7.
STANDARD_RANGES = {
    "n": list(range(1, 10)),
    "k": list(range(-4, 5)),
    "m": list(range(-3, 1)),
    "p": list(range(-4, 5)),
    "q": list(range(-3, 4)),
}


def declared_size(ranges=None) -> int:
    """Размер объявленного пространства как произведение длин диапазонов."""
    r = ranges or STANDARD_RANGES
    size = 1
    for key in ("n", "k", "m", "p", "q"):
        size *= len(r[key])
    return size


def value(n, k, m, p, q) -> float:
    """Значение формулы n * 3^k * pi^m * phi^p * e^q."""
    return n * 3.0 ** k * PI ** m * PHI ** p * E ** q


def enumerate_family(ranges=None):
    """Все значения семейства. Возвращает отсортированный список float."""
    r = ranges or STANDARD_RANGES
    out = []
    for n in r["n"]:
        for k in r["k"]:
            for m in r["m"]:
                for p in r["p"]:
                    for q in r["q"]:
                        out.append(value(n, k, m, p, q))
    out.sort()
    return out


def hits(values, target, eps) -> int:
    """Сколько членов семейства попадают в цель с относительной точностью eps.

    values обязан быть отсортирован: используется двоичный поиск, иначе перебор
    на каждой из тысяч случайных целей становится непозволительно медленным.
    """
    import bisect
    if target <= 0:
        raise ValueError("цель должна быть положительной")
    lo = target * (1.0 - eps)
    hi = target * (1.0 + eps)
    left = bisect.bisect_left(values, lo)
    right = bisect.bisect_right(values, hi)
    return right - left


def empirical_multiplicity(target_decades, eps, ranges=None, trials=2000, seed=0):
    """Частота случайных попаданий: КОНТРОЛЬ на подгонку под ответ.

    Цели берутся логарифмически равномерно в том же диапазоне порядков, что и
    реальные цели корпуса. Возвращает (доля целей с попаданием, среднее число
    попаданий). Логарифмическая равномерность выбрана потому, что и само
    семейство приблизительно логарифмически равномерно: сравнение идёт в той же
    мере, а не в удобной.
    """
    import random
    values = enumerate_family(ranges)
    rng = random.Random(seed)
    lo, hi = target_decades
    got = 0
    total = 0
    for _ in range(trials):
        t = 10.0 ** rng.uniform(lo, hi)
        h = hits(values, t, eps)
        total += h
        if h:
            got += 1
    return got / trials, total / trials


def analytic_multiplicity(eps, ranges=None, target_decades=(-1.0, 4.0)):
    """Второй, независимый путь к тому же числу — без случайных чисел.

    Первая версия этой функции считала плотность членов как M/D по ВСЕМУ размаху
    семейства, то есть предполагала равномерность в log10. Самопроверка показала
    расхождение с эмпирикой на 47%: семейство сгущается в середине, потому что
    log10 значения есть сумма пяти независимых слагаемых и распределён
    колоколообразно, а не равномерно. Правильная оценка использует плотность
    ИМЕННО в том диапазоне, откуда берутся цели:

        E[h] = (число членов семейства в диапазоне целей) / (ширина диапазона)
               * log10((1+eps)/(1-eps)).

    Случайные числа не используются, поэтому оценка остаётся независимой
    проверкой эмпирической.
    """
    import bisect
    values = enumerate_family(ranges)
    lo, hi = target_decades
    left = bisect.bisect_left(values, 10.0 ** lo)
    right = bisect.bisect_right(values, 10.0 ** hi)
    inside = right - left
    width = math.log10((1.0 + eps) / (1.0 - eps))
    return inside * width / (hi - lo)


def global_p(eps, size, target_decades=(-1.0, 4.0)):
    """Глобальная вероятность хотя бы одного попадания при переборе size раз.

    p_loc берётся как доля логарифмической оси, накрытая допуском:
    p_loc = log10((1+eps)/(1-eps)) / D_целей. Далее p_glob = 1 - (1-p_loc)^size.
    """
    span = target_decades[1] - target_decades[0]
    p_loc = math.log10((1.0 + eps) / (1.0 - eps)) / span
    p_loc = min(max(p_loc, 0.0), 1.0)
    return 1.0 - (1.0 - p_loc) ** size


def description_bits(size) -> float:
    """Сколько бит нужно, чтобы указать одного члена семейства: log2(M)."""
    return math.log2(size)


def match_bits(eps, target_relative_uncertainty=None) -> float:
    """Сколько бит информации несёт совпадение с точностью eps.

    Совпадение сужает возможное значение цели в 1/(2*eps) раз, что даёт
    log2(1/(2*eps)) бит. Если у цели есть собственная погрешность u, то точность
    лучше u бессмысленна: eps заменяется на max(eps, u). Это и есть аналог
    бюджета точности на уровне содержательности.
    """
    e = eps
    if target_relative_uncertainty is not None:
        e = max(eps, target_relative_uncertainty)
    if e <= 0:
        return float("inf")
    return math.log2(1.0 / (2.0 * e))


def out_of_declared_range(params, ranges=None):
    """Какие параметры вышли за объявленные границы перебора.

    params — словарь n,k,m,p,q. Возвращает список нарушений вида ('m', 4, [-3..0]).
    Сито объявленной области опирается на эту функцию: если формулы в таблице
    используют показатели вне объявленного пространства, заявленный размер
    перебора занижен, а значит занижена и поправка на множественность.
    """
    r = ranges or STANDARD_RANGES
    bad = []
    for key in ("n", "k", "m", "p", "q"):
        if key not in params:
            continue
        allowed = r[key]
        if params[key] not in allowed:
            bad.append((key, params[key], (min(allowed), max(allowed))))
    return bad


# ---------------------------------------------------------------------------
# самопроверка модуля: у эталона обязана быть своя проверка с подставкой
# ---------------------------------------------------------------------------

def selftest_family(report):
    """report(name, ok, detail) — вызывается из общего selftest."""
    size = declared_size()
    report("family: объявленный размер = 20412", size == 20412, "получено %d" % size)

    values = enumerate_family()
    report("family: перебор даёт объявленное число значений",
           len(values) == size, "%d против %d" % (len(values), size))
    report("family: список отсортирован",
           all(values[i] <= values[i + 1] for i in range(0, len(values) - 1, 97)),
           "нужна сортировка для двоичного поиска")

    # известное значение семейства воспроизводится
    v = value(4, 2, -1, 1, 2)
    report("family: 1/alpha-подобное значение 137.00 воспроизводится",
           abs(v / 137.0027 - 1.0) < 1e-5, "получено %.4f" % v)

    # подставка: попадание в цель, которой в семействе заведомо нет рядом.
    # Берём цель посреди самого разреженного места — очень большое число.
    far = values[-1] * 3.0
    report("family: подставка (цель вне охвата) даёт нуль попаданий",
           hits(values, far, 1e-6) == 0, "цель %.3e" % far)

    # попадание в саму точку семейства обязано находиться
    report("family: точное значение семейства находится",
           hits(values, v, 1e-9) >= 1, "не найдено собственное значение")

    # эмпирика и аналитика должны согласоваться в пределах 25%
    frac, mean = empirical_multiplicity((-1.0, 4.0), 1e-3, trials=1500, seed=7)
    ana = analytic_multiplicity(1e-3, target_decades=(-1.0, 4.0))
    report("family: эмпирическая и аналитическая множественность согласуются",
           abs(mean / ana - 1.0) < 0.12,
           "эмпирика %.3f против аналитики %.3f" % (mean, ana))

    # подставка на аналитику: оценка по всему размаху вместо диапазона целей
    # обязана заметно расходиться с эмпирикой — иначе проверка вырождена
    span_all = math.log10(values[-1]) - math.log10(values[0])
    naive = len(values) * math.log10((1.0 + 1e-3) / (1.0 - 1e-3)) / span_all
    report("family: подставка (равномерность по всему размаху) расходится",
           abs(naive / mean - 1.0) > 0.2,
           "наивно %.3f против эмпирики %.3f" % (naive, mean))

    # монотонность: чем грубее допуск, тем больше попаданий
    _, mean_coarse = empirical_multiplicity((-1.0, 4.0), 1e-2, trials=800, seed=7)
    report("family: множественность растёт с допуском", mean_coarse > mean,
           "%.3f против %.3f" % (mean_coarse, mean))

    # MDL: описание члена семейства стоит log2(20412) ~ 14.3 бит
    db = description_bits(size)
    report("family: описание члена семейства ~14.3 бит", abs(db - 14.317) < 0.01,
           "получено %.3f" % db)
    # совпадение на 0.001% даёт log2(1/2e-5) ~ 15.6 бит
    mb = match_bits(1e-5)
    report("family: совпадение 1e-5 даёт ~15.6 бит", abs(mb - 15.61) < 0.05,
           "получено %.3f" % mb)
    # ...но если у цели своя погрешность 1%, совпадение не может стоить больше
    mb2 = match_bits(1e-5, target_relative_uncertainty=1e-2)
    report("family: погрешность цели срезает биты совпадения",
           abs(mb2 - 5.64) < 0.05, "получено %.3f" % mb2)

    bad = out_of_declared_range({"n": 2, "k": 4, "m": 4, "p": -6, "q": 0})
    keys = sorted(k for k, _, _ in bad)
    report("family: выход за объявленный диапазон ловится",
           keys == ["m", "p"], "нарушения: %s" % (bad,))
    report("family: законные параметры нарушений не дают",
           out_of_declared_range({"n": 4, "k": 2, "m": -1, "p": 1, "q": 2}) == [],
           "ложное срабатывание")


def selftest():
    """Обёртка под общий формат: возвращает число провалов."""
    state = {"fail": 0}

    def report(name, ok, detail=""):
        if ok:
            print("     ok   %-52s %s" % (name, detail))
        else:
            state["fail"] += 1
            print("     FAIL %-52s %s" % (name, detail))

    selftest_family(report)
    return state["fail"]
