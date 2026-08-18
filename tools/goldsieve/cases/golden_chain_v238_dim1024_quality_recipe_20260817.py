# -*- coding: utf-8 -*-
"""Проверка разделения оценочных метрик и связной генерации в v2.38.

Кейс проверяет структуру отчёта: улучшение loss/PPL при dim=1024
сопровождается явным признанием, что генерация остаётся случайной.
Он не превращает отношение напечатанных чисел в подтверждение качества.
"""
import os
import re
import sys

from goldsieve.sieve import Claim

ИСТОЧНИК = (
    "/home/user/workspace/corpus/trinity/deploy/trinity-nexus/docs/research/"
    "trinity-golden-chain-v2-38-dim1024-report.md"
)

if __name__ in sys.modules:
    raise RuntimeError("кейс должен загружаться через module_from_spec без регистрации")


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Golden Chain v2.38 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def _число(шаблон, текст, имя):
    совпадение = re.search(шаблон, текст, re.I)
    if not совпадение:
        raise AssertionError("не найдено поле: " + имя)
    return float(совпадение.group(1))


def наблюдение():
    """Извлечь наблюдаемую карту из независимых сводных разделов."""
    текст = _текст()
    сводка = текст.split("## Key Metrics", 1)[0]
    метрики = текст.split("## Key Metrics", 1)[1].split("## Test Results", 1)[0]
    ограничения = текст.split("## What Works vs What Doesn't", 1)[1]
    return {
        "sr_eval_loss": _число(r"dim=1024 SR Eval Loss\s*\|\s*\**([0-9.]+)", метрики, "SR Eval Loss"),
        "mr_eval_loss": _число(r"dim=1024 MR Eval Loss\s*\|\s*\**([0-9.]+)", метрики, "MR Eval Loss"),
        "test_ppl": _число(r"dim=1024 Test PPL\s*\|\s*\**([0-9.]+)", метрики, "Test PPL"),
        "cosine_range": _число(r"Cosine Signal Range\s*\|\s*\**([0-9.]+)", метрики, "Cosine Signal Range"),
        "тесты": bool(re.search(r"All 23 integration tests pass", сводка, re.I)),
        "нет_связной_генерации": bool(re.search(r"Generation still not coherent English", ограничения, re.I)),
        "улучшение_оценки": bool(re.search(r"Eval loss improves for single-role", сводка, re.I)),
    }


def _разделы():
    блоки = {"начало": []}
    текущий = "начало"
    for строка in _текст().splitlines():
        заголовок = re.match(r"^#{2,3}\s+(.+?)\s*$", строка)
        if заголовок:
            текущий = заголовок.group(1).strip().lower()
            блоки.setdefault(текущий, [])
        блоки.setdefault(текущий, []).append(строка)
    return блоки


def эталон():
    """Вычислить структурную карту из Test 22/23 и ограничений отчёта."""
    блоки = _разделы()
    тест22 = "\n".join(строки for имя, строки in блоки.items() if "test 22" in имя for строки in строки)
    тест23 = "\n".join(строки for имя, строки in блоки.items() if "test 23" in имя for строки in строки)
    ограничения = "\n".join(
        строки
        for имя, строки in блоки.items()
        if ("what works vs what doesn't" in имя or "doesn't work" in имя)
        for строки in строки
    )
    сводка = "\n".join(блоки.get("summary", []))
    return {
        "sr_eval_loss": _число(r"dim=1024 eval loss:\s*([0-9.]+)", тест22, "Test 22 eval loss"),
        "mr_eval_loss": _число(r"dim=1024 multi-role eval loss:\s*([0-9.]+)", тест23, "Test 23 eval loss"),
        "test_ppl": _число(r"dim=1024 test PPL:\s*([0-9.]+)", тест23, "Test 23 test PPL"),
        "cosine_range": _число(r"Range:\s*([0-9.]+)", тест22, "cosine range"),
        "тесты": "all 23 integration tests pass" in сводка.lower(),
        "нет_связной_генерации": "generation still not coherent english" in ограничения.lower(),
        "улучшение_оценки": "eval loss improves for single-role" in сводка.lower(),
    }


def эталон_альт():
    """Второй путь: построчно разобрать Test 22, Test 23 и ограничения."""
    строки = _текст().splitlines()
    в22 = в23 = вогр = False
    out = {}
    for строка in строки:
        ниж = строка.lower()
        if ниж.startswith("### test 22"):
            в22, в23, вогр = True, False, False
        elif ниж.startswith("### test 23"):
            в22, в23, вогр = False, True, False
        elif ниж == "## what works vs what doesn't":
            в22, в23, вогр = False, False, True
        elif ниж.startswith("## ") and ниж != "## what works vs what doesn't":
            в22 = в23 = вогр = False
        if в22:
            if "dim=1024 eval loss:" in ниж:
                out["sr_eval_loss"] = float(re.search(r"dim=1024 eval loss:\s*([0-9.]+)", строка, re.I).group(1))
            if "range:" in ниж:
                out["cosine_range"] = float(re.search(r"range:\s*([0-9.]+)", строка, re.I).group(1))
        if в23:
            if "dim=1024 multi-role eval loss:" in ниж:
                out["mr_eval_loss"] = float(re.search(r"dim=1024 multi-role eval loss:\s*([0-9.]+)", строка, re.I).group(1))
            if "dim=1024 test ppl:" in ниж:
                out["test_ppl"] = float(re.search(r"dim=1024 test ppl:\s*([0-9.]+)", строка, re.I).group(1))
        if вогр and "generation still not coherent english" in ниж:
            out["нет_связной_генерации"] = True
    out["тесты"] = "all 23 integration tests pass" in _текст().split("## Key Metrics", 1)[0].lower()
    out["улучшение_оценки"] = "eval loss improves for single-role" in _текст().split("## Key Metrics", 1)[0].lower()
    out.setdefault("нет_связной_генерации", False)
    return out


def _неверная_подстановка():
    результат = эталон()
    результат["нет_связной_генерации"] = False
    return результат


def _нулевая_модель():
    return {
        "sr_eval_loss": 0.0,
        "mr_eval_loss": 0.0,
        "test_ppl": 0.0,
        "cosine_range": 0.0,
        "тесты": False,
        "нет_связной_генерации": False,
        "улучшение_оценки": False,
    }


НАБЛЮДАЕМОЕ = наблюдение()
_ЭТАЛОН = эталон()
_АЛЬТ = эталон_альт()
assert НАБЛЮДАЕМОЕ == {
    "sr_eval_loss": 0.7552,
    "mr_eval_loss": 0.7730,
    "test_ppl": 1.8,
    "cosine_range": 0.7388,
    "тесты": True,
    "нет_связной_генерации": True,
    "улучшение_оценки": True,
}
assert _ЭТАЛОН == НАБЛЮДАЕМОЕ
assert _АЛЬТ == НАБЛЮДАЕМОЕ
assert _неверная_подстановка() != НАБЛЮДАЕМОЕ
assert _нулевая_модель() != НАБЛЮДАЕМОЕ


CLAIMS = [
    Claim(
        name="Отчёт Golden Chain v2.38 отделяет улучшение оценочных метрик от связной генерации",
        source="deploy/trinity-nexus/docs/research/trinity-golden-chain-v2-38-dim1024-report.md:1-260",
        claim_kind="statistical",
        stated=НАБЛЮДАЕМОЕ,
        reference=эталон,
        observed=наблюдение,
        wrong=_неверная_подстановка,
        null_model=_нулевая_модель,
        null_expect=None,
        null_kind="negative",
        tolerance=0.0,
        reference_alt=эталон_альт,
        alt_tolerance=lambda: 0.0,
        inputs=[ИСТОЧНИК],
        claim_family="аудит риска смешения PPL и качества генерации",
        observable="сопоставление dim=1024 loss/PPL с явным признанием случайной генерации",
        measurement_source="отдельный отчёт Golden Chain v2.38 о размерности HV",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v238:dim1024_quality_recipe:v1",
        information_class="новый источник и новая категория риска смешения оценочных метрик с качеством генерации",
        purpose="audit",
        models=("оценка loss/PPL на корпусе Shakespeare", "качественная оценка связности генерации"),
        independent_of={"source":"отдельный отчёт v2.38, ранее не проверенный", "observable":"сводка, Test 22, Test 23 и раздел ограничений"},
        tests_independent="unknown",
        reason_code_hint="independence_unknown",
        notes="Проверяется только внутренняя структура одного отчёта: наличие оценочных метрик и отдельного признания случайной генерации. Не доказаны воспроизводимость обучения, качество модели, причинность улучшения от размерности, перенос на другие корпуса, версии CPython и ОС.",
        skip_reasons={
            "С6": "рецепт обучения, состояние и реализация не раскрыты",
            "С7": "полная схема разбиения и выборки не раскрыта",
            "С8": "неопределённость метрик не задана",
            "С9": "конечный размер и независимая выборка не установлены",
            "С10": "повторное обучение не предоставлено",
            "С11": "внешнее сравнение качества не является целью",
            "С12": "оба маршрута используют один отчёт",
            "С13": "обязательные пропуски перечислены явно",
            "С15": "внешняя числовая цель отсутствует",
            "С16": "перебор формул к отчёту не относится",
            "С17": "описание метрик не является задачей сжатия",
            "С18": "перенос на платформы не заявлен",
            "С19": "утверждение структурное, а не арифметическое",
            "С20": "эффективное число попыток не определено",
            "С21": "алгебраическая форма отсутствует",
        },
    )
]
