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


# Вердикты, при которых цель признаётся ИСЧЕРПАННОЙ как класс: повторять её
# аналогом бессмысленно, потому что проверка оказалась вырожденной, а не
# утверждение — неверным.
VOID_VERDICTS = ("ПУСТО",)


def registry_entries(path: str) -> list:
    """Записи реестра как список dict: имя, источник, вердикт, подтип.

    Разбор строчный намеренно: реестр правится руками и обязан читаться даже
    когда он не полностью валидный YAML — иначе гейт замолчит именно в тот
    момент, когда он нужнее всего.
    """
    entries, cur = [], None
    if not os.path.exists(path):
        return entries
    with open(path, "r", errors="replace") as f:
        for line in f:
            t = line.strip()
            if t.startswith("- "):
                if cur:
                    entries.append(cur)
                cur = {}
                t = t[2:].strip()
            if cur is None or ":" not in t:
                continue
            k, v = t.split(":", 1)
            cur[k.strip().lstrip("- ")] = v.strip().strip('"\'')
    if cur:
        entries.append(cur)
    return entries


def novelty_key_of(rel: str, prio: int) -> str:
    """Ключ новизны для цели ИЗ КОРПУСА.

    Найденный дефект первой версии: ключ включал ИМЯ ФАЙЛА, поэтому каждый файл
    оказывался новым классом и гейт допускал 828 целей из 828 — ось новизны
    была вырождена по построению, а «отпечаток настроек» придавал этому вид
    работающей проверки. Класс обязан быть шире одного файла, иначе бюджет
    невозможно исчерпать.

    Класс определяется приоритетом цели: п0 — печатное значение замкнутого
    выражения (проверяет округление), п1 — статистическое заявление, п2 — за
    числом стоит внешнее измерение. Имя файла остаётся в observable, поэтому
    другой файл того же класса всё равно проходит, если меняется observable, —
    но лишь до первого ПУСТО по этому классу.
    """
    return "corpus:p%d" % prio


def e_prio(entry: dict) -> int:
    """Приоритет класса для записи реестра.

    По умолчанию 2: запись реестра появляется у утверждений, за которыми стоит
    внешняя величина. Явное поле priority уважается, если оно есть.
    """
    try:
        return int(entry.get("priority", 2))
    except (TypeError, ValueError):
        return 2


def budget_from_registry(registry_path: str, root: str):
    """Бюджет гейта, СОБРАННЫЙ ИЗ УЖЕ ВЫНЕСЕННЫХ ВЕРДИКТОВ.

    Смысл: если по классу целей уже получено ПУСТО, следующая цель того же
    класса не добавит информации, и гейт обязан отказать ДО прогона. Бюджет
    восстанавливается из реестра, а не хранится отдельно, — тогда его нельзя
    рассинхронизировать с ведомостью.
    """
    from .gate import FamilyBudget
    spent = {}

    def field_list(value):
        """Извлечь короткий список моделей из строкового разбора реестра."""
        value = (value or "").strip()
        if not (value.startswith("[") and value.endswith("]")):
            return []
        return [item.strip().strip("\"'") for item in value[1:-1].split(",")
                if item.strip()]

    for e in registry_entries(registry_path):
        # Явно паспортизированный класс тратится независимо от вердикта:
        # повторное ОПРОВЕРГНУТО не даёт новой информации само по себе.
        # Исключение возможно только через новый источник, observable,
        # различающий механизм или объявленный прирост точности в Target.
        key = e.get("novelty_key", "")
        source = e.get("measurement_source", "")
        observable = e.get("observable", "")
        if key and source and observable:
            spent.setdefault(key, {
                "case": e.get("case", e.get("name", "?")),
                "source": source,
                "observable": observable,
                "models": field_list(e.get("models", "")),
            })
            continue
        if e.get("verdict") not in VOID_VERDICTS:
            continue
        src = e.get("source", "")
        rel = src.split(":")[0] if src else ""
        if not rel:
            continue
        spent.setdefault(novelty_key_of(rel, e_prio(e)), {
            "case": e.get("case", e.get("name", "?")),
            # source — КЛАСС цели, а не файл: иначе цель из другого файла
            # всегда считается «другим источником измерения» и класс
            # невозможно исчерпать.
            "source": novelty_key_of(rel, e_prio(e)),
            # observable — ФАЙЛ корпуса, а не имя утверждения: гейт
            # сопоставляет цели по источнику, а имена утверждений уникальны и
            # никогда не совпали бы, обнуляя проверку.
            "observable": rel,
            "models": [],
        })
    return FamilyBudget(spent=spent)


def gate_report(root: str, registry_path: str, top: int = 12,
                per_file=None) -> str:
    """Решение гейта по целям триажа: какие из них стоит запускать.

    Без этого шага триаж предлагает цели по одному лишь приоритету, и тик
    тратится на класс, где ответ уже известен (накопленные ПУСТО по грубым
    внешним величинам — ровно этот случай).
    """
    from .gate import Target, evaluate, fingerprint, DEFAULT_U_MIN
    per_file = per_file if per_file is not None else scan_tree(root)
    budget = budget_from_registry(registry_path, root)
    rows = []
    for p, v in per_file.items():
        rel = os.path.relpath(p, root)
        best = max((h[3] for h in v), default=0)
        n_best = sum(1 for h in v if h[3] == best)
        t = Target(
            name=rel,
            claim_family="corpus_numeric",
            observable=rel,   # сопоставляется с observable бюджета
            measurement_source=novelty_key_of(rel, best),
            uncertainty_type="unknown",
            # Ни ожидаемый эффект, ни разрешение до прогона НЕИЗВЕСТНЫ:
            # подставлять сюда приоритет триажа означало бы измерять
            # информативность самой сортировкой и получать допуск всегда
            # (первая версия так и делала: 828 из 828). Ось precision честно
            # остаётся необъявленной.
            expected_effect_sigma=None,
            resolution_sigma=None,
            novelty_key=novelty_key_of(rel, best),
            information_class="triage",
            purpose="external_prediction",
            # Различающие модели известны только после того, как автор
            # напишет кейс; объявлять их за него — самообман. Ось
            # discrimination остаётся необъявленной, и решение гейта
            # опирается на то единственное, что известно ДО прогона: не
            # исчерпан ли уже класс целей вердиктом ПУСТО.
            models=(),
        )
        d = evaluate(t, budget)
        rows.append((-best, not d.admitted, -n_best, rel, best, n_best, d))
    rows.sort()
    admitted = sum(1 for r in rows if r[6].admitted)
    lines = ["", "  ГЕЙТ ПОЛЕЗНОСТИ: какие цели стоит запускать",
             "  (U_min = %.2f, отпечаток настроек %s)"
             % (DEFAULT_U_MIN, fingerprint(DEFAULT_U_MIN, budget)),
             "  допущено %d из %d файлов; SKIPPED_LOW_INFORMATION %d"
             % (admitted, len(rows), len(rows) - admitted)]
    for _, _, _, rel, best, n_best, d in rows[:top]:
        lines.append("    %s п%d %4d строк  %s" %
                     ("ДОПУСК " if d.admitted else "ОТКАЗ  ", best, n_best, rel))
        lines.append("             %s" % d.line())
    lines.append("  Отказ гейта — РЕШЕНИЕ О ЗАПУСКЕ, а не вердикт по "
                 "утверждению.")
    return "\n".join(lines)


def report(root: str, registry_path: str, top: int = 12,
           per_file=None) -> str:
    per_file = scan_tree(root) if per_file is None else per_file
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
    lines.append(gate_report(root, registry_path, top=top, per_file=per_file))
    return "\n".join(lines)


def _selftest_gate_integration() -> int:
    """Гейт обязан ОТКАЗЫВАТЬ там, где класс цели исчерпан вердиктом ПУСТО.

    Подставка стоит там, где неверный ответ отличается: цель того же класса, но
    ИЗ ДРУГОГО файла, обязана остаться допущенной, иначе один вердикт ПУСТО
    закрыл бы весь корпус.
    """
    import tempfile
    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "corpus")
        os.makedirs(root)
        for nm in ("a.md", "b.md"):
            with open(os.path.join(root, nm), "w") as f:
                f.write("измеренное значение 1.23456 +- 0.00002 sigma\n")
        reg = os.path.join(d, "claims.yaml")
        with open(reg, "w") as f:
            f.write('- name: "утв"\n  source: "a.md:1"\n  verdict: "ПУСТО"\n')
        out = gate_report(root, reg, top=10)
        check("исчерпанный класс получает отказ", "ОТКАЗ" in out)
        check("другой файл того же класса остаётся допущенным",
              "ДОПУСК" in out and "b.md" in out)
    return fail


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
    fail += _selftest_gate_integration()
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
