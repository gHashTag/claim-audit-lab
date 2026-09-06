#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож конструкций, для которых анализатор не заявляет поддержку.

Каскад не должен молча объявлять кейс проверенным, если его рецепт использует
генератор, корутину, contextvars, exec/eval или метакласс. Эти конструкции
отмечаются как unsupported с путём прочитанного файла и строкой наблюдения.
Сторож проверяет наличие риска, но не исполняет кейсы.
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
OUT = HERE / "unsupported_construct_guard.json"


def _kind(node: ast.AST) -> str | None:
    if isinstance(node, (ast.Yield, ast.YieldFrom, ast.GeneratorExp)):
        return "генератор"
    if isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor,
                         ast.AsyncWith)):
        return "корутина"
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        names = [alias.name for alias in node.names]
        if any(name == "contextvars" or name.startswith("contextvars.")
               for name in names):
            return "contextvars"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"exec", "eval"}:
            return "exec/eval"
    if isinstance(node, ast.ClassDef):
        if any(keyword.arg == "metaclass" for keyword in node.keywords):
            return "метакласс"
    return None


def inspect(path: Path) -> list[dict]:
    """Вернуть все явно найденные неохваченные конструкции одного файла."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rows = []
    seen = set()
    for node in ast.walk(tree):
        kind = _kind(node)
        if kind is None:
            continue
        key = (kind, getattr(node, "lineno", 0))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "путь": str(path),
            "строка": getattr(node, "lineno", None),
            "риск": kind,
            "статус": "unsupported",
            "причина": "анализатор не заявляет поддержку этой конструкции",
        })
    return rows


def scan(cases_dir: Path = CASES) -> dict:
    rows = []
    parse_errors = []
    for path in sorted(cases_dir.glob("*.py")):
        try:
            rows.extend(inspect(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors.append({
                "путь": str(path),
                "статус": "not-evaluated",
                "причина": "файл не удалось разобрать: %s" % exc,
            })
    if parse_errors:
        rows.extend(parse_errors)
    status = "unsupported" if rows else "verified-in-scope"
    return {
        "статус": status,
        "прочитано_кейсов": len(list(cases_dir.glob("*.py"))),
        "неохваченные_конструкции": len(rows),
        "наблюдения": rows,
        "ограничение": (
            "отсутствие найденной конструкции не доказывает научную истинность "
            "кейса; неизвестные динамические конструкции могут остаться "
            "not-evaluated"
        ),
    }


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            bad += 1
            print("  ПРОВАЛ  " + name)

    with tempfile.TemporaryDirectory(prefix="goldsieve-unsupported-") as tmp:
        root = Path(tmp)
        clean = root / "clean.py"
        clean.write_text("VALUE = 1\n", encoding="utf-8")
        check("обычный файл не получает риск",
              inspect(clean) == [])

        risky = root / "risky.py"
        risky.write_text(
            "import contextvars\n"
            "def stream():\n"
            "    yield 1\n"
            "async def load():\n"
            "    await task()\n"
            "class C(metaclass=Meta):\n"
            "    pass\n"
            "x = eval('1')\n",
            encoding="utf-8",
        )
        found = inspect(risky)
        kinds = {row["риск"] for row in found}
        check("все пять типов риска отмечены",
              kinds == {"contextvars", "генератор", "корутина",
                        "метакласс", "exec/eval"})
        check("каждый риск имеет путь и статус",
              all(row["путь"] == str(risky)
                  and row["статус"] == "unsupported"
                  and isinstance(row["строка"], int)
                  for row in found))

        broken = root / "broken.py"
        broken.write_text("def broken(:\n", encoding="utf-8")
        report = scan(root)
        check("ошибка разбора не становится покрытием",
              report["статус"] == "unsupported"
              and any(row["статус"] == "not-evaluated"
                      for row in report["наблюдения"]))

    print("самопроверка сторожа неохваченных конструкций: %d пройдено, "
          "%d провалено" % (good, bad))
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv not in ([], ["--scan"]):
        print("использование: --selftest или --scan")
        return 2
    result = scan()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож неохваченных конструкций: %s; кейсов: %d; рисков: %d"
          % (result["статус"], result["прочитано_кейсов"],
             result["неохваченные_конструкции"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
