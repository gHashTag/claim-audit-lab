# -*- coding: utf-8 -*-
"""Проверка воспроизводимости 4-граммной KN-перплексии Golden Chain v2.51.

Кейс не принимает напечатанное значение за вычислимый эталон. Он проверяет,
достаточно ли отчёт раскрывает исходы, границы разбиения, реализацию и
независимый повтор для утверждения о PPL 1,94.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-51-4gram-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Golden Chain v2.51 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    текст = _текст()
    совпадение = re.search(r"\| 4-gram Eval PPL \| \*\*([0-9.]+)\*\*", текст)
    if not совпадение:
        raise AssertionError("строка 4-gram eval PPL не найдена")
    значение = float(совпадение.group(1))
    if значение != 1.94:
        raise AssertionError("значение 4-gram eval PPL изменилось")
    return значение


def _контроль():
    совпадение = re.search(r"KN trigram baseline: eval CE [0-9.]+, PPL ([0-9.]+)", _текст())
    if not совпадение:
        raise AssertionError("контрольный KN trigram PPL не найден")
    return float(совпадение.group(1))


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
    return 3.88


def _самопроверка():
    assert наблюдение() == 1.94
    assert _контроль() == 4.84
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert set(инвентарь["отсутствует"]) == {
        "исходный корпус", "seed", "версия кода", "контрольная сумма входа", "независимый повтор",
    }
    assert _код_причины() == "metrics_incommensurable"
    assert _неверный_ответ() != наблюдение()
    assert _контроль() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="4-граммная KN-перплексия eval 1,94 в Golden Chain v2.51 воспроизводима по полному рецепту",
        source="deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-51-4gram-report.md:1-260",
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
        claim_family="воспроизводимость 4-граммной KN-перплексии и риск меморизации",
        observable="4-граммная KN perplexity eval на корпусе Shakespeare",
        measurement_source="отчёт Golden Chain v2.51 4-Gram KN Extension",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v251:4gram_kn_recipe:v1",
        information_class="новый источник и новый риск воспроизводимости 4-граммной метрики и меморизации",
        purpose="audit",
        models=["заявленный 4-граммный KN PPL", "воспроизводимый 4-граммный KN PPL"],
        independent_of={"source": "отдельный отчёт v2.51 и независимая реализация Kneser-Ney"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Отчёт сообщает корпус, словарь, размер eval, формулу KN и таблицу "
            "сглаживания, но не даёт исходный корпус или checksum, точные границы "
            "разбиения, seed, commit реализации и независимый replay. Контроль 4,84 "
            "относится к KN trigram и не является эталоном 4-граммного PPL."
        ),
        skip_reasons={
            "С1": "вычислимый эталон отсутствует без исходного корпуса, границ split и версии реализации",
            "С2": "независимая оценка 4-граммного PPL не задана полным входом и кодом",
            "С3": "наблюдение есть, но независимый повтор не предоставлен",
            "С4": "подставка не восполняет отсутствующие входы рецепта",
            "С5": "контроль имеет другую глубину контекста и не является эталоном",
            "С6": "ряд вариантов 4-граммного KN не даёт независимого рецепта",
            "С7": "границы train/eval и точная последовательность токенов не раскрыты",
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
            "С19": "согласие train/eval строк не доказывает независимую воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
