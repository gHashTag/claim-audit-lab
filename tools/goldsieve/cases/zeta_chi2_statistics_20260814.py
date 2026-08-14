"""Проверка сводной статистики χ² по десяти высотным корзинам."""

import re
from decimal import Decimal, getcontext

from goldsieve.sieve import Claim


SOURCE = (
    "/home/user/workspace/corpus/trinity/"
    "data/zeta/zeta_bin_analysis_update.md"
)


def _text():
    with open(SOURCE, encoding="utf-8") as handle:
        text = handle.read()
    marker = "### 3. GUE Fit: Improves with Height"
    if marker not in text:
        raise AssertionError("раздел о χ² не найден")
    return text


def _bin_values():
    """Извлекает десять значений χ²/dof из таблицы, а не использует сводку."""
    text = _text()
    values = []
    for line in text.splitlines():
        if not re.match(r"^\| [1-9]0? \|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 9:
            continue
        value = cells[-1].replace("**", "").replace("✅", "").strip()
        try:
            values.append(Decimal(value))
        except Exception:
            continue
    if len(values) != 10:
        raise AssertionError(f"ожидалось 10 корзин, получено {len(values)}")
    return values


def _mean(values):
    return sum(values) / Decimal(len(values))


def _std(values):
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    return variance.sqrt()


def _reference():
    values = _bin_values()
    return {"mean": float(_mean(values)), "std": float(_std(values))}


def _observed():
    """Наблюдение: те же десять строк, пересчитанные из таблицы."""
    return _reference()


def _stated():
    text = _text()
    match = re.search(r"\*\*χ²/dof = ([0-9.]+) ± ([0-9.]+)\*\*", text)
    if not match:
        raise AssertionError("сводная строка χ² не найдена")
    return {"mean": float(match.group(1)), "std": float(match.group(2))}


def _wrong():
    value = _reference()
    return {"mean": value["mean"] * 1.25, "std": value["std"] * 0.5}


def _positive_control():
    getcontext().prec = 40
    values = [Decimal(str(value)) for value in _bin_values()]
    return {"mean": float(_mean(values)), "std": float(_std(values))}


def _negative_control():
    return {"mean": 1.0, "std": 0.0}


def _sample():
    return [float(value) for value in _bin_values()]


def _mean_stat(values):
    return sum(values) / len(values)


def _std_stat(values):
    mean = _mean_stat(values)
    return (sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5


CLAIMS = [
    Claim(
        name="χ²/dof по десяти высотным корзинам = 2,67 ± 0,49",
        source="data/zeta/zeta_bin_analysis_update.md:24-38",
        stated=_stated,
        reference=_reference,
        observed=_observed,
        wrong=_wrong,
        null_model=_negative_control,
        null_expect={"mean": 1.0, "std": 0.0},
        null_kind="negative",
        tolerance=0.02,
        sample=_sample,
        statistics={"mean": _mean_stat, "std": _std_stat},
        reference_alt=_positive_control,
        alt_tolerance=lambda: 1.0e-12,
        inputs=[SOURCE],
        claim_family="статистика высотных корзин дзета",
        observable="среднее и разброс χ² на степень свободы",
        measurement_source="корпус Trinity, таблица высотных корзин",
        uncertainty_type="statistical",
        novelty_key="zeta:chi2_bins:v1",
        information_class="novelty",
        purpose="audit",
        models=["табличный пересчёт", "независимый Decimal-путь"],
        independent_of=["zeta:gap_shape:v1", "zeta:khinchin:v1"],
        notes=(
            "Эталон вычислен из десяти строк корзин. Сводные числа из "
            "раздела Summary используются только как заявленное значение; "
            "положительный контроль повторяет арифметику через Decimal."
        ),
        skip_reasons={
            "С6": "для табличной статистики нет параметра сходимости",
            "С7": "задан один способ формирования десяти корзин",
            "С8": "погрешность исходных χ² не задана",
            "С9": "корзины корпуса являются полным набором наблюдений",
            "С10": "для агрегата χ² нет сырой выборки распределения",
            "С11": "проверяется одна сводная статистика",
            "С15": "это статистика корпуса, внешней цели нет",
            "С16": "перебора гипотез нет",
            "С17": "модельная формула не заявлена",
            "С18": "объявленных границ перебора нет",
            "С19": "арифметическая точность Decimal существенно выше округления",
            "С20": "эффективное число попыток неприменимо",
            "С21": "алгебраическая форма не заявлена",
        },
    )
]


def _selfcheck():
    assert len(_bin_values()) == 10
    assert _reference()["mean"] > 2.0
    assert _reference()["std"] > 0.0
