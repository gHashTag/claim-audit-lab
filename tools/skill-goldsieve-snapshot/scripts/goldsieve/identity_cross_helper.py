"""Вспомогательный модуль для межмодульной калибровки тождественности.

`reference` — вычисляемый эталон. `relay` намеренно прозрачно вызывает его и
нужен как положительная подставка детектора. `read_catalog` читает корпус своим
путём и нужен как честный межмодульный контроль.
"""

import re


SOURCE = (
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/"
    "MASTER_SACRED_CATALOG.md"
)


def reference():
    """Эталон из определения числа Лукаса L(10)."""
    return 3 * 41


def relay():
    """Прозрачное межмодульное звено: положительная подставка детектора."""
    return reference()


def read_catalog():
    """Независимое наблюдение: прочитать число из строки корпуса."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "| 10 |" in line:
                match = re.search(r"\|\s*10\s*\|\s*(\d+)\s*\|", line)
                if match:
                    return int(match.group(1))
    raise ValueError("строка каталога не найдена")
