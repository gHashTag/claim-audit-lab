# -*- coding: utf-8 -*-
"""Аудит воспроизводимости benchmark точности ANN Brute+SIMD.

Кейс не превращает строку 100 процентов в подтверждение. Наблюдение,
отрицательный контроль и контроль тестового маршрута извлекаются разными
шаблонами; затем проверяется полнота рецепта независимого воспроизведения.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/docs/docs/research/trinity-ann-benchmark-verdict-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("ANN-отчёт отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    совпадение = re.search(
        r"\| \*\*Brute\+SIMD\*\*\s*\|\s*\*\*0ms\*\*\s*\|.*?\|\s*\*\*100%\*\*\s*\|",
        _текст(), re.S)
    if not совпадение:
        raise AssertionError("строка наблюдения Brute+SIMD не найдена")
    return 100.0


def _контроль_отрицательный():
    совпадение = re.search(
        r"\| HNSW\s*\|.*?\|\s*~?([0-9.]+)%\s*\|",
        _текст())
    if not совпадение:
        raise AssertionError("отрицательный контроль HNSW не найден")
    return float(совпадение.group(1))


def _контроль_положительный():
    совпадение = re.search(r"All BruteIndex tests passed \((\d+)/(\d+)\)", _текст())
    if not совпадение:
        raise AssertionError("положительный контроль тестов BruteIndex не найден")
    пройдено, всего = map(int, совпадение.groups())
    if пройдено != всего:
        raise AssertionError("положительный контроль тестов не пройден")
    return float(пройдено)


def _инвентарь_рецепта():
    текст = _текст().lower()
    поля = {
        "исходные векторы и запросы": bool(re.search(r"raw vectors|query vectors|исходные векторы|набор запросов", текст)),
        "разметка истинных соседей": bool(re.search(r"ground truth|истинн(?:ые|ых) сосед", текст)),
        "точное определение recall": bool(re.search(r"recall@|точн(?:ое|ый) определение полноты", текст)),
        "модель и версия эмбеддингов": bool(re.search(r"embedding model|model commit|версия эмбеддинг", текст)),
        "контрольная сумма входов": bool(re.search(r"sha256|checksum|контрольная сумма", текст)),
        "компилятор и аппаратная среда": bool(re.search(r"compiler version|cpu model|аппаратн(?:ая|ой) сред", текст)),
        "seed": bool(re.search(r"\bseed\b|random state", текст)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|независим(?:ый|ая) повтор", текст)),
    }
    поля["рецепт_полон"] = all(поля.values())
    поля["отсутствует"] = [имя for имя, есть in поля.items()
                           if имя not in {"рецепт_полон", "отсутствует"} and not есть]
    return поля


def _код_причины():
    return "" if _инвентарь_рецепта()["рецепт_полон"] else "metrics_incommensurable"


def _неверная_подстановка():
    return 50.0


def _самопроверка():
    assert наблюдение() == 100.0
    assert _контроль_отрицательный() == 95.0
    assert _контроль_положительный() == 9.0
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert _код_причины() == "metrics_incommensurable"
    assert _неверная_подстановка() != наблюдение()
    assert _контроль_отрицательный() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт ANN Brute+SIMD раскрывает воспроизводимый benchmark точности поиска",
        source="docs/docs/research/trinity-ann-benchmark-verdict-report.md:1-240",
        claim_kind="statistical",
        stated=наблюдение(),
        reference=None,
        observed=наблюдение,
        wrong=_неверная_подстановка,
        null_model=_контроль_отрицательный,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость ANN benchmark",
        observable="полнота поиска Brute+SIMD 100 процентов на наборах 1000 и 5000 символов",
        measurement_source="отчёт ANN Benchmark Verdict",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:ann:brute_simd_benchmark_recipe:v1",
        information_class="новый источник и новый риск воспроизводимости benchmark точности ANN",
        purpose="audit",
        models=["заявленный benchmark Brute+SIMD", "независимый benchmark на исходных векторах и запросах"],
        independent_of={"source": "отчёт ANN Benchmark и независимый запуск на исходных векторах"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Наблюдение полноты поиска извлечено из строки Brute+SIMD, "
            "отрицательный контроль — из строки HNSW, положительный контроль — "
            "из отдельной строки тестов BruteIndex. Число 100 процентов не "
            "используется как вычисляемый эталон."
        ),
        skip_reasons={
            "С1": "вычисляемый эталон полноты отсутствует без исходных векторов, запросов и разметки",
            "С2": "заявленная полнота не сопоставлена с независимым вычислением",
            "С3": "benchmark не содержит независимого повторного запуска",
            "С4": "подстановка не восполняет отсутствующие данные и реализацию",
            "С5": "контроль HNSW относится к другому алгоритму",
            "С6": "размеры наборов указаны без полного протокола тестов",
            "С7": "правило формирования запросов и истинных соседей не раскрыто",
            "С8": "неопределённость полноты и доверительный интервал отсутствуют",
            "С9": "исходные векторы и набор запросов не приложены",
            "С10": "ошибки по отдельным запросам отсутствуют",
            "С11": "повторения и разброс по запускам не представлены",
            "С12": "второй эталон невозможен без входов и полной реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул к benchmark не относится",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство условий benchmark не задано",
            "С19": "сравнение строк таблицы не доказывает воспроизводимость",
            "С20": "эффективное число независимых запросов не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
