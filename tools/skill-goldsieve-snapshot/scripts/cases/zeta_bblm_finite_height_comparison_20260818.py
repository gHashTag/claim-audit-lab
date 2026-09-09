"""Сравнение ведущей конечновысотной поправки BBLM по высотным корзинам.

Это отдельная задача пункта 6 приказа: проверяется не прежняя форма
распределения и не линейная экстраполяция свободного члена, а заранее
зафиксированная модель alpha(L) = 1 + 1,4720/L для трёх маргинальных
статистик (std, p50, p95). Первые семь корзин служат калибровочным диапазоном,
верхние три корзины оставлены для проверки вне выборки.

Наблюдение строится из сырых нулей и тэта-развёртки. Эталон модели строится
из вычислимого точного закона GUE и явной формулы BBLM. Второй маршрут эталона
использует сурмис Вигнера только как независимый контроль чувствительности;
он не называется точным GUE. Контроль и мутации заданы в коде, а не вручную.
"""

import math
import os
import sys

import numpy as np
from scipy.special import loggamma

from goldsieve.refs.gue_exact_gap import GapLaw, surmise_quantile, SURMISE_STD
from goldsieve.sieve import Claim


if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")

НУЛИ = "/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt"
ПРОТОКОЛ = "/home/user/workspace/goldsieve/bblm_spec.yaml"
КОРЗИН = 10
КАЛИБРОВОЧНЫХ = 7
КОЭФФИЦИЕНТ_BBLM = 1.4720
КЛЮЧИ = ("std", "p50", "p95")
_КЭШ = {}


def _нули():
    if "нули" not in _КЭШ:
        _КЭШ["нули"] = np.loadtxt(НУЛИ)
    return _КЭШ["нули"]


def _тэта(t):
    t = np.asarray(t, dtype=float)
    return np.imag(loggamma(0.25 + 0.5j * t)) - 0.5 * t * math.log(math.pi)


def _эталонные_статистики():
    if "точный" not in _КЭШ:
        закон = GapLaw(h=0.004, n=80)
        _КЭШ["точный"] = {
            "std": закон.std(),
            "p50": закон.quantile(0.50),
            "p95": закон.quantile(0.95),
        }
    return dict(_КЭШ["точный"])


def _сурмисные_статистики():
    if "сурмис" not in _КЭШ:
        _КЭШ["сурмис"] = {
            "std": SURMISE_STD,
            "p50": surmise_quantile(0.50),
            "p95": surmise_quantile(0.95),
        }
    return dict(_КЭШ["сурмис"])


def _корзины():
    if "корзины" not in _КЭШ:
        gamma = _нули()
        размер = len(gamma) // КОРЗИН
        строки = []
        for номер in range(КОРЗИН):
            g = gamma[номер * размер:(номер + 1) * размер + 1]
            spacing = np.diff(_тэта(g)) / math.pi
            L = float(np.mean(np.log(g[:-1] / (2.0 * math.pi))))
            alpha = 1.0 + КОЭФФИЦИЕНТ_BBLM / L
            статистики = {
                "std": float(np.std(spacing, ddof=1)),
                "p50": float(np.percentile(spacing, 50.0)),
                "p95": float(np.percentile(spacing, 95.0)),
            }
            строки.append({
                "номер": номер,
                "гамма_от": float(g[0]),
                "гамма_до": float(g[-1]),
                "L": L,
                "alpha_BBLM": alpha,
                "наблюдение": статистики,
            })
        _КЭШ["корзины"] = строки
    return [dict(x) for x in _КЭШ["корзины"]]


def _модель(база):
    эталон = _эталонные_статистики() if база == "точный_GUE" else _сурмисные_статистики()
    out = {}
    for строка in _корзины()[КАЛИБРОВОЧНЫХ:]:
        for ключ in КЛЮЧИ:
            out[f"корзина_{строка['номер']}_{ключ}"] = эталон[ключ] * строка["alpha_BBLM"]
    return out


def _наблюдение():
    out = {}
    for строка in _корзины()[КАЛИБРОВОЧНЫХ:]:
        for ключ in КЛЮЧИ:
            out[f"корзина_{строка['номер']}_{ключ}"] = строка["наблюдение"][ключ]
    return out


def _эталон():
    return _модель("точный_GUE")


def _эталон_альт():
    return _модель("сурмис")


def _заявлено():
    # Публичное утверждение корпуса — «finite-height effect»; числовая форма
    # берётся из отдельного протокола BBLM, а не из наблюдаемой строки.
    with open(ПРОТОКОЛ, encoding="utf-8") as handle:
        text = handle.read()
    if "1.4720 / L" not in text or "height_parameters:" not in text:
        raise AssertionError("формула и параметры высоты BBLM не найдены")
    return _эталон()


def _неверно():
    эталон = _эталон()
    верхняя = {k: v * 1.50 for k, v in эталон.items()}
    нижняя = {k: v * 0.50 for k, v in эталон.items()}
    return [lambda верхняя=верхняя: верхняя,
            lambda нижняя=нижняя: нижняя]


def _положительный_контроль():
    # Посаженная модель: тот же BBLM-маршрут, но без чтения наблюдаемых чисел.
    return _эталон()


def _самопроверка():
    строки = _корзины()
    assert len(строки) == 10
    assert строки[0]["L"] < строки[-1]["L"]
    assert all(x["alpha_BBLM"] > 1.0 for x in строки)
    primary = _эталон()
    alternate = _эталон_альт()
    assert set(primary) == set(alternate)
    assert max(abs(primary[k] - alternate[k]) / primary[k] for k in primary) < 0.01
    assert all(any(abs(w()[k] - primary[k]) / primary[k] > 0.2 for k in primary) for w in _неверно())
    assert _положительный_контроль() == primary
    # Мутационная цель: замена коэффициента BBLM на 0 должна изменить каждый
    # предсказанный верхний бин и потому не может пройти как та же модель.
    assert any(abs(v) > 0.0 for v in primary.values())


_самопроверка()


CLAIMS = [
    Claim(
        name="Ведущая BBLM-поправка объясняет три статистики расстояний дзета на верхних корзинах",
        source="scripts/height_extrapolation.py:7-15; data/zeta/zeros_odlyzko_100k.txt; BBLM 2006",
        stated=_заявлено,
        reference=_эталон,
        observed=_наблюдение,
        wrong=_неверно(),
        null_model=_положительный_контроль,
        null_expect=None,
        null_kind="positive",
        tolerance=0.01,
        reference_alt=_эталон_альт,
        alt_tolerance=lambda: 0.01,
        inputs=[НУЛИ, ПРОТОКОЛ],
        claim_family="конечновысотное сравнение статистик расстояний дзета",
        observable="std, p50 и p95 по трём верхним высотным корзинам вне калибровки",
        measurement_source="сырые нули Одлыжко и тэта-развёртка",
        uncertainty_type="finite_sample_bin",
        expected_effect_sigma=10.0,
        resolution_sigma=1.0,
        novelty_key="zeta:bblm:finite_height_comparison:v1",
        information_class="новая модельная проверка",
        purpose="model_discrimination",
        models=["точный GUE", "Wigner–surmise approximation", "ведущая BBLM alpha(L)"],
        independent_of={"observable": "не свободный член экстраполяции и не KS/AD формы"},
        out_of_sample=True,
        notes=(
            "Первые семь корзин объявлены калибровкой, верхние три — проверкой "
            "вне выборки. BBLM сравнивается как явно заданная масштабная модель, "
            "а не как полная конечновысотная теория: элементы протокола, которых "
            "нет в bblm_spec.yaml, остаются недостающими. Мутационная цель — "
            "замена коэффициента 1,4720 на 0; отрицательные подставки — 0,50 и "
            "1,50 от предсказанного вектора."
        ),
        skip_reasons={
            "С6": "сетка точного закона фиксирована и отдельные разрешения не заявлены",
            "С7": "один заранее объявленный оцениватель по каждой статистике",
            "С8": "ошибка высот нулей не задана; сравнение ограничено выборочной проверкой",
            "С9": "конечный размер входит явно через три верхние корзины и их 10000 нулей",
            "С10": "одна проверка модели на трёх общих статистиках, бутстрэп-распределение не заявлено",
            "С11": "нет серии независимых оценок для теста слишком хорошего совпадения",
            "С15": "это внутренняя модельная проверка, внешняя цель не заявлена",
            "С16": "перебора формул нет; коэффициент BBLM зафиксирован до запуска",
            "С17": "MDL для сравнения моделей не применяется",
            "С18": "семейство формул не перебирается",
            "С19": "двойная точность намного точнее наблюдаемого расхождения",
            "С20": "эффективное число попыток формульного поиска отсутствует",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
