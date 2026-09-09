# -*- coding: utf-8 -*-
"""Аудит строки Tsirelson в рукописи Trinity.

Наблюдаемое извлекается из столбца Computed. Эталон вычисляется из кортежа
параметров по определению V=n·3^k·π^m·φ^p·e^q. Второй эталон собирается
логарифмическим маршрутом. Внешняя цель — точная граница 2√2; она не является
литералом из корпуса и нужна для проверки содержательного физического
утверждения, а не для подтверждения округлённой строки таблицы.
"""
import math
import os
import re
import sys

from goldsieve import family
from goldsieve import threshold
from goldsieve.sieve import Claim

ИСТОЧНИК = os.environ.get(
    "TRINITY_TSIRELSON_SOURCE",
    "/home/user/workspace/corpus/trinity/docs/papers/trinity-sacred-mathematics.tex",
)
СТАНДАРТНЫЕ_ДИАПАЗОНЫ = family.STANDARD_RANGES
ПОИСК = family.declared_size(СТАНДАРТНЫЕ_ДИАПАЗОНЫ)
ФИ = (1.0 + math.sqrt(5.0)) / 2.0

if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("рукопись Trinity отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _строка():
    совпадение = None
    for строка in _текст().splitlines():
        if "Tsirelson bound $2\\sqrt{2}" not in строка:
            continue
        совпадение = re.search(
            r"&\s*([0-9]+\.[0-9]+)\s*&\s*\$\([^)]*\)\$?\s*&\s*([0-9]+\.[0-9]+)",
            строка,
        )
        if совпадение:
            break
    if not совпадение:
        raise AssertionError("строка Tsirelson в таблице не найдена")
    return float(совпадение.group(1)), float(совпадение.group(2))


def _наблюдаемое():
    """Извлечь Computed, не вычисляя его из формулы."""
    return _строка()[1]


def _заявленное():
    return _наблюдаемое()


def _из_параметров():
    n, k, m, p, q = (8, 4, -3, 0, -2)
    return n * (3.0 ** k) * (math.pi ** m) * (ФИ ** p) * (math.e ** q)


def _эталон():
    return _из_параметров()


def _эталон_альт():
    """Принципиально иной маршрут: сумма логарифмов и экспонента."""
    return math.exp(
        math.log(8.0) + 4.0 * math.log(3.0)
        - 3.0 * math.log(math.pi) - 2.0
    )


def _положительный_контроль():
    """Положительный контроль вычисляет параметрическую формулу отдельно."""
    return 8.0 * math.pow(3.0, 4.0) / (math.pow(math.pi, 3.0) * math.exp(2.0))


def _неверные():
    return [
        lambda: _эталон() * 1.01,
        lambda: _эталон() * 0.99,
        lambda: _эталон() + 0.1,
    ]


def _среднее(values):
    return float(sum(values) / len(values))


def _выборка():
    return [_наблюдаемое()]


def _внешняя_цель():
    return {
        "value": 2.0 * math.sqrt(2.0),
        "uncertainty": 1.0e-15,
        "source": (
            "теорема Tsirelson, оригинальная публикация, "
            "https://doi.org/10.1007/BF01646019"
        ),
    }


def _заявленная_внешняя_цель():
    return _строка()[0]


def _множественность():
    цель = _внешняя_цель()
    eps = цель["uncertainty"] / abs(цель["value"])
    доля, ожидание = family.empirical_multiplicity(
        (-3, 4), eps, ranges=СТАНДАРТНЫЕ_ДИАПАЗОНЫ,
        trials=1000, seed=20260817,
    )
    return {
        "expected_hits": ожидание,
        "p_global": доля,
        "fraction_random_targets_hit": доля,
        "search_size": ПОИСК,
    }


def _значения_семейства():
    цель = _внешняя_цель()["value"]
    значения = family.enumerate_family(СТАНДАРТНЫЕ_ДИАПАЗОНЫ)
    return [v for v in значения if цель / 5.0 <= v <= цель * 5.0]


def _эффективное_число():
    цель = _внешняя_цель()
    return {
        "values": _значения_семейства(),
        "eps": цель["uncertainty"] / abs(цель["value"]),
        "sigma": abs((_эталон() - цель["value"]) / цель["uncertainty"]),
        "search_size": ПОИСК,
    }


def _описание():
    цель = _внешняя_цель()
    eps = цель["uncertainty"] / abs(цель["value"])
    return {
        "description_bits": math.log2(ПОИСК),
        "match_bits": math.log2(1.0 / (2.0 * eps)),
    }


def _область():
    assert family.declared_size(СТАНДАРТНЫЕ_ДИАПАЗОНЫ) == 20412
    return []


def _арифметика():
    цель = _внешняя_цель()
    return {
        "params": (8, 4, -3, 0, -2),
        "rel_uncertainty": цель["uncertainty"] / abs(цель["value"]),
    }


def _алгебраика():
    цель = _внешняя_цель()
    return {
        "target": цель["value"],
        "coeffs": (8, 4, -3, 0, -2),
        "has_pi": True,
        "rel_deviation": abs(_эталон() - цель["value"]) / abs(цель["value"]),
        "max_coeff": 9,
        "free_coeff_limit": 6,
    }


def _самопроверка():
    измеренное, напечатанное = _строка()
    assert измеренное == 2.82843
    assert напечатанное == 2.82837
    assert abs(_эталон() - _эталон_альт()) < 1e-12
    assert abs(_эталон() - _положительный_контроль()) < 1e-12
    assert abs(_эталон() - _наблюдаемое()) < 2e-6
    assert all(abs(неверный() - _эталон()) > 1e-6 for неверный in _неверные())
    assert family.declared_size(СТАНДАРТНЫЕ_ДИАПАЗОНЫ) == 20412


_самопроверка()

CLAIMS = [
    Claim(
        name="Формула Tsirelson в рукописи Trinity воспроизводит точную квантовую границу",
        source="docs/papers/trinity-sacred-mathematics.tex:1499",
        claim_kind="prediction",
        stated=_заявленное,
        reference=_эталон,
        observed=_наблюдаемое,
        wrong=_неверные(),
        null_model=_положительный_контроль,
        null_expect=_эталон(),
        null_kind="positive",
        tolerance=1.0e-6,
        sample=_выборка,
        statistics={"value": _среднее},
        reference_alt=_эталон_альт,
        alt_tolerance=lambda: max(
            abs(_эталон() - _эталон_альт()) / abs(_эталон()),
            2.0 * math.ulp(_эталон()) / abs(_эталон()),
        ),
        precision=1.0e-15,
        external_target=_внешняя_цель,
        stated_target=_заявленная_внешняя_цель,
        search_size=ПОИСК,
        multiplicity=_множественность,
        mdl=_описание,
        declared_domain=_область,
        arithmetic=_арифметика,
        meff=_эффективное_число,
        algebraic=_алгебраика,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость точной внешней физической формулы",
        observable="вычисленная величина Tsirelson из параметров (8,4,-3,0,-2)",
        measurement_source="точная граница Tsirelson и рукопись Trinity",
        uncertainty_type="exact_identity",
        novelty_key="trinity:sacred_math:tsirelson_exact_external:v1",
        information_class="новый источник и новая категория ошибки точного внешнего эталона",
        purpose="audit",
        models=("формула n·3^k·π^m·φ^p·e^q из рукописи", "точная граница 2√2"),
        independent_of={
            "source": "рукопись Trinity и теорема Tsirelson",
            "observable": "вычисленная строка и точный внешний эталон",
        },
        tests_independent="unknown",
        reason_code_hint="external_mismatch",
        notes=(
            "Наблюдаемое извлечено из столбца Computed. Эталон вычислен из "
            "кортежа (8,4,-3,0,-2), а reference_alt — через логарифмы; "
            "внешняя цель 2√2 хранится отдельно от строки корпуса. "
            "Округление 2,82837 не является самостоятельным подтверждением."
        ),
        skip_reasons={
            "С6": "замкнутая формула, сетка и разрешение не заявлены",
            "С7": "для точной формулы альтернативная оценка не задана",
            "С8": "погрешность исходных физических параметров отсутствует",
            "С9": "конечная выборка для точного тождества неприменима",
            "С10": "одна детерминированная строка не образует выборочную статистику",
            "С11": "проверяется одна внешняя величина",
            "С17": "описание содержит явный рецепт параметров",
            "С18": "пределы семейства проверяются отдельным ситом",
            "С19": "ошибка арифметики double меньше внешнего допуска",
        },
    )
]
