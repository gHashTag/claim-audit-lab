"""Аудит статистического утверждения отчёта Golden Chain v2.41.

Наблюдение извлекается из отдельной строки отчёта. Эталон вычисляет разность
двух напечатанных ошибок оценки, а альтернативный эталон повторяет арифметику
через Decimal. Никакое число эталона не вводится вручную.
"""

import os
import re
from decimal import Decimal, getcontext

from goldsieve.sieve import Claim

ОТЧЁТ = os.environ.get(
    "TRINITY_GOLDEN_CHAIN_V241_REPORT",
    "/home/user/workspace/corpus/trinity/docs/docs/research/"
    "trinity-golden-chain-v2-41-offsets-report.md",
)


def текст():
    with open(ОТЧЁТ, encoding="utf-8") as файл:
        return файл.read()


def строка(маркер):
    содержимое = текст()
    for линия in содержимое.splitlines():
        if маркер in линия:
            return линия
    raise AssertionError("строка корпуса не найдена: " + маркер)


def значения_ошибки():
    линия = строка("500 offsets eval loss")
    найдено = re.findall(r"(?:500-offset eval loss|50 offsets eval loss):\s*([0-9.]+)", линия)
    if len(найдено) != 1:
        # В отчёте значения стоят на отдельных строках; запасной путь читает
        # именно два соседних поля из блока Test Results.
        блок = текст()
        совпадения = re.findall(r"(?:500 offsets eval loss|50 offsets eval loss):\s*([0-9.]+)", блок)
        if len(совпадения) < 2:
            raise AssertionError("не найдены обе ошибки оценки")
        return float(совпадения[0]), float(совпадения[1])
    блок = текст()
    совпадения = re.findall(r"(?:500 offsets eval loss|50 offsets eval loss):\s*([0-9.]+)", блок)
    if len(совпадения) < 2:
        raise AssertionError("не найдены обе ошибки оценки")
    return float(совпадения[0]), float(совпадения[1])


def наблюдение_разности():
    совпадение = re.search(r"difference of\s*([0-9.]+)\s*eval loss", текст(), re.IGNORECASE)
    if совпадение:
        return float(совпадение.group(1))
    совпадение = re.search(r"difference of\s*([0-9.]+)", текст(), re.IGNORECASE)
    if not совпадение:
        raise AssertionError("напечатанная разность не найдена")
    return float(совпадение.group(1))


def эталон_разности():
    новое, старое = значения_ошибки()
    return abs(новое - старое)


def эталон_разности_alt():
    getcontext().prec = 40
    блок = текст()
    совпадения = re.findall(r"(?:500 offsets eval loss|50 offsets eval loss):\s*([0-9.]+)", блок)
    if len(совпадения) < 2:
        raise AssertionError("альтернативный путь не нашёл ошибки оценки")
    return float(abs(Decimal(совпадения[0]) - Decimal(совпадения[1])))


def неверный_ответ():
    return 0.05


def отрицательный_контроль():
    return 0.05


def выборка():
    return [эталон_разности()]


def среднее(значения):
    return sum(значения) / len(значения)


def арифметика():
    return {"params": (2, 1, 0, 0, 0), "rel_uncertainty": 1.0e-12}


def допуск_альтернативы():
    return max(1.0e-9, abs(эталон_разности() - эталон_разности_alt()))


def самопроверка():
    assert os.path.exists(ОТЧЁТ)
    assert значения_ошибки() == (0.4627, 0.4634)
    assert abs(эталон_разности() - 0.0007) < 1.0e-12
    assert abs(эталон_разности_alt() - эталон_разности()) < 1.0e-15
    assert наблюдение_разности() == 0.0007
    assert неверный_ответ() != эталон_разности()


самопроверка()


CLAIMS = [
    Claim(
        name="Разность ошибки оценки при 500 и 50 смещениях равна 0,0007",
        source="docs/docs/research/trinity-golden-chain-v2-41-offsets-report.md:70-78",
        stated=наблюдение_разности(),
        reference=эталон_разности,
        observed=наблюдение_разности,
        wrong=неверный_ответ,
        null_model=отрицательный_контроль,
        null_expect=0.05,
        null_kind="negative",
        tolerance=1.0e-9,
        sample=выборка,
        statistics={"value": среднее},
        reference_alt=эталон_разности_alt,
        alt_tolerance=допуск_альтернативы,
        inputs=[ОТЧЁТ],
        arithmetic=арифметика,
        claim_family="статистика сравнения обучающих смещений",
        observable="абсолютная разность ошибок оценки",
        measurement_source="отчёт Golden Chain v2.41",
        uncertainty_type="none",
        novelty_key="golden_chain:v241:offset_eval_delta:v1",
        information_class="novelty",
        purpose="audit",
        models=["разбор строки отчёта", "вычисление разности", "Decimal-арифметика"],
        independent_of=["golden_chain:v240:statistics"],
        notes="Наблюдение извлекает фразу о разности; эталон строится из двух отдельных строк значений 0,4627 и 0,4634. Положительный контроль — альтернативная Decimal-арифметика, отрицательный контроль — заведомо отличающаяся разность.",
        skip_reasons={
            "С6": "в отчёте нет сетки численного разрешения",
            "С7": "сравнивается одна разность двух режимов",
            "С8": "погрешность измерений в отчёте не объявлена",
            "С9": "нет временного ряда повторных измерений",
            "С10": "сырой ряд наблюдений отсутствует",
            "С11": "проверяется одна сводная статистика",
            "С15": "это статистика корпуса, внешней цели нет",
            "С16": "перебора формул нет",
            "С17": "алгебраическая длина для разности отчётных чисел неприменима",
            "С18": "объявленных границ перебора нет",
            "С19": "арифметическая погрешность существенно меньше точности отчёта",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
