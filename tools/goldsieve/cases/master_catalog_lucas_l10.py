"""Аудит строки L(10)=123 в каталоге Trinity.

Проверяется ровно одно численное утверждение из корпуса. Эталон вычисляется
по определению из строки документа, второй метод использует независимую
целочисленную рекурсию Лукаса, а наблюдение извлекается из файла корпуса.
Вердикт возвращает только каскад золотого сита.
"""

from decimal import Decimal, localcontext
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md"
N = 10


def _phi():
    return (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)


def reference():
    """Эталон: вычисление φ^10 + φ^-10 по формуле источника."""
    with localcontext() as ctx:
        ctx.prec = 80
        phi = _phi()
        value = phi ** N + (Decimal(1) / phi) ** N
        return float(value)


def reference_alt():
    """Второй метод: целочисленная рекурсия Лукаса для чётного n."""
    a, b = 2, 1
    for _ in range(N):
        a, b = b, a + b
    return float(a)


def observed_from_corpus():
    """Извлекает число из строки таблицы, не пересчитывая его."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if re.match(r"^\|\s*10\s*\|", line):
                match = re.match(r"^\|\s*10\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*\|", line)
                if match:
                    return float(match.group(1))
    raise ValueError("строка таблицы для n=10 не найдена")


def wrong_minus_one():
    """Подставка: значение на единицу меньше заявленного."""
    return reference() - 1.0


def wrong_plus_one():
    """Подставка: значение на единицу больше заявленного."""
    return reference() + 1.0


def wrong_neighbour_index():
    """Подставка: значение той же формулы для соседнего n=9."""
    with localcontext() as ctx:
        ctx.prec = 80
        phi = _phi()
        return float(phi ** 9 + (Decimal(1) / phi) ** 9)


def negative_control():
    """Негативный контроль: соседний индекс n=9 вместо заявленного n=10."""
    return wrong_neighbour_index()


def deterministic_sample():
    """Наблюдаемая величина из одной строки корпуса."""
    return [observed_from_corpus()]


def sample_mean(values):
    return float(sum(values) / len(values))


def alt_tolerance():
    """Разброс независимого целочисленного метода: повторный результат точен."""
    return 0.0


CLAIMS = [
    Claim(
        name="В таблице каталога для n=10 указано L(10)=123",
        source="deploy/trinity-nexus/docs/research/MASTER_SACRED_CATALOG.md:138",
        stated=123,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_minus_one, wrong_plus_one, wrong_neighbour_index],
        null_model=negative_control,
        null_expect=wrong_neighbour_index(),
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
            "С6": "эталон вычисляется по фиксированному определению; численной сетки или разрешения нет",
            "С7": "проверяется точное значение, а не статистическая оценка с несколькими оценивателями",
            "С8": "вход — точная формула и целочисленная таблица; измерительная погрешность не задана",
            "С9": "утверждение не является выборочным измерением, зависящим от размера выборки",
            "С11": "одна детерминированная статистика; тест слишком хорошего согласия неприменим",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes="Чётный индекс делает φ^n + φ^-n совпадающим с целым числом Лукаса; это проверяется вторым методом.",
    ),
]
