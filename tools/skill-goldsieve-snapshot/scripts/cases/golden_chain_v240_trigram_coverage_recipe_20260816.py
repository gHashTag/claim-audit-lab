# -*- coding: utf-8 -*-
"""Аудит рецепта покрытия триграмм в отчёте Golden Chain v2.40.

Сравнение 311/161 и округлённого 1,9x не используется как самостоятельное
дешёвое подтверждение. Проверяется наличие полного воспроизводимого рецепта
и разделяется контроль интеграционных тестов.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-40-large-corpus-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")

def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт v2.40 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()

def наблюдение():
    m = re.search(r"\| Trigram Coverage \|\s*([0-9.]+)%\s*\|\s*Was\s*([0-9.]+)%", _текст())
    if not m:
        raise AssertionError("строка покрытия триграмм не найдена")
    return float(m.group(1))

def _контроль():
    m = re.search(r"All (\d+) integration tests pass", _текст(), re.I)
    if not m:
        m = re.search(r"\| Integration Tests \|\s*(\d+)/(\d+) pass", _текст(), re.I)
        if not m:
            raise AssertionError("контроль интеграционных тестов не найден")
        return float(m.group(1)) / float(m.group(2)) * 100.0
    return float(m.group(1))

def _инвентарь():
    t = _текст().lower()
    поля = {
        "сырой корпус": bool(re.search(r"raw corpus|исходн(?:ый|ого) корпус", t)),
        "точная реализация": bool(re.search(r"commit sha|git sha|точн(?:ая|ый) версия кода", t)),
        "границы train eval": bool(re.search(r"train/eval boundaries|границ(?:ы|а) train", t)),
        "токенизация": bool(re.search(r"tokeniz|токенизац", t)),
        "seed": bool(re.search(r"\bseed\b|random state", t)),
        "контрольная сумма": bool(re.search(r"sha256|checksum|контрольная сумма", t)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|независим(?:ый|ая) повтор", t)),
    }
    поля["полный эталон"] = all(поля.values())
    поля["отсутствует"] = [k for k, v in поля.items() if k not in {"полный эталон", "отсутствует"} and not v]
    return поля

def _код_причины():
    return "" if _инвентарь()["полный эталон"] else "metrics_incommensurable"

def _подстановка():
    return 12.0

def _самопроверка():
    assert наблюдение() == 3.4
    assert _контроль() == 27.0
    inv = _инвентарь()
    assert not inv["полный эталон"]
    assert _код_причины() == "metrics_incommensurable"
    assert _подстановка() != наблюдение()
    assert _контроль() != наблюдение()

_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт Golden Chain v2.40 воспроизводимо подтверждает рост покрытия триграмм",
        source="deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-40-large-corpus-report.md:1-120",
        claim_kind="statistical",
        stated=наблюдение(),
        reference=None,
        observed=наблюдение,
        wrong=_подстановка,
        null_model=_контроль,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость рецепта покрытия триграмм",
        observable="покрытие триграмм большого корпуса 3,4 процента против 1,8 процента",
        measurement_source="отчёт Golden Chain v2.40 Large Corpus",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v240:trigram_coverage_recipe:v1",
        information_class="новый observable покрытия и новый риск воспроизводимости статистики корпуса",
        purpose="audit",
        models=["заявленная статистика покрытия v2.40", "воспроизводимая статистика на сыром корпусе и точной реализации"],
        independent_of={"source": "отчёт v2.40 и независимый запуск на корпусе, коде и конфигурации"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes="Наблюдение покрытия извлечено отдельным шаблоном, контроль тестов — отдельным путём. Отношение напечатанных чисел и округление 1,9x не используются как эталон.",
        skip_reasons={
            "С1": "вычисляемый эталон покрытия отсутствует без сырого корпуса и точной реализации",
            "С2": "независимая оценка покрытия не задана полным рецептом",
            "С3": "наблюдение есть, но независимый запуск отсутствует",
            "С4": "подстановка не восполняет отсутствующие входы",
            "С5": "контроль интеграционных тестов является отдельной строкой",
            "С6": "варианты реализации и среды не раскрыты",
            "С7": "не заданы точные границы и правило подсчёта покрытия",
            "С8": "неопределённость оценки покрытия не задана",
            "С9": "сырой корпус и таблица триграмм отсутствуют",
            "С10": "ошибки по отдельным ключам отсутствуют",
            "С11": "несколько независимых оценок не представлены",
            "С12": "второй вычислимый эталон невозможен без входов и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул к покрытию не относится",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "сводные строки не доказывают воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
