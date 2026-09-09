# -*- coding: utf-8 -*-
"""Алгебраическая объяснимость совпадения: PSLQ и границы линейных форм.

Идея, которую даёт теория трансцендентных чисел: близость члена семейства к
цели — это малость линейной формы в логарифмах

    Lambda = log(V / t) = log n + k log 3 + m log pi + p log phi + q - log t.

Для линейных форм в логарифмах АЛГЕБРАИЧЕСКИХ чисел есть доказанные снизу
оценки (Бейкер-Вюстхольц, усиление Матвеева 2000,
https://doi.org/10.1070/IM2000v064n06ABEH000314): |Lambda| не может быть
меньше явной функции от высот и от максимума коэффициентов. Это превращает
ось перебора из статистической оценки в теорему — но только там, где теорема
применима.

ГРАНИЦА ПРИМЕНИМОСТИ, которую нельзя замалчивать: log pi НЕ является
логарифмом алгебраического числа, и оценок бейкеровского типа для линейных
форм, содержащих log pi, не существует. Поэтому:

- при m = 0 (член без pi) граница считается и является теоремой;
- при m != 0 сито обязано вернуть OPEN с этой причиной, а не подставить
  границу, для которой нет доказательства.

Второй, всегда применимый инструмент — PSLQ (Фергюсон-Бейли-Арно,
https://www.davidhbailey.com/dhbpapers/cpslq.pdf): он ищет целочисленное
соотношение между log t и логарифмами базиса. Если соотношение находится при
МАЛЫХ коэффициентах, значит цель лежит в семействе почти точно и совпадение
получено бесплатно — вердикт ПУСТО, а не находка.
"""

import math

PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _mpmath():
    try:
        import mpmath
        return mpmath
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("нужен mpmath: %r" % exc)


def pslq_relation(target, basis=None, max_coeff=12, precision=60):
    """Ищет целочисленное соотношение log(target) = sum c_i * log(basis_i).

    Возвращает (coeffs, max_abs_coeff) или (None, None). Малые коэффициенты
    означают, что цель воспроизводится семейством почти точно и близость не
    несёт информации.
    """
    mp = _mpmath()
    with mp.workprec(int(precision * 3.33)):
        # Базис вычисляется В mpmath, а не приводится из double: иначе
        # логарифмы базиса сами несут ошибку 1e-16 и точное соотношение
        # перестаёт быть точным. На этой ошибке падала самопроверка.
        if basis is None:
            base = [mp.mpf(3), mp.pi, (1 + mp.sqrt(5)) / 2, mp.e]
        else:
            base = [mp.mpf(str(b)) for b in basis]
        vec = [mp.log(mp.mpf(str(target)))] + [mp.log(b) for b in base]
        # Терпимость привязана к точности ВХОДА (цель приходит как double),
        # а не к рабочей точности: искать соотношение точнее входа бессмысленно.
        rel = mp.pslq(vec, tol=mp.mpf(10) ** -13, maxcoeff=max_coeff,
                      maxsteps=50000)
    if not rel:
        return None, None
    return list(int(x) for x in rel), max(abs(int(x)) for x in rel)


def baker_wustholz_bound(coeffs, heights, degree=2):
    """Явная нижняя граница log|Lambda| бейкеровского типа.

    Используется классическая форма Бейкера-Вюстхольца

        log|Lambda| > -C(n, d) * h(alpha_1) * ... * h(alpha_n) * log B,
        C(n, d) = 18 * (n+1)! * n^(n+1) * (32 d)^(n+2) * log(2 n d),

    где n — число логарифмов, d — степень поля, B = max|b_i|. Улучшение
    Матвеева меняет константу, но не характер границы, поэтому для ответа на
    вопрос «ограничивает ли теорема наблюдённую близость» достаточно этой формы:
    она заведомо не сильнее матвеевской.

    Возвращает log|Lambda|_min (отрицательное число).
    """
    n = len(heights)
    if n < 1:
        raise ValueError("нужен хотя бы один логарифм")
    b_max = max(1, max(abs(int(c)) for c in coeffs))
    factorial = math.factorial(n + 1)
    c_const = (18.0 * factorial * n ** (n + 1)
               * (32.0 * degree) ** (n + 2) * math.log(2.0 * n * degree))
    product = 1.0
    for h in heights:
        product *= max(1.0, float(h))
    return -c_const * product * math.log(max(2.0, b_max))


def bound_is_binding(observed_rel_deviation, log_bound):
    """Ограничивает ли теорема наблюдённую близость.

    Если наблюдённое |Lambda| много больше теоретического минимума, теорема
    ничего не запрещает: близость возможна, и объяснять её нужно перебором, а
    не трансцендентностью. Это ожидаемый случай — границы бейкеровского типа
    астрономически слабы. Честный вывод: третья ось НЕ заменяет ось перебора.
    """
    observed = abs(float(observed_rel_deviation))
    if observed <= 0.0:
        return True, float("-inf")
    log_observed = math.log(observed)
    return (log_observed < log_bound), log_observed


def analyse(target, coeffs, has_pi, observed_rel_deviation,
            heights=(3.0, 1.0, 2.0), max_coeff=12):
    """Полный разбор одной цели. Возвращает dict для сита С21."""
    out = {"target": float(target), "has_pi": bool(has_pi),
           "observed_rel_deviation": float(observed_rel_deviation)}
    try:
        rel, mx = pslq_relation(target, max_coeff=max_coeff)
        out["pslq_relation"] = rel
        out["pslq_max_coeff"] = mx
    except RuntimeError as exc:
        out["pslq_error"] = str(exc)
    if has_pi:
        out["bound_applicable"] = False
        out["bound_reason"] = ("линейная форма содержит log pi; оценок "
                               "бейкеровского типа для неё не доказано")
        return out
    out["bound_applicable"] = True
    log_bound = baker_wustholz_bound(coeffs, heights)
    binding, log_obs = bound_is_binding(observed_rel_deviation, log_bound)
    out["log_bound"] = log_bound
    out["log_observed"] = log_obs
    out["bound_binding"] = binding
    return out


def selftest():
    """Самопроверка с подставками. Возвращает число провалов."""
    fail = 0

    def check(name, ok, detail=""):
        nonlocal fail
        print("  %s %s%s" % ("ok  " if ok else "FAIL", name,
                             ("  " + detail) if detail else ""))
        if not ok:
            fail += 1

    # 1. PSLQ обязан найти точное соотношение там, где оно есть по построению.
    exact = 9.0 * PHI ** 2 / math.pi  # = 3^2 * phi^2 * pi^-1
    rel, mx = pslq_relation(exact, max_coeff=20)
    check("PSLQ находит соотношение для члена семейства", rel is not None,
          "соотношение %s" % (rel,))

    # 2. ПОДСТАВКА: у числа, заведомо не лежащего в семействе при малых
    # коэффициентах, соотношение находиться не должно. Детектор, который
    # «находит» соотношение всегда, здесь падает.
    rel2, mx2 = pslq_relation(1.0000000001234567, max_coeff=6)
    check("PSLQ не выдаёт малое соотношение для чужого числа",
          rel2 is None or (mx2 or 0) > 6, "получено %s" % (rel2,))

    # 3. Граница бейкеровского типа обязана быть отрицательной и очень малой.
    log_bound = baker_wustholz_bound((1, 2, 3), (3.0, 1.0, 2.0))
    check("граница логарифма формы отрицательна", log_bound < 0.0,
          "log_bound=%.3e" % log_bound)

    # 4. Ключевой честный вывод: граница НЕ ограничивает реальную близость 1e-5.
    binding, log_obs = bound_is_binding(1e-5, log_bound)
    check("граница слабее наблюдаемой близости (не ограничивает)",
          not binding, "log_obs=%.2f против log_bound=%.3e"
          % (log_obs, log_bound))

    # 5. ПОДСТАВКА: если близость абсурдно мала, граница обязана сработать.
    binding2, _ = bound_is_binding(math.exp(log_bound * 2.0), log_bound)
    check("на невозможной близости граница срабатывает", binding2)

    # 6. Монотонность: больше коэффициенты — слабее граница.
    weaker = baker_wustholz_bound((1000, 1, 1), (3.0, 1.0, 2.0))
    check("рост коэффициентов ослабляет границу", weaker < log_bound,
          "%.3e < %.3e" % (weaker, log_bound))

    # 7. Область применимости: при наличии pi граница не выдаётся.
    res = analyse(math.pi ** 2, (1, 0, 2, 0), True, 1e-4)
    check("при log pi граница объявлена неприменимой",
          res.get("bound_applicable") is False)

    # 8. Без pi граница выдаётся.
    res2 = analyse(9.0 * PHI ** 2, (9, 0, 0, 2), False, 1e-4)
    check("без log pi граница выдаётся", res2.get("bound_applicable") is True)

    return fail


if __name__ == "__main__":
    raise SystemExit(1 if selftest() else 0)
