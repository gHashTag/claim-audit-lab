# -*- coding: utf-8 -*-
"""Аудит рецепта benchmark VSA SIMD.

Кейс проверяет не скорость как таковую, а раскрытие границ измерения:
строка dot product относится к одной операции ядра, тогда как отчёт делает
более широкие выводы о производительности архитектуры. Наблюдение, эталон и
альтернативный эталон получают структурную карту разными маршрутами. Отсутствие
сырого входа, commit, повторов и контрольной суммы не превращается в дешёвое
подтверждение скорости.
"""
import csv
import os
import re
import sys

from goldsieve.sieve import Claim

ИСТОЧНИК = (
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/benchmarks/"
    "BENCHMARK_REPORT.md"
)

# Реальный CLI обязан загружать кейс без регистрации в sys.modules.
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт VSA SIMD отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _строка_dot_product(текст):
    совпадение = re.search(
        r"\|\s*\*\*Dot Product\*\*\s*\|\s*([0-9]+)\s*\|"
        r"\s*([0-9,]+(?:\.[0-9]+)?)\s*\|\s*([0-9,]+)\s*\|"
        r"\s*\*\*~?([0-9,]+)x\*\*\s*\|",
        текст,
    )
    if not совпадение:
        raise AssertionError("строка Dot Product не найдена")
    задержка, пропускная, операции, ускорение = совпадение.groups()
    return {
        "задержка_нс": float(задержка.replace(",", "")),
        "пропускная_способность": float(пропускная.replace(",", "")),
        "операций_в_секунду": float(операции.replace(",", "")),
        "ускорение": float(ускорение.replace(",", "")),
    }


def наблюдение():
    """Извлечь карту заявленного протокола по полям и строке таблицы."""
    текст = _текст()
    строка = _строка_dot_product(текст)
    среда = текст.split("## VSA SIMD Results", 1)[0]
    return {
        "размерность_256": bool(re.search(r"Vector Dimension\**:\s*256", среда)),
        "замер_времени_операции": bool(re.search(
            r"Measurement\**:\s*Execution time per operation", среда)),
        "dot_задержка_нс": строка["задержка_нс"],
        "dot_пропускная_способность": строка["пропускная_способность"],
        "dot_операций_в_секунду": строка["операций_в_секунду"],
        "dot_ускорение": строка["ускорение"],
        "аппаратная_среда_выведена": bool(re.search(
            r"Hardware\**:\s*Apple Silicon \(inferred from `mac` OS\)", среда)),
        "commit_не_указан": not bool(re.search(r"\bCommit\s*:", текст)),
        "сырые_входы_не_указаны": not bool(re.search(
            r"raw vectors|input vectors|исходные векторы", текст, re.I)),
        "повторы_не_указаны": not bool(re.search(
            r"repeated runs|repetitions|number of runs|повтор(?:ы|ов)", текст, re.I)),
        "контрольная_сумма_не_указана": not bool(re.search(
            r"sha256|checksum|контрольная сумма", текст, re.I)),
    }


def _разделы():
    """Разделить отчёт на блоки для независимого маршрута эталона."""
    блоки = {"начало": []}
    текущий = "начало"
    for строка in _текст().splitlines():
        заголовок = re.match(r"^#{2,3}\s+(.+?)\s*$", строка)
        if заголовок:
            текущий = заголовок.group(1).strip().lower()
            блоки.setdefault(текущий, [])
        блоки.setdefault(текущий, []).append(строка)
    return блоки


def эталон():
    """Вычислить структурную карту из раздельных блоков отчёта."""
    блоки = _разделы()
    среда = "\n".join(блоки.get("test environment", []))
    результаты = "\n".join(блоки.get("vsa simd results (256d vectors)", []))
    таблица = _строка_dot_product(результаты)
    полный = _текст()
    return {
        "размерность_256": bool(re.search(r"Vector Dimension\**:\s*256", среда)),
        "замер_времени_операции": bool(re.search(
            r"Measurement\**:\s*Execution time per operation", среда)),
        "dot_задержка_нс": таблица["задержка_нс"],
        "dot_пропускная_способность": таблица["пропускная_способность"],
        "dot_операций_в_секунду": таблица["операций_в_секунду"],
        "dot_ускорение": таблица["ускорение"],
        "аппаратная_среда_выведена": bool(re.search(
            r"Hardware\**:\s*Apple Silicon \(inferred from `mac` OS\)", среда)),
        "commit_не_указан": not bool(re.search(r"\bCommit\s*:", полный)),
        "сырые_входы_не_указаны": not bool(re.search(
            r"raw vectors|input vectors|исходные векторы", полный, re.I)),
        "повторы_не_указаны": not bool(re.search(
            r"repeated runs|repetitions|number of runs|повтор(?:ы|ов)", полный, re.I)),
        "контрольная_сумма_не_указана": not bool(re.search(
            r"sha256|checksum|контрольная сумма", полный, re.I)),
    }


def эталон_альт():
    """Извлечь ту же карту CSV-разбором таблицы и инвентарём среды."""
    найдено = None
    в_таблице = False
    строки = _текст().splitlines()
    for строка in строки:
        if строка.strip() == "| Operation | Latency (ns/op) | Throughput (M trits/sec) | Ops/Sec (approx) | Speedup vs Baseline (est) |":
            в_таблице = True
            continue
        if в_таблице and строка.startswith("|"):
            ячейки = [поле.strip() for поле in next(csv.reader([строка], delimiter="|"))]
            if len(ячейки) >= 5 and "Dot Product" in ячейки[1]:
                числа = re.findall(r"[0-9][0-9,]*(?:\.[0-9]+)?", строка)
                if len(числа) >= 4:
                    найдено = {
                        "задержка_нс": float(числа[0].replace(",", "")),
                        "пропускная_способность": float(числа[1].replace(",", "")),
                        "операций_в_секунду": float(числа[2].replace(",", "")),
                        "ускорение": float(числа[3].replace(",", "")),
                    }
                    break
    if найдено is None:
        raise AssertionError("CSV-разбор не нашёл строку Dot Product")
    текст = _текст()
    среда = текст.split("## VSA SIMD Results", 1)[0]
    return {
        "размерность_256": bool(re.search(r"Vector Dimension\**:\s*256", среда)),
        "замер_времени_операции": bool(re.search(
            r"Measurement\**:\s*Execution time per operation", среда)),
        "dot_задержка_нс": найдено["задержка_нс"],
        "dot_пропускная_способность": найдено["пропускная_способность"],
        "dot_операций_в_секунду": найдено["операций_в_секунду"],
        "dot_ускорение": найдено["ускорение"],
        "аппаратная_среда_выведена": "Apple Silicon" in среда and "inferred" in среда,
        "commit_не_указан": not bool(re.search(r"\bCommit\s*:", текст)),
        "сырые_входы_не_указаны": not bool(re.search(r"raw vectors|input vectors|исходные векторы", текст, re.I)),
        "повторы_не_указаны": not bool(re.search(r"repeated runs|repetitions|number of runs|повтор(?:ы|ов)", текст, re.I)),
        "контрольная_сумма_не_указана": not bool(re.search(r"sha256|checksum|контрольная сумма", текст, re.I)),
    }


def _неверная_подстановка():
    карта = эталон()
    карта["dot_задержка_нс"] = 60.0
    return карта


def _нулевая_модель():
    карта = эталон()
    карта["аппаратная_среда_выведена"] = False
    карта["сырые_входы_не_указаны"] = False
    return карта


def _самопроверка():
    наблюдаемое = наблюдение()
    assert наблюдаемое["размерность_256"] is True
    assert наблюдаемое["dot_задержка_нс"] == 6.0
    assert наблюдаемое["dot_пропускная_способность"] == 40000.0
    assert наблюдаемое["dot_операций_в_секунду"] == 166666666.0
    assert наблюдаемое["dot_ускорение"] == 16000.0
    эт = эталон()
    алт = эталон_альт()
    assert эт == наблюдаемое
    assert алт == эт
    assert _неверная_подстановка() != наблюдаемое
    assert _нулевая_модель() != наблюдаемое


_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт VSA SIMD отделяет замер dot product от полноценной воспроизводимости производительности",
        source="deploy/trinity-nexus/benchmarks/BENCHMARK_REPORT.md:1-63",
        claim_kind="statistical",
        stated=наблюдение(),
        reference=эталон,
        observed=наблюдение,
        wrong=_неверная_подстановка,
        null_model=_нулевая_модель,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        reference_alt=эталон_альт,
        alt_tolerance=lambda: 0.0,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость VSA SIMD benchmark",
        observable="разделение параметров dot product, среды замера и отсутствующих частей рецепта",
        measurement_source="корпус Trinity: VSA SIMD Benchmark Report",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:vsa_simd:benchmark_recipe:v1",
        information_class="новый источник и новый риск смешения замера ядра с полной производительностью",
        purpose="audit",
        models=["заявленный замер VSA SIMD", "воспроизводимый benchmark на исходных векторах и реализации"],
        independent_of={
            "source": "отдельный отчёт VSA SIMD, не прежние Golden Chain и Level 11",
            "observable": "таблица dot product и паспорт среды замера",
        },
        tests_independent="unknown",
        reason_code_hint="metrics_incommensurable",
        notes=(
            "Кейс машинно проверяет структуру опубликованного протокола и явно "
            "фиксирует отсутствие сырых векторов, commit, повторов и контрольной "
            "суммы. Числа 6 нс/операцию и 40 миллиардов trits/секунду не "
            "используются как достаточное доказательство производительности."
        ),
        skip_reasons={
            "С6": "серия размерностей и границы изменения параметров не заданы полным рецептом",
            "С7": "варианты оценки пропускной способности не раскрыты",
            "С8": "неопределённость времени и разброс запусков не заданы",
            "С9": "сырой входной набор не приложен",
            "С10": "повторные запуски и их разброс не указаны",
            "С11": "несколько независимых статистик benchmark не представлены",
            "С12": "альтернативный разбор остаётся внутри одного отчёта",
            "С13": "пропуски по ситам объявлены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул к benchmark не относится",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "согласие строк таблицы не доказывает воспроизводимость",
            "С20": "эффективное число независимых измерений не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
