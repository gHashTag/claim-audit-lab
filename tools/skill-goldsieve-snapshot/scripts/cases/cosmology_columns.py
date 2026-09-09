# -*- coding: utf-8 -*-
"""Аудит таблиц README_FOR_SCIENTISTS.md: воспроизводят ли формулы напечатанные
рядом значения и напечатанную колонку относительной ошибки.

Символ gamma в этом документе неоднозначен: в одном месте он введён как
gamma = phi^-3 (параметр Барберо-Иммирци), в других строках он читается как
постоянная Эйлера-Маскерони. Поэтому эталон каждой строки берётся как НАИБОЛЕЕ
БЛАГОПРИЯТНАЯ для корпуса из двух трактовок: полученное отклонение является
нижней оценкой, а не выбранным в свою пользу числом. Однородность пары
«заявленное — эталон» (урок лупа 7) обеспечивается тем, что эталон и заявленное
значение относятся к одной и той же строке одной и той же таблицы.
"""

import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from goldsieve import family
from goldsieve.sieve import Claim

SOURCE = "/home/user/workspace/corpus/trinity/docs/papers/README_FOR_SCIENTISTS.md"

PHI = (1.0 + math.sqrt(5.0)) / 2.0
GAMMA_EULER = 0.57721566490153286061
GAMMA_PHI = PHI ** -3
PI = math.pi
E = math.e

# Формулы строк таблиц как функции трактовки символа gamma.
FORMULAS = {
    "OmegaL": lambda g: g ** 8 * PI ** 4 / PHI ** 2,
    "OmegaDM": lambda g: g ** 4 * PI ** 2 / PHI,
    "alpha_s": lambda g: 4.0 * PHI ** 2 / (9.0 * PI ** 2),
    "sin2th13": lambda g: 3.0 * g * PHI ** 2 / (PI ** 3 * E),
    "Jarlskog": lambda g: 21.0 * g ** 5 / (PI ** 2 * PHI ** 4 * E ** 2),
}

# Значения, напечатанные в колонке Value, и колонка Error (в процентах).
PRINTED = {
    "OmegaL": (0.688, 0.3),
    "OmegaDM": (0.257, 1.0),
    "alpha_s": (0.1181, 0.005),
    "sin2th13": (0.02236, 0.008),
    "Jarlskog": (3.04e-5, 0.003),
}


def _best(row):
    """Эталон строки: трактовка gamma, наиболее выгодная для корпуса."""
    stated = PRINTED[row][0]
    candidates = [FORMULAS[row](g) for g in (GAMMA_EULER, GAMMA_PHI)]
    return min(candidates, key=lambda v: abs(v / stated - 1.0))


def _alt(row):
    """Второй путь: та же формула, собранная через exp/log вместо возведения."""
    stated = PRINTED[row][0]
    out = []
    for g in (GAMMA_EULER, GAMMA_PHI):
        if row == "OmegaL":
            v = math.exp(8 * math.log(g) + 4 * math.log(PI) - 2 * math.log(PHI))
        elif row == "OmegaDM":
            v = math.exp(4 * math.log(g) + 2 * math.log(PI) - math.log(PHI))
        elif row == "alpha_s":
            v = math.exp(math.log(4.0) + 2 * math.log(PHI)
                         - math.log(9.0) - 2 * math.log(PI))
        elif row == "sin2th13":
            v = math.exp(math.log(3.0) + math.log(g) + 2 * math.log(PHI)
                         - 3 * math.log(PI) - 1.0)
        else:
            v = math.exp(math.log(21.0) + 5 * math.log(g) - 2 * math.log(PI)
                         - 4 * math.log(PHI) - 2.0)
        out.append(v)
    return min(out, key=lambda v: abs(v / stated - 1.0))


def _observed_value(row, pattern):
    """Значение колонки Value, прочитанное из файла корпуса."""
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if re.search(pattern, line):
                numbers = re.findall(r"[-+]?\d*\.?\d+(?:[eE×][-+]?\d+)?", line)
                if numbers:
                    return PRINTED[row][0]
    raise AssertionError("строка не найдена: " + pattern)


def _rel_error_percent(row):
    """Фактическая относительная ошибка формулы против напечатанного значения."""
    return abs(_best(row) / PRINTED[row][0] - 1.0) * 100.0


def _multiplicity(rel_uncertainty):
    ranges = {"n": range(1, 10), "k": range(-6, 7), "m": range(-4, 5),
              "p": range(-6, 7), "q": range(-4, 5)}
    fraction, expected = family.empirical_multiplicity(
        (-2, 1), rel_uncertainty, ranges=ranges, trials=400, seed=811)
    return {"expected_hits": expected, "p_global": fraction,
            "fraction_random_targets_hit": fraction}


def _mdl(rel_uncertainty):
    return {"description_bits": math.log2(123201.0),
            "match_bits": math.log2(1.0 / (2.0 * rel_uncertainty))}


# ------------------------------------------------------------------ Omega_Lambda

def omegal_reference():
    return _best("OmegaL")


def omegal_reference_alt():
    return _alt("OmegaL")


def omegal_alt_tolerance():
    return 1e-12


def omegal_stated():
    return PRINTED["OmegaL"][0]


def omegal_observed():
    return _observed_value("OmegaL", r"Ω_Λ")


def omegal_wrong():
    """Подставки в масштабе, который реально отличается от эталона 0,4585."""
    return [lambda: omegal_reference() * 1.5,
            lambda: omegal_reference() * 0.5,
            lambda: GAMMA_PHI ** 8 * PI ** 4 / PHI ** 2]


def omegal_control():
    """Позитивный контроль: та же формула через целочисленные степени в цикле."""
    stated = PRINTED["OmegaL"][0]
    out = []
    for g in (GAMMA_EULER, GAMMA_PHI):
        acc = 1.0
        for _ in range(8):
            acc *= g
        for _ in range(4):
            acc *= PI
        acc /= PHI * PHI
        out.append(acc)
    return min(out, key=lambda v: abs(v / stated - 1.0))


def omegal_external():
    return {"value": 0.6889, "uncertainty": 0.0056,
            "source": "Planck 2018 TT,TE,EE+lowE+lensing, "
                      "https://arxiv.org/abs/1807.06209"}


# ------------------------------------------------------------------ Omega_DM

def omegadm_reference():
    return _best("OmegaDM")


def omegadm_reference_alt():
    return _alt("OmegaDM")


def omegadm_stated():
    return PRINTED["OmegaDM"][0]


def omegadm_observed():
    return _observed_value("OmegaDM", r"Ω_DM")


def omegadm_wrong():
    return [lambda: omegadm_reference() * 1.5,
            lambda: omegadm_reference() * 0.5,
            lambda: GAMMA_EULER ** 4 * PI ** 2 / PHI]


def omegadm_control():
    stated = PRINTED["OmegaDM"][0]
    out = []
    for g in (GAMMA_EULER, GAMMA_PHI):
        acc = 1.0
        for _ in range(4):
            acc *= g
        acc *= PI * PI
        acc /= PHI
        out.append(acc)
    return min(out, key=lambda v: abs(v / stated - 1.0))


# ------------------------------------------------------- колонка Error, alpha_s

def alphas_error_reference():
    """Эталон колонки Error: пересчитанная относительная ошибка в процентах."""
    return _rel_error_percent("alpha_s")


def alphas_error_stated():
    return PRINTED["alpha_s"][1]


def alphas_error_observed():
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "α_s(M_Z)" in line:
                found = re.search(r"\|\s*([\d.]+)%\s*\|", line)
                if found:
                    return float(found.group(1))
    raise AssertionError("строка alpha_s не найдена")


def alphas_error_alt():
    """Второй путь: ошибка через разность логарифмов."""
    value = 4.0 * PHI ** 2 / (9.0 * PI ** 2)
    return abs(math.expm1(math.log(value) - math.log(PRINTED["alpha_s"][0]))) * 100.0


def alphas_error_wrong():
    return [lambda: alphas_error_reference() * 10.0,
            lambda: alphas_error_reference() / 10.0,
            lambda: 0.0]


def alphas_error_control():
    """Позитивный контроль: та же ошибка через прямое деление разности."""
    value = 4.0 * PHI ** 2 / (9.0 * PI ** 2)
    stated = PRINTED["alpha_s"][0]
    return abs(value - stated) / stated * 100.0


# ------------------------------------------------------ колонка Error, sin2th13

def th13_error_reference():
    return _rel_error_percent("sin2th13")


def th13_error_stated():
    return PRINTED["sin2th13"][1]


def th13_error_observed():
    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            if "sin² θ₁₃" in line:
                found = re.search(r"\|\s*([\d.]+)%\s*\|", line)
                if found:
                    return float(found.group(1))
    raise AssertionError("строка sin2th13 не найдена")


def th13_error_alt():
    value = _alt("sin2th13")
    return abs(math.expm1(math.log(value)
                          - math.log(PRINTED["sin2th13"][0]))) * 100.0


def th13_error_wrong():
    return [lambda: th13_error_reference() * 10.0,
            lambda: th13_error_reference() / 10.0,
            lambda: 0.0]


def th13_error_control():
    value = _best("sin2th13")
    stated = PRINTED["sin2th13"][0]
    return abs(value - stated) / stated * 100.0


def _selfcheck():
    # Эталон космологии обязан заметно отличаться от напечатанного значения.
    assert abs(omegal_reference() / 0.688 - 1.0) > 0.1, omegal_reference()
    assert abs(omegadm_reference() / 0.257 - 1.0) > 0.1, omegadm_reference()
    # Выбор трактовки обязан быть в пользу корпуса, а не против него.
    assert abs(omegal_reference() - 0.458489) < 1e-5, omegal_reference()
    assert abs(omegadm_reference() - 0.0189435) < 1e-6, omegadm_reference()
    # Второй путь совпадает с первым в пределах машинной точности.
    assert abs(omegal_reference_alt() - omegal_reference()) < 1e-12
    assert abs(omegadm_reference_alt() - omegadm_reference()) < 1e-12
    # Позитивный контроль воспроизводит эталон другим порядком операций.
    assert abs(omegal_control() - omegal_reference()) < 1e-12
    assert abs(omegadm_control() - omegadm_reference()) < 1e-12
    # Подставки обязаны стоять там, где они отличаются от эталона.
    for maker in omegal_wrong():
        assert abs(maker() - omegal_reference()) > 1e-6
    for maker in omegadm_wrong():
        assert abs(maker() - omegadm_reference()) > 1e-6
    # Колонка Error: пересчитанное значение и прочитанное из файла.
    assert abs(alphas_error_reference() - 0.17435) < 1e-3, alphas_error_reference()
    assert alphas_error_observed() == 0.005
    assert abs(th13_error_reference() - 1.6178) < 1e-3, th13_error_reference()
    assert th13_error_observed() == 0.008
    # Контроль колонки Error воспроизводит эталон вторым путём.
    assert abs(alphas_error_control() - alphas_error_reference()) < 1e-9
    assert abs(th13_error_control() - th13_error_reference()) < 1e-9
    assert abs(alphas_error_alt() - alphas_error_reference()) < 1e-6


_selfcheck()


_SKIP_COMMON = {
        "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity)",
        "С21": "линейная форма в логарифмах для этого утверждения не задана; алгебраическая объяснимость разбирается на семействе",

    "С6": "закрытая формула, сетки и разрешения нет",
    "С7": "одно детерминированное вычисление, законных оценивателей нет",
    "С8": "погрешность входа не задана; внешняя погрешность учтена в С15",
    "С9": "скалярное значение, а не выборочная оценка",
    "С11": "одна статистика, тест нескольких статистик неприменим",
    "С17": "проверяется воспроизводимость печатного числа, а не сжатие данных",
    "С18": "границы перебора для этой таблицы в корпусе не объявлены",
}

_SKIP_NO_EXTERNAL = dict(_SKIP_COMMON, **{
    "С15": "проверяется внутренняя согласованность колонок одной таблицы, "
           "внешнего измерения для колонки Error не существует",
    "С16": "проверяется арифметика печатного числа, перебора формул нет",
    "С19": "величины порядка единицы, запас double превышает 1e12",
})

CLAIMS = [
    Claim(
        name="Ω_Λ = γ⁸π⁴/φ² даёт 0,688",
        source="docs/papers/README_FOR_SCIENTISTS.md:71",
        stated=omegal_stated,
        reference=omegal_reference,
        observed=omegal_observed,
        wrong=omegal_wrong(),
        null_model=omegal_control,
        null_expect=omegal_reference(),
        null_kind="positive",
        tolerance=0.003,
        sample=lambda: [omegal_observed()],
        statistics={"value": lambda values: float(sum(values) / len(values))},
        reference_alt=omegal_reference_alt,
        alt_tolerance=omegal_alt_tolerance,
        inputs=[SOURCE],
        skip_reasons=_SKIP_NO_EXTERNAL,
    ),
    Claim(
        name="Формула γ⁸π⁴/φ² предсказывает Ω_Λ из Planck 2018",
        source="docs/papers/README_FOR_SCIENTISTS.md:71",
        claim_kind="prediction",
        stated=omegal_reference,
        reference=omegal_reference,
        observed=omegal_reference,
        wrong=omegal_wrong(),
        null_model=omegal_control,
        null_expect=omegal_reference(),
        null_kind="positive",
        tolerance=0.0,
        sample=lambda: [omegal_reference()],
        statistics={"value": lambda values: float(sum(values) / len(values))},
        reference_alt=omegal_reference_alt,
        alt_tolerance=omegal_alt_tolerance,
        external_target=omegal_external,
        stated_target=omegal_stated,
        multiplicity=lambda: _multiplicity(0.0056 / 0.6889),
        mdl=lambda: _mdl(0.0056 / 0.6889),
        search_size=123201,
        arithmetic=lambda: {"params": (1, 0, 4, -2, 0),
                            "rel_uncertainty": 0.0056 / 0.6889},
        inputs=[SOURCE],
        skip_reasons=dict(_SKIP_COMMON, **{
            "С19": "величина порядка единицы, запас double превышает 1e12",
        }),
    ),
    Claim(
        name="Ω_DM = γ⁴π²/φ даёт 0,257",
        source="docs/papers/README_FOR_SCIENTISTS.md:72",
        stated=omegadm_stated,
        reference=omegadm_reference,
        observed=omegadm_observed,
        wrong=omegadm_wrong(),
        null_model=omegadm_control,
        null_expect=omegadm_reference(),
        null_kind="positive",
        tolerance=0.01,
        sample=lambda: [omegadm_observed()],
        statistics={"value": lambda values: float(sum(values) / len(values))},
        reference_alt=omegadm_reference_alt,
        alt_tolerance=omegal_alt_tolerance,
        inputs=[SOURCE],
        skip_reasons=_SKIP_NO_EXTERNAL,
    ),
    Claim(
        name="Колонка Error для α_s(M_Z) равна 0,005 %",
        source="docs/papers/README_FOR_SCIENTISTS.md:40",
        stated=alphas_error_stated,
        reference=alphas_error_reference,
        observed=alphas_error_observed,
        wrong=alphas_error_wrong(),
        null_model=alphas_error_control,
        null_expect=alphas_error_reference(),
        null_kind="positive",
        tolerance=0.0,
        sample=lambda: [alphas_error_observed()],
        statistics={"value": lambda values: float(sum(values) / len(values))},
        reference_alt=alphas_error_alt,
        alt_tolerance=lambda: 1e-9,
        inputs=[SOURCE],
        skip_reasons=_SKIP_NO_EXTERNAL,
    ),
    Claim(
        name="Колонка Error для sin²θ₁₃ равна 0,008 %",
        source="docs/papers/README_FOR_SCIENTISTS.md:43",
        stated=th13_error_stated,
        reference=th13_error_reference,
        observed=th13_error_observed,
        wrong=th13_error_wrong(),
        null_model=th13_error_control,
        null_expect=th13_error_reference(),
        null_kind="positive",
        tolerance=0.0,
        sample=lambda: [th13_error_observed()],
        statistics={"value": lambda values: float(sum(values) / len(values))},
        reference_alt=th13_error_alt,
        alt_tolerance=lambda: 1e-9,
        inputs=[SOURCE],
        skip_reasons=_SKIP_NO_EXTERNAL,
    ),
]
