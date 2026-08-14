#!/usr/bin/env python3
"""Независимость разметки: разметчик не делит извлечение с детектором.

Зачем. Калибровка меряет ложные срабатывания детектора, сравнивая его вердикт с
РАЗМЕТКОЙ. Если разметка получена теми же внутренними функциями извлечения, что
и вердикт, измерение вырождается: ошибка извлечения одинаково испортит и то, что
проверяют, и то, чем проверяют, и калибровка этого не увидит. Это тот же дефект,
что тавтологическая проверка в сите С15, только на уровне инструмента.

Что проверяется машинно (AST, без исполнения):
  1. Разметчик (`calibrate_identity.py`) обращается к детектору ТОЛЬКО через
     публичный вердикт `derives_from`. Любой импорт `goldsieve.identity_deep`
     или приватного имени из `goldsieve.identity` — отказ.
  2. Корпус фикстур (`goldsieve/identity_corpus.py`) не импортирует детектор
     вообще: фикстуры описывают исходный текст, а не его разбор.
  3. Разметчик имеет СВОЮ функцию извлечения (определённую в его собственном
     файле) — иначе «независимость» была бы формальной.

Код возврата: 0 — независимость держится; 1 — нарушение.
"""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

MARKER = os.path.join(ROOT, "calibrate_identity.py")
CORPUS = os.path.join(ROOT, "goldsieve", "identity_corpus.py")

# Единственное разрешённое разметчику имя детектора: публичный вердикт.
ALLOWED_FROM_IDENTITY = {"derives_from"}
DETECTOR_MODULES = {"goldsieve.identity_deep", "identity_deep",
                    "goldsieve.modgraph"}


def _imports(path: str) -> list[tuple[str, str]]:
    """Список (модуль, имя) для всех импортов файла, включая локальные."""
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.append((a.name, ""))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:
                mod = "goldsieve." + mod if mod else "goldsieve"
            for a in node.names:
                out.append((mod, a.name))
    return out


def _local_functions(path: str) -> set[str]:
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    return {n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def violations(marker: str = MARKER, corpus: str = CORPUS) -> list[str]:
    """Список нарушений независимости. Пустой список — нарушений нет."""
    bad: list[str] = []
    for mod, name in _imports(marker):
        if mod in DETECTOR_MODULES:
            bad.append("разметчик импортирует внутренности детектора: %s" % mod)
        if mod in ("goldsieve.identity", "identity"):
            if name and name not in ALLOWED_FROM_IDENTITY:
                bad.append("разметчик берёт из детектора не только вердикт: %s"
                           % name)
            if not name:
                bad.append("разметчик импортирует модуль детектора целиком")
    for mod, _name in _imports(corpus):
        if mod in DETECTOR_MODULES or mod in ("goldsieve.identity", "identity"):
            bad.append("корпус фикстур зависит от детектора: %s" % mod)
    own = _local_functions(marker)
    if not any(n.startswith("_extract") or "label" in n or "mark" in n
               for n in own):
        bad.append("у разметчика нет собственной функции извлечения/разметки")
    return bad


def main() -> int:
    ok = fail = 0

    def check(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ок      %s" % name)
        else:
            fail += 1
            print("  ПРОВАЛ  %s %s" % (name, note))

    v = violations()
    check("независимость разметки держится", not v, "; ".join(v))

    # ПОДСТАВКИ: каждая внесённая зависимость обязана быть замечена.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        src = open(MARKER, encoding="utf-8").read()
        p1 = os.path.join(tmp, "m1.py")
        open(p1, "w", encoding="utf-8").write(
            src + "\nfrom goldsieve.identity_deep import origin_is\n")
        check("подставка: импорт внутренностей детектора замечен",
              any("внутренности" in x for x in violations(p1)))
        p2 = os.path.join(tmp, "m2.py")
        open(p2, "w", encoding="utf-8").write(
            src + "\nfrom goldsieve.identity import _functions_of\n")
        check("подставка: приватное имя детектора замечено",
              any("не только вердикт" in x for x in violations(p2)))
        p3 = os.path.join(tmp, "c3.py")
        open(p3, "w", encoding="utf-8").write(
            "from goldsieve.identity import derives_from\n")
        check("подставка: зависимость корпуса замечена",
              any("корпус фикстур" in x for x in violations(MARKER, p3)))
        p4 = os.path.join(tmp, "m4.py")
        open(p4, "w", encoding="utf-8").write(
            "from goldsieve.identity import derives_from\n"
            "def helper():\n    return 1\n")
        check("подставка: отсутствие своей разметки замечено",
              any("собственной функции" in x for x in violations(p4)))

    print("независимость: %d пройдено, %d провалено" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    raise SystemExit(main())
