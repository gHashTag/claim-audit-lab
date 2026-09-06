#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож границы путей локальных источников реестра.

Проверка существования файла недостаточна: символическая ссылка может
разрешиться за пределами корпуса или рабочей копии и подменить наблюдаемое.
Этот сторож отделяет разрешимость входа от его допустимой области.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - штатный пропуск среды без yaml
    yaml = None


HERE = Path(__file__).resolve().parent
CORPUS = Path("/home/user/workspace/corpus/trinity").resolve()
REGISTRY = HERE / "claims.yaml"
OUT = HERE / "source_path_boundary_guard.json"


def _inside(path: Path, roots: tuple[Path, ...]) -> bool:
    """Проверить разрешённый путь после разрешения символических ссылок."""
    return any(
        path == root or root in path.parents
        for root in roots
    )


def _fragments(value: object) -> list[str]:
    text = str(value or "").strip()
    return [item.strip() for item in re.split(r";", text) if item.strip()]


def _candidates(fragment: str) -> list[Path]:
    raw_values = [fragment]
    if ":" in fragment and not fragment.startswith("/"):
        raw_values.append(fragment.split(":", 1)[0].strip())
    candidates: list[Path] = []
    for raw_value in raw_values:
        raw = Path(raw_value)
        candidates.extend(
            [raw] if raw.is_absolute() else [CORPUS / raw, HERE / raw]
        )
    return candidates


def scan(registry: Path = REGISTRY) -> dict:
    """Проверить область всех разрешимых локальных фрагментов ``source``."""
    if yaml is None:
        return {
            "статус": "unsupported",
            "причина": "модуль yaml отсутствует",
            "реестр": str(registry),
        }
    data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    entries = data.get("claims", [])
    roots = (CORPUS, HERE)
    violations: list[dict] = []
    checked = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        for fragment in _fragments(entry.get("source")):
            if fragment.startswith(("http://", "https://")):
                continue
            for candidate in _candidates(fragment):
                resolved = candidate.resolve()
                if not resolved.is_file():
                    continue
                checked += 1
                if not _inside(resolved, roots):
                    violations.append({
                        "индекс": index,
                        "case": entry.get("case", ""),
                        "фрагмент": fragment,
                        "разрешённый_путь": str(resolved),
                    })
                break
    return {
        "статус": "verified-in-scope" if not violations else "not-evaluated",
        "реестр": str(registry),
        "проверено_локальных_файлов": checked,
        "нарушения": violations,
        "разрешённые_корни": [str(root) for root in roots],
        "ограничение": (
            "граница пути не доказывает содержательную независимость "
            "observed/reference"
        ),
    }


def selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="goldsieve-source-boundary-") as tmp:
        root = Path(tmp)
        inside = root / "inside.md"
        outside = root / "outside.md"
        inside.write_text("наблюдаемое\n", encoding="utf-8")
        outside.write_text("внешнее\n", encoding="utf-8")
        link = root / "link.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            print("самопроверка границы путей источника: unsupported (нет symlink)")
            return 0
        good = _inside(inside.resolve(), (root,))
        bad = not _inside(link.resolve(), (inside.parent / "другая",))
        checks = [good, bad]
    passed = sum(checks)
    failed = len(checks) - passed
    print("самопроверка границы путей источника: "
          "пройдено %d, провалено %d" % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="проверка области source")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = scan()
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("сторож границы путей источника: %s; проверено %d; нарушений %d" % (
        result["статус"],
        result.get("проверено_локальных_файлов", 0),
        len(result.get("нарушения", [])),
    ))
    return 0 if result["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    raise SystemExit(main())
