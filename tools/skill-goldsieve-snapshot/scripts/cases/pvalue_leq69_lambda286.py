"""Аудит численного хвоста Пуассона из корпуса Trinity.

Проверяется ровно одно утверждение: в выходной таблице корпуса для
X ~ Poisson(286) заявлено P(X <= 69) = 1.46894459373474e-53.
Эталон пересчитывается двумя различными способами, а наблюдение читается из
JSON-результата корпуса.
"""

import json
import math
import os
import sys

from scipy.special import gammaincc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goldsieve.sieve import Claim  # noqa: E402


CORPUS_ROOT = "/home/user/workspace/corpus/t27"
TABLE = os.path.join(
    CORPUS_ROOT, "scripts/trinity-pellis-pipeline/output/pvalue_table.md"
)
RESULTS = os.path.join(
    CORPUS_ROOT, "scripts/trinity-pellis-pipeline/output/monte_carlo_pvalue.json"
)

N_EXPRESSIONS = 286000
NULL_RATE = 0.001
OBSERVED_HITS = 69


def poisson_cdf_reference():
    """Вычисляемый эталон через регуляризованную неполную гамма-функцию."""
    lam = N_EXPRESSIONS * NULL_RATE
    return float(gammaincc(OBSERVED_HITS + 1, lam))


def poisson_cdf_recurrence():
    """Независимый эталон: рекуррентная сумма вероятностей Пуассона."""
    lam = N_EXPRESSIONS * NULL_RATE
    term = math.exp(-lam)
    total = term
    for i in range(1, OBSERVED_HITS + 1):
        term *= lam / i
        total += term
    return float(total)


def observed_from_corpus():
    """Наблюдение из JSON-артефакта корпуса, без повторного вычисления."""
    with open(RESULTS, encoding="utf-8") as handle:
        return float(json.load(handle)["p_value_leq_observed"])


def positive_control():
    """Позитивный контроль, обязанный воспроизвести эталон."""
    return poisson_cdf_recurrence()


CLAIMS = [
    Claim(
        name="P(X <= 69) при Poisson(lambda=286) = 1.46894459373474e-53",
        source=(
            "t27/scripts/trinity-pellis-pipeline/output/pvalue_table.md:22-26; "
            "monte_carlo_pvalue.json:3-11"
        ),
        stated=1.46894459373474e-53,
        reference=poisson_cdf_reference,
        observed=observed_from_corpus,
        wrong=lambda: poisson_cdf_reference() * 100.0,
        null_model=positive_control,
        null_kind="positive",
        tolerance=1e-10,
        reference_alt=poisson_cdf_recurrence,
        alt_tolerance=lambda: 1e-12,
        inputs=[TABLE, RESULTS],
        skip_reasons={
            "С20": "эффективное число попыток разбирается на семействе формул целиком (случай sacred_fit_multiplicity); для одиночного утверждения перебор не воспроизводим",
            "С21": "алгебраическая объяснимость разбирается на семействе формул целиком (случай sacred_fit_multiplicity); здесь линейная форма в логарифмах не задана",
            "С15": "утверждение о числе в документе, внешней величины нет",
            "С16": "перебора формул в этом утверждении нет",
            "С17": "длина описания неприменима: это не закон, а запись числа",
            "С18": "объявленных границ перебора это утверждение не касается",
            "С6": "для фиксированной формулы хвоста сетка или разрешение не задаются",
            "С7": "у утверждения нет альтернативных оценок одной величины",
            "С8": "погрешность входных данных не заявлена",
            "С9": "утверждение не является выборочным измерением по размеру корпуса",
            "С10": "наблюдение — детерминированное числовое поле, выборочная неопределённость не задаётся",
            "С11": "нет выборки и набора статистик для теста подозрительно точного согласия",
            "С19": "утверждение не о члене семейства формул; ошибка double несопоставимо меньше сравниваемой погрешности",
        },
    ),
]
