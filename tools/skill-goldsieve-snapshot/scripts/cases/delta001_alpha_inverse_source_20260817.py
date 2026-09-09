# -*- coding: utf-8 -*-
"""Аудит записи DELTA-001 о формуле обратной постоянной тонкой структуры."""
import math
import os
import re
import sys

from goldsieve import family
from goldsieve.sieve import Claim
from goldsieve import threshold

ИСТОЧНИК = os.environ.get(
    "TRINITY_DELTA001_ALPHA",
    "/home/user/workspace/corpus/trinity/.trinity/experience/DELTA-001.md",
)
ПОИСК = 123201
ДИАПАЗОНЫ = threshold.ACTUAL_RANGES
ФИ = (1.0 + math.sqrt(5.0)) / 2.0

if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("источник DELTA-001 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _наблюдаемое():
    """Извлечь напечатанное значение α⁻¹, не вычисляя его из формулы."""
    совпадение = re.search(
        r"α⁻¹_measured\s*=\s*([0-9]+\.[0-9]+)",
        _текст(),
    )
    if not совпадение:
        raise AssertionError("напечатанное измерение α⁻¹ не найдено")
    return float(совпадение.group(1))


def _эталон():
    """Обратная величина вычисляемой в источнике формулы α."""
    альфа = 4.0 * ФИ ** 2 / (9.0 * math.pi ** 2)
    return 1.0 / альфа


def _эталон_альт():
    """Независимая логарифмическая сборка обратной величины."""
    return math.exp(
        math.log(9.0)
        + 2.0 * math.log(math.pi)
        - math.log(4.0)
        - 2.0 * math.log(ФИ)
    )


def _положительный_контроль():
    """Контроль вычисляет ту же формулу в ином порядке операций."""
    return 9.0 * math.pi ** 2 / (4.0 * ((1.0 + math.sqrt(5.0)) / 2.0) ** 2)


def _неверные():
    return [
        lambda: _эталон() * 1.5,
        lambda: _эталон() * 0.5,
        lambda: _эталон() + 1.0,
    ]


def _среднее(values):
    return float(sum(values) / len(values))


def _выборка():
    return [_наблюдаемое()]


def _внешняя_цель():
    return {
        "value": 137.035999084,
        "uncertainty": 0.000000021,
        "source": (
            "CODATA 2022, постоянная тонкой структуры, "
            "https://physics.nist.gov/cuu/pdf/wall_2022.pdf"
        ),
    }


def _заявленная_цель():
    return 137.036000


def _множественность():
    цель = _внешняя_цель()
    eps = цель["uncertainty"] / abs(цель["value"])
    доля, ожидание = family.empirical_multiplicity(
        (-2, 1), eps, ranges=ДИАПАЗОНЫ, trials=1000, seed=20260817
    )
    return {
        "expected_hits": ожидание,
        "p_global": доля,
        "fraction_random_targets_hit": доля,
        "search_size": ПОИСК,
    }


def _значения_семейства():
    цель = _внешняя_цель()
    значения = family.enumerate_family(ДИАПАЗОНЫ)
    нижняя, верхняя = цель["value"] / 5.0, цель["value"] * 5.0
    return [значение for значение in значения if нижняя <= значение <= верхняя]


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
    assert family.declared_size(ДИАПАЗОНЫ) == ПОИСК
    return []


def _арифметика():
    цель = _внешняя_цель()
    return {
        "params": (4, 0, -2, 2, 0),
        "rel_uncertainty": цель["uncertainty"] / abs(цель["value"]),
    }


def _алгебраика():
    цель = _внешняя_цель()
    return {
        "target": цель["value"],
        "coeffs": (4, 0, -2, 2, 0),
        "has_pi": True,
        "rel_deviation": abs(_эталон() - цель["value"]) / abs(цель["value"]),
        "max_coeff": 9,
        "free_coeff_limit": 6,
    }


def _код_причины():
    return "observation_mismatch"


def _самопроверка():
    assert abs(_эталон() - _эталон_альт()) < 1e-12
    assert abs(_эталон() - _положительный_контроль()) < 1e-12
    assert abs(_эталон() - _наблюдаемое()) > 1.0
    assert all(abs(неверный() - _эталон()) > 1e-6 for неверный in _неверные())
    assert family.declared_size(ДИАПАЗОНЫ) == ПОИСК


_самопроверка()

CLAIMS = [
    Claim(
        name="Сводка DELTA-001 ошибочно заявляет воспроизведение обратной постоянной тонкой структуры",
        source=".trinity/experience/DELTA-001.md:43-47",
        claim_kind="prediction",
        stated=_заявленная_цель,
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
        external_target=_внешняя_цель,
        stated_target=_заявленная_цель,
        search_size=ПОИСК,
        multiplicity=_множественность,
        mdl=_описание,
        declared_domain=_область,
        arithmetic=_арифметика,
        meff=_эффективное_число,
        algebraic=_алгебраика,
        inputs=[ИСТОЧНИК],
        claim_family="воспроизводимость обратной постоянной тонкой структуры",
        observable="напечатанное α⁻¹ и формула α = 4φ²/(9π²)",
        measurement_source="сводка DELTA-001 и CODATA 2022",
        uncertainty_type="external_measurement",
        novelty_key="trinity:delta001:alpha_inverse:independent_source:v1",
        information_class="новый источник и новая категория ошибки инвертирования величины",
        purpose="audit",
        models=("формула и α⁻¹ из сводки DELTA-001", "независимый пересчёт обратной величины"),
        independent_of={
            "source": "сводка DELTA-001 и CODATA",
            "observable": "формула α и напечатанная α⁻¹",
        },
        tests_independent="unknown",
        reason_code_hint=_код_причины(),
        notes=(
            "Наблюдаемое извлечено из строки α⁻¹_measured. Эталон вычислен "
            "из формулы α, а внешняя цель CODATA хранится отдельно; число "
            "из соседней строки не используется как эталон."
        ),
        skip_reasons={
            "С6": "замкнутая формула, сетки и разрешения неприменимы",
            "С7": "один законный оцениватель, альтернативные оценки не заданы",
            "С8": "погрешность формулы не задана; внешняя погрешность проверяется С15",
            "С9": "детерминированная формула, конечная выборка неприменима",
            "С11": "одна внешняя статистика, сравнение нескольких статистик неприменимо",
        },
    )
]
