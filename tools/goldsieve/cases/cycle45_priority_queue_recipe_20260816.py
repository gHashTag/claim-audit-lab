# -*- coding: utf-8 -*-
"""Проверка воспроизводимости benchmark очереди приоритетных задач Cycle 45.

Кейс не считает отношение напечатанных чисел доказательством. Он проверяет,
раскрывает ли отчёт полный рецепт запуска, входные задания, среду и
независимый повтор.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/cycle45-priority-queue-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Cycle 45 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    совпадение = re.search(r"\| Improvement Rate \| ([0-9.]+) \|", _текст())
    if not совпадение:
        raise AssertionError("коэффициент улучшения не найден")
    значение = float(совпадение.group(1))
    if значение != 0.667:
        raise AssertionError("коэффициент улучшения изменился")
    return значение


def _контроль():
    совпадение = re.search(r"Critical first:\s+100/100 \(([0-9.]+)%\)", _текст())
    if not совпадение:
        raise AssertionError("контроль порядка выполнения не найден")
    return float(совпадение.group(1))


def _инвентарь_рецепта():
    текст = _текст().lower()
    поля = {
        "описание алгоритма": bool(re.search(r"scheduling algorithm|pop from highest priority", текст)),
        "параметры нагрузки": bool(re.search(r"jobs pushed|jobs popped|400", текст)),
        "сырые задания": bool(re.search(r"job list|input jobs|raw jobs|исходн(?:ые|ый) задания", текст)),
        "точная реализация": bool(re.search(r"commit sha|git commit|git sha|точн(?:ая|ый) версия кода", текст)),
        "среда выполнения": bool(re.search(r"python|zig version|compiler version|операционная система", текст)),
        "контрольная сумма входа": bool(re.search(r"sha256|checksum|input hash|контрольная сумма", текст)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|independent reproduction|независим(?:ый|ая) повтор", текст)),
        "seed": bool(re.search(r"\bseed\b|random state", текст)),
    }
    поля["рецепт_полон"] = all(поля.values())
    поля["отсутствует"] = [имя for имя, есть in поля.items()
                           if имя not in {"рецепт_полон", "отсутствует"} and not есть]
    return поля


def _код_причины():
    return "" if _инвентарь_рецепта()["рецепт_полон"] else "metrics_incommensurable"


def _неверный_ответ():
    return 0.5


def _самопроверка():
    assert наблюдение() == 0.667
    assert _контроль() == 100.0
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert set(инвентарь["отсутствует"]) == {
        "сырые задания", "точная реализация", "среда выполнения",
        "контрольная сумма входа", "независимый повтор", "seed",
    }
    assert _код_причины() == "metrics_incommensurable"
    assert _неверный_ответ() != наблюдение()
    assert _контроль() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт Cycle 45 воспроизводимо подтверждает улучшение очереди приоритетных задач",
        source="deploy/trinity-nexus/docs/research/cycle45-priority-queue-report.md:1-180",
        claim_kind="statistical",
        stated=наблюдение(),
        reference=None,
        observed=наблюдение,
        wrong=_неверный_ответ,
        null_model=_контроль,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость benchmark-метрики очереди приоритетов",
        observable="коэффициент улучшения benchmark и порядок выполнения очереди",
        measurement_source="отчёт Cycle 45 Priority Queue Integration Report",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:cycle45:priority_queue_recipe:v1",
        information_class="новый источник и новый риск воспроизводимости benchmark-рецепта планировщика",
        purpose="audit",
        models=["заявленный benchmark очереди", "воспроизводимый benchmark очереди"],
        independent_of={"source": "отдельный отчёт Cycle 45 и независимый запуск очереди"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Отчёт раскрывает четыре уровня приоритета, сводные счётчики и "
            "описание алгоритма, но не даёт списка исходных заданий, точной "
            "версии реализации, среды, checksum, seed и независимого повтора. "
            "Числа improvement rate и critical-first извлечены из разных строк "
            "отчёта; простое сравнение с phi^-1 не используется как подтверждение."
        ),
        skip_reasons={
            "С1": "вычислимый benchmark-эталон отсутствует без исходных заданий, кода и среды",
            "С2": "независимая оценка коэффициента улучшения не задана полным рецептом",
            "С3": "наблюдение есть, но независимый запуск очереди не предоставлен",
            "С4": "подставка не восполняет отсутствующие входы benchmark",
            "С5": "контроль порядка выполнения является отдельной метрикой, а не эталоном коэффициента",
            "С6": "варианты планировщика и повторные нагрузки не раскрыты",
            "С7": "не заданы точные границы и последовательность входных заданий",
            "С8": "неопределённость времени и коэффициента не задана",
            "С9": "сырой список заданий отсутствует",
            "С10": "ошибки по отдельным заданиям отсутствуют",
            "С11": "несколько независимых оценок не представлены",
            "С12": "второй вычислимый эталон невозможен без входов и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул не относится к benchmark очереди",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "согласие сводных строк не доказывает независимую воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
