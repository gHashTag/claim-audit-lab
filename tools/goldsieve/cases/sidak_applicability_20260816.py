# -*- coding: utf-8 -*-
"""Аудит применимости поправки Шидака к зависимому семейству формул.

Кейс не перепроверяет дешёвое тождество порога само по себе. Он связывает
напечатанный порог с фактическим семейством ACTUAL_RANGES и запускает С20:
вывод сравнивается с порогом при полном M и при измеренном M_eff. Поэтому
результат отвечает на новый риск публичного утверждения — можно ли переносить
формулу независимых испытаний на зависимую логарифмическую решётку.
"""

import math
import os
import re
import sys

from goldsieve.family import enumerate_family
from goldsieve.meff import meff_from_family
from goldsieve.sidak import bonferroni_local_p, sidak_local_p, sigma_from_p
from goldsieve.sieve import Claim
from goldsieve.threshold import ACTUAL_RANGES


# Guard для реального режима CLI: cli.py грузит case через module_from_spec и не
# регистрирует его в sys.modules. Тихий переход на inspect.getmodule здесь не
# допускается.
if __name__ in sys.modules:
    raise RuntimeError(
        "кейс должен быть загружен через module_from_spec без регистрации"
    )

ИСТОЧНИК = os.environ.get(
    "TRINITY_SIDAK_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/docs/math-foundations/"
    "sacred-formulas.md",
)
АЛЬФА = 0.05
M_FULL = 123201
ПОЛОСА = 0.0056 / 0.6889


def _текст():
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _строка_порога():
    for строка in _текст().splitlines():
        if "require **5.06σ**, not 3σ" in строка:
            return строка
    raise AssertionError("строка с порогом Шидака не найдена")


def наблюдение():
    найдено = re.search(r"require \*\*([0-9.]+)σ\*\*", _строка_порога())
    if not найдено:
        raise AssertionError("число сигм не найдено")
    return float(найдено.group(1))


def _порог_Шидака():
    локальный = sidak_local_p(АЛЬФА, M_FULL)
    return sigma_from_p(локальный)


def эталон():
    # Эталон не читает напечатанное 5,06: он заново выводит порог из M и alpha.
    return _порог_Шидака()


def эталон_альт():
    # Принципиально иная поправка: Бонферрони опирается на неравенство Буля и
    # не требует независимости. Это не второе имя Шидака.
    локальный = bonferroni_local_p(АЛЬФА, M_FULL)
    return sigma_from_p(локальный)


def _семейство():
    значения = enumerate_family(ACTUAL_RANGES)
    if len(значения) != M_FULL:
        raise AssertionError("ACTUAL_RANGES не дают 123 201 членов")
    return значения


def _meff():
    return {
        "values": _семейство(),
        "eps": ПОЛОСА,
        "sigma": наблюдение(),
        "search_size": M_FULL,
    }


def _wrong():
    # Заведомо неверная подставка отличается от обоих порогов.
    return 3.0


def _null_model():
    # Негативный контроль не должен совпасть с вычисленным порогом.
    return 1.0


def _sample():
    return [наблюдение()]


def _selfcheck():
    assert __name__ not in sys.modules
    assert abs(наблюдение() - 5.06) < 1e-12
    assert abs(эталон() - 5.0613316768) < 1e-6
    assert abs(эталон_альт() - 5.0661974955) < 1e-6
    assert _wrong() != эталон()
    assert _null_model() != эталон()
    info = meff_from_family(_семейство(), ПОЛОСА, subsample=180, seed=0)
    assert info["M"] == M_FULL
    assert 0 < info["M_eff_cluster"] < M_FULL
    assert info["M_eff_eigen"] is not None


_selfcheck()


CLAIMS = [
    Claim(
        name="Порог Шидака 5,06σ применим к зависимому семейству формул",
        source="docs/docs/math-foundations/sacred-formulas.md:257-259",
        stated=наблюдение(),
        reference=эталон,
        observed=наблюдение,
        wrong=_wrong,
        null_model=_null_model,
        null_expect=1.0,
        null_kind="negative",
        tolerance=0.01,
        reference_alt=эталон_альт,
        alt_tolerance=lambda: 0.01,
        sample=_sample,
        statistics={"value": lambda values: sum(values) / len(values)},
        meff=_meff,
        inputs=[ИСТОЧНИК],
        claim_kind="statistical",
        claim_family="применимость поправки множественности к зависимому семейству",
        observable="устойчивость порога к замене M на измеренное M_eff",
        measurement_source="фактические ACTUAL_RANGES корпуса Trinity и строка порога",
        uncertainty_type="model_dependence",
        expected_effect_sigma=1.0,
        resolution_sigma=0.01,
        novelty_key="sacred:statistics:sidak_applicability:v1",
        information_class="новая категория риска публичного утверждения",
        purpose="model_discrimination",
        models=[
            "Sidak_independence",
            "Bonferroni_dependence_safe",
            "M_eff_cluster",
            "M_eff_eigen",
        ],
        independent_of=["sacred:statistics:sidak_threshold:v1"],
        search_size=M_FULL,
        tests_independent="unknown",
        reason_code_hint="meff_unstable",
        notes=(
            "Наблюдение читает отдельную строку корпуса. Эталон выводит "
            "порог по alpha и фактическому M, альтернативный эталон использует "
            "Бонферрони. С20 измеряет зависимость членов ACTUAL_RANGES двумя "
            "методами; это не доказательство истинного порога для любой другой "
            "выборки. Источники методов: "
            "https://doi.org/10.1080/01621459.1967.10482935; "
            "https://doi.org/10.1038/sj.hdy.6800717; "
            "https://doi.org/10.1140/epjc/s10052-010-1470-8."
        ),
        skip_reasons={
            "С6": "одна фиксированная полоса сравнения, сетка разрешений не заявлена",
            "С7": "оценка задаётся двумя методами поправки, отдельная выборка оценок отсутствует",
            "С8": "погрешность модельной зависимости не сведена к физической погрешности",
            "С9": "семейство фиксировано одним корпусным диапазоном",
            "С10": "одна детерминированная строка порога; выборочный шум не оценивается",
            "С11": "проверяется один порог, а не серия независимых статистик",
            "С15": "внешней измерительной цели нет",
            "С16": "перебор формул является входом аудита, а не пространством подгонки цели",
            "С17": "сжатие формулы не является предметом этого кейса",
            "С18": "границы проверяются через ACTUAL_RANGES, отдельная объявленная область не задана",
            "С19": "арифметический запас не определяет риск; С20 сравнивает модели зависимости",
            "С21": "алгебраическая объяснимость не является предметом этого кейса",
        },
    )
]
