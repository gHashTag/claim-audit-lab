# -*- coding: utf-8 -*-
"""Проверка разделения когерентности и производительности BitNet.

Отчёт содержит два разных типа свидетельств: примеры связного текста и
измерение скорости ядра I2_S. Цель не превращает напечатанное число скорости
в подтверждение полной производительности генерации: проверяется, раскрывает ли
сам отчёт различие между режимом benchmark ядра и полной генерацией.
"""
import os
import re
import sys

from goldsieve.sieve import Claim

ИСТОЧНИК = (
    "/home/user/workspace/corpus/trinity/docs/docs/research/"
    "bitnet-report.md"
)

if __name__ in sys.modules:
    raise RuntimeError(
        "кейс должен загружаться через module_from_spec без регистрации"
    )


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт BitNet отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    """Извлечь свидетельства разными шаблонами из всего документа."""
    текст = _текст()
    абстракт = bool(re.search(
        r"GPU testing .*?confirmed coherent text generation",
        текст,
        re.I | re.S,
    ))
    предупреждение = bool(re.search(
        r"missing pre-tokenizer type.*?GENERATION QUALITY WILL BE DEGRADED",
        текст,
        re.I | re.S,
    ))
    осторожность = bool(re.search(
        r"throughput numbers reflect CPU-only inference.*?"
        r"(?:not|rather than) end-to-end text generation speed",
        текст,
        re.I | re.S,
    ))
    примеры = len(re.findall(
        r"\|\s*\"[^\"]+\"\s*\|\s*\"[^\"]+\"\s*\|\s*Yes\s*\|",
        текст,
        re.I,
    ))
    return {
        "связная_генерация_на_втором_этапе": абстракт,
        "предупреждение_о_токенизаторе": предупреждение,
        "скорость_ядра_не_end_to_end": осторожность,
        "связные_примеры": float(примеры),
    }


def _разделы():
    """Вернуть блоки документа по заголовкам, не используя шаблоны наблюдения."""
    строки = _текст().splitlines()
    блоки = {}
    текущий = "начало"
    блоки[текущий] = []
    for строка in строки:
        заголовок = re.match(r"^#{2,3}\s+(.+?)\s*$", строка)
        if заголовок:
            текущий = заголовок.group(1).strip().lower()
            блоки.setdefault(текущий, [])
        блоки.setdefault(текущий, []).append(строка)
    return блоки


def эталон():
    """Вычислить структурный эталон по независимым разделам отчёта."""
    блоки = _разделы()
    абстракт = "\n".join(блоки.get("начало", []))
    этап = "\n".join(
        строка for имя, строки in блоки.items()
        if (
            "update: gpu results" in имя
            or "coherent generation" in имя
            or "gpu performance" in имя
        )
        for строка in строки
    )
    причина = "\n".join(
        строка for имя, строки in блоки.items()
        if (
            "root cause" in имя
            or "hypothesis 2" in имя
            or "test 3" in имя
        )
        for строка in строки
    )
    заключение = "\n".join(
        строка for имя, строки in блоки.items() if "conclusion" in имя
        for строка in строки
    )
    примеры = sum(
        1 for строка in этап.splitlines()
        if re.search(r"\|\s*Yes\s*\|", строка, re.I)
    )
    return {
        "связная_генерация_на_втором_этапе": (
            "confirmed coherent text generation" in абстракт.lower()
            and "coherent" in этап.lower()
        ),
        "предупреждение_о_токенизаторе": (
            "missing pre-tokenizer type" in причина.lower()
            and "generation quality will be degraded" in причина.lower()
        ),
        "скорость_ядра_не_end_to_end": (
            "cpu-only i2_s kernel" in этап.lower()
            and (
                "rather than end-to-end text generation speed" in этап.lower()
                or "not end-to-end text generation speed" in этап.lower()
                or "rather than end-to-end text generation speed" in заключение.lower()
                or "not end-to-end text generation speed" in заключение.lower()
            )
        ),
        "связные_примеры": float(примеры),
    }


def эталон_альт():
    """Альтернатива: конечный автомат по строкам таблицы и блока caution."""
    строки = _текст().splitlines()
    в_обновлении = False
    в_caution = False
    примеры = 0
    есть_связность = False
    есть_предупреждение = False
    есть_разделение = False
    for строка in строки:
        ниж = строка.lower()
        if ниж.startswith("## update: gpu results"):
            в_обновлении = True
        elif в_обновлении and ниж.startswith("## ") and not ниж.startswith(
            "## update:"
        ):
            в_обновлении = False
        if "<div class=\"abstract\">" in ниж:
            есть_связность = False
        if "confirmed coherent text generation" in ниж:
            есть_связность = True
        if "missing pre-tokenizer type" in ниж:
            есть_предупреждение = True
        if ":::caution" in ниж:
            в_caution = True
        elif (
            в_caution
            and "throughput" in ниж
            and ("kernel benchmark" in ниж or "rather than end-to-end" in ниж)
        ):
            есть_разделение = True
        elif в_caution and "not end-to-end" in ниж:
            есть_разделение = True
        if в_обновлении and re.search(r"\|\s*Yes\s*\|", строка, re.I):
            примеры += 1
    return {
        "связная_генерация_на_втором_этапе": есть_связность,
        "предупреждение_о_токенизаторе": есть_предупреждение,
        "скорость_ядра_не_end_to_end": есть_разделение,
        "связные_примеры": float(примеры),
    }


def _неверная_подстановка():
    результат = эталон()
    результат["скорость_ядра_не_end_to_end"] = False
    return результат


def _нулевая_модель():
    return {
        "связная_генерация_на_втором_этапе": True,
        "предупреждение_о_токенизаторе": False,
        "скорость_ядра_не_end_to_end": False,
        "связные_примеры": 0.0,
    }


def _самопроверка():
    наблюдаемое = наблюдение()
    assert наблюдаемое == {
        "связная_генерация_на_втором_этапе": True,
        "предупреждение_о_токенизаторе": True,
        "скорость_ядра_не_end_to_end": True,
        "связные_примеры": 3.0,
    }
    эт = эталон()
    алт = эталон_альт()
    assert эт == наблюдаемое
    assert алт == эт
    assert _неверная_подстановка() != наблюдаемое
    assert _нулевая_модель() != наблюдаемое


_самопроверка()

CLAIMS = [
    Claim(
        name=(
            "Отчёт BitNet отделяет связную генерацию от "
            "производительности теста ядра"
        ),
        source="docs/docs/research/bitnet-report.md:1-220",
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
        claim_family="аудит воспроизводимости benchmark инференса",
        observable=(
            "разделение примеров связного текста, предупреждения токенизатора "
            "и режима измерения скорости от полной генерации"
        ),
        measurement_source="корпус Trinity: отчёт BitNet b1.58 Coherence Report",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:bitnet:coherence_throughput_recipe:v1",
        information_class=(
            "новый риск смешения качества генерации с производительностью ядра"
        ),
        purpose="audit",
        models=("режим ЦП", "тест ядра I2_S", "генерация на этапе ГП"),
        independent_of={
            "source": "отдельный отчёт BitNet, не прежние Golden Chain и Level 11",
            "observable": "текстовое предупреждение и блок GPU Results",
        },
        tests_independent="unknown",
        reason_code_hint="metrics_incommensurable",
        notes=(
            "Наблюдение, эталон и альтернативный эталон получают одну "
            "структурную карту разными путями. Проверка не утверждает "
            "достоверность скорости или качества модели; она проверяет, "
            "что отчёт не выдаёт тест ядра за полную генерацию от начала до конца."
        ),
        skip_reasons={
            "С6": "рецепт обучения модели не является целью этого аудита",
            "С7": "сравниваются режимы измерения, а не статистические модели",
            "С8": "неопределённость качества генерации не задана отчётом",
            "С9": "независимая выборка текстов не раскрыта",
            "С10": "повтор генерации не является частью структурной проверки",
            "С11": "внешнее сравнение производительности не проверяется",
            "С12": "альтернативный путь остаётся в том же отчёте",
            "С13": "обязательные пропуски объявлены",
            "С15": "внешняя измеренная цель отсутствует",
            "С16": "перебора формул нет",
            "С17": "сжатие описания не проверяется",
            "С18": "перенос на другие платформы не заявляется",
            "С19": "это не подтверждение качества модели",
            "С20": "эффективное число попыток не определено",
            "С21": "алгебраическая форма отсутствует",
        },
    )
]
