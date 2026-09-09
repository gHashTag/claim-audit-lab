# -*- coding: utf-8 -*-
"""Проверка воспроизводимости оценочной KN-перплексии Golden Chain v2.50.

Наблюдение извлекается из строки с оценочной KN-PPL, а контроль — из отдельной
строки с числом интеграционных тестов и из отдельной строки базовой модели.
Напечатанное значение не объявляется вычисляемым эталоном: без исходного
корпуса, границ разбиения, версии реализации и независимого повтора эталон
остаётся недоступным, поэтому итогом может быть только машинный вопрос.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/docs/docs/research/trinity-golden-chain-v2-50-kneser-ney-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Golden Chain v2.50 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    текст = _текст()
    совпадение = re.search(r"\| KN Eval PPL \| \*\*([0-9.]+)\*\*", текст)
    if not совпадение:
        raise AssertionError("строка KN Eval PPL не найдена")
    значение = float(совпадение.group(1))
    if значение != 4.84:
        raise AssertionError("значение KN Eval PPL изменилось")
    return значение


def контроль_базовой_модели():
    совпадение = re.search(r"Laplace eval CE: [0-9.]+ \([0-9.]+% below random\), PPL ([0-9.]+)", _текст())
    if not совпадение:
        raise AssertionError("контрольная PPL базовой модели не найдена")
    return float(совпадение.group(1))


def контроль_тестов():
    совпадение = re.search(r"All ([0-9]+) integration tests pass", _текст())
    if not совпадение:
        raise AssertionError("контроль интеграционных тестов не найден")
    return int(совпадение.group(1))


def _инвентарь_рецепта():
    текст = _текст().lower()
    поля = {
        "исходный корпус": bool(re.search(r"raw corpus|corpus archive|source corpus|исходн(?:ый|ые) корпус", текст)),
        "точные границы разбиения": bool(re.search(r"exact split|train.?eval boundary|disjoint passages|точн(?:ая|ые) границ", текст)),
        "точная токенизация": bool(re.search(r"tokeniz|word vocabulary|токенизац", текст)),
        "формула kn": bool(re.search(r"kneser.?ney|max\(c.?d|backoff", текст)),
        "seed": bool(re.search(r"\bseed\b|random state", текст)),
        "версия кода": bool(re.search(r"git commit|commit sha|git sha|release version", текст)),
        "контрольная сумма входа": bool(re.search(r"sha256|checksum|input hash", текст)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|independent reproduction", текст)),
    }
    поля["рецепт_полон"] = all(поля.values())
    поля["отсутствует"] = [имя for имя, есть in поля.items()
                           if имя not in {"рецепт_полон", "отсутствует"} and not есть]
    return поля


def _код_причины():
    return "" if _инвентарь_рецепта()["рецепт_полон"] else "metrics_incommensurable"


def _неверный_ответ():
    return 3.14


def _самопроверка():
    assert наблюдение() == 4.84
    assert контроль_базовой_модели() == 28.50
    assert контроль_тестов() == 47
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert set(инвентарь["отсутствует"]) == {
        "исходный корпус", "точные границы разбиения", "точная токенизация", "seed",
        "версия кода", "контрольная сумма входа", "независимый повтор",
    }
    assert _код_причины() == "metrics_incommensurable"
    assert _неверный_ответ() != наблюдение()
    assert контроль_базовой_модели() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Оценочная KN-перплексия 4,84 в Golden Chain v2.50 воспроизводима по полному рецепту",
        source="docs/docs/research/trinity-golden-chain-v2-50-kneser-ney-report.md:1-232",
        claim_kind="statistical",
        stated=наблюдение(),
        reference=None,
        observed=наблюдение,
        wrong=_неверный_ответ,
        null_model=контроль_базовой_модели,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость оценочной KN-перплексии и риск пересечения контекстов",
        observable="оценочная перплексия Kneser–Ney на корпусе Shakespeare",
        measurement_source="отчёт Golden Chain v2.50 о сглаживании Kneser–Ney",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v250:kneser_ney_recipe:v1",
        information_class="новый источник и новая категория риска рецепта сглаживания и утечки контекста",
        purpose="audit",
        models=["заявленная KN-перплексия", "воспроизводимая KN-перплексия по независимому рецепту"],
        independent_of={"source": "отдельный отчёт v2.50 и независимый запуск на исходном корпусе"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Наблюдение 4,84 извлечено из строки KN Eval PPL; контроль 28,50 — "
            "из отдельной строки Laplace eval PPL, а 47/47 — из отдельной строки "
            "тестов. Ни одно печатное число не используется как эталон независимого "
            "воспроизведения. Отсутствуют сырой корпус, точные границы train/eval, "
            "seed, commit реализации, контрольная сумма входа и независимый replay."
        ),
        skip_reasons={
            "С1": "вычислимый эталон отсутствует без сырого корпуса и полного рецепта",
            "С2": "независимая оценка KN-PPL не задана полными входами и реализацией",
            "С3": "наблюдение есть, но независимый повтор не предоставлен",
            "С4": "подставка не восполняет отсутствующие входы рецепта",
            "С5": "контроль Laplace имеет другую модель сглаживания",
            "С6": "варианты D и lambda не являются независимым рецептом",
            "С7": "точные границы train/eval и последовательность токенов не раскрыты",
            "С8": "неопределённость PPL и доверительный интервал не заданы",
            "С9": "исходный ряд токенов отсутствует",
            "С10": "ошибки по отдельным eval-токенам отсутствуют",
            "С11": "несколько независимых оценок не представлены",
            "С12": "второй вычислимый эталон невозможен без входов и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул не относится к PPL-рецепту",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "согласие строк отчёта не доказывает независимую воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
