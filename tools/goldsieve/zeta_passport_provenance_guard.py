#!/usr/bin/env python3
"""Сторож происхождения наблюдаемого числа в паспорте zeta.

Риск: паспорт может сохранить число 0,4009 и ссылку на документ, но не
проверить, что ссылка существует, что число действительно прочитано из неё и
что снимок входов соответствует тому же корпусу. Такой разрыв происхождения
не является научным опровержением; он понижает запись до not-evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CORPUS = Path("/home/user/workspace/corpus/trinity")
DOC_GUE = CORPUS / "data/zeta/zeta_gue_analysis_results.md"
ZEROS = CORPUS / "data/zeta/zeros_odlyzko_100k.txt"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _observed(path: Path) -> float:
    text = path.read_text(encoding="utf-8", errors="strict")
    rows = re.findall(
        r"^\|\s*Std deviation\s*\|\s*([0-9]+(?:[.,][0-9]+)?)\s*\|",
        text,
        flags=re.MULTILINE,
    )
    if len(rows) != 1:
        raise ValueError(
            "ожидалась ровно одна строка Std deviation, найдено %d" % len(rows)
        )
    return float(rows[0].replace(",", "."))


def _validate(passport: dict, document: Path, zeros: Path) -> list[str]:
    problems: list[str] = []
    if not isinstance(passport, dict):
        return ["корень паспорта не является объектом"]
    recipe = passport.get("паспорт_рецепта")
    observed = passport.get("наблюдаемое_из_корпуса")
    if not isinstance(recipe, dict):
        problems.append("отсутствует объект паспорт_рецепта")
    if not isinstance(observed, dict):
        problems.append("отсутствует объект наблюдаемое_из_корпуса")
        return problems
    if observed.get("source") != str(document):
        problems.append("источник наблюдаемого не совпадает с проверяемым путём")
    if observed.get("field") != "Std deviation / Value":
        problems.append("поле наблюдаемого не совпадает с корпусным полем")
    try:
        value = float(observed["value"])
        actual = _observed(document)
        if abs(value - actual) > 1e-12:
            problems.append("число наблюдаемого не совпадает с прочитанным числом")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        problems.append("наблюдаемое не прочитано строго: %s" % exc)
    if not document.is_file():
        problems.append("файл наблюдаемого отсутствует")
    if not zeros.is_file():
        problems.append("файл нулей отсутствует")
    if isinstance(recipe, dict):
        if recipe.get("документы", {}).get(str(document)) != _sha256(document):
            problems.append("хеш документа наблюдаемого не совпадает")
        if recipe.get("набор_нулей") != str(zeros):
            problems.append("путь набора нулей не совпадает")
        if recipe.get("sha256") != _sha256(zeros):
            problems.append("хеш набора нулей не совпадает")
    return problems


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="zeta-passport-") as name:
        base = Path(name)
        doc = base / "наблюдаемое.md"
        zeros = base / "нули.txt"
        doc.write_text("| Std deviation | 0,4009 |\n", encoding="utf-8")
        zeros.write_text("1\n2\n", encoding="utf-8")
        good = {
            "паспорт_рецепта": {
                "документы": {str(doc): _sha256(doc)},
                "набор_нулей": str(zeros),
                "sha256": _sha256(zeros),
            },
            "наблюдаемое_из_корпуса": {
                "value": 0.4009,
                "source": str(doc),
                "field": "Std deviation / Value",
            },
        }
        cases = [
            ("полный источник принимается", good, False),
            ("подмена числа отвергается", {**good, "наблюдаемое_из_корпуса": {
                **good["наблюдаемое_из_корпуса"], "value": 0.401,
            }}, True),
            ("подмена пути отвергается", {**good, "наблюдаемое_из_корпуса": {
                **good["наблюдаемое_из_корпуса"], "source": "/tmp/чужой.md",
            }}, True),
        ]
        failed = 0
        for title, passport, should_fail in cases:
            got_fail = bool(_validate(passport, doc, zeros))
            if got_fail != should_fail:
                failed += 1
                print("ПРОВАЛ %s" % title)
            else:
                print("ok      %s" % title)
        print("самопроверка происхождения паспорта zeta: %d пройдено, %d провалено"
              % (len(cases) - failed, failed))
        return 1 if failed else 0


def _scan() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "zeta_passport.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=300,
        check=False,
    )
    if proc.returncode != 0:
        print("сторож происхождения паспорта zeta: паспорт не завершился кодом 0")
        return 1
    try:
        passport = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print("сторож происхождения паспорта zeta: вывод не является JSON: %s" % exc)
        return 1
    problems = _validate(passport, DOC_GUE, ZEROS)
    result = {
        "статус": "verified-in-scope" if not problems else "not-evaluated",
        "прочитано": str(DOC_GUE),
        "проблемы": problems,
    }
    (ROOT / "zeta_passport_provenance_guard.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if problems:
        print("сторож происхождения паспорта zeta: not-evaluated")
        for problem in problems:
            print("  %s" % problem)
        return 1
    print("сторож происхождения паспорта zeta: verified-in-scope; "
          "наблюдаемое прочитано из %s" % DOC_GUE)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    return _selftest() if args.selftest else _scan()


if __name__ == "__main__":
    sys.exit(main())
