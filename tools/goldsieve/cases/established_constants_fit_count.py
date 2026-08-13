"""Аудит числа совпадений в разделе Established Constants.

Проверяется одно численное утверждение из корпуса Trinity. Эталон вычисляется
из строк таблиц, наблюдение извлекается из заголовка раздела, а второй эталон
получается независимым подсчётом чисел в заголовках подразделов.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve.sieve import Claim  # noqa: E402


SOURCE = "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/sacred-formulas.md"


def _lines():
    with open(SOURCE, encoding="utf-8") as handle:
        return handle.readlines()


def _established_region():
    lines = _lines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## Established Constants"))
    end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
               if line.startswith("## Predictions"))
    return lines[start:end]


def _table_row_count(lines):
    """Число строк данных таблиц: заголовки и разделители исключены."""
    count = 0
    for line in lines:
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5 or cells[0] == "Name" or set(cells[0]) <= {"-"}:
            continue
        # Единица измерения (например, знак градуса) может следовать за числом.
        if re.match(r"^[-+]?\d+(?:\.\d+)?(?:\D|$)", cells[1]):
            count += 1
    return count


def reference():
    """Вычисляемый эталон: число строк данных в разделе до Predictions."""
    return float(_table_row_count(_established_region()))


def reference_alt():
    """Второй метод: сумма чисел в заголовках подразделов раздела."""
    total = 0
    for line in _established_region():
        match = re.match(r"^### .+ \((\d+)\)\s*$", line)
        if match:
            total += int(match.group(1))
    return float(total)


def observed_from_corpus():
    """Извлекает заявленное число из заголовка, не пересчитывая его."""
    for line in _lines():
        match = re.match(r"^## Established Constants \((\d+) fits\)", line)
        if match:
            return float(match.group(1))
    raise ValueError("заголовок Established Constants не найден")


def wrong_plus_one():
    """Подставка: число на единицу выше вычисляемого эталона."""
    return reference() + 1.0


def wrong_minus_one():
    """Подставка: число на единицу ниже вычисляемого эталона."""
    return reference() - 1.0


def wrong_stated_value():
    """Подставка: исходное число из заголовка, заведомо отличное от эталона."""
    return observed_from_corpus()


def negative_control():
    """Негативный контроль: число строк таблицы в следующем разделе Predictions."""
    lines = _lines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## Predictions"))
    end = next((i for i, line in enumerate(lines[start + 1:], start + 1)
                if line.startswith("## Error Classification")), len(lines))
    count = 0
    for line in lines[start:end]:
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] not in {"Name", "---"} and not set(cells[0]) <= {"-"}:
            if cells[0] != "Name":
                count += 1
    return float(count)


def deterministic_sample():
    """Сырая наблюдаемая величина из заголовка корпуса."""
    return [observed_from_corpus()]


def sample_sum(values):
    return float(sum(values))


def alt_tolerance():
    """Второй метод детерминирован; измеренный разброс повторов равен нулю."""
    return 0.0


CLAIMS = [
    Claim(
        name="Раздел Established Constants содержит 75 совпадений",
        source="docs/docs/math-foundations/sacred-formulas.md:30",
        stated=75.0,
        reference=reference,
        observed=observed_from_corpus,
        wrong=[wrong_plus_one, wrong_minus_one, wrong_stated_value],
        null_model=negative_control,
        null_expect=20.0,
        null_kind="negative",
        tolerance=0.0,
        sample=deterministic_sample,
        statistics={"value": sample_sum},
        reference_alt=reference_alt,
        alt_tolerance=alt_tolerance,
        inputs=[SOURCE],
        skip_reasons={
            "С15": "утверждение о числе в документе, внешней величины нет",
            "С16": "перебора формул в этом утверждении нет",
            "С17": "длина описания неприменима: это не закон, а запись числа",
            "С18": "объявленных границ перебора это утверждение не касается",
            "С6": "эталон — подсчёт строк; численной сетки или разрешения нет",
            "С7": "проверяется точный счёт, а не оценка с несколькими оценивателями",
            "С8": "целочисленный счёт строк; погрешность входа не задана",
            "С9": "утверждение не является выборочным измерением, зависящим от размера выборки",
            "С11": "доступна одна статистика; тест слишком хорошего согласия неприменим",
        },
        notes=(
            "Сито сравнивает число в заголовке с машинным подсчётом строк данных "
            "в таблицах и с независимой суммой чисел в заголовках подразделов."
        ),
    ),
]
