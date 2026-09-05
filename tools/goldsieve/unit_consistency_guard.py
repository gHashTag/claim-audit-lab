#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож согласованности единиц внешней сверки.

Числа с одинаковым написанием не сопоставимы, если наблюдаемое и внешний
эталон предъявлены в разных единицах. Отсутствие единицы не превращается в
совпадение: такой артефакт остаётся ``not-evaluated``. Несогласованная или
повреждённая единица получает ``unsupported``. Сторож проверяет только
контракт единиц и не выносит научный вердикт.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
TRACKING = Path("/home/user/workspace/cron_tracking/8dff7aa3")
OUT = HERE / "unit_consistency_guard.json"

OBSERVED_UNIT_KEYS = (
    "observed_unit",
    "единица_наблюдаемого",
    "единица_наблюдения",
    "unit_observed",
)
TARGET_UNIT_KEYS = ("unit", "единица", "units")

# Канонизация ограничена очевидными вариантами написания; неизвестное
# обозначение не угадывается и остаётся отдельной единицей.
ALIASES = {
    "gev": "gev",
    "гэв": "gev",
    "гэв/c2": "gev/c2",
    "gev/c2": "gev/c2",
    "mev": "mev",
    "мэв": "mev",
    "kev": "kev",
    "кэв": "kev",
    "ev": "ev",
    "эв": "ev",
    "k": "k",
    "к": "k",
    "fm": "fm",
    "фм": "fm",
    "degree": "degree",
    "degrees": "degree",
    "градус": "degree",
    "градусы": "degree",
    "°": "degree",
}


def _unit(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = re.sub(r"\s+", " ", str(value).strip().lower())
    if not text:
        return None
    text = text.replace("−", "-").replace("²", "^2")
    text = text.replace(" ", "")
    return ALIASES.get(text, text)


def _external_target(artifact: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    for key in ("external_target", "внешняя_цель"):
        if key not in artifact:
            continue
        value = artifact[key]
        return True, value if isinstance(value, dict) else None
    return False, None


def _observed_unit(artifact: dict[str, Any]) -> str | None:
    for key in OBSERVED_UNIT_KEYS:
        if key in artifact:
            return _unit(artifact[key])
    observed = artifact.get("наблюдаемое")
    if isinstance(observed, dict):
        for key in ("unit", "единица"):
            if key in observed:
                return _unit(observed[key])
    return None


def _target_unit(target: dict[str, Any]) -> str | None:
    for key in TARGET_UNIT_KEYS:
        if key in target:
            return _unit(target[key])
    return None


def inspect(artifact: dict[str, Any], path: str) -> dict[str, Any]:
    found, target = _external_target(artifact)
    row: dict[str, Any] = {"путь": path, "прочитано": True}
    if not found:
        row.update({"статус": "not-evaluated", "причина": "внешняя цель не предъявлена"})
        return row
    if target is None:
        row.update({
            "статус": "unsupported",
            "причина": "поле внешней цели не является объектом",
        })
        return row
    observed = _observed_unit(artifact)
    external = _target_unit(target)
    row["единица_наблюдаемого"] = observed
    row["единица_внешней_цели"] = external
    if observed is None or external is None:
        row.update({
            "статус": "not-evaluated",
            "причина": "явные единицы наблюдаемого и внешней цели не предъявлены",
        })
    elif observed != external:
        row.update({
            "статус": "unsupported",
            "причина": "единицы наблюдаемого и внешней цели расходятся",
        })
    else:
        row.update({
            "статус": "verified-in-scope",
            "причина": "канонизированные единицы совпадают",
        })
    return row


def _documents(root: Path = TRACKING) -> list[Path]:
    return sorted(path for path in root.glob("*.json") if path.name != OUT.name)


def scan(root: Path = TRACKING) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in _documents(root):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        items = document if isinstance(document, list) else [document]
        for number, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            row = inspect(item, f"{path}#{number}" if isinstance(document, list) else str(path))
            if "external_target" in item or "внешняя_цель" in item:
                rows.append(row)
    counts: dict[str, int] = {}
    for row in rows:
        status = row["статус"]
        counts[status] = counts.get(status, 0) + 1
    return {
        "статус": "verified-in-scope",
        "проверено_артефактов": len(rows),
        "сводка": counts,
        "наблюдения": rows,
        "ограничение": (
            "проверка единиц не подтверждает значение измерения; "
            "отсутствующая единица остаётся not-evaluated"
        ),
    }


def selftest() -> int:
    fixtures = [
        ("одинаковые единицы", {"observed_unit": "МэВ", "external_target": {"unit": "MeV"}}, "verified-in-scope"),
        ("разные единицы", {"observed_unit": "МэВ", "external_target": {"unit": "ГэВ"}}, "unsupported"),
        ("нет единицы наблюдаемого", {"external_target": {"unit": "МэВ"}}, "not-evaluated"),
        ("нет единицы внешней цели", {"observed_unit": "МэВ", "external_target": {}}, "not-evaluated"),
        ("повреждённая внешняя цель", {"external_target": "не объект"}, "unsupported"),
        ("синонимы градуса", {"наблюдаемое": {"единица": "градусы"}, "внешняя_цель": {"единица": "°"}}, "verified-in-scope"),
    ]
    failed = 0
    for name, artifact, expected in fixtures:
        actual = inspect(artifact, name)["статус"]
        ok = actual == expected
        print("  %s  %s" % ("ок" if ok else "ПРОВАЛ", name))
        failed += 0 if ok else 1
    print("самопроверка согласованности единиц: пройдено %d, провалено %d"
          % (len(fixtures) - failed, failed))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    result = scan()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("сторож согласованности единиц: %s; артефактов: %d; сводка: %s"
          % (result["статус"], result["проверено_артефактов"],
             json.dumps(result["сводка"], ensure_ascii=False, sort_keys=True)))
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
