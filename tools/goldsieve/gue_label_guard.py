#!/usr/bin/env python3
"""Регрессионный запрет метки exact_gue на числе 0,4220 (пункт 1 приказа 2026-08-18).

Критерий ОДНОСТРОЧНЫЙ: нарушение фиксируется, когда в одной и той же строке
стоит число 0,4220… и подпись, утверждающая ТОЧНЫЙ закон GUE, а слова
«surmise / Wigner / Вигнер» в этой строке нет. Однострочность выбрана
осознанно: оконный критерий (±240 символов) даёт шум на связных абзацах,
где точный GUE упоминается как КОНТРАСТ и это корректно.

Две области с разной строгостью:
  A. корпус /home/user/workspace/corpus/trinity — строгий набор подписей,
     включая «vs GUE», «по GUE», «против GUE»: читатель таблицы видит
     заголовок в отрыве от абзаца-оговорки;
  B. артефакты инструмента (goldsieve, cron_tracking) — только ЯВНЫЕ метки
     точности (exact_gue, exact GUE, точный GUE, GUE (computed), GUE Expected).
     Причина: имена claim цитируют формулировку корпуса дословно
     («0,4009 против 0,4220 по GUE») и переименованию не подлежат — имя claim
     является ключом регресса.

Код возврата 1 при любом нарушении. Ключ --selftest измеряет чувствительность
на фикстурах (нарушение обязано быть поймано, корректная подпись — пропущена).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
# Кодировка потоков: импорт пакета задаёт utf-8 (тик 171, дефект Windows cp1252).
try:
    import goldsieve as _gs  # noqa: F401
except Exception:
    pass


CORPUS_ROOT = Path("/home/user/workspace/corpus/trinity")
TOOL_ROOTS = [
    Path("/home/user/workspace/goldsieve"),
    Path("/home/user/workspace/cron_tracking"),
]
# --- Тик 171, пункт 4 приказа: роль по КОРНЮ, а не по имени файла ----------
# Гейт колебался открыт/закрыт три десятка раз: каждый тик создавал новое имя
# диагностического файла (tickNNN-gate.txt, tickNNN-summary.txt,
# tickNNN-gue-guard.txt, state-tickNNN.md ...), guard ловил собственный доклад,
# а следующий тик дописывал в AUDIT_LOG_GLOBS ещё один шаблон. Гонка шаблона с
# генератором имён не выигрывается: имён бесконечно много. Каталог
# cron_tracking/ — это ЖУРНАЛ ПРОГОНОВ целиком, по построению, а не корпус и не
# публичный текст. Роль определяется корнем, поэтому любое НОВОЕ, ранее
# неизвестное имя внутри журнала автоматически имеет роль audit_log.
AUDIT_LOG_ROOTS = [Path("/home/user/workspace/cron_tracking")]
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache"}
SKIP_FILES = {
    "gue_label_audit.py", "gue_label_audit.json",
    "gue_label_guard.py", "gue_label_guard.json",
    "gue_label_fix.py", "gue_label_fix.json",
    "zeros_odlyzko_100k.txt",
}
TEXT_EXT = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".csv", ".tsv", ".rst",
            ".html", ".js", ".ts", ".zig", ".rs", ".toml", ".ipynb"}
MAX_BYTES = 4_000_000

NUM_RE = re.compile(r"(?<![\d.,])0[.,]4220\d*")
EXPLICIT_RE = re.compile(
    r"exact[_\s-]*gue|gue[_\s-]*exact|точн\w*\s+(?:закон\w*\s+)?gue|"
    r"gue\s*\(computed\)|gue[_\s-]*expected",
    re.IGNORECASE,
)
LOOSE_RE = re.compile(
    r"vs\.?\s+gue|по\s+gue|против\s+gue|=\s*gue|gue\s*=|gue\s*[:|]",
    re.IGNORECASE,
)
OK_RE = re.compile(r"surmise|wigner|вигнер", re.IGNORECASE)


# Имя шага гейта «запрет метки exact_gue на 0,4220» само содержит и число, и
# запрещённую метку, поэтому любая запись о работе запрета срабатывала бы на
# самой себе (тик 89: гейт закрылся из-за строки в ведомости). Литерал имени
# УДАЛЯЕТСЯ из строки перед проверкой, а не отключает проверку строки целиком:
# если рядом с именем шага стоит настоящее нарушение, оно всё равно ловится.
# Чувствительность этой поправки измерена фикстурами в selftest.
ALLOWED_LITERALS = (
    "запрет метки exact_gue на 0,4220",
    "чувствительность запрета exact_gue",
)


def strip_allowed(line: str) -> str:
    for literal in ALLOWED_LITERALS:
        line = line.replace(literal, " ")
    return line


# --- Тик 91: роль файла вместо цитатной заплатки -----------------------------
# Дефект, из-за которого гейт закрывался в тиках 89 и 90: журнал аудита сам
# лежит внутри проверяемого дерева, поэтому ЗАПИСЬ О РАБОТЕ ЗАПРЕТА становилась
# новым нарушением, а вывод запрета, скопированный в ведомость, - ещё одним.
# Счёт нарушений рос сам собой: 1 -> 9 -> 26 без единой правки корпуса. Это
# самоусиление, а не находка. Лечится не расширением списка разрешённых цитат
# (он всегда будет отставать от свободного текста доклада), а РОЛЬЮ файла:
#   corpus     - утверждение корпуса, строгий набор подписей;
#   tool       - исходники и реестр инструмента, только явные метки точности;
#   audit_log  - журнал/протокол/вывод прогонов: описывает САМ запрет и не
#                является утверждением о GUE, проверке подписей не подлежит.
# Исключение ОБЪЯВЛЕНО (список файлов и причина попадают в JSON), а его
# чувствительность измерена фикстурами: подмена роли не должна прикрывать
# нарушение в корпусе, а корневой каталог корпуса сильнее любого имени файла.
AUDIT_LOG_NAMES = {
    "audit-ledger.md", "tick-counters.json", "runs.jsonl", "current-state.md",
    "cross-platform-replay.json", "prefilter-decisions.jsonl",
    "gue_label_guard.json", "gue_label_audit.json", "gue_label_fix.json",
}
# Диагностические файлы тика используют и подчёркивание, и дефис. Оба
# варианта являются журналом, а не утверждением корпуса: без hyphen-варианта
# собственный tick104-gate.txt снова попадал в область B и сам закрывал гейт.
# Скрипт записи доклада также является артефактом журнала, поэтому его имя
# явно включено в роль audit_log.
AUDIT_LOG_GLOBS = ("tick*_gate.txt", "tick*-gate.txt", "tick*-findings.md",
                   "tick*_record.py", "tick*-record.py", "append_tick*.py",
                   "tick*_state.md", "tick*_state.txt", "tick*_state.json",
                   "tick*_summary.md", "tick*_summary.txt", "tick*_summary.json",
                   "*_gate.txt",
                   "gate*.txt", "reg*.txt", "tick*_audit*.txt",
                   "tick*_terminology*.txt", "tick*_terminology*.json",
                   "tick*_guard*.txt", "tick*_gate*.txt",
                   "state-*.md", "state-*.txt", "state-*.json",
                   # Самопроверки и снимки состояния тика — диагностические
                   # артефакты, а не утверждения корпуса. В отрицательной
                   # фикстуре намеренно присутствуют неправильные метки;
                   # без этих шаблонов журнал сам закрывает гейт.
                   "tick*-selftest.txt", "tick*-selftest.json",
                   "tick*-gue.txt", "tick*_gue.txt",
                   "tick*-gue-label-guard.txt", "tick*-gue-label-guard.json",
                   "tick*-gue-label-*.txt", "tick*-gue-label-*.json",
                   "tick*-state.md", "tick*-state.txt", "tick*-state.json",
                   "tick*-audit.txt", "tick*-audit.json",
                   "tick*-ledger-tail.txt")


def classify_role(path: Path) -> str:
    try:
        path.relative_to(CORPUS_ROOT)
    except ValueError:
        pass
    else:
        return "corpus"          # корень корпуса сильнее имени файла
    for r in AUDIT_LOG_ROOTS:
        try:
            path.relative_to(r)
        except ValueError:
            continue
        return "audit_log"      # корень журнала сильнее любого имени файла
    if path.name in AUDIT_LOG_NAMES:
        return "audit_log"
    if any(path.match(g) for g in AUDIT_LOG_GLOBS):
        return "audit_log"
    return "tool"


def scan_line(line: str, strict: bool) -> str | None:
    line = strip_allowed(line)
    if not NUM_RE.search(line):
        return None
    if OK_RE.search(line):
        return None
    if EXPLICIT_RE.search(line):
        return "explicit_exact_gue_label"
    if strict and LOOSE_RE.search(line):
        return "bare_gue_label"
    return None


def iter_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_FILES or p.suffix.lower() not in TEXT_EXT:
            continue
        try:
            if p.stat().st_size > MAX_BYTES:
                continue
        except OSError:
            continue
        yield p


def scan_tree(root: Path, strict: bool, exempt: list[dict] | None = None) -> list[dict]:
    """strict=True оставлен для совместимости фикстур; реальная строгость — по роли."""
    out = []
    for p in iter_files(root):
        role = classify_role(p)
        if role == "audit_log":
            if exempt is not None:
                exempt.append({"file": str(p), "role": role,
                               "reason": "журнал аудита: описывает сам запрет, "
                                         "не является утверждением о GUE"})
            continue
        line_strict = strict if role != "corpus" else True
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            kind = scan_line(line, line_strict)
            if kind:
                out.append({"file": str(p), "line": i, "kind": kind, "role": role,
                            "text": line.strip()[:200],
                            "area": "A" if line_strict else "B"})
    return out


def selftest() -> int:
    """Измеренная чувствительность: фикстуры обязаны дать ожидаемый результат."""
    cases = [
        # (строка, strict, ожидается ли нарушение)
        ("| Std deviation | 0.4009 | 0.4220 | exact GUE |", False, True),
        ("| Metric | Value | GUE (computed) | 0.4220 |", False, True),
        ("std 0,4220 против точного закона GUE", False, True),
        ("| Std vs GUE | 0.4009 vs 0.4220 (-5.0%) |", True, True),
        ("std = 0.4220 по GUE", True, True),
        ("std = 0.4220 по GUE", False, False),        # область B терпит цитату claim
        ("| GUE Wigner surmise (computed) | 0.4220 |", True, False),
        ("0.4220 — Wigner surmise, а не точный GUE", True, False),
        ("exact GUE gives 0.4242576222440628", True, False),   # другое число
        ("27040.422044460", True, False),                      # хвост нуля дзеты
        # Тик 89: имя шага гейта не является нарушением…
        ("  ok  запрет метки exact_gue на 0,4220  [Python 3.14.3]", True, False),
        ("шаги «чувствительность запрета exact_gue», «запрет метки exact_gue на 0,4220»",
         True, False),
        # …но снятие литерала НЕ должно прикрывать настоящее нарушение рядом:
        # если в той же строке 0,4220 подписано точным GUE, оно обязано найтись.
        ("запрет метки exact_gue на 0,4220; при этом 0.4220 — exact GUE", True, True),
        # и обратная подстава: одно имя шага без второго числа тоже безопасно
        ("проверка «запрет метки exact_gue на 0,4220» пройдена", False, False),
    ]
    bad = 0
    for text, strict, expect in cases:
        got = scan_line(text, strict) is not None
        ok = got == expect
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} strict={int(strict)} ожидалось={int(expect)} "
              f"получено={int(got)} :: {text[:70]}")
    # мутационная цель: временный файл с нарушением обязан быть найден при обходе
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "mutant.md"
        f.write_text("| Std | 0.4009 | 0.4220 | exact GUE |\n", encoding="utf-8")
        hits = scan_tree(Path(td), strict=False)
        ok = len(hits) == 1
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} мутационная цель на обходе дерева: найдено {len(hits)}")
    # --- тик 91: роль файла и неподвижная точка -------------------------------
    VIOL = "| Std | 0.4009 | 0.4220 | exact GUE |\n"
    role_cases = [
        ("corpus/trinity/reports/zeta.md", "corpus"),
        ("corpus/trinity/audit-ledger.md", "corpus"),   # корень сильнее имени
        ("goldsieve/cases/zeta_std.py", "tool"),
        ("cron_tracking/8dff7aa3/audit-ledger.md", "audit_log"),
        ("cron_tracking/20fee222/tick90_gate.txt", "audit_log"),
        ("cron_tracking/20fee222/tick89-findings.md", "audit_log"),
        ("cron_tracking/20fee222/tick157_state.md", "audit_log"),
        ("cron_tracking/20fee222/append_tick158_ledger.py", "audit_log"),
        ("cron_tracking/8dff7aa3/tick-counters.json", "audit_log"),
        ("cron_tracking/20fee222/tick110-gue-selftest.txt", "audit_log"),
        ("cron_tracking/20fee222/tick296-gue-label-guard-full.txt", "audit_log"),
        ("cron_tracking/20fee222/tick111-state.md", "audit_log"),
    ]
    for rel, want in role_cases:
        p = (CORPUS_ROOT.parent.parent / rel) if rel.startswith("corpus/") \
            else (Path("/home/user/workspace") / rel)
        got = classify_role(p)
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} роль {want:9s} получено {got:9s} :: {rel}")

    # исключение по роли НЕ должно прикрывать нарушение в проверяемом файле:
    # в одном дереве лежат журнал и обычный файл с ОДИНАКОВЫМ текстом.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "audit-ledger.md").write_text(VIOL, encoding="utf-8")
        (d / "claims.md").write_text(VIOL, encoding="utf-8")
        hits = scan_tree(d, strict=False)
        ok = len(hits) == 1 and hits[0]["file"].endswith("claims.md")
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} роль не прикрывает нарушение рядом: найдено {len(hits)}")

    # неподвижная точка: запись вывода запрета в журнал внутри того же
    # дерева не должна менять число нарушений — именно это свойство
    # отсутствовало в тиках 89-90 (1 -> 9 -> 26).
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "clean.md").write_text("| GUE Wigner surmise (computed) | 0.4220 |\n",
                                    encoding="utf-8")
        first = scan_tree(d, strict=False)
        report = ("ЗАПРЕТ НАРУШЕН: 0 строк связывают 0,4220 с меткой точного GUE\n"
                  "0,4220 нигде не подписано как точный GUE\n")
        (d / "tick99_gate.txt").write_text(report, encoding="utf-8")
        (d / "audit-ledger.md").write_text(report, encoding="utf-8")
        second = scan_tree(d, strict=False)
        ok = len(first) == 0 and len(second) == 0
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} неподвижная точка после записи доклада: "
              f"{len(first)} -> {len(second)}")

    # мутационная цель на правило роли: если audit_log перестать исключать,
    # неподвижная точка обязана сломаться — проверяем это явно.
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "audit-ledger.md").write_text(
            "0,4220 нигде не подписано как точный GUE\n", encoding="utf-8")
        saved = set(AUDIT_LOG_NAMES)
        AUDIT_LOG_NAMES.clear()
        mutated = scan_tree(d, strict=False)
        AUDIT_LOG_NAMES.update(saved)
        restored = scan_tree(d, strict=False)
        ok = len(mutated) == 1 and len(restored) == 0
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} мутация правила роли ловится: "
              f"без правила {len(mutated)}, с правилом {len(restored)}")

    # --- Тик 171, пункт 4: регресс на ИСТОРИЧЕСКИХ ложных срабатываниях ------
    # Имена взяты из реальных писем закрытых гейтов (gate_closed 3..34). Каждое
    # из них закрывало гейт, будучи собственным докладом инструмента. Плюс два
    # заведомо НОВЫХ имени, которых не было ни в одном шаблоне: правило корня
    # обязано покрывать и их, иначе гонка шаблона с генератором имён вернётся.
    historic = ["tick102-gate.txt", "tick103-gate.txt", "tick110-gue-selftest.txt",
                "tick111-state.md", "tick125-summary.txt", "tick126-summary.txt",
                "tick145-gue-guard.txt", "tick146-gate.txt", "tick160-gate.txt",
                "state-tick136.md", "tick142-state.md", "append_tick169_report.py",
                "нечто-совсем-новое-2026.md", "otchet_bez_shablona.json"]
    bad_line = "std = 0,4220 exact_gue\n"
    with tempfile.TemporaryDirectory() as td:
        journal = Path(td) / "cron_tracking" / "20fee222"
        journal.mkdir(parents=True)
        for name in historic:
            (journal / name).write_text(bad_line, encoding="utf-8")
        saved_roots = list(AUDIT_LOG_ROOTS)
        AUDIT_LOG_ROOTS[:] = [Path(td) / "cron_tracking"]
        found = scan_tree(Path(td), strict=False)
        # мутация: убрать правило корня — все исторические строки обязаны
        # снова стать нарушениями, иначе тест ничего не измеряет.
        AUDIT_LOG_ROOTS[:] = []
        saved_names, saved_globs = set(AUDIT_LOG_NAMES), tuple(AUDIT_LOG_GLOBS)
        AUDIT_LOG_NAMES.clear()
        globals()["AUDIT_LOG_GLOBS"] = ()
        mutated = scan_tree(Path(td), strict=False)
        AUDIT_LOG_ROOTS[:] = saved_roots
        AUDIT_LOG_NAMES.update(saved_names)
        globals()["AUDIT_LOG_GLOBS"] = saved_globs
        ok = len(found) == 0 and len(mutated) == len(historic)
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} исторические ложные срабатывания "
              f"({len(historic)} имён): с правилом корня {len(found)}, "
              f"без правила {len(mutated)}")

    # Чувствительность не должна пострадать: ТОТ ЖЕ текст в корпусе — нарушение.
    with tempfile.TemporaryDirectory() as td:
        corp = Path(td) / "corpus"
        corp.mkdir()
        (corp / "tick102-gate.txt").write_text(bad_line, encoding="utf-8")
        saved_corpus = globals()["CORPUS_ROOT"]
        globals()["CORPUS_ROOT"] = corp
        strict_found = scan_tree(corp, strict=True)
        globals()["CORPUS_ROOT"] = saved_corpus
        ok = len(strict_found) == 1
        bad += 0 if ok else 1
        print(f"  {'ok ' if ok else 'ПРОВАЛ'} имя журнала НЕ прикрывает корпус: "
              f"найдено {len(strict_found)} (ожидается 1)")

    print(f"самопроверка запрета: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    exempt: list[dict] = []
    violations = scan_tree(CORPUS_ROOT, strict=True, exempt=exempt)
    for r in TOOL_ROOTS:
        violations += scan_tree(r, strict=False, exempt=exempt)
    dest = Path("/home/user/workspace/goldsieve/gue_label_guard.json")
    dest.write_text(json.dumps({"violations": violations, "count": len(violations),
                                "exempt_files": exempt, "exempt_count": len(exempt),
                                "roles": ["corpus", "tool", "audit_log"]},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"объявленное исключение по роли audit_log: файлов {len(exempt)}")
    if violations:
        print(f"ЗАПРЕТ НАРУШЕН: {len(violations)} строк связывают 0,4220 с меткой точного GUE")
        for v in violations[:40]:
            print(f"  [{v['area']}/{v['kind']}] {v['file']}:{v['line']}: {v['text']}")
        return 1
    print("запрет соблюдён: 0,4220 нигде не подписано как точный GUE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
