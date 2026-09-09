#!/usr/bin/env python3
"""Пункт 1 приказа 2026-08-18: точная правка подписей числа 0,4220 в корпусе.

Число 0,4220156929501229 = sqrt(3*pi/8 - 1) — стандартное отклонение WIGNER
SURMISE, а не точного (Fredholm) закона GUE, который даёт 0,4242576222440628.
Правка НЕ меняет ни одного числа: меняются ТОЛЬКО подписи столбцов и строк,
где стоит «GUE» без указания, что это surmise.

Скрипт идемпотентен: повторный прогон не делает изменений.
Каждый файл фиксируется sha256 до и после; отчёт — JSON + unified diff.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import sys
from pathlib import Path

CORPUS = Path("/home/user/workspace/corpus/trinity/data/zeta")

# (файл, что заменить, на что) — точные строки, без regex.
EDITS: list[tuple[str, str, str]] = [
    (
        "zeta_gue_analysis_results.md",
        "| Metric | Value | GUE (computed) | Deviation | Status |",
        "| Metric | Value | GUE Wigner surmise (computed) | Deviation | Status |",
    ),
    (
        "zeta_gue_analysis_results.md",
        "3. ⚠️ **Std deviation = 0.401** vs GUE 0.4220 = √(3π/8 − 1) → −5.0%",
        "3. ⚠️ **Std deviation = 0.401** vs GUE Wigner surmise 0.4220 = √(3π/8 − 1) "
        "(exact Fredholm GUE gives 0.4242576222440628) → −5.0%",
    ),
    (
        "zeta_bin_analysis_update.md",
        "| p95 vs GUE | 1.7186 vs 1.7518 (−1.9%)",
        "| p95 vs GUE Wigner surmise | 1.7186 vs 1.7518 (−1.9%)",
    ),
    (
        "zeta_bin_analysis_update.md",
        "| Std vs GUE | 0.4009 vs 0.4220 (−5.0%)",
        "| Std vs GUE Wigner surmise | 0.4009 vs 0.4220 (−5.0%)",
    ),
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(apply: bool) -> int:
    report: dict[str, object] = {"apply": apply, "files": {}, "missing": [], "already": []}
    per_file: dict[str, list[tuple[str, str]]] = {}
    for name, old, new in EDITS:
        per_file.setdefault(name, []).append((old, new))

    for name, pairs in per_file.items():
        path = CORPUS / name
        if not path.exists():
            report["missing"].append(str(path))
            continue
        before = path.read_text(encoding="utf-8")
        after = before
        applied, skipped = [], []
        for old, new in pairs:
            if new in after and old not in after:
                skipped.append(old)  # уже исправлено
                continue
            if old not in after:
                report["missing"].append(f"{name}: НЕ НАЙДЕНО «{old[:60]}…»")
                continue
            if after.count(old) != 1:
                report["missing"].append(
                    f"{name}: строка встречается {after.count(old)} раз, правка не однозначна"
                )
                continue
            after = after.replace(old, new)
            applied.append(old)
        entry = {
            "sha256_before": sha256(path),
            "applied": applied,
            "already_correct": skipped,
            "changed": after != before,
        }
        if after != before:
            diff = list(
                difflib.unified_diff(
                    before.splitlines(True), after.splitlines(True),
                    fromfile=f"a/{name}", tofile=f"b/{name}", n=1,
                )
            )
            entry["diff"] = "".join(diff)
            if apply:
                path.write_text(after, encoding="utf-8")
                entry["sha256_after"] = sha256(path)
        report["files"][name] = entry

    dest = Path("/home/user/workspace/goldsieve/gue_label_fix.json")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, e in report["files"].items():  # type: ignore[union-attr]
        print(f"{name}: применено {len(e['applied'])}, уже верно {len(e['already_correct'])}, "
              f"изменён={e['changed']}")
        if e.get("diff"):
            print(e["diff"])
    if report["missing"]:
        print("ПРОБЛЕМЫ:")
        for m in report["missing"]:  # type: ignore[union-attr]
            print("  ", m)
    print(f"отчёт: {dest}")
    return 1 if report["missing"] else 0


if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
