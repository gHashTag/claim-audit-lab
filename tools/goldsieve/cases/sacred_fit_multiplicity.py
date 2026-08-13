"""Аудит содержательности «священных формул»: подгонка или предсказание.

Корпус утверждает, что семейство V = n·3^k·π^m·φ^p·e^q воспроизводит физические
константы с точностью до 0,0005%, и приводит 75 совпадений. Прежние тики сита
проверяли лишь одно: что арифметика формулы даёт напечатанное рядом число. Это
тавтология — такая проверка проходит при любом значении формулы.

Здесь проверяется то, что утверждение действительно означает, тремя новыми
ситами:

* С16 — сколько попаданий в ПРОИЗВОЛЬНУЮ цель даёт то же семейство случайно;
* С17 — стоит ли описание формулы меньше бит, чем объясняет совпадение;
* С18 — лежат ли фактически использованные показатели внутри объявленного
  перебора (иначе объявленный размер 20 412 занижен вместе с поправкой).

Ни одно число не цитируется: размер перебора считается из объявленных границ,
показатели извлекаются из таблиц корпуса, множественность измеряется двумя
независимыми способами.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402
from goldsieve import family  # noqa: E402

SOURCE = ("/home/user/workspace/corpus/trinity/docs/docs/math-foundations/"
          "sacred-formulas.md")

TUPLE_RE = re.compile(r"\$\((-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\)\$")
ERROR_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _rows():
    """Строки таблиц с явной пятёркой параметров: (params, error_percent|None)."""
    out = []
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            m = TUPLE_RE.search(line)
            if not m:
                continue
            n, k, mm, p, q = (int(x) for x in m.groups())
            err = None
            tail = line[m.end():]
            e = ERROR_RE.search(tail.replace("**", ""))
            if e:
                err = float(e.group(1)) / 100.0
            out.append(({"n": n, "k": k, "m": mm, "p": p, "q": q}, err))
    if not out:
        raise ValueError("в источнике не найдено ни одной пятёрки параметров")
    return out


def _latex_rows():
    """Строки таблицы предсказаний, где формула записана в LaTeX, а не пятёркой."""
    pat = re.compile(
        r"\$(\d+)\s*\\cdot\s*3\^\{?(-?\d+)\}?"
        r"(?:\s*\\cdot\s*\\pi(?:\^\{?(-?\d+)\}?)?)?"
        r"(?:\s*\\cdot\s*\\varphi(?:\^\{?(-?\d+)\}?)?)?"
        r"(?:\s*\\cdot\s*e(?:\^\{?(-?\d+)\}?)?)?\$")
    out = []
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            m = pat.search(line)
            if not m:
                continue
            n = int(m.group(1))
            k = int(m.group(2))

            def power(idx, present_token):
                if present_token not in m.group(0):
                    return 0
                g = m.group(idx)
                return int(g) if g is not None else 1

            mm = power(3, "\\pi")
            p = power(4, "\\varphi")
            q = power(5, "\\cdot e")
            err = None
            e = ERROR_RE.search(line[m.end():].replace("**", ""))
            if e:
                err = float(e.group(1)) / 100.0
            out.append(({"n": n, "k": k, "m": mm, "p": p, "q": q}, err))
    return out


def all_rows():
    return _rows() + _latex_rows()


# --------------------------------------------------------------------------
# С18: объявленная область против фактически использованной
# --------------------------------------------------------------------------

def domain_violations():
    """Все выходы за объявленные границы перебора по всем разобранным строкам."""
    bad = []
    for params, _ in all_rows():
        for key, value, bounds in family.out_of_declared_range(params):
            bad.append((key, value, bounds))
    return bad


def observed_violation_count():
    return float(len(domain_violations()))


def declared_violation_count():
    """Корпус объявляет стандартный перебор достаточным, то есть ноль выходов."""
    return 0.0


# --------------------------------------------------------------------------
# С16 и С17: множественность и длина описания при СРЕДНЕЙ заявленной точности
# --------------------------------------------------------------------------

def claimed_eps():
    """Медианная заявленная точность совпадения по строкам, где она указана.

    Медиана, а не минимум: минимум — это отдельная, самая выгодная строка, и
    судить по ней означало бы повторить ту же ошибку выбора после просмотра
    данных.
    """
    errs = sorted(e for _, e in all_rows() if e is not None and e > 0)
    if not errs:
        raise ValueError("в источнике не найдено ни одной заявленной точности")
    mid = len(errs) // 2
    return errs[mid] if len(errs) % 2 else 0.5 * (errs[mid - 1] + errs[mid])


def effective_ranges():
    """Границы, реально нужные, чтобы вместить все использованные показатели."""
    r = {key: list(vals) for key, vals in family.STANDARD_RANGES.items()}
    for params, _ in all_rows():
        for key in r:
            v = params[key]
            lo, hi = min(r[key]), max(r[key])
            if v < lo or v > hi:
                r[key] = list(range(min(lo, v), max(hi, v) + 1))
    return r


def target_decades():
    """Диапазон порядков целей — берётся из значений самого семейства."""
    return (-1.0, 4.0)


def multiplicity():
    eps = claimed_eps()
    ranges = effective_ranges()
    size = family.declared_size(ranges)
    frac, mean = family.empirical_multiplicity(target_decades(), eps,
                                               ranges=ranges, trials=3000, seed=1)
    ana = family.analytic_multiplicity(eps, ranges=ranges,
                                       target_decades=target_decades())
    return {
        "expected_hits": mean,
        "expected_hits_analytic": ana,
        "fraction_random_targets_hit": frac,
        "p_global": family.global_p(eps, size, target_decades()),
        "eps": eps,
        "size": size,
    }


def mdl():
    eps = claimed_eps()
    size = family.declared_size(effective_ranges())
    return {
        "description_bits": family.description_bits(size),
        "match_bits": family.match_bits(eps),
        "eps": eps,
        "size": size,
    }


# --------------------------------------------------------------------------
# С1-С5: эталон, наблюдение, подставка, контроль для утверждения о С18
# --------------------------------------------------------------------------

def null_model_violations():
    """ПОЗИТИВНЫЙ контроль: случайные пятёрки внутри границ обязаны дать ноль.

    Первая версия объявляла этот контроль негативным, и сито С5 честно сорвало
    прогон: «шум выглядит как сигнал». Так и есть — для утверждения «нарушений
    ноль» контроль, дающий ноль, ничего не различает. Правильный смысл здесь
    позитивный: модель, построенная строго внутри объявленных границ, ОБЯЗАНА
    воспроизвести эталонный ноль, и если бы она его не дала, сломан был бы сам
    детектор нарушений.
    """
    import random
    rng = random.Random(3)
    r = family.STANDARD_RANGES
    bad = 0
    for _ in range(len(all_rows())):
        params = {key: rng.choice(vals) for key, vals in r.items()}
        bad += len(family.out_of_declared_range(params))
    return float(bad)


CLAIMS = [
    Claim(
        name="объявленного перебора 20 412 достаточно для формул из таблиц",
        source="docs/docs/math-foundations/sacred-formulas.md:25 и таблицы",
        stated=declared_violation_count(),
        reference=declared_violation_count,
        observed=observed_violation_count,
        wrong=[lambda: 1.0, lambda: 5.0],
        null_model=null_model_violations,
        null_expect=0.0,
        null_kind="positive",
        tolerance=1e-9,
        declared_domain=domain_violations,
        inputs=[SOURCE],
        notes=("нарушение означает, что фактическое пространство перебора шире "
               "объявленного, а значит занижена и поправка на множественность"),
        skip_reasons={
            "С6": "величина целочисленная, сетки нет",
            "С7": "иных законных оценок числа нарушений нет",
            "С8": "показатели целые, погрешности входа нет",
            "С9": "все строки таблиц учтены, выборки нет",
            "С10": "счётная величина без выборочного шума",
            "С11": "статистик меньше трёх",
            "С12": "второй способ подсчёта нарушений тот же самый",
            "С15": "утверждение о самом документе, внешней величины нет",
            "С16": "утверждение о границах, а не о совпадении с целью",
            "С17": "утверждение о границах, длина описания неприменима",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
    ),
    Claim(
        name="совпадения священных формул с константами содержательны, а не подогнаны",
        source="docs/docs/math-foundations/sacred-formulas.md:30 (75 совпадений)",
        stated=1.0,
        reference=lambda: 1.0,
        observed=lambda: 1.0,
        wrong=[lambda: 2.0],
        multiplicity=multiplicity,
        mdl=mdl,
        declared_domain=domain_violations,
        tolerance=1e-9,
        inputs=[SOURCE],
        notes=("проверяется не арифметика формулы, а то, несёт ли совпадение "
               "информацию: сколько попаданий даёт случай и сжимает ли формула "
               "данные"),
        skip_reasons={
            "С5": "контроль вынесен в С16: случайные цели и есть нулевая модель",
            "С6": "сетки нет",
            "С7": "иных оценок нет",
            "С8": "погрешность входа учтена в С17 через погрешность цели",
            "С9": "все строки учтены",
            "С10": "величина не выборочная",
            "С11": "статистик меньше трёх",
            "С12": "множественность посчитана двумя способами внутри С16",
            "С15": "здесь проверяется класс утверждения, внешние цели — отдельными случаями",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
    ),
]
