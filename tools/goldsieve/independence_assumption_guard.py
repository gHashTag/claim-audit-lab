#!/usr/bin/env python3
"""Сторож предпосылки независимости испытаний в кейсах.

Риск. Поле ``tests_independent`` влияет на смысл порогов множественности, но
старые кейсы могли молча не предъявлять его. Молчание не считается
независимостью: запись получает ``not-evaluated`` с точным путём и строкой.
Сторож не доказывает научную независимость и не превращает декларацию в
подтверждение; он только делает отсутствие предпосылки наблюдаемым.

Режимы:
  python3 independence_assumption_guard.py --selftest
  python3 independence_assumption_guard.py --scan
"""
from __future__ import annotations

import ast
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases"
OUT = ROOT / "independence_assumption_guard.json"
ALLOWED = {"unknown", "not-declared", "true", "false", True, False}


def _call_is_claim(node: ast.Call) -> bool:
    return ((isinstance(node.func, ast.Name) and node.func.id == "Claim")
            or (isinstance(node.func, ast.Attribute)
                and node.func.attr == "Claim"))


def _constant(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def scan(cases_dir: Path = CASES) -> dict:
    """Сканирует AST кейсов, не импортируя их и не меняя sys.modules."""
    observations: list[dict] = []
    parse_errors: list[dict] = []
    for path in sorted(cases_dir.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            parse_errors.append({
                "путь": str(path),
                "статус": "unsupported",
                "причина": "файл кейса не разобран: %s" % exc,
            })
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _call_is_claim(node):
                continue
            kw = next((item for item in node.keywords
                       if item.arg == "tests_independent"), None)
            if kw is None:
                status = "not-evaluated"
                reason = "independence_assumption_absent"
                value = None
            else:
                value = _constant(kw.value)
                if value in ("true", True):
                    # Декларация автора кейса — наблюдаемое поле, но не
                    # независимое доказательство независимости испытаний.
                    # Нельзя повышать такой вход до verified-in-scope:
                    # иначе сам сторож принимает предпосылку за её проверку.
                    status = "not-evaluated"
                    reason = "independence_assumption_declared_true_unverified"
                elif value in ("false", False):
                    status = "unsupported"
                    reason = "tests_declared_not_independent"
                elif value in ("unknown", "not-declared"):
                    status = "not-evaluated"
                    reason = "independence_assumption_unknown"
                else:
                    status = "unsupported"
                    reason = "independence_assumption_nonliteral"
            observations.append({
                "путь": str(path),
                "строка": node.lineno,
                "статус": status,
                "код_причины": reason,
                "tests_independent": value,
            })

    counts = {key: sum(x["статус"] == key for x in observations)
              for key in ("verified-in-scope", "not-evaluated",
                          "unsupported", "platform-unverified")}
    report = {
        "контракт": "явная предпосылка независимости испытаний",
        "статус": ("unsupported" if parse_errors else
                   ("not-evaluated" if counts["not-evaluated"]
                    else "verified-in-scope")),
        "причина": (
            "отсутствующие и неизвестные декларации не считаются независимостью"
            if counts["not-evaluated"] else
            "все найденные декларации имеют допустимое значение"),
        "источник_наблюдения": str(cases_dir),
        "кейсов": len(observations),
        "сводка": counts,
        "наблюдения": observations,
        "ошибки_разбора": parse_errors,
    }
    return report


def _assert(condition: bool, text: str) -> None:
    if not condition:
        raise AssertionError(text)


def selftest() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "positive.py").write_text(
            "class Claim: pass\n"
            "x = Claim(tests_independent='true')\n",
            encoding="utf-8")
        (root / "unknown.py").write_text(
            "class Claim: pass\n"
            "x = Claim(tests_independent='unknown')\n",
            encoding="utf-8")
        (root / "missing.py").write_text(
            "class Claim: pass\n"
            "x = Claim()\n",
            encoding="utf-8")
        (root / "negative.py").write_text(
            "class Claim: pass\n"
            "x = Claim(tests_independent='false')\n",
            encoding="utf-8")
        report = scan(root)
        values = {x["статус"] for x in report["наблюдения"]}
        _assert(report["кейсов"] == 4, "обнаружены не все фикстуры")
        _assert(values == {"not-evaluated", "unsupported"},
                "неверная классификация фикстур")
        _assert(report["сводка"]["not-evaluated"] == 3,
                "декларация true или молчание не понижены до not-evaluated")
        print("самопроверка предпосылки независимости: 4/0")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--scan" not in argv:
        print("режим: --selftest или --scan")
        return 2
    report = scan()
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож предпосылки независимости: %s; кейсов %d; сводка %s" %
          (report["статус"], report["кейсов"],
           json.dumps(report["сводка"], ensure_ascii=False, sort_keys=True)))
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
