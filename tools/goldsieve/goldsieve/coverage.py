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

# Приоритет цели. Введён в лупе 7 после того, как четыре тика подряд выдали
# ПОДТВЕРЖДЕНО на печатных значениях вида phi^phi = 2,17846. Такие утверждения
# проверяют лишь правильность округления калькулятора: внешней величины за ними
# нет, опровергнуть их нечем, находок там не будет. Сортировка по числу констант
# в файле систематически выносила их наверх, потому что таблиц значений в корпусе
# больше всего. Сортировка по количеству — свойство корпуса, а не ценности.
#
# Приоритет 2 (сначала): за числом стоит ВНЕШНЕЕ измерение или статистическое
# заявление — то есть проверка может дать ОПРОВЕРГНУТО или ПУСТО.
EXTERNAL_HINT = re.compile(
    r"(measured|measurement|observ|experiment|PDG|CODATA|Planck|HotQCD|"
    r"\bNIST\b|±|\+-|\\pm|sigma|σ|p-value|p_value|significan|confidence|"
    r"uncertaint|error\s*(bar|budget)?|предсказ|измерен|погрешност|значимост)", re.I)
# Приоритет 1: статистическое или выборочное утверждение без внешней величины.
STATISTIC_HINT = re.compile(
    r"(probabilit|expected|baseline|random|chance|distribution|variance|"
    r"std|mean|median|percentile|quantile|correlat|fit(s|ted)?\b|count|"
    r"combinations|search|threshold|вероятност|ожида|распределен|порог)", re.I)
# Приоритет 0: печатное значение замкнутого выражения — дешёвый класс.
PRINTED_VALUE = re.compile(
    r"^\s*\|?\s*\$?[^|=]{0,40}\$?\s*(=|\|)\s*\$?\s*\d+\.\d{3,}\s*\$?\s*\|?\s*$")

PRIORITY_NAME = {2: "внешнее измерение", 1: "статистика", 0: "печатное значение"}


def priority(line: str) -> int:
    """Ценность строки как цели аудита: 2 — высшая, 0 — низшая.

    Порядок проверок важен. Внешнее измерение бьёт всё: даже если строка похожа
    на печатное значение, наличие погрешности измерения делает её проверяемой по
    существу. Печатное значение проверяется ПОСЛЕ статистики, потому что строка
    «probability = 0.998» формально выглядит как печатное значение, но за ней
    стоит содержательное заявление.
    """
    if EXTERNAL_HINT.search(line):
        return 2
    if STATISTIC_HINT.search(line):
        return 1
    if PRINTED_VALUE.match(line):
        return 0
    return 1


def scan_file(path: str) -> list:
    out = []
    try:
        with open(path, "r", errors="replace") as f:
            for i, line in enumerate(f, 1):
                for m in NUM.finditer(line):
                    out.append((i, m.group(1), bool(FORMULA_HINT.search(line)),
                                priority(line)))
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
    bare = sum(1 for v in per_file.values() for h in v if not h[2])
    by_prio = Counter(h[3] for v in per_file.values() for h in v)
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
             "  по приоритету цели:"]
    for pr in (2, 1, 0):
        lines.append("    %d (%s): %d" % (pr, PRIORITY_NAME[pr], by_prio.get(pr, 0)))
    lines.append("")
    lines.append("  ЦЕЛИ СЛЕДУЮЩИХ ТИКОВ, по убыванию приоритета")
    lines.append("  (сортировка по ЦЕННОСТИ, а не по числу констант в файле:")
    lines.append("   печатные значения замкнутых выражений идут последними):")
    ranked = []
    for p, v in per_file.items():
        rel = os.path.relpath(p, root)
        covered = any(r in rel or rel in r for r in reg)
        best = max((h[3] for h in v), default=0)
        n_best = sum(1 for h in v if h[3] == best)
        # непокрытый файл идёт раньше покрытого при равном приоритете
        ranked.append((-best, covered, -n_best, rel, best, n_best))
    ranked.sort()
    for _, covered, _, rel, best, n_best in ranked[:top]:
        lines.append("    приоритет %d (%-18s) %4d строк  %s%s"
                     % (best, PRIORITY_NAME[best], n_best, rel,
                        "  [в реестре]" if covered else ""))
    lines.append("")
    lines.append("  Приоритет 0 брать в тик только если целей 2 и 1 не осталось:")
    lines.append("  печатное значение проверяет округление, а не утверждение.")
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
        fail += _selftest_priority()
    return fail


def _selftest_priority() -> int:
    """Самопроверка приоритета цели с подставками.

    Подставка стоит там, где неверный ответ реально отличается: строка с
    внешним измерением одновременно подходит под шаблон печатного значения,
    и наивный порядок проверок отправил бы её в конец очереди.
    """
    fail = 0
    cases = [
        ("| tau_n | 879.4 | s | Measured: 878.4 ± 0.5 s |", 2, "внешнее измерение"),
        ("probability of a random hit is 0.998", 1, "статистика"),
        ("| $\\varphi^\\varphi$ | 2.17846 |", 0, "печатное значение"),
        ("$e^\\varphi = 5.04317$", 0, "печатное значение"),
        # подставка: выглядит как печатное значение, но есть погрешность
        ("$z_{re} = 7.670 \\pm 0.73$", 2, "погрешность бьёт шаблон значения"),
    ]
    for line, want, what in cases:
        got = priority(line)
        ok = got == want
        print("  %s приоритет %d (%s): %s"
              % ("ok  " if ok else "FAIL", want, what,
                 "" if ok else "получено %d" % got))
        fail += 0 if ok else 1
    # печатное значение ОБЯЗАНО стоять строго ниже внешнего измерения:
    # без этого правило можно «починить», вернув всем одинаковый приоритет
    ok = priority("| tau | 879.4 | Measured: 878.4 ± 0.5 |") > priority("$e^\\varphi = 5.04317$")
    print("  %s внешнее измерение строго выше печатного значения"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1
    return fail


if __name__ == "__main__":
    print("самопроверка покрытия:")
    raise SystemExit(1 if selftest() else 0)
