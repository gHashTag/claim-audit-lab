# -*- coding: utf-8 -*-
"""Аудит воспроизводимости word-level PPL Golden Chain v2.45.

Кейс не подтверждает равенство напечатанных чисел. Он проверяет, раскрыт ли
полный рецепт word bigram: исходный корпус, точная граница split, код, seed,
контрольная сумма входа и независимый повтор. При их отсутствии эталон не
достраивается и машинный результат остаётся ВОПРОС.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-45-word-level-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Golden Chain v2.45 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    текст = _текст()
    совпадение = re.search(r"Word PPL:\s*train=([0-9.]+)\s+eval=([0-9.]+)\s+gap=([-0-9.]+)", текст)
    if not совпадение:
        raise AssertionError("строка Word PPL не найдена")
    train, evaluation, gap = map(float, совпадение.groups())
    if (train, evaluation, gap) != (23.38, 15.52, -7.86):
        raise AssertionError("сводка Word PPL изменилась")
    return evaluation


def _контроль():
    # Отдельная char-level метрика из той же таблицы; это контроль иной шкалы,
    # а не эталон для word-level PPL.
    совпадение = re.search(r"Char raw freq:\s*train=([0-9.]+)\s+eval=([0-9.]+)\s+gap=([-0-9.]+)", _текст())
    if not совпадение:
        raise AssertionError("контроль char raw freq не найден")
    return float(совпадение.group(2))


def _инвентарь_рецепта():
    текст = _текст().lower()
    поля = {
        "исходный корпус": bool(re.search(r"raw corpus|corpus archive|source corpus|исходн(?:ый|ые) корпус", текст)),
        "точная токенизация": bool(re.search(r"space.?split|tokeniz", текст)),
        "точное разбиение": bool(re.search(r"80/20|train.?eval split|split", текст)),
        "определение потерь": bool(re.search(r"cross.?entropy|loss|laplace", текст)),
        "агрегация": bool(re.search(r"mean|average|averaged|средн", текст)),
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
    return 4.12


def _самопроверка():
    assert наблюдение() == 15.52
    assert _контроль() == 5.59
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert set(инвентарь["отсутствует"]) == {
        "исходный корпус", "версия кода", "контрольная сумма входа", "независимый повтор",
    }
    assert _код_причины() == "metrics_incommensurable"
    assert _неверный_ответ() != наблюдение()
    assert _контроль() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Word PPL eval 15,52 в Golden Chain v2.45 воспроизводим по полному рецепту",
        source="deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-45-word-level-report.md:1-190",
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
        claim_family="воспроизводимость word-level PPL и сопоставимость уровней токенизации",
        observable="word-level perplexity eval на 5014-символьном корпусе Shakespeare",
        measurement_source="отчёт Golden Chain v2.45 Word-Level Statistics",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v245:word_ppl_recipe:v1",
        information_class="новый риск рецепта word-level метрики и сопоставимости токенизации",
        purpose="audit",
        models=["заявленный word-level PPL", "воспроизводимый word-level PPL"],
        independent_of={"source": "отдельный отчёт v2.45 и независимая реализация word bigram"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Отчёт раскрывает токенизацию, размеры корпуса, 80/20 split, Laplace smoothing "
            "и агрегаты train/eval, но не даёт исходный корпус или его checksum, commit "
            "реализации и независимый replay. Word PPL и char PPL имеют разные пространства "
            "токенов; контроль 5,59 не является эталоном word-level PPL."
        ),
        skip_reasons={
            "С1": "вычислимый эталон отсутствует без исходного корпуса и версии реализации",
            "С2": "независимая оценка word-level PPL не задана полным входом и кодом",
            "С3": "наблюдение есть, но независимый повтор не предоставлен",
            "С4": "подставка не восполняет отсутствующие входы рецепта",
            "С5": "char-level контроль имеет другую токенизацию и шкалу",
            "С6": "ряд вариантов word bigram не опубликован",
            "С7": "все варианты сглаживания и границы split не раскрыты полностью",
            "С8": "неопределённость PPL и доверительный интервал не заданы",
            "С9": "исходная последовательность токенов отсутствует",
            "С10": "ошибки по отдельным токенам отсутствуют",
            "С11": "несколько независимых оценок не представлены",
            "С12": "второй вычислимый эталон невозможен без входов и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул не относится к PPL-рецепту",
            "С17": "MDL не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "согласие train/eval строк не доказывает независимую воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
