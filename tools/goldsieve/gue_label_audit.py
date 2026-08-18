#!/usr/bin/env python3
"""Пункт 1 приказа 2026-08-18: аудит метки величины 0,4220 (std Wigner surmise).

Задача: найти все места, где число 0,4220... стоит рядом со словами,
утверждающими ТОЧНЫЙ закон GUE, и отделить их от мест, где стоит
корректная метка «Wigner surmise».

Детерминированное делается кодом: поиск, классификация, отчёт.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOTS = [
    Path("/home/user/workspace/corpus/trinity"),
    Path("/home/user/workspace/goldsieve"),
    Path("/home/user/workspace/cron_tracking"),
]

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache"}
# Файлы, которые исключаются по существу: сырые данные (числа, а не текст) и
# сам аудитор с его отчётом (иначе паттерны ловят себя же).
SKIP_FILES = {
    "gue_label_audit.py",
    "gue_label_audit.json",
    "zeros_odlyzko_100k.txt",
}
TEXT_EXT = {
    ".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".tsv",
    ".rst", ".html", ".js", ".ts", ".zig", ".rs", ".toml", ".ipynb",
}
MAX_BYTES = 4_000_000

# 0.4220..., 0,4220..., 0.42201569..., но НЕ 0.4242 (точный GUE).
# Границы обязательны: иначе в файле нулей дзеты ловится хвост 27040.422044460.
NUM_RE = re.compile(r"(?<![\d.,])0[.,]4220\d*")

# ПОДПИСИ, утверждающие точный закон GUE. Слова «Fredholm» и «det(I−K)» здесь
# НЕ используются: в наших отчётах они стоят как КОНТРАСТ («точный Fredholm-GUE
# даёт 0,424258, поэтому 0,4220 — surmise»), то есть корректно.
EXACT_RE = re.compile(
    r"exact[_\s-]*gue|gue[_\s-]*exact|точн\w*\s+(?:закон\w*\s+)?gue|"
    r"gue\s*\(computed\)|gue[_\s-]*expected|(?:по|против)\s+GUE",
    re.IGNORECASE,
)
# Корректная метка.
SURMISE_RE = re.compile(r"surmise|вигнер|wigner", re.IGNORECASE)

WINDOW = 240  # символов контекста в каждую сторону


def iter_files():
    for root in ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in TEXT_EXT:
                continue
            if p.name in SKIP_FILES:
                continue
            try:
                if p.stat().st_size > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


def classify(text: str, m: re.Match) -> tuple[str, str]:
    lo = max(0, m.start() - WINDOW)
    hi = min(len(text), m.end() + WINDOW)
    ctx = text[lo:hi]
    exact = bool(EXACT_RE.search(ctx))
    surmise = bool(SURMISE_RE.search(ctx))
    if exact and not surmise:
        cls = "MISLABEL_EXACT"       # число surmise выдано за точный GUE
    elif exact and surmise:
        cls = "AMBIGUOUS_BOTH"      # оба слова рядом — требует чтения
    elif surmise:
        cls = "OK_SURMISE"
    else:
        cls = "UNLABELED"           # метки нет вовсе
    return cls, ctx.replace("\n", " ⏎ ")


def main() -> int:
    findings = []
    scanned = 0
    for p in iter_files():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        scanned += 1
        for m in NUM_RE.finditer(text):
            cls, ctx = classify(text, m)
            line = text.count("\n", 0, m.start()) + 1
            findings.append(
                {
                    "file": str(p),
                    "line": line,
                    "value": m.group(0),
                    "class": cls,
                    "context": ctx,
                }
            )
    counts: dict[str, int] = {}
    for f in findings:
        counts[f["class"]] = counts.get(f["class"], 0) + 1
    out = {
        "scanned_files": scanned,
        "hits": len(findings),
        "counts": counts,
        "findings": findings,
    }
    dest = Path("/home/user/workspace/goldsieve/gue_label_audit.json")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"файлов просмотрено: {scanned}; попаданий: {len(findings)}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"отчёт: {dest}")
    # для быстрой ручной сверки печатаем только проблемные классы
    for f in findings:
        if f["class"] in ("MISLABEL_EXACT", "UNLABELED", "AMBIGUOUS_BOTH"):
            print(f"\n[{f['class']}] {f['file']}:{f['line']}  {f['value']}")
            print(f"   …{f['context'][:300]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
