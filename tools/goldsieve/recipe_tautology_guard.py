#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож прямого повторения рецепта observed/reference в кейсах.

Проверка файлов observed/reference не ловит вырожденный рецепт, если оба
callable вычисляют одно и то же выражение внутри одного кейса. Такой путь
должен оставаться ``not-evaluated``: это аудит инструмента, а не научный
вердикт. Проверка намеренно ограничена буквальным совпадением AST; более
глубокие цепочки остаются областью ``goldsieve.identity``.

Команды:
    python3 recipe_tautology_guard.py --selftest
    python3 recipe_tautology_guard.py
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
OUT = HERE / "recipe_tautology_guard.json"


def _normal(node: ast.AST) -> str:
    """Каноническое представление выражения без позиций в файле."""
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def _claim_rows(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rows: list[dict] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Claim"
        ):
            continue
        values = {item.arg: item.value for item in node.keywords if item.arg}
        observed = values.get("observed")
        reference = values.get("reference")
        if observed is None or reference is None:
            continue
        if _normal(observed) != _normal(reference):
            continue
        rows.append(
            {
                "путь": str(path),
                "строка": getattr(node, "lineno", None),
                "риск": "observed_reference_same_recipe",
                "статус": "not-evaluated",
                "причина": (
                    "поля observed и reference содержат один и тот же "
                    "рецепт; сравнение не является независимым"
                ),
            }
        )
    return rows


def scan(cases_dir: Path = CASES) -> dict:
    rows: list[dict] = []
    errors: list[dict] = []
    paths = sorted(cases_dir.glob("*.py"))
    for path in paths:
        try:
            rows.extend(_claim_rows(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(
                {
                    "путь": str(path),
                    "статус": "not-evaluated",
                    "причина": "файл не удалось разобрать: %s" % exc,
                }
            )
    rows.extend(errors)
    return {
        "статус": "not-evaluated" if rows else "verified-in-scope",
        "прочитано_кейсов": len(paths),
        "прямых_повторов_рецепта": len(rows),
        "наблюдения": rows,
        "ограничение": (
            "сравнивается только буквальная форма AST; косвенные цепочки "
            "проверяются отдельным детектором identity; отсутствие строки "
            "не доказывает научную независимость"
        ),
    }


def selftest() -> int:
    good = failed = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, failed
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            failed += 1
            print("  ПРОВАЛ  " + name)

    with tempfile.TemporaryDirectory(prefix="goldsieve-recipe-tautology-") as tmp:
        root = Path(tmp)
        same = root / "same.py"
        same.write_text(
            "from goldsieve.sieve import Claim\n"
            "CLAIMS = [Claim(name='same', source='x', "
            "reference=lambda: 1.0, observed=lambda: 1.0)]\n",
            encoding="utf-8",
        )
        different = root / "different.py"
        different.write_text(
            "from goldsieve.sieve import Claim\n"
            "def ref(): return 1.0\n"
            "def obs(): return 1.0\n"
            "CLAIMS = [Claim(name='different', source='x', "
            "reference=ref, observed=obs)]\n",
            encoding="utf-8",
        )
        same_rows = _claim_rows(same)
        different_rows = _claim_rows(different)
        check("одинаковый AST получает not-evaluated", len(same_rows) == 1)
        check("разные имена callable не получают прямой повтор",
              different_rows == [])
        broken = root / "broken.py"
        broken.write_text("def broken(:\n", encoding="utf-8")
        report = scan(root)
        check("ошибка разбора не становится покрытием",
              report["статус"] == "not-evaluated"
              and any(row["статус"] == "not-evaluated"
                      for row in report["наблюдения"]))

    print(
        "самопроверка сторожа прямого повтора рецепта: %d пройдено, %d провалено"
        % (good, failed)
    )
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv not in ([], ["--scan"]):
        print("использование: --selftest или --scan")
        return 2
    result = scan()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(
        "сторож прямого повтора рецепта: %s; кейсов: %d; повторов: %d"
        % (
            result["статус"],
            result["прочитано_кейсов"],
            result["прямых_повторов_рецепта"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
