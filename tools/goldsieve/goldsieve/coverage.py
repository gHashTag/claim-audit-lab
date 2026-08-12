"""Покрытие корпуса: сколько численных утверждений вообще прошло через сито.

ВАЖНО: вывод этого модуля — ТРИАЖ, а не аудит. Найденная десятичная константа
не является находкой и не является дефектом. Она означает лишь одно: число
существует, а вердикта по нему нет. Подавать такой список как результат проверки
запрещено правилами честности.

Считается две величины:
  всего   — сколько десятичных констант с тремя и более знаками найдено в текстах;
  покрыто — сколько файлов-источников упомянуто в реестре claims.yaml, то есть
            имеет хотя бы одно утверждение, прогнанное через каскад.
"""

from __future__ import annotations

import os
import re
from collections import Counter

NUM = re.compile(r"(?<![\w.])(\d+\.\d{3,})(?![\w])")
FORMULA_HINT = re.compile(r"(=|sqrt|exp|log|ln|pi|\\frac|\^|prod|sum|int_)", re.I)


def scan_file(path: str) -> list:
    out = []
    try:
        with open(path, "r", errors="replace") as f:
            for i, line in enumerate(f, 1):
                for m in NUM.finditer(line):
                    out.append((i, m.group(1), bool(FORMULA_HINT.search(line))))
    except OSError:
        pass
    return out


def scan_tree(root: str, exts=(".md", ".rst")) -> dict:
    """По умолчанию сырые данные (.txt) не считаются утверждениями: это входы,
    а не заявления автора."""
    per_file = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "zig-out",
                                                "__pycache__", ".zig-cache")]
        for fn in files:
            if fn.endswith(exts):
                p = os.path.join(base, fn)
                hits = scan_file(p)
                if hits:
                    per_file[p] = hits
    return per_file


def registry(path: str) -> set:
    """Реестр источников: строки вида '- source: <путь>' в claims.yaml."""
    srcs = set()
    if not os.path.exists(path):
        return srcs
    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- source:") or line.startswith("source:"):
                srcs.add(line.split(":", 1)[1].strip().strip('"\''))
    return srcs


def report(root: str, registry_path: str, top: int = 12) -> str:
    per_file = scan_tree(root)
    reg = registry(registry_path)
    total = sum(len(v) for v in per_file.values())
    bare = sum(1 for v in per_file.values() for _, _, has in v if not has)
    covered_files = 0
    for p in per_file:
        rel = os.path.relpath(p, root)
        if any(r in rel or rel in r for r in reg):
            covered_files += 1
    lines = ["ТРИАЖ (не аудит): численные константы в текстах корпуса",
             "  корень:            %s" % root,
             "  файлов с числами:  %d" % len(per_file),
             "  констант всего:    %d" % total,
             "  из них без формулы в строке: %d" % bare,
             "  файлов в реестре утверждений: %d из %d (%.1f%%)"
             % (covered_files, len(per_file),
                100.0 * covered_files / max(1, len(per_file))),
             "",
             "  наиболее насыщенные файлы (кандидаты на следующие тики):"]
    cnt = Counter({p: len(v) for p, v in per_file.items()})
    for p, n in cnt.most_common(top):
        lines.append("    %5d  %s" % (n, os.path.relpath(p, root)))
    lines.append("")
    lines.append("  Вердикта по этим числам НЕТ. Пока утверждение не прогнано через")
    lines.append("  каскад, его статус — ВОПРОС, а не дефект.")
    return "\n".join(lines)


def selftest() -> int:
    import tempfile
    fail = 0
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.md"), "w") as f:
            f.write("std = 0.424258 по формуле det(I-K)\nзначение 2.6854520 без вывода\n")
        with open(os.path.join(d, "claims.yaml"), "w") as f:
            f.write("- source: a.md\n")
        per = scan_tree(d)
        hits = per[os.path.join(d, "a.md")]
        ok = len(hits) == 2 and hits[0][2] is True and hits[1][2] is False
        print("  %s найдены обе константы, формула различена: %s"
              % ("ok  " if ok else "FAIL", hits))
        fail += 0 if ok else 1
        txt = report(d, os.path.join(d, "claims.yaml"))
        ok = "1 из 1" in txt and "ТРИАЖ" in txt
        print("  %s реестр учтён и вывод помечен как триаж" % ("ok  " if ok else "FAIL"))
        fail += 0 if ok else 1
        # подставка: число в строке без десятичных знаков не должно ловиться
        with open(os.path.join(d, "b.md"), "w") as f:
            f.write("версия 3.14 и год 2026 и 1.5\n")
        per = scan_tree(d)
        ok = os.path.join(d, "b.md") not in per
        print("  %s подставка: 3.14 / 2026 / 1.5 не считаются утверждениями"
              % ("ok  " if ok else "FAIL"))
        fail += 0 if ok else 1
    return fail


if __name__ == "__main__":
    print("самопроверка покрытия:")
    raise SystemExit(1 if selftest() else 0)
