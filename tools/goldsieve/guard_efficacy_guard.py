#!/usr/bin/env python3
"""Сторож содержательности сторожей.

Аномалия, ради которой он написан (измерена на тиках 303-401): число файлов
*_guard.py выросло до 43, число шагов гейта 69 -> 147, а срывы по таймауту
39 -> 53. При этом значительная часть новых сторожей на настоящих входах
выдаёт только `not-evaluated` или `unsupported`, то есть НИЧЕГО не
устанавливает: стоимость тика растёт, знание не растёт.

Правило, которое вводит этот сторож:

    новый сторож допустим, только если на настоящем входе он предъявляет
    хотя бы один статус `verified-in-scope`.

Классы (иных не бывает, класс выводится ТОЛЬКО из напечатанных статусов):

  устанавливает  - напечатал >= 1 `verified-in-scope`;
  пустой         - напечатал статусы, но ни одного `verified-in-scope`;
  без-статусов   - режим данных не печатает статусов вовсе; класс НЕ
                   установлен (метастатус `not-evaluated`). Молчание
                   проверки не считается покрытием и не считается долгом.

Долг тика = число сторожей класса `пустой`. Он замораживается в
guard_efficacy_baseline.json и расти не имеет права.

Режимы:
  --audit                 таблица по всем сторожам
  --json ФАЙЛ             вместе с --audit: машинный отчёт
  --check ФАЙЛ            код 1, если сторож не класса `устанавливает`
  --baseline              заморозить текущий долг
  --gate                  код 1 при росте долга, код 2 без записанного долга
  --selftest              самопроверка
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "guard_efficacy_baseline.json"

STATUSES = ("verified-in-scope", "not-evaluated", "unsupported", "platform-unverified")

# режимы только для ЧТЕНИЯ: ни --clean, ни --record, ни --baseline
READ_MODES: tuple[list[str], ...] = (["--audit"], ["--scan"], [])

# сторожа, которые обслуживают сам тик, а не утверждения корпуса
INFRA = {"disk_guard.py", "progress_guard.py", "repo_sync_guard.py", "guard_efficacy_guard.py"}

CLASS_ESTABLISHES = "устанавливает"
CLASS_EMPTY = "пустой"
CLASS_SILENT = "без-статусов"


def count_statuses(text: str) -> dict[str, int]:
    return {s: len(re.findall(re.escape(s), text)) for s in STATUSES}


def classify(counts: dict[str, int]) -> str:
    if counts["verified-in-scope"] > 0:
        return CLASS_ESTABLISHES
    if sum(counts.values()) > 0:
        return CLASS_EMPTY
    return CLASS_SILENT


def probe(path: Path, timeout: float = 60.0) -> dict:
    """Запустить сторож в читающем режиме и определить класс."""
    best: dict | None = None
    for mode in READ_MODES:
        cmd = [sys.executable, str(path), *mode]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            cand = {
                "сторож": path.name,
                "режим": " ".join(mode) or "(без аргументов)",
                "код": None,
                "статусы": {s: 0 for s in STATUSES},
                "класс": CLASS_SILENT,
                "причина": "таймаут режима данных",
            }
            if best is None:
                best = cand
            continue
        out = (proc.stdout or "") + (proc.stderr or "")
        counts = count_statuses(out)
        cand = {
            "сторож": path.name,
            "режим": " ".join(mode) or "(без аргументов)",
            "код": proc.returncode,
            "статусы": counts,
            "класс": classify(counts),
            "причина": "" if sum(counts.values()) else "режим не печатает статусов",
        }
        if cand["класс"] == CLASS_ESTABLISHES:
            return cand
        if best is None or (best["класс"] == CLASS_SILENT and cand["класс"] == CLASS_EMPTY):
            best = cand
    assert best is not None
    return best


def guards() -> list[Path]:
    return sorted(p for p in ROOT.glob("*_guard.py") if p.name not in INFRA)


def audit(timeout: float = 60.0) -> dict:
    files = guards()
    rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(probe, f, timeout): f for f in files}
        for fut in concurrent.futures.as_completed(futures):
            rows.append(fut.result())
    rows.sort(key=lambda r: r["сторож"])
    counts = {c: sum(1 for r in rows if r["класс"] == c) for c in (CLASS_ESTABLISHES, CLASS_EMPTY, CLASS_SILENT)}
    return {"всего": len(rows), "классы": counts, "долг_пустых": counts[CLASS_EMPTY], "сторожа": rows}


def print_audit(rep: dict) -> None:
    print(f"=== содержательность сторожей: всего {rep['всего']}")
    for cls in (CLASS_ESTABLISHES, CLASS_EMPTY, CLASS_SILENT):
        names = [r["сторож"] for r in rep["сторожа"] if r["класс"] == cls]
        print(f"\n-- {cls}: {len(names)}")
        for r in rep["сторожа"]:
            if r["класс"] != cls:
                continue
            st = r["статусы"]
            marks = ", ".join(f"{k}={v}" for k, v in st.items() if v)
            print(f"   {r['сторож']:<44} режим {r['режим']:<16} код {r['код']} {marks or r['причина']}")
    print(f"\nдолг пустых сторожей: {rep['долг_пустых']}")


def cmd_baseline() -> int:
    rep = audit()
    BASELINE.write_text(
        json.dumps({"долг_пустых": rep["долг_пустых"], "всего": rep["всего"],
                    "пустые": [r["сторож"] for r in rep["сторожа"] if r["класс"] == CLASS_EMPTY]},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"долг заморожен: {rep['долг_пустых']} пустых сторожей из {rep['всего']}")
    return 0


def cmd_gate() -> int:
    if not BASELINE.exists():
        print("НЕТ ЗАПИСАННОГО ДОЛГА: сначала --baseline", file=sys.stderr)
        return 2
    frozen = json.loads(BASELINE.read_text(encoding="utf-8"))
    rep = audit()
    now, was = rep["долг_пустых"], int(frozen["долг_пустых"])
    if now > was:
        новые = sorted(set(r["сторож"] for r in rep["сторожа"] if r["класс"] == CLASS_EMPTY)
                       - set(frozen.get("пустые", [])))
        print(f"РОСТ ДОЛГА: пустых сторожей {was} -> {now}; новые: {', '.join(новые) or '(имена совпали)'}",
              file=sys.stderr)
        return 1
    print(f"долг пустых сторожей {now} при замороженных {was}: роста нет")
    return 0


def cmd_check(target: str) -> int:
    path = Path(target)
    if not path.is_absolute():
        path = ROOT / path.name
    if not path.exists():
        print(f"нет файла: {path}", file=sys.stderr)
        return 2
    row = probe(path)
    st = ", ".join(f"{k}={v}" for k, v in row["статусы"].items() if v) or row["причина"]
    print(f"{row['сторож']}: класс {row['класс']} (режим {row['режим']}, код {row['код']}; {st})")
    if row["класс"] == CLASS_ESTABLISHES:
        return 0
    print("ОТКАЗ: новый сторож обязан предъявить verified-in-scope хотя бы на одном настоящем входе",
          file=sys.stderr)
    return 1


def selftest() -> int:
    ok = 0
    fails: list[str] = []

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        if cond:
            ok += 1
        else:
            fails.append(name)

    check("verified даёт класс устанавливает",
          classify(count_statuses("итог: verified-in-scope")) == CLASS_ESTABLISHES)
    check("только not-evaluated даёт пустой",
          classify(count_statuses("a not-evaluated b not-evaluated")) == CLASS_EMPTY)
    check("только unsupported даёт пустой",
          classify(count_statuses("unsupported")) == CLASS_EMPTY)
    check("platform-unverified даёт пустой",
          classify(count_statuses("platform-unverified")) == CLASS_EMPTY)
    check("нет статусов даёт без-статусов", classify(count_statuses("71 ok, 0 провалов")) == CLASS_SILENT)
    check("смесь с verified даёт устанавливает",
          classify(count_statuses("verified-in-scope и not-evaluated")) == CLASS_ESTABLISHES)
    check("счёт статусов точен", count_statuses("not-evaluated not-evaluated")["not-evaluated"] == 2)
    check("verified не считается подстрокой unsupported",
          count_statuses("unsupported")["verified-in-scope"] == 0)
    check("читающие режимы не содержат разрушительных",
          not any(f in sum((list(m) for m in READ_MODES), []) for f in ("--clean", "--record", "--baseline")))
    check("сам сторож исключён из выборки", "guard_efficacy_guard.py" in INFRA)
    check("инфраструктурные исключены", {"disk_guard.py", "repo_sync_guard.py"} <= INFRA)
    check("список сторожей непуст", len(guards()) > 0)
    check("сам не попал в список", all(p.name != "guard_efficacy_guard.py" for p in guards()))
    check("класс пустой не совпадает с без-статусов", CLASS_EMPTY != CLASS_SILENT)
    check("домен статусов ровно четыре", len(STATUSES) == 4)

    print(f"самопроверка: {ok} пройдено, {len(fails)} провалено")
    for f in fails:
        print(f"  ПРОВАЛ: {f}")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--audit", action="store_true")
    g.add_argument("--check", metavar="ФАЙЛ")
    g.add_argument("--baseline", action="store_true")
    g.add_argument("--gate", action="store_true")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", metavar="ФАЙЛ")
    ns = ap.parse_args(argv)

    if ns.selftest:
        return selftest()
    if ns.baseline:
        return cmd_baseline()
    if ns.gate:
        return cmd_gate()
    if ns.check:
        return cmd_check(ns.check)
    rep = audit()
    print_audit(rep)
    if ns.json:
        Path(ns.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"машинный отчёт: {ns.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
