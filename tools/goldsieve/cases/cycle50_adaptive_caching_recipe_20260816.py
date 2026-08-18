# -*- coding: utf-8 -*-
"""Аудит воспроизводимости отчёта Cycle 50 об адаптивном кэшировании.

Сводные 1,000 и 18/18 не используются как дешёвое подтверждение. Наблюдение
и контроль извлекаются разными шаблонами; основной эталон отсутствует без
сырой нагрузки, реализации и независимого запуска.
"""
import os
import re
import sys
from goldsieve.sieve import Claim

ИСТОЧНИК = "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/cycle50-adaptive-caching-report.md"
if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться без регистрации в sys.modules")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Cycle 50 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    m = re.search(r"\| Improvement Rate \| \*\*?([0-9.]+)\*\*? \|", _текст())
    if not m:
        raise AssertionError("Improvement Rate не найден")
    return float(m.group(1))


def _контроль():
    m = re.search(r"\| Tests Passed \| \*\*?(\d+)/(\d+)\*\*? \|", _текст())
    if not m:
        raise AssertionError("Tests Passed не найден")
    passed, total = map(int, m.groups())
    return float(passed) / float(total) * 100.0


def _вычисляемый_контроль():
    m = re.search(r"\| Tests Passed \| \*\*?(\d+)/(\d+)\*\*? \|", _текст())
    if not m:
        raise AssertionError("контроль не вычисляется")
    passed, total = map(int, m.groups())
    return {"passed": passed, "total": total, "rate": passed / total if total else 0.0}


def _инвентарь():
    t = _текст().lower()
    поля = {
        "сырая нагрузка": bool(re.search(r"raw workload|raw requests|input trace|исходн(?:ая|ую) нагруз", t)),
        "точная реализация": bool(re.search(r"commit sha|git commit|git sha|точн(?:ая|ый) версия кода", t)),
        "среда выполнения": bool(re.search(r"python|zig version|compiler version|операционная система", t)),
        "контрольная сумма входа": bool(re.search(r"sha256|checksum|контрольная сумма", t)),
        "seed": bool(re.search(r"\bseed\b|random state", t)),
        "независимый повтор": bool(re.search(r"independent replay|independent run|independent reproduction|независим(?:ый|ая) повтор", t)),
        "полный эталон": False,
    }
    поля["полный эталон"] = all(поля[k] for k in поля if k != "полный эталон")
    поля["отсутствует"] = [k for k, v in поля.items() if k not in {"полный эталон", "отсутствует"} and not v]
    return поля


def _код_причины():
    return "" if _инвентарь()["полный эталон"] else "metrics_incommensurable"


def _подстановка():
    return 0.5


def _самопроверка():
    assert наблюдение() == 1.0
    assert _контроль() == 100.0
    assert _вычисляемый_контроль() == {"passed": 18, "total": 18, "rate": 1.0}
    inv = _инвентарь()
    assert not inv["полный эталон"]
    assert set(inv["отсутствует"]) == {"сырая нагрузка", "точная реализация", "среда выполнения", "контрольная сумма входа", "seed", "независимый повтор"}
    assert _код_причины() == "metrics_incommensurable"
    assert _подстановка() != наблюдение()
    assert _контроль() != наблюдение()


_самопроверка()

CLAIMS = [
    Claim(
        name="Отчёт Cycle 50 воспроизводимо подтверждает адаптивное кэширование",
        source="deploy/trinity-nexus/docs/research/cycle50-adaptive-caching-report.md:1-190",
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
        claim_family="воспроизводимость benchmark адаптивного кэширования",
        observable="Improvement Rate 1,000, контроль 18/18 и сводные показатели кэширования",
        measurement_source="отчёт Cycle 50 Adaptive Caching & Memoization",
        uncertainty_type="recipe_missing",
        novelty_key="trinity:cycle50:adaptive_caching_recipe:v1",
        information_class="новый источник и новый риск воспроизводимости benchmark кэширования и мемоизации",
        purpose="audit",
        models=["заявленный benchmark адаптивного кэширования", "воспроизводимый benchmark на независимой нагрузке"],
        independent_of={"source": "отчёт Cycle 50 и независимый запуск на сыром следе обращений"},
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes="Наблюдение и контроль извлечены отдельными путями. Отчёт не даёт сырой нагрузки, точной реализации, контрольной суммы, seed и независимого повтора; сравнение с phi^-1 намеренно не используется.",
        skip_reasons={
            "С1": "вычисляемый эталон benchmark отсутствует без сырой нагрузки и точной реализации",
            "С2": "независимая оценка Improvement Rate не задана полным рецептом",
            "С3": "наблюдение есть, но независимый запуск кэша не предоставлен",
            "С4": "подстановка не восполняет отсутствующие входы benchmark",
            "С5": "контроль 18/18 является отдельной строкой, а не эталоном кэширования",
            "С6": "варианты реализации и среды не раскрыты",
            "С7": "не заданы точный след обращений и границы нагрузки",
            "С8": "неопределённость benchmark не задана",
            "С9": "сырой след обращений отсутствует",
            "С10": "ошибки по отдельным операциям отсутствуют",
            "С11": "несколько независимых оценок не представлены",
            "С12": "второй вычислимый эталон невозможен без входов и реализации",
            "С13": "пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул к benchmark не относится",
            "С17": "сжатие описания не является предметом заявления",
            "С18": "семейство формул отсутствует",
            "С19": "согласие сводных строк не доказывает воспроизводимость",
            "С20": "эффективное число попыток для одного отчёта не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
