"""Достаточность машинной арифметики: проверка, а не вера.

Слабость, записанная в прошлом лупе, формулировалась как «заменить float на
интервальную арифметику там, где погрешность важна». Сама формулировка
содержит незакрытый вопрос: где именно важна? Замена float на mpmath везде
подряд ничего не доказывает — она лишь прячет вопрос, потому что и у mpmath
конечная точность, просто выше.

Здесь сделано другое. Для каждого вычисляемого значения ошибка машинного
представления ОЦЕНИВАЕТСЯ сравнением с тем же вычислением на 50 знаках, и эта
ошибка сопоставляется с погрешностью, относительно которой считается вердикт.
Если ошибка арифметики на порядки меньше погрешности измерения, float допустим
и это доказано числом. Если сопоставима — вердикт по такому утверждению
выносить нельзя, и сито обязано сказать об этом вместо того, чтобы молча
выдать ответ.

Правило, которое отсюда следует: арифметика считается достаточной, когда
относительная ошибка вычисления не превышает одной сотой относительной
погрешности, с которой сравнивается результат. Запас в сто раз выбран так,
чтобы накопление ошибки в нескольких операциях не могло изменить вывод.

Без mpmath модуль честно сообщает, что проверить не может, и не подменяет
проверку оценкой сверху.
"""

import math

MARGIN = 100.0      # требуемый запас арифметики над погрешностью сравнения

try:
    import mpmath
    HAVE_MPMATH = True
except ImportError:      # pragma: no cover - зависит от окружения
    HAVE_MPMATH = False


def family_value_float(n, k, m, p, q):
    """Член семейства в обычной арифметике double."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return n * 3.0 ** k * math.pi ** m * phi ** p * math.e ** q


def family_value_exact(n, k, m, p, q, digits=50):
    """Тот же член семейства на 50 знаках.

    Возвращает mpmath.mpf. Требует mpmath: если его нет, вызывающий обязан
    получить отказ, а не приближение.
    """
    if not HAVE_MPMATH:
        raise RuntimeError("mpmath недоступен: точное значение не вычислить")
    with mpmath.workdps(digits):
        phi = (1 + mpmath.sqrt(5)) / 2
        return (mpmath.mpf(n) * mpmath.mpf(3) ** k * mpmath.pi ** m
                * phi ** p * mpmath.e ** q)


def arithmetic_error(n, k, m, p, q, digits=50):
    """Относительная ошибка double против 50 знаков для данного члена."""
    exact = family_value_exact(n, k, m, p, q, digits)
    approx = family_value_float(n, k, m, p, q)
    return float(abs(mpmath.mpf(approx) - exact) / abs(exact))


def arithmetic_is_sufficient(params, compared_rel_uncertainty, digits=50):
    """Достаточна ли double-арифметика для вывода при данной погрешности.

    params: (n, k, m, p, q); compared_rel_uncertainty: относительная
    погрешность, с которой сравнивается результат (например, погрешность
    измерения CODATA).

    Возвращает (достаточна, ошибка_арифметики, требуемый_предел).
    """
    err = arithmetic_error(*params, digits=digits)
    limit = compared_rel_uncertainty / MARGIN
    return err <= limit, err, limit


def worst_case_error(ranges, digits=50, sample=200, seed=0):
    """Худшая ошибка double по выборке из семейства.

    Полный обход 123 201 члена на 50 знаках занял бы минуты, поэтому берётся
    случайная выборка ПЛЮС принудительно углы диапазона, где показатели
    максимальны по модулю и ошибка заведомо худшая. Без углов выборка могла бы
    занизить оценку.
    """
    import random
    rnd = random.Random(seed)
    keys = ("n", "k", "m", "p", "q")
    pts = []
    # углы: крайние значения каждого параметра
    corners = [tuple(r[0] if bit else r[-1] for r in
                     [list(ranges[k]) for k in keys])
               for bit in (0, 1)]
    pts.extend(corners)
    for _ in range(sample):
        pts.append(tuple(rnd.choice(list(ranges[k])) for k in keys))
    worst, at = 0.0, None
    for p_ in pts:
        e = arithmetic_error(*p_, digits=digits)
        if e > worst:
            worst, at = e, p_
    return worst, at


# --------------------------------------------------------------------------
# самопроверка
# --------------------------------------------------------------------------

def selftest():
    """5 проверок. Возвращает число провалов."""
    fail = 0

    def check(name, cond):
        nonlocal fail
        if cond:
            print("  ok   %s" % name)
        else:
            fail += 1
            print("  FAIL %s" % name)

    if not HAVE_MPMATH:
        print("  -- mpmath недоступен: проверка достаточности невозможна")
        print("  FAIL модуль не может подтвердить достаточность арифметики")
        return 1

    # 1. Ошибка double на типичном члене семейства крайне мала.
    err = arithmetic_error(2, 0, -2, 4, -1)      # члены формулы для m_e
    check("ошибка double на типичном члене мала (%.2e)" % err, err < 1e-14)

    # 2. Ошибка растёт на крайних показателях, но остаётся ниже 1e-12.
    worst, at = worst_case_error({"n": range(1, 10), "k": range(-6, 7),
                                  "m": range(-4, 5), "p": range(-6, 7),
                                  "q": range(-4, 5)}, sample=120)
    check("худшая ошибка по выборке (%.2e при %s)" % (worst, at),
          worst < 1e-12)

    # 3. Для CODATA-погрешности m_p/m_e (1,7e-11) double достаточна, и это
    # ДОКАЗАНО числом: запас более чем стократный.
    okc, e, lim = arithmetic_is_sufficient((9, 4, 0, 4, -1), 1.7e-11)
    check("double достаточна для CODATA (ошибка %.1e, предел %.1e)" % (e, lim),
          okc)

    # 4. ПОДСТАВКА: при вымышленной погрешности 1e-16 (точнее самой double)
    # арифметика ОБЯЗАНА быть признана недостаточной. Без этого guard пункт 3
    # проходил бы при любой реализации, всегда возвращающей «достаточна».
    bad, e2, lim2 = arithmetic_is_sufficient((9, 4, 0, 4, -1), 1e-16)
    check("недостаточность при погрешности 1e-16 распознана (%.1e > %.1e)"
          % (e2, lim2), not bad)

    # 5. Точное и приближённое значения совпадают в пределах ошибки, но НЕ
    # тождественны: если бы family_value_exact просто возвращала double,
    # разность была бы ровно нулём и все проверки выше стали бы пустыми.
    d = arithmetic_error(7, -5, 4, 6, -4)
    check("точный путь не является копией double (разность %.2e)" % d, d > 0.0)

    return fail


if __name__ == "__main__":
    raise SystemExit(1 if selftest() else 0)
