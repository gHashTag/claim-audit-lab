# -*- coding: utf-8 -*-
"""Аудит рецепта gamma_BI по уравнению Мейсснера.

Наблюдаемое извлекается из спецификации корпуса. Эталон Trinity считается
из определения φ⁻³. Внешняя цель считается независимо: корень уравнения
Мейсснера sum_k exp(-πγ√(k(k+2))) = 1/2. Напечатанное число и внешний эталон
не используются как взаимные эталоны.
"""
import math
import os
import re
import sys

from goldsieve import family, threshold
from goldsieve.sieve import Claim

ИСТОЧНИК = os.environ.get(
    "TRINITY_GAMMA_SOURCE",
    "/home/user/workspace/corpus/trinity/specs/physics/gamma_conjecture.t27",
)
ДИАПАЗОНЫ = threshold.ACTUAL_RANGES
РАЗМЕР = family.declared_size(ДИАПАЗОНЫ)

if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("спецификация gamma_conjecture.t27 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _число(имя):
    совпадение = re.search(
        rf"{re.escape(имя)}\s*=\s*([0-9]+\.[0-9]+)", _текст()
    )
    if not совпадение:
        raise AssertionError("число не найдено: " + имя)
    return float(совпадение.group(1))


def _наблюдаемое():
    """Значение γ_phi извлекается из строки constants, без пересчёта."""
    return _число("GAMMA_PHI")


def _заявленное():
    """Эталонное значение формулы вычисляется из определения φ."""
    фи = (1.0 + math.sqrt(5.0)) / 2.0
    return фи ** -3


def _эталон_альт():
    фи = (1.0 + math.sqrt(5.0)) / 2.0
    return math.exp(-3.0 * math.log(фи))


def _сумма_мейсснера(гамма):
    сумма = 0.0
    for k in range(1, 100000):
        член = math.exp(-math.pi * гамма * math.sqrt(k * (k + 2.0)))
        сумма += член
        if член < 1.0e-17:
            break
    return сумма


def _внешний_эталон():
    """Корень независимого уравнения Мейсснера, а не литерал корпуса."""
    низ, верх = 0.20, 0.30
    for _ in range(100):
        середина = (низ + верх) / 2.0
        if _сумма_мейсснера(середина) > 0.5:
            низ = середина
        else:
            верх = середина
    return {
        "value": (низ + верх) / 2.0,
        "uncertainty": 1.0e-12,
        "source": (
            "Meissner, Class. Quantum Grav. 21 (2004), "
            "https://arxiv.org/abs/gr-qc/0407052"
        ),
    }


def _заявленная_внешняя_цель():
    return _число("GAMMA_LQG_MEISSNER")


def _среднее(values):
    return float(sum(values) / len(values))


def _выборка():
    return [_наблюдаемое()]


def _неверные():
    return [
        lambda: _заявленное() * 1.01,
        lambda: _заявленное() * 0.99,
        lambda: _заявленное() + 0.01,
    ]


def _положительный_контроль():
    фи = (1.0 + math.sqrt(5.0)) / 2.0
    return math.exp(-3.0 * math.log(фи))


def _множественность():
    цель = _внешний_эталон()
    относительная = цель["uncertainty"] / abs(цель["value"])
    доля, ожидание = family.empirical_multiplicity(
        (-2, 1), относительная, ranges=ДИАПАЗОНЫ,
        trials=1000, seed=20260817,
    )
    return {
        "expected_hits": ожидание,
        "p_global": доля,
        "fraction_random_targets_hit": доля,
        "search_size": РАЗМЕР,
    }


def _семейство():
    цель = _внешний_эталон()["value"]
    return [
        значение for значение in family.enumerate_family(ДИАПАЗОНЫ)
        if цель / 5.0 <= значение <= цель * 5.0
    ]


def _эффективное_число():
    цель = _внешний_эталон()
    return {
        "values": _семейство(),
        "eps": цель["uncertainty"] / abs(цель["value"]),
        "sigma": abs((_заявленное() - цель["value"]) / цель["uncertainty"]),
        "search_size": РАЗМЕР,
    }


def _описание():
    цель = _внешний_эталон()
    относительная = цель["uncertainty"] / abs(цель["value"])
    return {
        "description_bits": math.log2(РАЗМЕР),
        "match_bits": math.log2(1.0 / (2.0 * относительная)),
    }


def _область():
    assert family.declared_size(ДИАПАЗОНЫ) == 123201
    return []


def _арифметика():
    цель = _внешний_эталон()
    return {
        "params": (1, 0, 0, -3, 0),
        "rel_uncertainty": цель["uncertainty"] / abs(цель["value"]),
    }


def _алгебраика():
    цель = _внешний_эталон()
    return {
        "target": цель["value"],
        "coeffs": (1, 0, 0, -3, 0),
        "has_pi": False,
        "rel_deviation": abs(_заявленное() - цель["value"]) / abs(цель["value"]),
        "max_coeff": 3,
        "free_coeff_limit": 6,
    }


def _самопроверка():
    assert abs(_заявленное() - _наблюдаемое()) < 1.0e-14
    assert abs(_заявленное() - _эталон_альт()) < 1.0e-14
    assert abs(_заявленное() - _положительный_контроль()) < 1.0e-14
    assert abs(_заявленное() - _внешний_эталон()["value"]) > 1.0e-3
    assert all(abs(неверный() - _заявленное()) > 1.0e-5
               for неверный in _неверные())
    assert family.declared_size(ДИАПАЗОНЫ) == 123201
    assert abs(_сумма_мейсснера(_внешний_эталон()["value"]) - 0.5) < 1.0e-12


_самопроверка()

CLAIMS = [
    Claim(
        name="Формула gamma_BI = φ⁻³ согласуется с уравнением Мейсснера",
        source="specs/physics/gamma_conjecture.t27:4-20",
        claim_kind="prediction",
        stated=_заявленное,
        reference=_заявленное,
        observed=_наблюдаемое,
        wrong=_неверные(),
        null_model=_положительный_контроль,
        null_expect=_заявленное(),
        null_kind="positive",
        tolerance=1.0e-12,
        sample=_выборка,
        statistics={"value": _среднее},
        reference_alt=_эталон_альт,
        alt_tolerance=lambda: max(
            abs(_заявленное() - _эталон_альт()) / abs(_заявленное()),
            2.0 * math.ulp(_заявленное()) / abs(_заявленное()),
        ),
        external_target=_внешний_эталон,
        stated_target=_заявленная_внешняя_цель,
        search_size=РАЗМЕР,
        multiplicity=_множественность,
        mdl=_описание,
        declared_domain=_область,
        arithmetic=_арифметика,
        meff=_эффективное_число,
        algebraic=_алгебраика,
        inputs=[ИСТОЧНИК],
        claim_family="внешнее сравнение параметра Барберо–Иммирци",
        observable="GAMMA_PHI из спецификации и корень уравнения Мейсснера",
        measurement_source="спецификация Trinity и независимое уравнение Мейсснера",
        uncertainty_type="external_exact_recipe",
        novelty_key="trinity:gamma_bi:meissner_equation:v1",
        information_class="новый источник и новая категория ошибки рецепта внешнего эталона",
        purpose="audit",
        models=("формула φ⁻³", "уравнение Мейсснера с суммой по k"),
        independent_of={
            "source": "спецификация Trinity и публикация Мейсснера",
            "observable": "константа GAMMA_PHI и независимо вычисленный корень",
        },
        tests_independent="unknown",
        reason_code_hint="external_mismatch",
        notes=(
            "Наблюдаемое извлечено из GAMMA_PHI. Эталон φ⁻³ вычисляется из φ, "
            "reference_alt использует логарифм и экспоненту. Внешняя цель "
            "вычисляется бисекцией корня суммы Мейсснера; число из корпуса "
            "не используется как внешний эталон."
        ),
        skip_reasons={
            "С6": "замкнутая формула и ряд с контролируемой сходимостью",
            "С7": "единственная законная оценка корня заданного уравнения",
            "С8": "погрешность формулы не задана; внешняя точность проверяется С15",
            "С9": "внешний эталон вычисляется из сходящегося ряда",
            "С10": "одна детерминированная формула не образует выборочную статистику",
            "С11": "проверяется одна внешняя величина",
            "С17": "полный рецепт уравнения и диапазон суммы объявлены",
            "С18": "границы семейства проверены отдельным ситом",
            "С19": "численная ошибка корня ограничена проверкой остатка",
        },
    )
]
