# -*- coding: utf-8 -*-
"""Проверка разделения запоминания фраз и связной генерации в v2.46.

Отчёт сообщает о фрагментах Шекспира, полученных при низкой температуре,
одновременно признавая, что это не связные английские предложения. Кейс
проверяет именно это структурное различие, а не объявляет качество модели по
одному напечатанному числу перплексии.
"""
import os
import re
import sys

from goldsieve.sieve import Claim


ИСТОЧНИК = (
    "/home/user/workspace/corpus/trinity/docs/docs/research/"
    "trinity-golden-chain-v2-46-word-trigram-report.md"
)

if __name__ in sys.modules:
    raise RuntimeError(
        "кейс должен загружаться через module_from_spec без регистрации"
    )


def _текст():
    if not os.path.isfile(ИСТОЧНИК):
        raise AssertionError("отчёт Golden Chain v2.46 отсутствует")
    with open(ИСТОЧНИК, encoding="utf-8") as файл:
        return файл.read()


def наблюдение():
    """Извлечь сводку отдельными шаблонами, не используя эталон."""
    текст = _текст()
    сводка = текст.split("## Key Metrics", 1)[0]
    неудачи = текст.split("## What Works vs What Doesn't", 1)[1]
    совпадение = re.search(
        r"Word Trigram PPL:\s*train=([0-9.]+),\s*eval=([0-9.]+)",
        сводка,
        re.I,
    )
    if not совпадение:
        raise AssertionError("сводка PPL не найдена")
    return {
        "фразовое_воспроизведение": bool(
            re.search(r"actual Shakespeare phrases recalled", сводка, re.I)
        ),
        "низкая_температура": bool(
            re.search(r"T=0\.3 recalls Shakespeare phrases", сводка, re.I)
        ),
        "не_связные_предложения": bool(
            re.search(r'Not "coherent English sentences"', неудачи, re.I)
        ),
        "оценочная_перплексия": float(совпадение.group(2)),
    }


def _разделы():
    """Разбить отчёт по заголовкам для независимого структурного маршрута."""
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
    """Вычислить структурную карту по разным разделам отчёта."""
    блоки = _разделы()
    сводка = "\n".join(
        блоки.get("summary", блоки.get("начало", []))
    )
    результаты = "\n".join(
        строка
        for имя, строки in блоки.items()
        if (
            "test results" in имя
            or "test 38" in имя
            or "low temperature degeneration" in имя
        )
        for строка in строки
    )
    ограничения = "\n".join(
        строка
        for имя, строки in блоки.items()
        if (
            "what works vs what doesn't" in имя
            or "works" in имя
            or "doesn't work" in имя
        )
        for строка in строки
    )
    таблица = "\n".join(
        строка
        for имя, строки in блоки.items()
        if "key metrics" in имя
        for строка in строки
    )
    ппл = re.search(
        r"\|\s*Word Trigram PPL Eval\s*\|\s*([0-9.]+)",
        таблица,
        re.I,
    )
    if not ппл:
        raise AssertionError("строка PPL в таблице не найдена")
    return {
        "фразовое_воспроизведение": (
            "actual shakespeare phrases recalled" in сводка.lower()
            and "phrase recall" in результаты.lower()
        ),
        "низкая_температура": (
            "t=0.3" in результаты.lower()
            and (
                "actual phrases" in результаты.lower()
                or "actual multi-word shakespeare phrases" in результаты.lower()
            )
        ),
        "не_связные_предложения": (
            'not "coherent english sentences"' in ограничения.lower()
        ),
        "оценочная_перплексия": float(ппл.group(1)),
    }


def эталон_альт():
    """Второй путь: построчный разбор таблицы и списка ограничений."""
    строки = _текст().splitlines()
    в_метриках = False
    в_тесте = False
    в_ограничениях = False
    ппл = None
    есть_фразы = False
    есть_низкая_температура = False
    нет_связности = False
    for строка in строки:
        ниж = строка.lower()
        if ниж == "## key metrics":
            в_метриках = True
        elif в_метриках and ниж.startswith("## "):
            в_метриках = False
        if ниж == "### test 38 (new): word trigram statistics + generation":
            в_тесте = True
        elif в_тесте and ниж.startswith("### "):
            в_тесте = False
        if ниж == "## what works vs what doesn't":
            в_ограничениях = True
        elif в_ограничениях and ниж.startswith("## "):
            в_ограничениях = False
        if в_метриках:
            совпадение = re.search(
                r"\|\s*Word Trigram PPL Eval\s*\|\s*([0-9.]+)",
                строка,
                re.I,
            )
            if совпадение:
                ппл = float(совпадение.group(1))
        if в_тесте and "t=0.3" in ниж:
            есть_низкая_температура = True
        if в_тесте and (
            "phrase recall" in ниж
            or "actual multi-word shakespeare phrases" in ниж
        ):
            есть_фразы = True
        if в_ограничениях and 'not "coherent english sentences"' in ниж:
            нет_связности = True
    if ппл is None:
        raise AssertionError("построчный разбор PPL не найден")
    return {
        "фразовое_воспроизведение": есть_фразы,
        "низкая_температура": есть_низкая_температура,
        "не_связные_предложения": нет_связности,
        "оценочная_перплексия": ппл,
    }


def _неверная_подстановка():
    результат = эталон()
    результат["не_связные_предложения"] = False
    return результат


def _нулевая_модель():
    return {
        "фразовое_воспроизведение": False,
        "низкая_температура": False,
        "не_связные_предложения": False,
        "оценочная_перплексия": 0.0,
    }


def _самопроверка():
    наблюдаемое = наблюдение()
    assert наблюдаемое == {
        "фразовое_воспроизведение": True,
        "низкая_температура": True,
        "не_связные_предложения": True,
        "оценочная_перплексия": 21.16,
    }
    эт = эталон()
    алт = эталон_альт()
    assert эт == наблюдаемое
    assert алт == эт
    assert _неверная_подстановка() != наблюдаемое
    assert _нулевая_модель() != наблюдаемое


_самопроверка()


CLAIMS = [
    Claim(
        name=(
            "Отчёт Golden Chain v2.46 отделяет запоминание фраз "
            "от связной генерации"
        ),
        source=(
            "docs/docs/research/"
            "trinity-golden-chain-v2-46-word-trigram-report.md:1-220"
        ),
        claim_kind="statistical",
        stated=наблюдение(),
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
        claim_family="аудит риска смешения запоминания и генерации",
        observable=(
            "свидетельства фразового воспроизведения при T=0,3, "
            "признание отсутствия связных предложений и PPL eval"
        ),
        measurement_source="отчёт Golden Chain v2.46 о word-trigram",
        uncertainty_type="recipe_missing",
        novelty_key="golden_chain:v246:phrase_memorization_recipe:v1",
        information_class=(
            "новый источник и новая категория риска смешения запоминания "
            "фраз с качеством генерации"
        ),
        purpose="audit",
        models=(
            "фразовый replay по двум словам контекста",
            "связная генерация новых предложений",
        ),
        independent_of={
            "source": "отдельный отчёт v2.46, не ранее проверенные отчёты PPL",
            "observable": "сводка, Test 38 и раздел ограничений",
        },
        tests_independent="unknown",
        reason_code_hint="independence_unknown",
        notes=(
            "Наблюдение, эталон и reference_alt строят одну структурную карту "
            "разными маршрутами по разным разделам. Результат не подтверждает "
            "качество модели, переносимость PPL или независимость отчёта; "
            "он проверяет, что заявленное запоминание фраз не выдано за "
            "связное сочинение."
        ),
        skip_reasons={
            "С6": "рецепт обучения и варианты модели не являются целью",
            "С7": "сравниваются структурные свидетельства, а не сетка оценки",
            "С8": "неопределённость качества генерации не задана",
            "С9": "исходные запросы и независимая выборка не раскрыты",
            "С10": "повтор генерации не предоставлен",
            "С11": "внешнее сравнение качества не выполняется",
            "С12": "второй маршрут остаётся внутри одного отчёта",
            "С13": "обязательные пропуски перечислены явно",
            "С15": "внешней измеренной цели нет",
            "С16": "перебор формул к генерации не относится",
            "С17": "сжатие описания не является предметом проверки",
            "С18": "перенос на другие платформы не заявлен",
            "С19": "структурная карта не является арифметическим подтверждением",
            "С20": "эффективное число попыток не определено",
            "С21": "алгебраическая форма утверждения отсутствует",
        },
    )
]
