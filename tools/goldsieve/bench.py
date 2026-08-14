#!/usr/bin/env python3
"""Измерение времени команд. Пункт 1 приказа тика 43.

Что здесь ДОКАЗЫВАЕТСЯ и что нет — сказано прямо, потому что в тике 42
«ускорение» было заявлено без единого измерения.

Измеряется машинное время двух путей на одном фиксированном наборе:
  прежний путь — прямой вызов инструментов (python3 …), как до оболочки;
  новый путь   — та же работа через `tri`.

Оболочка НЕ может ускорить саму работу: под ней те же процессы. Ожидаемый
результат — накладной расход около нуля или небольшой минус. Настоящая
экономия тика была в числе команд и в отсутствии ошибок набора, и это
величина не секундная; она отдельно печатается как ЧИСЛО КОМАНД, а не как
время, и помечается гипотезой в части влияния на длительность тика.

Режимы:
  cold — перед вызовом удаляются каталоги __pycache__ (первый запуск после
         правки кода: интерпретатор перекомпилирует модули);
  warm — байткод уже собран.

Публикуются median, p95, минимум и максимум. Среднее не публикуется: одна
случайная задержка планировщика сдвигает его сильнее, чем весь эффект.

    python3 bench.py --repeats 20 [--out bench.json]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TRI = os.path.join(ROOT, "tri")

# Фиксированный набор. Для каждой позиции: прежний путь, новый путь, число
# повторов и причина, если повторов меньше двадцати.
SUITE = [
    {
        "name": "proof",
        "old": [["python3", "execution_proof.py"]],
        "new": [[TRI, "proof"]],
        "repeats": None,
        "reason": None,
    },
    {
        "name": "quick",
        "old": [["python3", "-m", "goldsieve.selftest"],
                ["python3", "measure_identity.py"],
                ["python3", "mutation_identity.py"],
                ["python3", "independence.py"]],
        "new": [[TRI, "quick"]],
        "repeats": None,
        "reason": None,
    },
    {
        "name": "gate",
        "old": [["bash", os.path.join(ROOT, "ci_gate.sh")]],
        "new": [[TRI, "gate"]],
        "repeats": 2,
        "reason": ("гейт идёт минуты; двадцать повторов двух путей не "
                   "помещаются в бюджет тика. Опорные величины здесь — "
                   "минимум и максимум по двум запускам; median по двум "
                   "точкам равен их полусумме и устойчивостью не обладает, "
                   "а p95 не считается вовсе"),
    },
    {
        "name": "regress",
        "old": [["python3", "-m", "goldsieve", "regress",
                 "--registry", "claims.yaml"]],
        "new": [[TRI, "regress"]],
        "repeats": 0,
        "reason": ("регресс идёт 6–10 минут и обязан идти в фоне; двадцать "
                   "повторов — это более трёх часов, то есть дороже всего "
                   "тика. Не измерено — и не заявлено измеренным"),
    },
]


def _clear_pycache() -> None:
    for root, dirs, _ in os.walk(ROOT):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                dirs.remove(d)


def _time(cmds: list[list[str]], env: dict) -> float:
    t0 = time.perf_counter()
    for cmd in cmds:
        subprocess.run(cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    return time.perf_counter() - t0


def _stats(xs: list[float]) -> dict:
    xs = sorted(xs)
    out = {"n": len(xs), "min": xs[0] if xs else None,
           "max": xs[-1] if xs else None}
    if len(xs) >= 2:
        out["median"] = statistics.median(xs)
    if len(xs) >= 20:
        # p95 по методу «ближайший ранг»: при двадцати точках это девятнадцатая.
        out["p95"] = xs[min(len(xs) - 1, int(round(0.95 * len(xs))) - 1)]
    return out


def bench(repeats: int, out_path: str | None) -> int:
    env = dict(os.environ)
    # Журнал вызовов и замок уводятся во временные файлы: измерение не должно
    # засорять рабочий журнал сотней событий и мешать настоящему тику.
    env["GOLDSIEVE_RUNS"] = "/tmp/bench-runs.jsonl"
    env["TRI_LOCK"] = "/tmp/bench-tri.lock"
    report: dict = {"repeats_requested": repeats, "items": []}
    print("измерение: повторов запрошено %d" % repeats, flush=True)
    for item in SUITE:
        n = item["repeats"] if item["repeats"] is not None else repeats
        row = {"name": item["name"], "repeats": n, "reason": item["reason"]}
        if n == 0:
            print("\n=== %s: НЕ ИЗМЕРЕНО. %s" % (item["name"], item["reason"]),
                  flush=True)
            row["measured"] = False
            report["items"].append(row)
            continue
        print("\n=== %s: %d повторов на путь" % (item["name"], n), flush=True)
        if item["reason"]:
            print("    оговорка: %s" % item["reason"], flush=True)
        for path in ("old", "new"):
            # Первый запуск каждого пути — cold: байткод удалён.
            _clear_pycache()
            cold = _time(item[path], env)
            # Повторов ровно n в ТЁПЛОМ режиме: cold — отдельная точка, а
            # не первая из двадцати. Иначе тёплых остаётся девятнадцать,
            # а p95 (порог — двадцать точек) молча не считается.
            warm = [_time(item[path], env) for _ in range(n)]
            row[path] = {"cold": cold, "warm": _stats(warm),
                         "warm_samples": warm}
            st = row[path]["warm"]
            print("    %-4s cold %6.3f c   warm n=%d min %6.3f  median %s  "
                  "p95 %s  max %6.3f"
                  % (path, cold, st["n"], st["min"] or 0,
                     ("%6.3f" % st["median"]) if "median" in st else "  —   ",
                     ("%6.3f" % st["p95"]) if "p95" in st else "  —   ",
                     st["max"] or 0), flush=True)
        so, sn = row["old"]["warm"], row["new"]["warm"]
        if "median" in so and "median" in sn:
            delta = sn["median"] - so["median"]
            row["delta_median_seconds"] = delta
            row["overhead_ratio"] = sn["median"] / so["median"]
            print("    накладной расход оболочки по медиане: %+.3f c "
                  "(отношение %.3f)" % (delta, row["overhead_ratio"]),
                  flush=True)
        report["items"].append(row)
        row["measured"] = True

    # Число команд: единственная величина, в которой оболочка действительно
    # выигрывает. Считается кодом по составу набора, а не на глаз.
    counts = {i["name"]: {"old": len(i["old"]), "new": len(i["new"])}
              for i in SUITE}
    report["command_counts"] = counts
    print("\n=== число команд на позицию (прежний путь → новый):", flush=True)
    for k, v in counts.items():
        print("    %-8s %d → %d" % (k, v["old"], v["new"]), flush=True)
    print("\nЧТО ДОКАЗАНО: машинное время двух путей на указанном наборе и "
          "накладной расход оболочки.\nЧТО НЕ ДОКАЗАНО: влияние оболочки на "
          "длительность тика в целом — оно определяется числом обращений и "
          "ошибками набора, здесь не измеренными.", flush=True)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print("отчёт: %s" % out_path, flush=True)
    return 0


def selftest() -> tuple[int, int]:
    ok = fail = 0

    def chk(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ок      %s" % name)
        else:
            fail += 1
            print("  ПРОВАЛ  %s %s" % (name, note))

    chk("p95 не выводится при малом числе точек",
        "p95" not in _stats([1.0, 2.0, 3.0]))
    st = _stats([float(i) for i in range(1, 21)])
    chk("p95 при двадцати точках — девятнадцатая по возрастанию",
        st["p95"] == 19.0, str(st))
    chk("median считается при двух точках", _stats([1.0, 3.0])["median"] == 2.0)
    chk("пустая выборка не роняет статистику", _stats([])["n"] == 0)
    chk("среднее не публикуется", "mean" not in st)
    chk("у каждой позиции без двадцати повторов объявлена причина",
        all(i["repeats"] is None or i["reason"] for i in SUITE))
    chk("прежний и новый путь заданы для каждой позиции",
        all(i["old"] and i["new"] for i in SUITE))
    chk("измерение уводит журнал вызовов во временный файл",
        "GOLDSIEVE_RUNS" in open(__file__, encoding="utf-8").read())
    print("bench: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--out", default="/home/user/workspace/loop16/bench.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 1 if selftest()[1] else 0
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
    return bench(a.repeats, a.out)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
