"""Внешняя проверка отношения масс из отдельного научного обзора Trinity."""
import math
import os
import re
import sys

from goldsieve import family, threshold
from goldsieve.sieve import Claim

ИСТОЧНИК = os.environ.get(
    "TRINITY_SCIENTIFIC_OVERVIEW",
    "/home/user/workspace/corpus/trinity/docs/papers/README_FOR_SCIENTISTS.md",
)
ПОИСК = 123201
ДИАПАЗОНЫ = threshold.ACTUAL_RANGES
ФИ = (1.0 + math.sqrt(5.0)) / 2.0

if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _наблюдаемое():
    текст = _текст()
    маркеры = (
        "| m_p / m_e | 6 π⁵ | 1836.15267 | 0.002% | 1836.15267343 |",
        "| 3 | m_p/m_e ratio | 6 π⁵ | 1836.15 | CONSISTENT |",
    )
    if not all(маркер in текст for маркер in маркеры):
        raise AssertionError("строки отношения масс в источнике не найдены")
    совпадение = re.search(r"\| m_p / m_e \| 6 π⁵ \| [^|]+ \| [^|]+ \| ([0-9.]+) \|", текст)
    if совпадение is None:
        raise AssertionError("точное напечатанное значение не найдено")
    # Наблюдение извлечено из строки, а эталон строится отдельным кодовым путём.
    return float(совпадение.group(1))


def _эталон():
    return 6.0 * math.pi**5


def _эталон_альт():
    return math.exp(math.log(6.0) + 5.0 * math.log(math.pi))


def _положительный_контроль():
    return 6.0 * (math.pi * math.pi) * (math.pi * math.pi) * math.pi


def _неверные():
    return [lambda: _эталон() * 1.01, lambda: _эталон() * 0.99]


def _внешняя_цель():
    return {
        "value": 1836.152673426,
        "uncertainty": 3.2e-8,
        "source": "CODATA 2022, https://physics.nist.gov/cuu/pdf/wall_2022.pdf",
    }


def _заявленная_цель():
    return 1836.15267343


def _среднее(values):
    return float(sum(values) / len(values))


def _выборка():
    return [_наблюдаемое()]


def _множественность():
    цель = _внешняя_цель()
    eps = цель["uncertainty"] / abs(цель["value"])
    доля, ожидание = family.empirical_multiplicity(
        (-1, 4), eps, ranges=ДИАПАЗОНЫ, trials=1000, seed=20260818
    )
    return {
        "expected_hits": ожидание, "p_global": доля,
        "fraction_random_targets_hit": доля, "search_size": ПОИСК,
    }


def _значения_семейства():
    цель = _внешняя_цель()
    значения = family.enumerate_family(ДИАПАЗОНЫ)
    return [x for x in значения if цель["value"] / 5.0 <= x <= цель["value"] * 5.0]


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
    return {"description_bits": math.log2(ПОИСК), "match_bits": math.log2(1.0 / (2.0 * eps))}


def _область():
    assert family.declared_size(ДИАПАЗОНЫ) == ПОИСК
    return []


def _арифметика():
    цель = _внешняя_цель()
    return {"params": (6, 0, 5, 0, 0), "rel_uncertainty": цель["uncertainty"] / abs(цель["value"])}


def _алгебраика():
    цель = _внешняя_цель()
    return {
        "target": цель["value"], "coeffs": (6, 0, 5, 0, 0), "has_pi": True,
        "rel_deviation": abs(_эталон() - цель["value"]) / abs(цель["value"]),
        "max_coeff": 6, "free_coeff_limit": 9,
    }


def _самопроверка():
    assert abs(_эталон() - _эталон_альт()) / _эталон() < 1e-12
    assert abs(_эталон() - _положительный_контроль()) / _эталон() < 1e-12
    assert math.isfinite(_наблюдаемое())
    assert abs(_наблюдаемое() - _эталон()) > 1e-6
    assert all(abs(неверный() - _эталон()) > 1e-6 for неверный in _неверные())
    assert family.declared_size(ДИАПАЗОНЫ) == ПОИСК


_самопроверка()

CLAIMS = [
    Claim(
        name="Формула 6π⁵ в научном обзоре воспроизводит отношение масс протона и электрона",
        source="docs/papers/README_FOR_SCIENTISTS.md:38-54",
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
        claim_family="внешняя проверка физической формулы",
        observable="отношение масс протона и электрона",
        measurement_source="научный обзор Trinity и внешний эталон CODATA/NIST",
        uncertainty_type="external_measurement",
        novelty_key="trinity:readme:mp_me_external:v1",
        information_class="новый источник и новая категория риска внешнего утверждения",
        purpose="external_prediction",
        models=("формула 6π⁵", "измерение CODATA/NIST"),
        independent_of={"source": "отдельный научный обзор и CODATA", "observable": "внешнее отношение масс"},
        tests_independent="unknown",
        notes=("Новый источник отделён от ранее проверенных документов. "
               "Публичное число корпуса не используется как эталон; внешняя "
               "цель содержит значение, неопределённость и URL."),
        skip_reasons={
            "С6": "замкнутая формула, сетка сходимости неприменима",
            "С7": "одна внешняя физическая величина",
            "С8": "погрешность входов формулы не заявлена; внешняя проверяется С15",
            "С9": "детерминированная формула",
            "С11": "одна внешняя статистика",
        },
    )
]
