"""Аудит числа комбинаций стандартного поиска в формуле из корпуса Trinity.

Проверяется ровно одно утверждение. Эталон считается из пяти диапазонов,
наблюдение извлекается из строки документа, а альтернативный эталон строится
явным перечислением всех комбинаций.
"""

import itertools
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md"


# Диапазоны следуют определениям непосредственно перед заявлением в документе.
N_RANGE = range(1, 10)
K_RANGE = range(-4, 5)
M_RANGE = range(-3, 1)
P_RANGE = range(-4, 5)
Q_RANGE = range(-3, 4)


def reference():
    """Вычисляемый эталон: произведение размеров пяти включительных диапазонов."""
    return math.prod(len(r) for r in (N_RANGE, K_RANGE, M_RANGE, P_RANGE, Q_RANGE))


def reference_alt():
    """Независимый путь: явный подсчёт декартова произведения диапазонов."""
    return sum(
        1
        for _ in itertools.product(N_RANGE, K_RANGE, M_RANGE, P_RANGE, Q_RANGE)
    )


def observed_from_corpus():
    """Извлекает заявленное число из строки документа, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "Standard search:" in line:
                match = re.search(r"=\s*([0-9]+)\{,\}([0-9]+)\$\s+combinations", line)
                if not match:
                    raise ValueError("число в строке Standard search не распознано")
                return int(match.group(1) + match.group(2))
    raise ValueError("строка Standard search не найдена")


def wrong_plus_one():
    """Подставка: ошибка на одну комбинацию."""
    return reference() + 1


def wrong_extended_count():
    """Подставка: число расширенного, а не стандартного поиска."""
    return 123201


def negative_control():
    """Негативный контроль: изменённый диапазон коэффициента n = 1..8."""
    return math.prod((8, len(K_RANGE), len(M_RANGE), len(P_RANGE), len(Q_RANGE)))


def deterministic_sample():
    """Сырая детерминированная наблюдаемая величина из одной строки корпуса."""
    return [float(observed_from_corpus())]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Погрешность второго точного перечисления: разброс по повторным прогонам равен нулю."""
    return 0.0


CLAIMS = [
    Claim(
        name="Стандартный поиск содержит 20 412 комбинаций",
        source="docs/docs/math-foundations/sacred-formulas.md:25",
        stated=20412,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_plus_one, wrong_extended_count],
        null_model=negative_control,
        null_expect=18144,
        null_kind="negative",
        tolerance=0.0,
        sample=deterministic_sample,
        statistics={"value": sample_mean},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={
            "С15": "утверждение о числе в документе, внешней величины нет",
            "С16": "перебора формул в этом утверждении нет",
            "С17": "длина описания неприменима: это не закон, а запись числа",
            "С18": "объявленных границ перебора это утверждение не касается",
            "С6": "для точного подсчёта декартова произведения нет численной сетки или разрешения",
            "С7": "это точный подсчёт, а не оценка по нескольким статистическим оценивателям",
            "С8": "целочисленный комбинаторный результат; погрешность входных данных не заявлена",
            "С9": "утверждение не является выборочным измерением, зависящим от конечного размера корпуса",
            "С11": "одно детерминированное число и одна статистика; тест множественного слишком точного согласия неприменим",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes=(
            "Заявление проверяется как комбинаторный подсчёт. Негативный контроль "
            "меняет один из пяти диапазонов и потому обязан отличаться от эталона."
        ),
    ),
]
