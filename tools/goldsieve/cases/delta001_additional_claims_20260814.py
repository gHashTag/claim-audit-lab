# -*- coding: utf-8 -*-
"""Дополнительный аудит числовых утверждений DELTA-001.

Числа из отчёта используются только как observed. Эталон для ранга
пересчитывается по определённому в исходном анализе критерию дисперсии, а
эталон для числа совпадений — по формулам, выписанным в таблице. Сверка
напечатанного числа с самим собой не используется.
"""

import math
import os

import mpmath

from goldsieve.sieve import Claim


REPORT = os.environ.get(
    "TRINITY_DELTA001_REPORT",
    "/home/user/workspace/corpus/trinity/docs/docs/research/delta-001/phase4-consistency.md",
)
SOURCE_CODE = "/home/user/workspace/corpus/trinity/src/gravity/delta_001_phase2_numerical.zig"


def _text():
    with open(REPORT, encoding="utf-8") as handle:
        return handle.read()


def _require(marker):
    if marker not in _text():
        raise AssertionError("строка корпуса не найдена: " + marker)


def _phi():
    return (1.0 + math.sqrt(5.0)) / 2.0


def _gamma_trinity():
    return _phi() ** -3


def _candidates():
    return [
        0.200,
        0.210,
        0.220,
        0.230,
        _gamma_trinity(),
        0.240,
        0.250,
        0.260,
        0.270,
        0.274,
        0.280,
        0.290,
        0.300,
    ]


def _spacing_variance(gamma):
    spins = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    gaps = [
        gamma * (
            math.sqrt(j2 * (j2 + 1.0)) - math.sqrt(j1 * (j1 + 1.0))
        )
        for j1, j2 in zip(spins, spins[1:])
    ]
    mean = sum(gaps) / len(gaps)
    return sum((value - mean) ** 2 for value in gaps) / len(gaps)


def _reference_rank_0274():
    target = 0.274
    target_variance = _spacing_variance(target)
    return 1 + sum(
        _spacing_variance(candidate) < target_variance
        for candidate in _candidates()
    )


def _observed_rank_0274():
    _require("| **Spectral variance** | 5/13 | 10/13 | **1/13** ⭐ | γ = 0.200 |")
    return 10


def _reference_rank_0274_alt():
    mp = mpmath.mp
    old_dps = mp.dps
    mp.dps = 80
    try:
        spins = [mp.mpf("0.5"), mp.mpf("1"), mp.mpf("1.5"),
                 mp.mpf("2"), mp.mpf("2.5"), mp.mpf("3")]
        values = [
            mp.mpf("0.200"), mp.mpf("0.210"), mp.mpf("0.220"),
            mp.mpf("0.230"), ((mp.mpf(1) + mp.sqrt(5)) / 2) ** -3,
            mp.mpf("0.240"), mp.mpf("0.250"), mp.mpf("0.260"),
            mp.mpf("0.270"), mp.mpf("0.274"), mp.mpf("0.280"),
            mp.mpf("0.290"), mp.mpf("0.300"),
        ]

        def variance(gamma):
            gaps = [
                gamma * (
                    mp.sqrt(j2 * (j2 + 1)) - mp.sqrt(j1 * (j1 + 1))
                )
                for j1, j2 in zip(spins, spins[1:])
            ]
            mean = sum(gaps) / len(gaps)
            return sum((value - mean) ** 2 for value in gaps) / len(gaps)

        target_variance = variance(mp.mpf("0.274"))
        return 1 + sum(variance(candidate) < target_variance for candidate in values)
    finally:
        mp.dps = old_dps


def _strong_count():
    phi = _phi()
    pairs = [
        (math.sqrt(8.0 / 3.0), phi),
        (
            math.sqrt(0.5 * 1.5) / math.sqrt(1.0 * 2.0),
            phi ** -1,
        ),
    ]
    return sum(abs(value - target) / abs(target) < 0.01
               for value, target in pairs)


def _observed_strong_count():
    _require("**Total strong coincidences: 2**")
    return 2


def _strong_count_alt():
    mp = mpmath.mp
    old_dps = mp.dps
    mp.dps = 80
    try:
        phi = (mp.mpf(1) + mp.sqrt(5)) / 2
        pairs = [
            (mp.sqrt(mp.mpf(8) / 3), phi),
            (
                mp.sqrt(mp.mpf("0.5") * mp.mpf("1.5"))
                / mp.sqrt(mp.mpf(1) * 2),
                phi ** -1,
            ),
        ]
        return sum(abs(value - target) / abs(target) < mp.mpf("0.01")
                   for value, target in pairs)
    finally:
        mp.dps = old_dps


def _weak_count():
    # Формулы берутся из строк таблицы, а не из её напечатанных значений.
    phi_inv = _phi() ** -1
    pairs = [
        (
            math.sqrt(1.5 * 2.5) / math.sqrt(2.0 * 3.0),
            phi_inv,
        ),
        (
            math.sqrt(2.0 * 3.0) / math.sqrt(2.5 * 3.5),
            phi_inv,
        ),
    ]
    return sum(
        0.01 <= abs(value - target) / abs(target) < 0.05
        for value, target in pairs
    )


def _observed_weak_count():
    _require("**Total weak coincidences: 2 (both are actually > 95% error, essentially meaningless)**")
    return 2


def _weak_count_alt():
    mp = mpmath.mp
    old_dps = mp.dps
    mp.dps = 80
    try:
        phi_inv = ((mp.mpf(1) + mp.sqrt(5)) / 2) ** -1
        pairs = [
            (
                mp.sqrt(mp.mpf("1.5") * mp.mpf("2.5"))
                / mp.sqrt(mp.mpf(2) * 3),
                phi_inv,
            ),
            (
                mp.sqrt(mp.mpf(2) * 3)
                / mp.sqrt(mp.mpf("2.5") * mp.mpf("3.5")),
                phi_inv,
            ),
        ]
        return sum(
            mp.mpf("0.01") <= abs(value - target) / abs(target)
            < mp.mpf("0.05")
            for value, target in pairs
        )
    finally:
        mp.dps = old_dps


def _sample(observed):
    return lambda: [observed()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tolerance(reference, alternate):
    first = float(reference())
    second = float(alternate())
    return max(abs(first - second), 2.0 * math.ulp(first))


def _arithmetic():
    return {
        "params": (1, 0, 0, 0, 0),
        "rel_uncertainty": 1.0e-15,
    }


def _domain():
    assert len(_candidates()) == 13
    return []


def _claim(name, source, reference, observed, alternate, wrong, notes):
    return Claim(
        name=name,
        source=source,
        claim_kind="statistical",
        stated=observed,
        reference=reference,
        observed=observed,
        wrong=wrong,
        null_model=alternate,
        null_expect=reference(),
        null_kind="positive",
        tolerance=1.0e-12,
        sample=_sample(observed),
        statistics={"value": _mean},
        reference_alt=alternate,
        alt_tolerance=lambda: _alt_tolerance(reference, alternate),
        inputs=[REPORT, SOURCE_CODE],
        declared_domain=_domain,
        arithmetic=_arithmetic,
        skip_reasons={
            "С6": "статистика задана конечным списком формул, сетки нет",
            "С7": "законная оценка единственна: точный счёт по объявленным формулам",
            "С8": "входные формулы точные; арифметическая устойчивость вынесена в С19",
            "С9": "это полный конечный список строк таблицы, а не выборка",
            "С11": "утверждается один счёт, независимых статистик нет",
            "С15": "это статистическое утверждение, а не предсказание физической величины",
            "С16": "множественность внешнего семейства формул не является частью счёта строк",
            "С17": "MDL для счёта категорий не определён",
            "С18": "границы перебора корпуса не являются частью утверждения",
            "С20": "эффективное число попыток для локального списка не задано",
            "С21": "алгебраическая объяснимость не является частью утверждения о счёте",
        },
        notes=(
            "Эталон пересчитан из формул и определения критерия; положительный "
            "контроль использует mpmath и не возвращает число из корпуса. " + notes
        ),
    )


def _selfcheck():
    assert _reference_rank_0274() == 10
    assert _reference_rank_0274_alt() == 10
    assert _strong_count() == 2
    assert _strong_count_alt() == 2
    assert _weak_count() == 0
    assert _weak_count_alt() == 0
    assert all(w() != _reference_rank_0274() for w in [lambda: 1, lambda: 5, lambda: 13])
    assert all(w() != _strong_count() for w in [lambda: 0, lambda: 1, lambda: 3])
    assert all(w() != _weak_count() for w in [lambda: 1, lambda: 3, lambda: 4])
    assert os.path.exists(REPORT)
    assert os.path.exists(SOURCE_CODE)


_selfcheck()


CLAIMS = [
    _claim(
        "γ = 0,274 занимает 10-е место из 13 по спектральной дисперсии",
        "docs/docs/research/delta-001/phase4-consistency.md:63-88",
        _reference_rank_0274,
        _observed_rank_0274,
        _reference_rank_0274_alt,
        [lambda: 1, lambda: 5, lambda: 13],
        "Проверяется именно ранг γ=0,274, а не напечатанное значение дисперсии.",
    ),
    _claim(
        "В таблице DELTA-001 две сильные φ-коинциденции с ошибкой менее 1%",
        "docs/docs/research/delta-001/phase4-consistency.md:23-31",
        _strong_count,
        _observed_strong_count,
        _strong_count_alt,
        [lambda: 0, lambda: 1, lambda: 3],
        "Порог 1% применён к двум формульным парам из таблицы.",
    ),
    _claim(
        "В таблице DELTA-001 две слабые φ-коинциденции с ошибкой 1–5%",
        "docs/docs/research/delta-001/phase4-consistency.md:32-41",
        _weak_count,
        _observed_weak_count,
        _weak_count_alt,
        [lambda: 1, lambda: 3, lambda: 4],
        "Диапазон 1–5% пересчитан по формулам строк; их напечатанные значения не используются.",
    ),
]
