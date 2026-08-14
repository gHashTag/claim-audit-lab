#!/usr/bin/env python3
"""Стоимость журналирования с хеш-цепочкой. Пункт 6 приказа тика 44.

Что сравнивается. Один и тот же код оболочки на одной и той же работе, но
дозапись журнала идёт двумя путями: без связи записей (`GOLDSIEVE_CHAIN=0`,
точка «до») и с цепочкой (точка «после»). Сравнение с ПРЕЖНЕЙ версией файла
было бы хуже: различалась бы не только дозапись, и разницу нельзя было бы
отнести к цепочке.

Куда пишется журнал. В отдельный файл в /tmp, а не в журнал песочницы. Причина
не в аккуратности, а в проверке: записи без цепочки ПОСЛЕ цепочечных — это
нарушение `pre-chain-entry-after-chained`, и измерение в живом журнале само
закрыло бы гейт.

Что публикуется. Сырые точки, median, p95, минимум, максимум. Среднее НЕ
публикуется: одна задержка планировщика сдвигает его сильнее всего эффекта.
Разность медиан приводится вместе с полуразмахом p95−median обеих точек: если
разность меньше этого разброса, её нельзя называть измеренным замедлением.

    python3 chain_overhead.py [--repeats 20] [--out .../bench.json]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
TRI = os.path.join(ROOT, "tri")

# Позиции: имя, команда, число повторов (None — как задано ключом) и причина,
# если повторов меньше.
SUITE = [
    {"name": "quick", "cmd": [TRI, "quick"], "repeats": None, "reason": None},
    {"name": "gate", "cmd": [TRI, "gate"], "repeats": 3,
     "reason": "полный гейт идёт около 55 с; двадцать повторов в двух точках "
               "заняли бы больше 35 минут — это весь бюджет тика. Три "
               "повтора дают минимум и медиану, но НЕ дают p95: он помечен "
               "как не измеренный, а не посчитан по трём точкам."},
]


def _stats(xs: list[float], full: bool) -> dict:
    xs = sorted(xs)
    out = {
        "n": len(xs),
        "raw": [round(x, 4) for x in xs],
        "min": round(xs[0], 4),
        "max": round(xs[-1], 4),
        "median": round(statistics.median(xs), 4),
    }
    # p95 по трём точкам — это просто максимум, выданный за квантиль.
    out["p95"] = (round(sorted(xs)[max(0, int(round(0.95 * len(xs))) - 1)], 4)
                  if full else None)
    if not full:
        out["p95_reason"] = "повторов меньше двадцати: p95 не оценивается"
    return out


def _run(cmd: list[str], env: dict) -> float:
    t = time.perf_counter()
    subprocess.run(cmd, cwd=ROOT, capture_output=True, env=env)
    return time.perf_counter() - t


def measure(repeats: int) -> dict:
    base = dict(os.environ)
    # Журнал измерения — отдельный файл: см. пояснение в шапке модуля.
    log = "/tmp/chain-overhead-runs.jsonl"
    points = {}
    for pos in SUITE:
        n = pos["repeats"] or repeats
        full = n >= 20
        rec: dict = {"repeats": n, "reason": pos["reason"]}
        for label, chain_on in (("before", False), ("after", True)):
            env = dict(base)
            env["GOLDSIEVE_RUNS"] = log
            # Замок команд тоже отдельный: иначе измерение конкурировало бы
            # за замок с чем угодно, что идёт в песочнице.
            env["TRI_LOCK"] = "/tmp/chain-overhead.lock"
            if not chain_on:
                env["GOLDSIEVE_CHAIN"] = "0"
            else:
                env.pop("GOLDSIEVE_CHAIN", None)
            if os.path.exists(log):
                os.unlink(log)
            _run(pos["cmd"], env)          # прогрев: байткод и кеш файлов
            xs = [_run(pos["cmd"], env) for _ in range(n)]
            rec[label] = _stats(xs, full)
        d = rec["after"]["median"] - rec["before"]["median"]
        spread = max(rec["after"]["max"] - rec["after"]["median"],
                     rec["before"]["max"] - rec["before"]["median"])
        rec["delta_median"] = round(d, 4)
        rec["spread"] = round(spread, 4)
        rec["verdict"] = ("разность медиан меньше разброса самих повторов: "
                          "замедление НЕ измерено"
                          if abs(d) <= spread else
                          "разность медиан больше разброса повторов")
        points[pos["name"]] = rec
    return {
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python": sys.version.split()[0],
        "points": points,
        "not_published": "среднее (одна задержка планировщика сдвигает его "
                         "сильнее всего эффекта)",
        "limits": ["измерена стоимость ДОЗАПИСИ журнала, а не полного "
                   "wall-clock тика: вклад оболочки в длительность тика "
                   "по-прежнему не измерен",
                   "точка «до» получена переменной окружения в том же коде, "
                   "а не прежней версией файла: различается ровно дозапись"],
    }


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

    s = _stats([1.0, 2.0, 3.0], full=False)
    chk("median по трём точкам", s["median"] == 2.0)
    chk("p95 при малом числе повторов не выдаётся", s["p95"] is None
        and "повторов" in s["p95_reason"])
    chk("сырые точки сохраняются", s["raw"] == [1.0, 2.0, 3.0])
    s20 = _stats([float(i) for i in range(1, 21)], full=True)
    chk("p95 при двадцати повторах оценивается", s20["p95"] == 19.0)
    chk("среднее не публикуется", "mean" not in s and "mean" not in s20)
    # Правило вердикта обязано РАЗЛИЧАТЬ, иначе оно украшение.
    small = {"after": {"median": 10.1, "max": 10.9},
             "before": {"median": 10.0, "max": 10.6}}
    d = small["after"]["median"] - small["before"]["median"]
    spread = max(small["after"]["max"] - small["after"]["median"],
                 small["before"]["max"] - small["before"]["median"])
    chk("малая разность объявляется неизмеренной", abs(d) <= spread)
    big = {"after": {"median": 20.0, "max": 20.1},
           "before": {"median": 10.0, "max": 10.1}}
    d2 = big["after"]["median"] - big["before"]["median"]
    sp2 = max(big["after"]["max"] - big["after"]["median"],
              big["before"]["max"] - big["before"]["median"])
    chk("большая разность объявляется измеренной", abs(d2) > sp2)
    chk("у позиции gate объявлена причина малого числа повторов",
        all(p["reason"] for p in SUITE if (p["repeats"] or 20) < 20))
    print("chain_overhead: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--out", default="/home/user/workspace/loop17/bench.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 1 if selftest()[1] else 0
    body = measure(a.repeats)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2, sort_keys=True)
    for name, rec in sorted(body["points"].items()):
        print("%s: n=%d" % (name, rec["repeats"]))
        for label in ("before", "after"):
            st = rec[label]
            print("  %-7s median %.3f  min %.3f  max %.3f  p95 %s"
                  % (label, st["median"], st["min"], st["max"], st["p95"]))
        print("  разность медиан %+.3f при разбросе %.3f — %s"
              % (rec["delta_median"], rec["spread"], rec["verdict"]))
    print("сырые точки: %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
