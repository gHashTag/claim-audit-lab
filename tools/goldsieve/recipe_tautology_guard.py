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


def _bindings(tree: ast.AST) -> dict[str, ast.AST]:
    """Собрать только простые присваивания, пригодные для безопасного раскрытия.

    Прямое сравнение AST не видит вырожденный случай, когда один и тот же
    callable передан через простую псевдонимную цепочку::

        recipe = lambda: 1
        observed_recipe = recipe
        Claim(observed=observed_recipe, reference=recipe)

    Здесь намеренно не вычисляется произвольный Python-код: раскрываются лишь
    присваивания одного имени одному выражению. Сложные случаи остаются за
    пределами этого сторожа и не превращаются в доказательство независимости.
    """
    bindings: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                bindings[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                bindings[node.target.id] = node.value
    return bindings


def _normal(
    node: ast.AST,
    bindings: dict[str, ast.AST] | None = None,
    resolving: frozenset[str] = frozenset(),
) -> str:
    """Каноническое представление выражения без позиций в файле.

    Простые псевдонимы раскрываются до фиксированной точки. Циклические
    присваивания намеренно не раскрываются дальше имени.
    """
    bindings = bindings or {}
    if isinstance(node, ast.Name) and node.id in bindings:
        if node.id in resolving:
            return ast.dump(node, annotate_fields=True, include_attributes=False)
        return _normal(
            bindings[node.id], bindings, resolving | frozenset({node.id})
        )
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def _claim_rows(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bindings = _bindings(tree)
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
        if _normal(observed, bindings) != _normal(reference, bindings):
            continue
        rows.append(
            {
                "путь": str(path),
                "строка": getattr(node, "lineno", None),
                "риск": "observed_reference_same_recipe",
                "статус": "not-evaluated",
                "причина": (
                    "поля observed и reference содержат один и тот же "
                    "рецепт (включая простые псевдонимы); сравнение не является "
                    "независимым"
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
    # Область входа и научный результат — разные утверждения. Сам факт, что
    # реальные файлы кейсов найдены и прочитаны для AST-аудита, устанавливает
    # границу входа; найденный прямой повтор по-прежнему оставляет научный
    # риск not-evaluated. Не смешиваем эти статусы в один флаг.
    input_status = "verified-in-scope" if paths else "not-evaluated"
    return {
        "статус": "not-evaluated" if rows else "verified-in-scope",
        "статус_входа": input_status,
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
        indirect = root / "indirect.py"
        indirect.write_text(
            "from goldsieve.sieve import Claim\n"
            "recipe = lambda: 1\n"
            "observed_recipe = recipe\n"
            "CLAIMS = [Claim(name='indirect', source='x', "
            "reference=recipe, observed=observed_recipe)]\n",
            encoding="utf-8",
        )
        same_rows = _claim_rows(same)
        different_rows = _claim_rows(different)
        indirect_rows = _claim_rows(indirect)
        check("одинаковый AST получает not-evaluated", len(same_rows) == 1)
        check("разные имена callable не получают прямой повтор",
              different_rows == [])
        check("простая псевдонимная цепочка получает not-evaluated",
              len(indirect_rows) == 1
              and "псевдонимы" in indirect_rows[0]["причина"])
        broken = root / "broken.py"
        broken.write_text("def broken(:\n", encoding="utf-8")
        report = scan(root)
        check("ошибка разбора не становится покрытием",
              report["статус"] == "not-evaluated"
              and report["статус_входа"] == "verified-in-scope"
              and any(row["статус"] == "not-evaluated"
                      for row in report["наблюдения"]))
        empty = scan(root / "missing")
        check("отсутствие входа явно not-evaluated",
              empty["статус_входа"] == "not-evaluated")

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
        "сторож прямого повтора рецепта: %s; статус входа: %s; "
        "кейсов: %d; повторов: %d"
        % (
            result["статус"],
            result["статус_входа"],
            result["прочитано_кейсов"],
            result["прямых_повторов_рецепта"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
