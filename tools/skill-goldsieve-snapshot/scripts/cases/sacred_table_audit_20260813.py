"""Аудит двух численных утверждений из таблицы священных формул.

Первое утверждение — размер расширенного декартова поиска. Второе — число
строк, действительно дающих относительную ошибку меньше 0,01 процента.
Эталоны считаются из диапазонов и формул, а наблюдения читаются отдельно.
"""

import itertools
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402

SOURCE = "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md"
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def _lines():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.readlines()


def _line_containing(text):
    return next(line for line in _lines() if text in line)


def _parse_product(line):
    # Читает только числовые множители из записи 9 x 13 x ... = 123201.
    left = line.split("=", 1)[0]
    nums = [int(x) for x in re.findall(r"\d+", left)]
    return nums


def extended_reference():
    """Вычислимый эталон: произведение размеров расширенных диапазонов."""
    # Диапазоны в нормативной строке спецификации (включительные границы).
    ranges = [range(1, 10), range(-6, 7), range(-4, 5), range(-6, 7), range(-4, 5)]
    return math.prod(len(r) for r in ranges)


def extended_reference_alt():
    """Независимый эталон: явное перечисление декартова произведения."""
    ranges = [range(1, 10), range(-6, 7), range(-4, 5), range(-6, 7), range(-4, 5)]
    return sum(1 for _ in itertools.product(*ranges))


def extended_observed():
    line = _line_containing("Extended search:")
    match = re.search(r"=\s*([0-9]+)\{,\}([0-9]+)", line)
    if not match:
        raise ValueError("не найдено число расширенного поиска")
    return int(match.group(1) + match.group(2))


def extended_wrong_declared_standard():
    return 20412


def extended_wrong_off_by_one():
    # Отклонение достаточно велико для разрешающей способности сита.
    return extended_reference() + 1000


def extended_negative_control():
    # Сужаем диапазон k на одну крайнюю степень: контроль обязан отличаться.
    ranges = [range(1, 10), range(-5, 7), range(-4, 5), range(-6, 7), range(-4, 5)]
    return math.prod(len(r) for r in ranges)


def _established_rows():
    lines = _lines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## Established Constants"))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
               if line.startswith("## Predictions"))
    rows = []
    for line in lines[start:end]:
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] in {"Name", "------"} or set(cells[0]) <= {"-"}:
            continue
        tuple_match = re.search(r"\((-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\)", cells[2])
        target_match = re.search(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", cells[1])
        if not tuple_match or not target_match:
            continue
        params = tuple(int(x) for x in tuple_match.groups())
        target = float(target_match.group(0))
        rows.append((cells[0], params, target))
    return rows


def _formula(params):
    n, k, m, p, q = params
    return n * 3.0 ** k * math.pi ** m * PHI ** p * math.e ** q


def exact_reference():
    """Пересчитывает формулы и считает относительную ошибку < 0,01 %."""
    return sum(abs(_formula(params) - target) / abs(target) * 100.0 < 0.01
                           for _, params, target in _established_rows())


def exact_reference_alt():
    """Второй метод: считает то же множество через логарифмические ошибки."""
    count = 0
    for _, params, target in _established_rows():
        log_error = abs(math.log(_formula(params) / target))
        if log_error < math.log1p(0.0001):
            count += 1
    return float(count)


def exact_observed():
    line = _line_containing("| **EXACT**")
    match = re.search(r"\|\s*(\d+)\s*\(", line)
    if not match:
        raise ValueError("не найден счётчик EXACT")
    return int(match.group(1))


def exact_wrong_plus_one():
    return exact_reference() + 1


def exact_wrong_zero():
    return 0


def exact_negative_control():
    # Та же таблица, но более строгий порог 0,0001%; шум не должен совпасть.
    return sum(abs(_formula(params) - target) / abs(target) * 100.0 < 0.0001
               for _, params, target in _established_rows())


def extended_alt_tolerance():
    return 0.0


def exact_alt_tolerance():
    return 0.0


def deterministic_sample():
    return [float(extended_observed()), float(exact_observed())]


def sample_mean(values):
    return float(sum(values) / len(values))


def exact_sample():
    return [float(exact_observed())]


def exact_sample_value(values):
    return float(values[0])


COMMON_SKIPS = {
    "С6": "эталон — конечный подсчёт диапазонов или строк; сетки и разрешения нет",
    "С7": "точный подсчёт, законной смены оценивателя нет",
    "С8": "целочисленный счёт; погрешность входа не задана",
    "С9": "утверждение не является выборочным измерением, зависящим от размера выборки",
    "С11": "одна числовая статистика; тест слишком хорошего согласия неприменим",
    "С15": "это утверждение о счёте в документе, внешняя измерительная цель отсутствует",
    "С16": "перебора формул под внешнюю цель в утверждении нет",
    "С17": "формула не заявляет закон или описание данных; MDL неприменим",
    "С18": "утверждение не объявляет область перебора формул",
}


CLAIMS = [
    Claim(
        name="Расширенный поиск содержит 123 201 комбинацию",
        source="docs/docs/math-foundations/sacred-formulas.md:26",
        stated=123201,
        reference=extended_reference,
        observed=extended_observed,
        wrong=[extended_wrong_declared_standard, extended_wrong_off_by_one],
        null_model=extended_negative_control,
        null_expect=113724,
        null_kind="negative",
        tolerance=0.0,
        sample=lambda: [float(extended_observed())],
        statistics={"value": lambda values: float(values[0])},
        reference_alt=extended_reference_alt,
        alt_tolerance=extended_alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={
            "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity); для одиночного утверждения перебор не воспроизводим",
            "С21": "алгебраическая объяснимость разбирается на семействе формул целиком (случай sacred_fit_multiplicity); здесь линейная форма в логарифмах не задана",**COMMON_SKIPS,
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes="Эталон использует включительные диапазоны из расширенной спецификации; альтернативный путь перечисляет декартово произведение.",
    ),
    Claim(
        name="Раздел Error Classification содержит 35 совпадений с ошибкой менее 0,01%",
        source="docs/docs/math-foundations/sacred-formulas.md:214",
        stated=35,
        reference=exact_reference,
        observed=exact_observed,
        wrong=[exact_wrong_plus_one, exact_wrong_zero],
        null_model=exact_negative_control,
        null_expect=2,
        null_kind="negative",
        tolerance=0.0,
        sample=exact_sample,
        statistics={"value": exact_sample_value},
        reference_alt=exact_reference_alt,
        alt_tolerance=exact_alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={**COMMON_SKIPS,
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
        notes="Эталон заново вычисляет каждую формулу из пятёрки параметров и сравнивает её с числом цели; проверка не доверяет напечатанной колонке Error.",
    ),
]
