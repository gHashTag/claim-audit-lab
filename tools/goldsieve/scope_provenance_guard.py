#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож происхождения статуса verified-in-scope в реестре.

Разрешимый путь ``source`` ещё не доказывает принадлежность наблюдаемого
корпусу: путь может указывать на рабочую копию инструмента. Для записи,
помеченной ``verified-in-scope``, каждый локальный фрагмент источника обязан
разрешаться именно внутри corpus/trinity. Внешний URL и путь рабочей копии
оставляются как not-evaluated.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - штатный пропуск гейта
    yaml = None


HERE = Path(__file__).resolve().parent
CORPUS = Path("/home/user/workspace/corpus/trinity").resolve()
REGISTRY = HERE / "claims.yaml"
OUT = HERE / "scope_provenance_guard.json"


def _fragments(value: object) -> list[str]:
    text = str(value or "").strip()
    return [item.strip() for item in re.split(r";", text) if item.strip()]


def _resolve_in_corpus(fragment: str, corpus_root: Path) -> Path | None:
    if fragment.startswith(("http://", "https://")):
        return None
    raw = fragment
    if ":" in raw and not raw.startswith("/"):
        raw = raw.split(":", 1)[0].strip()
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = corpus_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(corpus_root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def scan(registry: Path = REGISTRY, corpus_root: Path = CORPUS) -> dict:
    if yaml is None:
        return {
            "статус": "unsupported",
            "причина": "модуль yaml отсутствует",
            "реестр": str(registry),
        }
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, ValueError) as exc:
        return {
            "статус": "not-evaluated",
            "причина": "реестр не прочитан: %s" % exc,
            "реестр": str(registry),
        }
    entries = data.get("claims", [])
    observations: list[dict] = []
    failures: list[dict] = []
    checked = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        if entry.get("scope_status") != "verified-in-scope":
            continue
        checked += 1
        source = entry.get("source", "")
        paths = []
        reasons = []
        for fragment in _fragments(source):
            path = _resolve_in_corpus(fragment, corpus_root)
            if path is None:
                reasons.append("фрагмент не разрешается внутри корпуса: %s"
                               % fragment)
            else:
                paths.append(str(path))
        row = {
            "индекс": index,
            "case": entry.get("case", ""),
            "источник": source,
            "пути_в_корпусе": paths,
        }
        if reasons:
            row["статус"] = "not-evaluated"
            row["причины"] = reasons
            failures.append(row)
        else:
            row["статус"] = "verified-in-scope"
            observations.append(row)
    status = "verified-in-scope" if checked and not failures else "not-evaluated"
    return {
        "статус": status,
        "реестр": str(registry),
        "корпус": str(corpus_root),
        "проверено_записей": checked,
        "наблюдения": observations,
        "неподтверждённые": failures,
        "ограничение": (
            "принадлежность пути корпусу не доказывает независимость "
            "наблюдаемого и эталонного вычислительных путей"
        ),
    }


def selftest() -> int:
    if yaml is None:
        print("самопроверка сторожа происхождения статуса: unsupported (нет yaml)")
        return 0
    with tempfile.TemporaryDirectory(prefix="goldsieve-scope-provenance-") as tmp:
        root = Path(tmp)
        corpus = root / "corpus"
        corpus.mkdir()
        (corpus / "observed.md").write_text("наблюдаемое\n", encoding="utf-8")
        (root / "tool.md").write_text("инструмент\n", encoding="utf-8")

        def registry(source: str) -> Path:
            path = root / ("registry-%d.yaml" % len(list(root.glob("registry-*.yaml"))))
            path.write_text(
                "claims:\n"
                "  - scope_status: verified-in-scope\n"
                "    source: %s\n"
                "    case: cases/x.py\n" % source,
                encoding="utf-8",
            )
            return path

        good = scan(registry("observed.md:1"), corpus)
        worktree = scan(registry(str(root / "tool.md")), corpus)
        url = scan(registry("https://example.invalid/observed"), corpus)
        missing = scan(registry("missing.md"), corpus)
    checks = [
        good["статус"] == "verified-in-scope",
        worktree["статус"] == "not-evaluated",
        url["статус"] == "not-evaluated",
        missing["статус"] == "not-evaluated",
    ]
    passed = sum(checks)
    failed = len(checks) - passed
    print("самопроверка сторожа происхождения статуса: "
          "пройдено %d, провалено %d" % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="проверка происхождения verified-in-scope")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    result = scan()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож происхождения статуса: %s; проверено %d; "
          "неподтверждённых %d" % (
              result["статус"],
              result.get("проверено_записей", 0),
              len(result.get("неподтверждённые", [])),
          ))
    return 0 if result["статус"] in ("verified-in-scope", "unsupported") else 1


if __name__ == "__main__":
    raise SystemExit(main())
