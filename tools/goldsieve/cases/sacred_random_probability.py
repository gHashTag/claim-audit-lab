"""Заявленные вероятности случайного попадания в класс EXACT.

Корпус в разделе Statistical Significance даёт ДВЕ вероятности в одной строке
таблицы: «1 из 500 (0,2 %)» для стандартного перебора и «1 из 35 (2,9 %)» для
расширенного, и выводит из них значимость «около 10 сигм».

ИСПРАВЛЕНИЕ ПОСТАНОВКИ (луп 7). Прежняя версия этого файла сравнивала эталон,
посчитанный для РАСШИРЕННОГО перебора (123 201 член), с заявленным числом
0,2 %, которое относится к СТАНДАРТНОМУ перебору. Отсюда взялся множитель
«в 500 раз», который цитировался в отчётах лупа 5 и 6. Вывод о занижении
сохраняется по обеим колонкам, но множитель был получен на неоднородной паре и
недействителен. Теперь каждая колонка проверяется против эталона СВОЕГО
перебора, а размер перебора берётся из объявленных в корпусе границ.

Третье утверждение проверяет согласованность самого корпуса: объявленный размер
стандартного перебора (20 412) против числа комбинаций, которое дают
объявленные там же границы стандартного перебора.

Вычисляемый эталон. Для каждой цели вероятность того, что хотя бы один член
семейства попадёт в относительную полосу +-1e-4, равна отношению ширины полосы
к локальному порогу разрешающей способности вблизи этой цели, то есть
1e-4 / eps_local, ограниченному единицей. Средняя по фактическим целям корпуса
вероятность и есть эталон. Цитаты не используются: плотность считается
перечислением семейства.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve import family                                    # noqa: E402
from goldsieve.sieve import Claim                               # noqa: E402
from goldsieve.threshold import local_threshold, ACTUAL_RANGES  # noqa: E402

SOURCE = ("/home/user/workspace/corpus/trinity/docs/docs/"
          "math-foundations/sacred-formulas.md")

EXACT_TOLERANCE = 1e-4      # класс EXACT: ошибка меньше 0,01 %

# Границы стандартного перебора, как они объявлены в корпусе: тот же набор, что
# и расширенный, но степень пи ограничена отрицательными значениями,
# m in [-3, 0]. Остальные границы берутся из ACTUAL_RANGES.
STANDARD_RANGES = dict(ACTUAL_RANGES, m=range(-3, 1))

STATED_STANDARD = 0.002     # «1 из 500» — колонка Standard Search
STATED_EXTENDED = 0.029     # «1 из 35»  — колонка Extended Search
STATED_STANDARD_SIZE = 20412    # объявленный размер стандартного перебора

_cache = {}


def _targets():
    """Цели из таблиц корпуса: те строки, где указана относительная ошибка."""
    if "t" in _cache:
        return _cache["t"]
    out = []
    for ln in open(SOURCE).read().split("\n"):
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if not re.search(r"\*{0,2}([\d.]+)\s*%\*{0,2}$", cells[-1]):
            continue
        raw = cells[1].replace(",", "").replace("$", "").strip()
        try:
            v = float(raw)
        except ValueError:
            continue
        if v != 0.0:
            out.append(abs(v))
    _cache["t"] = out
    return out


def _values(ranges, key):
    if key not in _cache:
        _cache[key] = family.enumerate_family(ranges)
    return _cache[key]


def _probability(ranges, key):
    """Средняя вероятность случайного попадания в класс EXACT при переборе."""
    vals = _values(ranges, key)
    ps = [min(1.0, EXACT_TOLERANCE / local_threshold(t, ranges, vals))
          for t in _targets()]
    return sum(ps) / len(ps)


def _density(ranges, key):
    """Фактическая плотность семейства вокруг целей: членов на декаду."""
    vals = _values(ranges, key)
    ds = [math.log(10.0) / (2.0 * local_threshold(t, ranges, vals))
          for t in _targets()]
    return sum(ds) / len(ds)


def _null_by_density(ranges, key):
    """Позитивный контроль: тот же эталон, посчитанный другим путём.

    Первый путь — локальный порог у каждой цели. Второй — средняя фактическая
    плотность членов на декаду, из неё порог, из порога вероятность. Оба обязаны
    дать эталон; расхождение означает поломку конвейера, а не утверждения.

    Контроль не имеет права воспроизводить ЗАЯВЛЕННОЕ значение: на этом я
    ошибался дважды в лупе 5. Он воспроизводит ЭТАЛОН.
    """
    thr = math.log(10.0) / (2.0 * _density(ranges, key))
    return min(1.0, EXACT_TOLERANCE / thr)


def reference_standard():
    return _probability(STANDARD_RANGES, "v_std")


def reference_extended():
    return _probability(ACTUAL_RANGES, "v_ext")


def observed_standard():
    return STATED_STANDARD


def observed_extended():
    return STATED_EXTENDED


def null_standard():
    return _null_by_density(STANDARD_RANGES, "v_std")


def null_extended():
    return _null_by_density(ACTUAL_RANGES, "v_ext")


def reference_standard_size():
    """Число комбинаций, которое дают объявленные границы стандартного перебора."""
    n = 1
    for rng in STANDARD_RANGES.values():
        n *= len(rng)
    return float(n)


def observed_standard_size():
    return float(STATED_STANDARD_SIZE)


def null_standard_size():
    """Позитивный контроль размера: то же число, но перечислением, а не произведением."""
    return float(len(_values(STANDARD_RANGES, "v_std")))


# Заведомо неверные ответы. Вероятность лежит в [0, 1], поэтому подставки
# берутся внутри отрезка и в точках, где они реально отличаются от эталона.

def wrong_stated_standard():
    return STATED_STANDARD


def wrong_stated_extended():
    return STATED_EXTENDED


def wrong_five_percent():
    return 0.05


def wrong_half():
    return 0.5


def wrong_size_stated():
    return float(STATED_STANDARD_SIZE)


def wrong_size_extended():
    return 123201.0


COMMON = {
        "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity)",
        "С21": "линейная форма в логарифмах для этого утверждения не задана; алгебраическая объяснимость разбирается на семействе",

    "С6": "перечисление семейства конечно и точно; сходимости по сетке нет",
    "С7": "оценивателей несколько не бывает: вероятность одна",
    "С8": "погрешность входа не задана: цели берутся как напечатаны",
    "С9": "величина не является выборочной оценкой, зависящей от размера данных",
    "С10": ("выборки за заявленным числом нет: это одно значение из текста. "
            "Разброс расчётных вероятностей по целям сюда НЕ подаётся: тогда "
            "С10 сравнивал бы эталон сам с собой"),
    "С11": "одна статистика, множественный тест слишком хорошего согласия не нужен",
    "С12": "второй независимый путь подан позитивным контролем через плотность",
    "С15": "утверждение о вероятности внутри работы, внешнего измерения нет",
    "С16": "проверяется сама поправка на множественность, а не результат под неё",
    "С17": "длина описания неприменима: это не закон, а вероятность",
    "С18": "границы перебора проверены отдельным утверждением этого же файла",
    "С19": "вероятность считается по перечислению, ошибка double несопоставимо мала",
}

SIZE_SKIPS = dict(COMMON, **{
    "С7": "число комбинаций одно, оценивателей не бывает",
    "С12": "второй путь подан позитивным контролем: перечисление против произведения",
    "С17": "длина описания неприменима: это размер перебора",
    "С18": "это и есть проверка объявленных границ",
    "С19": "целочисленный подсчёт, ошибки округления отсутствуют",
})

CLAIMS = [
    Claim(
        name=("Вероятность случайного попадания в класс EXACT при стандартном "
              "переборе равна 1 из 500 (0,2 %)"),
        stated=STATED_STANDARD,
        reference=reference_standard,
        observed=observed_standard,
        wrong=[wrong_stated_standard, wrong_five_percent, wrong_half],
        null_model=null_standard,
        null_kind="positive",
        tolerance=0.2,
        inputs=[SOURCE],
        skip_reasons=COMMON,
        notes=("Эталон считается для границ СТАНДАРТНОГО перебора (степень пи "
               "ограничена m in [-3, 0], как объявлено в корпусе), а не для "
               "расширенного. Прежняя версия проверки сравнивала заявленные "
               "0,2 % с эталоном расширенного перебора; множитель «в 500 раз» "
               "из отчётов лупов 5 и 6 получен на неоднородной паре и "
               "недействителен."),
    ),
    Claim(
        name=("Вероятность случайного попадания в класс EXACT при расширенном "
              "переборе равна 1 из 35 (2,9 %)"),
        stated=STATED_EXTENDED,
        reference=reference_extended,
        observed=observed_extended,
        wrong=[wrong_stated_extended, wrong_five_percent, wrong_half],
        null_model=null_extended,
        null_kind="positive",
        tolerance=0.2,
        inputs=[SOURCE],
        skip_reasons=COMMON,
        notes=("Однородная пара: заявленное значение и эталон относятся к одному "
               "и тому же перебору 123 201."),
    ),
    Claim(
        name=("Объявленный размер стандартного перебора 20 412 согласуется с "
              "объявленными границами стандартного перебора"),
        stated=float(STATED_STANDARD_SIZE),
        reference=reference_standard_size,
        observed=observed_standard_size,
        wrong=[wrong_size_stated, wrong_size_extended],
        null_model=null_standard_size,
        null_kind="positive",
        tolerance=0.0,
        inputs=[SOURCE],
        skip_reasons=SIZE_SKIPS,
        notes=("Границы стандартного перебора объявлены в корпусе как тот же "
               "набор, что и расширенный, но со степенью пи m in [-3, 0]. "
               "Произведение длин диапазонов сравнивается с объявленным числом."),
    ),
]
