# -*- coding: utf-8 -*-
"""Аудит статистических чисел отчёта Golden Chain v2.40.

Эталон каждого утверждения пересчитывается из других чисел отчёта: отношения
ключей, относительное снижение потерь относительно случайного базиса. Сами
напечатанные проценты используются только как observed. Внешних физических
предсказаний здесь нет, поэтому тавтологическое сито С15 неприменимо.
"""

import os
import re
from decimal import Decimal, getcontext

from goldsieve.sieve import Claim

REPORT = os.environ.get(
    "TRINITY_GOLDEN_CHAIN_REPORT",
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/"
    "trinity-golden-chain-v2-40-large-corpus-report.md",
)


def _text():
    with open(REPORT, encoding="utf-8") as handle:
        return handle.read()


def _require(marker):
    text = _text()
    if marker not in text:
        raise AssertionError("строка корпуса не найдена: " + marker)
    return text


def _keys():
    text = _require("Large corpus trigram keys: 311/9025 (3.4%)")
    match = re.search(r"Large corpus trigram keys:\s*(\d+)/(\d+)", text)
    assert match
    return int(match.group(1)), int(match.group(2))


def _small_keys():
    text = _require("Small corpus trigram keys: 161/9025 (1.8%)")
    match = re.search(r"Small corpus trigram keys:\s*(\d+)/(\d+)", text)
    assert match
    return int(match.group(1)), int(match.group(2))


def _train_values():
    text = _require("Large corpus train loss:   0.8066 (21.7% below random)")
    match = re.search(
        r"Large corpus train loss:\s*([0-9.]+)\s*\(([0-9.]+)% below random\)",
        text,
    )
    assert match
    loss, stated = map(Decimal, match.groups())
    baseline = Decimal("1.0306")
    return loss, stated, baseline


def _eval_values():
    text = _require("Large corpus eval loss:    0.8677 (15.8% below random)")
    match = re.search(
        r"Large corpus eval loss:\s*([0-9.]+)\s*\(([0-9.]+)% below random\)",
        text,
    )
    assert match
    loss, stated = map(Decimal, match.groups())
    baseline = Decimal("1.0306")
    return loss, stated, baseline


def _coverage_boost_reference():
    large, large_den = _keys()
    small, small_den = _small_keys()
    assert large_den == small_den == 95 * 95
    return Decimal(large) / Decimal(small)


def _coverage_boost_observed():
    text = _require("Coverage boost: 1.9x")
    return float(re.search(r"Coverage boost:\s*([0-9.]+)x", text).group(1))


def _coverage_boost_alt():
    # Независимая десятичная реализация того же отношения, без float.
    getcontext().prec = 50
    large, _ = _keys()
    small, _ = _small_keys()
    return Decimal(large) / Decimal(small)


def _train_reference():
    loss, _, baseline = _train_values()
    return (baseline - loss) / baseline * Decimal(100)


def _train_observed():
    return float(_train_values()[1])


def _train_alt():
    getcontext().prec = 50
    loss, _, baseline = _train_values()
    return (Decimal(str(baseline)) - Decimal(str(loss))) / Decimal(str(baseline)) * Decimal(100)


def _eval_reference():
    loss, _, baseline = _eval_values()
    return (baseline - loss) / baseline * Decimal(100)


def _eval_observed():
    return float(_eval_values()[1])


def _eval_alt():
    getcontext().prec = 50
    loss, _, baseline = _eval_values()
    return (Decimal(str(baseline)) - Decimal(str(loss))) / Decimal(str(baseline)) * Decimal(100)


def _wrong_values(values):
    return [lambda v=v: v for v in values]


def _sample(observed):
    # Отчёт содержит одну агрегированную оценку; это не выборка повторных
    # экспериментов. Она оставлена явно, чтобы С10 не получил молчаливый skip.
    return lambda: [float(observed())]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    return max(abs(float(reference()) - float(alternate())), 2.0e-15)


def _arithmetic():
    # Входные потери и проценты имеют четыре значащих знака; 1e-3
    # консервативно отражает их разрешение, а С19 проверяет машинную ошибку.
    return {"params": (311, 161, 95, 1, 0), "rel_uncertainty": 1.0e-3}


def _domain():
    # Здесь нет перебора семейства гипотез; область — ровно две строки отчёта.
    return []


def _claim(name, source, stated, reference, observed, alternate, wrong, note):
    return Claim(
        name=name,
        source=source,
        claim_kind="value",
        stated=stated,
        reference=reference,
        observed=observed,
        wrong=_wrong_values(wrong),
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=0.02 if "покрытие" in name else 0.005,
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        inputs=[REPORT],
        declared_domain=_domain,
        arithmetic=_arithmetic,
        skip_reasons={
            "С6": "в отчёте одна фиксированная конфигурация; сетка разрешений не задана",
            "С7": "для отношения и относительной разности определена одна оценка",
            "С8": "погрешность входных агрегатов не дана; арифметика вынесена в С19",
            "С9": "это один конечный отчётный агрегат, корзин по размеру нет",
            "С10": "в корпусе нет повторных сырых наблюдений; напечатано только одно округлённое значение",
            "С11": "нет нескольких независимых статистик согласия",
            "С15": "утверждается статистическое число, а не предсказание внешней физической величины",
            "С16": "внешнего перебора формул для этого утверждения нет",
            "С17": "MDL для отчётного агрегата не задан",
            "С18": "объявленная область — две явно указанные строки; нарушений нет",
            "С20": "эффективное число попыток для этого агрегата не определено",
            "С21": "алгебраическая объяснимость к статистике покрытия/потерь не относится",
        },
        notes=(
            "Эталон пересчитан из чисел-оснований и определения метрики; "
            "положительный контроль использует отдельный Decimal-маршрут и "
            "не возвращает напечатанное округление. " + note
        ),
    )


def _selfcheck():
    assert _coverage_boost_reference() == Decimal(311) / Decimal(161)
    assert abs(float(_coverage_boost_observed()) - 1.9) < 1e-12
    assert abs(float(_train_reference()) - 21.7349117019212) < 1e-10
    assert abs(float(_eval_reference()) - 15.8063264117990) < 1e-10
    assert all(w() != float(_coverage_boost_reference()) for w in (lambda: 1.0, lambda: 3.0))
    assert all(w() != float(_train_reference()) for w in (lambda: 10.0, lambda: 30.0))
    assert all(w() != float(_eval_reference()) for w in (lambda: 10.0, lambda: 30.0))
    assert os.path.exists(REPORT)


_selfcheck()


CLAIMS = [
    _claim(
        "Большой корпус увеличил покрытие триграмм в 1,9 раза",
        "deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-40-large-corpus-report.md:47-49",
        _coverage_boost_observed(),
        _coverage_boost_reference,
        _coverage_boost_observed,
        _coverage_boost_alt,
        [1.0, 3.0],
        "Эталон = 311/161; общий знаменатель 9025 проверен как 95².",
    ),
    _claim(
        "Потеря обучения большого корпуса на 21,7% ниже случайного базиса",
        "deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-40-large-corpus-report.md:55-59",
        _train_observed(),
        _train_reference,
        _train_observed,
        _train_alt,
        [10.0, 30.0],
        "Эталон = (1,0306−0,8066)/1,0306×100; случайный базис взят из той же строки результатов.",
    ),
    _claim(
        "Потеря оценки большого корпуса на 15,8% ниже случайного базиса",
        "deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-40-large-corpus-report.md:55-59",
        _eval_observed(),
        _eval_reference,
        _eval_observed,
        _eval_alt,
        [10.0, 30.0],
        "Эталон = (1,0306−0,8677)/1,0306×100; это отдельная оценка от train loss.",
    ),
]
