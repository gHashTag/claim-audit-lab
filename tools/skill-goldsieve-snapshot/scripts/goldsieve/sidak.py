# -*- coding: utf-8 -*-
"""Порог значимости при множественных испытаниях: два независимых пути.

Зачем отдельный модуль. Порог 5,06 сигма для 123 201 испытания корпус Trinity
использует как опорное число, а в каскаде он считался одной строкой
``1-(1-alpha)**(1/m)`` и одним обращением нормального распределения. У такой
реализации три разные слабости, и все три проверяются здесь кодом:

1. **Арифметика.** ``(1-alpha)**(1/m)`` при большом m даёт число вида
   ``1 - eps``, и разность ``1 - (1-eps)`` теряет значащие цифры (катастрофическое
   вычитание). Устойчивая запись ``-expm1(log1p(-alpha)/m)`` этой потери не
   имеет. Разница измеряется, а не предполагается: см. :func:`paths`.
2. **Второй путь.** Тот же порог считается на 50 знаках через mpmath —
   принципиально иным кодом (обратная функция ошибки вместо нормального
   распределения scipy). Совпадение путей — доказательство, расхождение —
   находка об инструменте.
3. **Разные поправки — разные числа.** Шидак и Бонферрони НЕ синонимы:
   ``1-(1-alpha)^(1/m)`` против ``alpha/m``. Šidák выводится из независимости
   испытаний, Бонферрони — из неравенства Буля и независимости НЕ требует.
   Хранятся оба числа и их разность; выдавать одно за другое запрещено.

Ограничение, которое модуль НЕ снимает: обе поправки говорят о числе испытаний,
а не о том, независимы ли они. Проверка предпосылки независимости — предмет
:mod:`goldsieve.preconditions` и сита С20.
"""

from __future__ import annotations

import math

ALPHA_DEFAULT = 0.05

# --------------------------------------------------------------------------
# локальный уровень: две РАЗНЫЕ поправки
# --------------------------------------------------------------------------


def sidak_local_p(alpha: float = ALPHA_DEFAULT, m: int = 1) -> float:
    """Локальный уровень по Šidák, устойчивая запись.

    Тождество: если m испытаний независимы и каждое отвергается на уровне
    p_loc, то вероятность хотя бы одной ложной тревоги равна 1-(1-p_loc)^m;
    приравнивание её к alpha даёт p_loc = 1-(1-alpha)^(1/m).
    """
    _check(alpha, m)
    if m == 1:
        return float(alpha)
    return -math.expm1(math.log1p(-alpha) / m)


def sidak_local_p_naive(alpha: float = ALPHA_DEFAULT, m: int = 1) -> float:
    """Прямая запись формулы. Оставлена НАМЕРЕННО, как объект измерения."""
    _check(alpha, m)
    return 1.0 - (1.0 - alpha) ** (1.0 / m)


def bonferroni_local_p(alpha: float = ALPHA_DEFAULT, m: int = 1) -> float:
    """Локальный уровень по Бонферрони: alpha/m.

    Предпосылка слабее: неравенство Буля верно при любой зависимости
    испытаний. Цена — консервативность: alpha/m <= 1-(1-alpha)^(1/m).
    """
    _check(alpha, m)
    return float(alpha) / m


def _check(alpha: float, m: int) -> None:
    if not (0.0 < alpha < 1.0):
        raise ValueError("семейный уровень ошибки обязан лежать в (0,1)")
    if int(m) != m or m < 1:
        raise ValueError("число испытаний обязано быть целым не меньше 1")


# --------------------------------------------------------------------------
# p -> сигмы (двусторонний порог)
# --------------------------------------------------------------------------


def sigma_from_p(p: float) -> float:
    """Двусторонний порог в сигмах: z, при котором erfc(z/sqrt2) = p."""
    if not (0.0 < p < 1.0):
        raise ValueError("вероятность обязана лежать в (0,1)")
    try:
        from scipy.stats import norm
        return float(norm.isf(p / 2.0))
    except Exception:  # noqa: BLE001
        return _isf_bisect(p / 2.0)


def _isf_bisect(q: float) -> float:
    lo, hi = 0.0, 60.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if 0.5 * math.erfc(mid / math.sqrt(2.0)) > q:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sigma_from_p_exact(p, dps: int = 50):
    """Второй путь: обратная функция ошибки на dps знаках (mpmath).

    Иной код и иная арифметика: z = sqrt(2)*erfinv(1-p) вместо обращения
    нормального распределения scipy.
    """
    from mpmath import mp, mpf, erfinv, sqrt
    with mp.workdps(dps):
        pp = mpf(str(p)) if not hasattr(p, "_mpf_") else p
        return sqrt(2) * erfinv(1 - pp)


def sidak_local_p_exact(alpha: float = ALPHA_DEFAULT, m: int = 1, dps: int = 50):
    """Локальный уровень по Šidák на dps знаках."""
    _check(alpha, m)
    from mpmath import mp, mpf
    with mp.workdps(dps):
        a = mpf(str(alpha))
        return 1 - (1 - a) ** (mpf(1) / mpf(m))


def bonferroni_local_p_exact(alpha: float = ALPHA_DEFAULT, m: int = 1,
                             dps: int = 50):
    _check(alpha, m)
    from mpmath import mp, mpf
    with mp.workdps(dps):
        return mpf(str(alpha)) / mpf(m)


# --------------------------------------------------------------------------
# сводка: оба пути, обе поправки, разности
# --------------------------------------------------------------------------


def paths(alpha: float = ALPHA_DEFAULT, m: int = 1, dps: int = 50) -> dict:
    """Порог двумя независимыми путями и двумя разными поправками.

    Возвращает машинную сводку. Ключи с суффиксом ``_exact`` посчитаны на dps
    знаках через mpmath, без суффикса — двойной точностью и scipy.
    """
    p_s = sidak_local_p(alpha, m)
    p_s_naive = sidak_local_p_naive(alpha, m)
    p_b = bonferroni_local_p(alpha, m)
    z_s = sigma_from_p(p_s)
    z_b = sigma_from_p(p_b)
    p_s_ex = sidak_local_p_exact(alpha, m, dps)
    p_b_ex = bonferroni_local_p_exact(alpha, m, dps)
    z_s_ex = sigma_from_p_exact(p_s_ex, dps)
    z_b_ex = sigma_from_p_exact(p_b_ex, dps)
    out = {
        "alpha": float(alpha),
        "m": int(m),
        "p_sidak": p_s,
        "p_sidak_naive": p_s_naive,
        "p_bonferroni": p_b,
        "sigma_sidak": z_s,
        "sigma_bonferroni": z_b,
        "p_sidak_exact": float(p_s_ex),
        "p_bonferroni_exact": float(p_b_ex),
        "sigma_sidak_exact": float(z_s_ex),
        "sigma_bonferroni_exact": float(z_b_ex),
        # разность поправок: это РАЗНЫЕ числа, а не два названия одного
        "delta_p_sidak_minus_bonferroni": p_s - p_b,
        "delta_sigma_bonferroni_minus_sidak": z_b - z_s,
        # расхождение путей: double против 50 знаков
        "rel_err_p_stable": _rel(p_s, p_s_ex),
        "rel_err_p_naive": _rel(p_s_naive, p_s_ex),
        "abs_err_sigma": abs(z_s - float(z_s_ex)),
    }
    return out


def _rel(value, exact) -> float:
    from mpmath import mpf
    e = mpf(str(exact)) if not hasattr(exact, "_mpf_") else exact
    if e == 0:
        return abs(float(value))
    return float(abs(mpf(str(value)) - e) / abs(e))


def roundtrip_alpha(alpha: float = ALPHA_DEFAULT, m: int = 1, dps: int = 60):
    """Обратная сверка: 1-(1-p_loc)^m обязано вернуть alpha.

    Проверяется именно ТОЖДЕСТВО, из которого выведена формула, а не её
    перепечатка: это независимый от знака ошибки контроль.
    """
    from mpmath import mp, mpf
    with mp.workdps(dps):
        p = sidak_local_p_exact(alpha, m, dps)
        return 1 - (1 - p) ** mpf(m)


# --------------------------------------------------------------------------
# граничные точки и монотонность
# --------------------------------------------------------------------------

BOUNDARY_M = (1, 2, 3, 10, 100, 20412, 123201, 10 ** 6, 10 ** 9)
BOUNDARY_ALPHA = (0.05, 0.01, 1e-6, 1e-12)


def monotonicity(alpha: float = ALPHA_DEFAULT, ms=BOUNDARY_M) -> dict:
    """С ростом m локальный p обязан падать, а порог в сигмах — расти.

    Строгая монотонность: равенство считается нарушением, потому что оно
    означает, что при разных m поправка не различает число испытаний.
    """
    ms = sorted(set(int(x) for x in ms))
    rows = [(m, sidak_local_p(alpha, m), sigma_from_p(sidak_local_p(alpha, m)))
            for m in ms]
    bad_p = [(a[0], b[0]) for a, b in zip(rows, rows[1:]) if not b[1] < a[1]]
    bad_z = [(a[0], b[0]) for a, b in zip(rows, rows[1:]) if not b[2] > a[2]]
    return {"rows": rows, "violations_p": bad_p, "violations_sigma": bad_z,
            "monotone": not bad_p and not bad_z}


def ordering(alpha: float = ALPHA_DEFAULT, ms=BOUNDARY_M) -> dict:
    """Šidák не может быть строже Бонферрони: p_sidak >= p_bonf.

    При m=1 обе поправки обязаны совпасть точно — это граничная точка, на
    которой видно, что формулы не перепутаны местами.
    """
    bad = []
    for m in ms:
        p_s, p_b = sidak_local_p(alpha, m), bonferroni_local_p(alpha, m)
        if p_s < p_b * (1 - 1e-15):
            bad.append((m, p_s, p_b))
    p1s, p1b = sidak_local_p(alpha, 1), bonferroni_local_p(alpha, 1)
    return {"violations": bad, "equal_at_one": p1s == p1b == alpha}


def table(alpha: float = ALPHA_DEFAULT, ms=BOUNDARY_M) -> str:
    head = ("%-12s %-14s %-14s %-10s %-10s %s"
            % ("m", "p Šidák", "p Бонферрони", "σ Šidák", "σ Бонф.", "Δσ"))
    lines = [head, "-" * len(head)]
    for m in ms:
        d = paths(alpha, m)
        lines.append("%-12d %-14.6g %-14.6g %-10.6f %-10.6f %+.2e"
                     % (m, d["p_sidak"], d["p_bonferroni"],
                        d["sigma_sidak"], d["sigma_bonferroni"],
                        d["delta_sigma_bonferroni_minus_sidak"]))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# самопроверка
# --------------------------------------------------------------------------


def selftest() -> int:
    """Возвращает число провалов. Проверок: 24."""
    import sys
    _self = sys.modules[__name__]
    fail = 0

    def ok(cond, msg):
        nonlocal fail
        if not cond:
            fail += 1
            print("    ПРОВАЛ: %s" % msg)

    # 1-3. граница m=1: обе поправки обязаны дать ровно alpha
    ok(_self.sidak_local_p(0.05, 1) == 0.05, "m=1: Šidák обязан дать alpha")
    ok(_self.bonferroni_local_p(0.05, 1) == 0.05,
       "m=1: Бонферрони обязан дать alpha")
    ok(abs(_self.sigma_from_p(0.05) - 1.959963985) < 1e-8,
       "двусторонний порог при alpha=0,05 равен 1,95996 сигма")

    # 4-5. малое m считается вручную
    ok(abs(_self.sidak_local_p(0.05, 2) - (1 - math.sqrt(0.95))) < 1e-15,
       "m=2: Šidák обязан равняться 1-sqrt(0,95)")
    ok(abs(_self.bonferroni_local_p(0.05, 2) - 0.025) < 1e-18,
       "m=2: Бонферрони обязан равняться 0,025")

    # 6-7. Šidák и Бонферрони — РАЗНЫЕ числа при m>1
    ok(_self.sidak_local_p(0.05, 2) > _self.bonferroni_local_p(0.05, 2),
       "при m>1 Šidák обязан быть мягче Бонферрони")
    o = _self.ordering()
    ok(not o["violations"] and o["equal_at_one"],
       "порядок поправок нарушен: %r" % (o["violations"],))

    # 8-10. корпусная точка 123 201
    d = _self.paths(0.05, 123201)
    ok(abs(d["sigma_sidak"] - 5.0613316768) < 1e-9,
       "порог для 123 201 испытания обязан быть 5,0613316768 сигма")
    ok(abs(d["p_sidak"] - 4.16336e-7) < 1e-11,
       "локальный уровень для 123 201 испытания около 4,163e-7")
    ok(d["delta_sigma_bonferroni_minus_sidak"] > 0,
       "Бонферрони обязан требовать БОЛЬШЕ сигм, чем Šidák")

    # 11-12. второй путь: 50 знаков против double
    ok(d["rel_err_p_stable"] < 1e-15,
       "устойчивая запись расходится с 50 знаками: %.3g"
       % d["rel_err_p_stable"])
    ok(d["abs_err_sigma"] < 1e-9,
       "порог в сигмах расходится между путями: %.3g" % d["abs_err_sigma"])

    # 13-14. прямая запись формулы теряет точность на большом m, и это
    # ИЗМЕРЕНО, а не объявлено
    big = _self.paths(0.05, 10 ** 9)
    ok(big["rel_err_p_stable"] < 1e-15,
       "устойчивая запись обязана держать точность при m=1e9")
    ok(big["rel_err_p_naive"] > 100 * max(big["rel_err_p_stable"], 1e-18),
       "прямая запись при m=1e9 обязана быть ЗАМЕТНО хуже устойчивой: "
       "naive %.3g против stable %.3g"
       % (big["rel_err_p_naive"], big["rel_err_p_stable"]))

    # 15-16. alpha близкое к нулю
    small = _self.paths(1e-12, 100)
    ok(small["sigma_sidak"] > 7.0,
       "при alpha=1e-12 и m=100 порог обязан превысить 7 сигм")
    ok(abs(small["p_sidak"] - 1e-14) / 1e-14 < 1e-6,
       "при малом alpha локальный уровень обязан быть близок к alpha/m")

    # 17-18. монотонность
    mono = _self.monotonicity()
    ok(mono["monotone"], "монотонность нарушена: %r" % (mono,))
    mono_small = _self.monotonicity(1e-6)
    ok(mono_small["monotone"],
       "монотонность нарушена при малом alpha: %r" % (mono_small,))

    # 19. обратная сверка тождества
    rt = _self.roundtrip_alpha(0.05, 123201)
    ok(abs(float(rt) - 0.05) < 1e-30,
       "обратная сверка тождества не вернула alpha: %s" % rt)

    # 20-23. отказы на недопустимых входах
    for bad_args in ((0.0, 10), (1.0, 10), (0.05, 0), (0.05, 2.5)):
        try:
            _self.sidak_local_p(*bad_args)
            ok(False, "недопустимый вход принят: %r" % (bad_args,))
        except ValueError:
            pass

    # 24. согласие с прежней реализацией каскада: новый модуль не имеет
    # права молча изменить порог, которым уже вынесены вердикты
    from .sieve import sidak_local_alpha
    ok(abs(sidak_local_alpha(0.05, 123201) - _self.sidak_local_p(0.05, 123201))
       < 1e-15, "новый модуль расходится с каскадом")

    return fail


def main(argv=None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--table":
        print(table())
        return 0
    print("самопроверка порога множественности")
    fail = selftest()
    print("  итог: %d провалов" % fail)
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
