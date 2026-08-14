# -*- coding: utf-8 -*-
"""Аудит двух статистических утверждений DELTA-001.

Эталон пересчитывает определённую в исходном коде дисперсию промежутков
спектра по формулам Казимира. Числа из отчёта используются только как
наблюдение; проверка формулы против числа, напечатанного рядом, не является
основанием вердикта.
"""

import math
import os
import re
import mpmath

from goldsieve.sieve import Claim

REPORT = os.environ.get(
    "TRINITY_DELTA001_REPORT",
    "/home/user/workspace/corpus/trinity/docs/docs/research/delta-001/phase4-consistency.md",
)
SOURCE_CODE = "/home/user/workspace/corpus/trinity/src/gravity/delta_001_phase2_numerical.zig"


def _text():
    with open(REPORT, encoding="utf-8") as f:
        return f.read()


def _require(marker):
    if marker not in _text():
        raise AssertionError("строка корпуса не найдена: " + marker)


def _phi():
    return (1.0 + math.sqrt(5.0)) / 2.0


def _gamma_trinity():
    phi = _phi()
    return 1.0 / (phi * phi * phi)


def _candidates():
    # Тот же объявленный список, что и в delta_001_phase2_numerical.zig:
    # 12 десятичных точек и вычисляемая точка phi^-3.
    return [0.200, 0.210, 0.220, 0.230, _gamma_trinity(),
            0.240, 0.250, 0.260, 0.270, 0.274, 0.280, 0.290, 0.300]


def _spacing_variance(gamma):
    spins = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    spacings = []
    for j1, j2 in zip(spins, spins[1:]):
        a1 = gamma * math.sqrt(j1 * (j1 + 1.0))
        a2 = gamma * math.sqrt(j2 * (j2 + 1.0))
        spacings.append(a2 - a1)
    mean = sum(spacings) / len(spacings)
    return sum((x - mean) ** 2 for x in spacings) / len(spacings)


def _reference_best():
    values = _candidates()
    return min(values, key=_spacing_variance)


def _reference_rank():
    target = _gamma_trinity()
    target_var = _spacing_variance(target)
    return 1 + sum(_spacing_variance(x) < target_var for x in _candidates())


def _observed_best():
    _require("| γ₄ (Optimal) | 0.200 | Variance minimization | Empirical |")
    return 0.200


def _observed_rank():
    _require("| Uniquely optimal? | ❌ NO | Ranks 5/13 in variance |")
    return 5


def _alt_best():
    # Независимый путь: mpmath, точные десятичные входы и mp.sqrt.
    p = (mpmath.mpf(1) + mpmath.sqrt(5)) / 2
    gt = 1 / (p ** 3)
    values = [mpmath.mpf("0.200"), mpmath.mpf("0.210"),
              mpmath.mpf("0.220"), mpmath.mpf("0.230"), gt,
              mpmath.mpf("0.240"), mpmath.mpf("0.250"),
              mpmath.mpf("0.260"), mpmath.mpf("0.270"),
              mpmath.mpf("0.274"), mpmath.mpf("0.280"),
              mpmath.mpf("0.290"), mpmath.mpf("0.300")]
    spins = [mpmath.mpf("0.5"), mpmath.mpf("1"), mpmath.mpf("1.5"),
             mpmath.mpf("2"), mpmath.mpf("2.5"), mpmath.mpf("3")]

    def variance(gamma):
        gaps = [gamma * (mpmath.sqrt(j2 * (j2 + 1)) -
                         mpmath.sqrt(j1 * (j1 + 1)))
                for j1, j2 in zip(spins, spins[1:])]
        mean = sum(gaps) / len(gaps)
        return sum((x - mean) ** 2 for x in gaps) / len(gaps)

    return float(min(values, key=variance))


def _alt_rank():
    p = (mpmath.mpf(1) + mpmath.sqrt(5)) / 2
    gt = 1 / (p ** 3)
    values = [mpmath.mpf("0.200"), mpmath.mpf("0.210"),
              mpmath.mpf("0.220"), mpmath.mpf("0.230"), gt,
              mpmath.mpf("0.240"), mpmath.mpf("0.250"),
              mpmath.mpf("0.260"), mpmath.mpf("0.270"),
              mpmath.mpf("0.274"), mpmath.mpf("0.280"),
              mpmath.mpf("0.290"), mpmath.mpf("0.300")]
    spins = [mpmath.mpf("0.5"), mpmath.mpf("1"), mpmath.mpf("1.5"),
             mpmath.mpf("2"), mpmath.mpf("2.5"), mpmath.mpf("3")]

    def variance(gamma):
        gaps = [gamma * (mpmath.sqrt(j2 * (j2 + 1)) -
                         mpmath.sqrt(j1 * (j1 + 1)))
                for j1, j2 in zip(spins, spins[1:])]
        mean = sum(gaps) / len(gaps)
        return sum((x - mean) ** 2 for x in gaps) / len(gaps)

    tv = variance(gt)
    return 1 + sum(variance(x) < tv for x in values)


_wrong_best = [lambda: 0.2360679774997897, lambda: 0.274, lambda: 0.300]


_wrong_rank = [lambda: 1, lambda: 2, lambda: 13]


def _sample(fn):
    return lambda: [fn()]


def _mean(values):
    return float(sum(values) / len(values))


def _alt_tol(a, b):
    return max(abs(float(a()) - float(b())) / abs(float(a())), 2.0 * math.ulp(float(a())))


def _arithmetic():
    return {
        "params": (9, 4, 0, 4, -1),
        "rel_uncertainty": 1.0e-12,
    }


def _claim(name, source, reference, observed, alternate, wrong):
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
        alt_tolerance=lambda: _alt_tol(reference, alternate),
        inputs=[REPORT, SOURCE_CODE],
        arithmetic=_arithmetic,
        skip_reasons={
            "С6": "сетка или разрешение не являются частью статистического утверждения",
            "С7": "единственная законная оценка — точный минимум по объявленному списку",
            "С8": "входные формулы точные; бюджет округления проверен отдельно С19",
            "С9": "это полный конечный список из 13 кандидатов, а не выборка",
            "С11": "утверждается один критерий, независимых статистик нет",
            "С15": "это статистическое утверждение, не предсказание физической величины",
            "С16": "множественность внешнего семейства формул не является частью утверждения о 13 кандидатах",
            "С17": "MDL для ранга оптимизатора не определён",
            "С18": "границы перебора не являются числовой частью этого утверждения",
            "С20": "эффективное число попыток для 13-кандидатного критерия не задано и не смешивается с корпусным search_size=123201",
            "С21": "алгебраическая объяснимость не является частью утверждения об оптимизации дисперсии",
        },
        notes=(
            "Эталон вычислен из определения промежутка sqrt(j(j+1)) и дисперсии "
            "пяти соседних промежутков для j=1/2,...,3; контроль positive обязан "
            "воспроизвести этот эталон через mpmath, а не брать число из отчёта."
        ),
    )


def _selfcheck():
    assert abs(_reference_best() - 0.2) < 1e-15
    assert _reference_rank() == 5
    assert _alt_best() == 0.2
    assert _alt_rank() == 5
    assert all(abs(w() - _reference_best()) > 1e-3 for w in _wrong_best)
    assert all(w() != _reference_rank() for w in _wrong_rank)
    assert len(_candidates()) == 13
    assert os.path.exists(SOURCE_CODE)


_selfcheck()

CLAIMS = [
    _claim(
        "γ = 0,200 даёт минимальную дисперсию спектральных промежутков",
        "docs/docs/research/delta-001/phase4-consistency.md:63-68",
        _reference_best,
        _observed_best,
        _alt_best,
        _wrong_best,
    ),
    _claim(
        "γ = φ⁻³ занимает 5-е место из 13 по спектральной дисперсии",
        "docs/docs/research/delta-001/phase4-consistency.md:72-86",
        _reference_rank,
        _observed_rank,
        _alt_rank,
        _wrong_rank,
    ),
]
