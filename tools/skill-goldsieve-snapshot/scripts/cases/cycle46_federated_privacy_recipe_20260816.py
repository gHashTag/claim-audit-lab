# -*- coding: utf-8 -*-
"""Аудит воспроизводимости privacy budget федеративного протокола Cycle 46.

Кейс не превращает напечатанные 1,0 или 18/18 в подтверждение. Он
извлекает наблюдение и контроль разными путями, затем проверяет полноту
рецепта приватности, агрегации и независимого воспроизведения.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/cycle46-federated-learning-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Cycle 46 о федеративном обучении отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    совпадение = re.search(r"\| Improvement Rate \| \*\*([0-9.]+)\*\*", _текст())
    if not совпадение:
        raise AssertionError("коэффициент улучшения не найден")
    значение = float(совпадение.group(1))
    if значение != 1.0:
        raise AssertionError("коэффициент улучшения изменился")
    return значение


def _контроль():
    совпадение = re.search(r"\| Tests Passed \| \*\*(\d+)/(\d+)\*\*", _текст())
    if not совпадение:
        raise AssertionError("контроль числа тестов не найден")
    пройдено, всего = map(int, совпадение.groups())
    if пройдено != всего:
        raise AssertionError("контроль числа тестов не пройден")
    return float(всего)


def _параметры():
    текст = _текст()
    совпадение = re.search(r"Default epsilon: ([0-9.]+), delta: ([0-9.e-]+)", текст)
    шум = re.search(r"Noise multiplier: ([0-9.]+)", текст)
    точность = re.search(r"Overall Average Accuracy \| ([0-9.]+)", текст)
    if not совпадение or not шум or not точность:
        raise AssertionError("параметры приватности или точность не найдены")
    return {
        "epsilon": float(совпадение.group(1)),
        "delta": float(совпадение.group(2)),
        "множитель шума": float(шум.group(1)),
        "средняя точность": float(точность.group(1)),
    }


def _инвентарь_рецепта():
    текст = _текст().lower()
    поля = {
        "сырые клиентские выборки": bool(re.search(r"raw client data|client dataset|raw datasets", текст)),
        "точные границы клиентских разбиений": bool(re.search(r"exact client partition|client split boundaries|disjoint client", текст)),
        "уравнение privacy accountant": bool(re.search(r"accountant equation|rdp accountant|privacy loss distribution", текст)),
        "точный генератор шума": bool(re.search(r"rng seed|random generator version|deterministic noise", текст)),
        "контрольная сумма реализации": bool(re.search(r"git commit|commit sha|code checksum|implementation hash", текст)),
        "seed": bool(re.search(r"\bseed\b|random state", текст)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|independent reproduction", текст)),
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
    assert наблюдение() == 1.0
    assert _контроль() == 18.0
    assert _параметры() == {
        "epsilon": 1.0, "delta": 1e-5,
        "множитель шума": 1.1, "средняя точность": 0.93,
    }
    инвентарь = _инвентарь_рецепта()
    assert not инвентарь["рецепт_полон"]
    assert set(инвентарь["отсутствует"]) == {
        "сырые клиентские выборки", "точные границы клиентских разбиений",
        "уравнение privacy accountant", "точный генератор шума",
        "контрольная сумма реализации", "seed", "независимый повтор",
    }
    assert _код_причины() == "metrics_incommensurable"
    assert _неверный_ответ() != наблюдение()
    assert _контроль() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт Cycle 46 о федеративном обучении раскрывает воспроизводимый рецепт приватности",
        source="deploy/trinity-nexus/docs/research/cycle46-federated-learning-report.md:1-220",
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
        claim_family="воспроизводимость дифференциальной приватности и федеративной агрегации",
        observable="epsilon=1,0, delta=1e-5, множитель шума=1,1 и средняя точность=0,93",
        measurement_source="отчёт Cycle 46 Federated Learning Protocol",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:cycle46:federated_privacy_recipe:v1",
        information_class="новый источник и новый риск воспроизводимости privacy budget/агрегации в федеративном обучении",
        purpose="audit",
        models=["заявленный федеративный протокол Cycle 46", "воспроизводимый протокол с независимым privacy accounting"],
        independent_of={"source": "отчёт Cycle 46 и независимая реализация DP-аккумулятора на клиентских данных"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Отчёт перечисляет epsilon, delta, множитель шума, стратегии агрегации "
            "и среднюю точность, но не даёт сырые клиентские выборки, границы "
            "разбиений, уравнение privacy accountant, точный генератор шума, seed, "
            "контрольную сумму реализации или независимый replay. Контроль 18/18 "
            "проверяет только разбор строки и не является эталоном приватности."
        ),
        skip_reasons={
            "С1": "вычислимый эталон privacy accounting отсутствует без клиентских данных и точной реализации",
            "С2": "независимая оценка приватностного бюджета не задана полным рецептом",
            "С3": "параметры отчёта есть, но независимый повтор не предоставлен",
            "С4": "подставка не восполняет отсутствующие входы и реализацию",
            "С5": "контроль 18/18 относится к тестам, а не к privacy accounting",
            "С6": "ряд стратегий агрегации не даёт независимый численный эталон",
            "С7": "клиентские границы, порядок раундов и точная конфигурация не раскрыты",
            "С8": "неопределённость epsilon и доверительный интервал точности не заданы",
            "С9": "сырые клиентские градиенты и выборки отсутствуют",
            "С10": "ошибки по раундам и клиентам отсутствуют",
            "С11": "несколько независимых запусков не представлены",
            "С12": "второй вычислимый эталон невозможен без данных и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул не относится к privacy-рецепту",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство воспроизводимых DP-рецептов отсутствует",
            "С19": "согласие параметров в одной таблице не доказывает независимую воспроизводимость",
            "С20": "эффективное число независимых испытаний не определено",
            "С21": "алгебраическая форма полного privacy-рецепта отсутствует",
        },
    )
]
