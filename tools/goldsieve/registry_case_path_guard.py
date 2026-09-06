#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож границы путей кейсов в реестре регресса.

Поле ``case`` является исполняемым входом регресса. Проверка существования
файла сама по себе недостаточна: ``../`` или симлинк могут вывести загрузку
модуля за пределы рабочей копии и корпуса. Этот сторож требует, чтобы
разрешённый путь кейса оставался внутри рабочей копии инструмента.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - штатный пропуск среды без yaml
    yaml = None


HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "claims.yaml"
OUT = HERE / "registry_case_path_guard.json"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def scan(registry: Path = REGISTRY, root: Path = HERE) -> dict:
    """Проверить существование и границу каждого пути ``case``."""
    if yaml is None:
        return {
            "статус": "unsupported",
            "причина": "модуль yaml отсутствует",
            "источник_наблюдения": str(registry),
            "записей": 0,
            "нарушения": [],
        }
    try:
        document = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError) as exc:
        return {
            "статус": "unsupported",
            "причина": str(exc),
            "источник_наблюдения": str(registry),
            "записей": 0,
            "нарушения": [],
        }
    rows = document.get("claims") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        return {
            "статус": "unsupported",
            "причина": "реестр не содержит списка claims",
            "источник_наблюдения": str(registry),
            "записей": 0,
            "нарушения": [],
        }

    root_resolved = root.resolve()
    violations: list[dict] = []
    for number, row in enumerate(rows, start=1):
        case = str(row.get("case") or "").strip() if isinstance(row, dict) else ""
        if not case:
            violations.append({
                "строка": number,
                "case": case,
                "причина": "пустой путь кейса",
                "источник_наблюдения": str(registry),
            })
            continue
        raw = Path(case)
        candidate = raw if raw.is_absolute() else root_resolved / raw
        resolved = candidate.resolve()
        if not _inside(resolved, root_resolved):
            violations.append({
                "строка": number,
                "case": case,
                "разрешённый_путь": str(resolved),
                "причина": "путь или симлинк выходит за пределы рабочей копии",
                "источник_наблюдения": str(registry),
            })
        elif not resolved.is_file():
            violations.append({
                "строка": number,
                "case": case,
                "разрешённый_путь": str(resolved),
                "причина": "файл кейса отсутствует",
                "источник_наблюдения": str(registry),
            })

    status = "verified-in-scope" if not violations else "unsupported"
    return {
        "статус": status,
        "причина": (
            "все пути кейсов внутри рабочей копии и предъявлены"
            if not violations else
            "граница или существование пути кейса не подтверждены"
        ),
        "источник_наблюдения": str(registry),
        "рабочая_копия": str(root_resolved),
        "записей": len(rows),
        "нарушения": violations,
        "ограничение": (
            "проверена только граница загрузочного пути; содержательная "
            "корректность кейса не оценивается"
        ),
    }


def selftest() -> int:
    """Проверить положительный путь, переход наружу и симлинк наружу."""
    if yaml is None:
        print("самопроверка границы путей кейсов: unsupported (нет yaml)")
        return 0
    with tempfile.TemporaryDirectory(prefix="goldsieve-case-path-") as tmp:
        root = Path(tmp)
        (root / "cases").mkdir()
        (root / "cases" / "ok.py").write_text("# кейс\n", encoding="utf-8")
        outside = root.parent / (root.name + "-outside.py")
        outside.write_text("# вне корня\n", encoding="utf-8")
        good = root / "good.yaml"
        good.write_text(
            "claims:\n- case: cases/ok.py\n  claim: одно\n",
            encoding="utf-8",
        )
        escape = root / "escape.yaml"
        escape.write_text(
            "claims:\n- case: ../outside.py\n  claim: другое\n",
            encoding="utf-8",
        )
        symlink = root / "cases" / "link.py"
        symlink_supported = True
        try:
            symlink.symlink_to(outside)
        except (OSError, NotImplementedError):
            symlink_supported = False
        link = root / "link.yaml"
        link.write_text(
            "claims:\n- case: cases/link.py\n  claim: третье\n",
            encoding="utf-8",
        )
        good_result = scan(good, root)
        escape_result = scan(escape, root)
        link_result = scan(link, root)
        outside.unlink(missing_ok=True)
    checks = [
        good_result["статус"] == "verified-in-scope",
        escape_result["статус"] == "unsupported",
    ]
    if symlink_supported:
        checks.append(link_result["статус"] == "unsupported")
    passed = sum(checks)
    failed = len(checks) - passed
    print("самопроверка границы путей кейсов: пройдено %d, провалено %d"
          % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="граница путей кейсов реестра")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = scan()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож границы путей кейсов: %s; записей %d; нарушений %d"
          % (result["статус"], result["записей"], len(result["нарушения"])))
    print("JSON: %s" % OUT)
    return 0 if result["статус"] in ("verified-in-scope", "unsupported") else 1


if __name__ == "__main__":
    raise SystemExit(main())
