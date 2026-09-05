#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож неоднозначного ключа реестра регресса.

Регресс сопоставляет свежий вердикт с парой ``case + claim``. Повтор такой
пары делает сопоставление неоднозначным: один новый результат может быть
сравнен с другой строкой реестра. Сторож проверяет этот риск до прогона и
отдельно удостоверяется, что указанные файлы кейсов существуют. Он не
исполняет модули кейсов и не восстанавливает отсутствующие записи.

Команды:
    python3 registry_identity_guard.py
    python3 registry_identity_guard.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "claims.yaml"
OUT = ROOT / "registry_identity_guard.json"


def _normalise(value: object) -> str:
    return " ".join(str(value or "").split()).casefold()


def _read_registry(path: Path) -> list[dict]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("зависимость yaml недоступна") from exc
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = document.get("claims") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        raise ValueError("реестр не содержит списка claims")
    return [row for row in rows if isinstance(row, dict)]


def inspect(registry: Path = REGISTRY, root: Path = ROOT) -> dict:
    try:
        rows = _read_registry(registry)
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "статус": "unsupported",
            "причина": str(exc),
            "источник_наблюдения": str(registry),
            "записей": 0,
            "дубли": [],
            "отсутствующие_кейсы": [],
        }

    seen: dict[tuple[str, str], list[int]] = {}
    missing: list[dict] = []
    malformed: list[int] = []
    for number, row in enumerate(rows, start=1):
        case = str(row.get("case") or "").strip()
        claim = _normalise(row.get("claim"))
        if not case or not claim:
            malformed.append(number)
            continue
        key = (case, claim)
        seen.setdefault(key, []).append(number)
        case_path = Path(case)
        if not case_path.is_absolute():
            case_path = root / case_path
        if not case_path.is_file():
            missing.append({
                "строка": number,
                "case": case,
                "источник_наблюдения": str(case_path),
            })

    duplicates = [
        {
            "case": case,
            "claim": claim,
            "строки": numbers,
        }
        for (case, claim), numbers in sorted(seen.items())
        if len(numbers) > 1
    ]
    if malformed or duplicates or missing:
        status = "unsupported"
        reasons = []
        if duplicates:
            reasons.append("найдены повторяющиеся пары case+claim")
        if malformed:
            reasons.append("есть записи без непустых case и claim")
        if missing:
            reasons.append("есть кейсы, которых нет по указанному пути")
        reason = "; ".join(reasons)
    else:
        status = "verified-in-scope"
        reason = "ключи case+claim однозначны, все файлы кейсов предъявлены"
    return {
        "статус": status,
        "причина": reason,
        "источник_наблюдения": str(registry),
        "записей": len(rows),
        "уникальных_ключей": len(seen),
        "дубли": duplicates,
        "неполные_строки": malformed,
        "отсутствующие_кейсы": missing,
        "ограничение": (
            "проверена однозначность ключа реестра; научная истинность "
            "вердиктов и содержимое модулей кейсов не оцениваются"
        ),
    }


def _write(result: dict) -> None:
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")


def selftest() -> int:
    good = bad = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            good += 1
            print("  ок   " + name)
        else:
            bad += 1
            print("  ПРОВАЛ   " + name)

    with tempfile.TemporaryDirectory(prefix="registry-identity-") as temp:
        root = Path(temp)
        (root / "cases").mkdir()
        (root / "cases" / "one.py").write_text("# фикстура\n", encoding="utf-8")
        good_registry = root / "good.yaml"
        good_registry.write_text(
            "claims:\n"
            "- case: cases/one.py\n"
            "  claim:  одно утверждение  \n",
            encoding="utf-8",
        )
        result = inspect(good_registry, root)
        check("уникальная пара и существующий кейс проходят",
              result["статус"] == "verified-in-scope")

        duplicate_registry = root / "duplicate.yaml"
        duplicate_registry.write_text(
            "claims:\n"
            "- case: cases/one.py\n"
            "  claim: одно утверждение\n"
            "- case: cases/one.py\n"
            "  claim:  одно   утверждение\n",
            encoding="utf-8",
        )
        result = inspect(duplicate_registry, root)
        check("повтор ключа ловится", bool(result["дубли"]))

        missing_registry = root / "missing.yaml"
        missing_registry.write_text(
            "claims:\n"
            "- case: cases/absent.py\n"
            "  claim: другое утверждение\n",
            encoding="utf-8",
        )
        result = inspect(missing_registry, root)
        check("отсутствующий файл не считается покрытием",
              result["статус"] == "unsupported")

    print("самопроверка неоднозначного ключа реестра: "
          f"{good} пройдено, {bad} провалено")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = inspect()
    _write(result)
    print("сторож неоднозначного ключа реестра: "
          f"{result['статус']}; записей {result['записей']}, "
          f"уникальных ключей {result.get('уникальных_ключей', 0)}, "
          f"дублей {len(result['дубли'])}, "
          f"отсутствующих кейсов {len(result['отсутствующие_кейсы'])}")
    print(f"JSON: {OUT}")
    return 0 if result["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    sys.exit(main())
