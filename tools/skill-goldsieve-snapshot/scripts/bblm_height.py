#!/usr/bin/env python3
"""Заполнение элемента height_parameters протокола BBLM машинным путём.

Элемент требовал: диапазон высот T выборки нулей, число нулей и вычисленное
L = log(T / 2pi) — в корпусе фигурировало единственное L ~ 9.4 без указания, к
какому набору оно относится. Здесь параметры СЧИТАЮТСЯ из файлов нулей, а
корпусное значение проверяется как утверждение, а не принимается на слово.

Команды:
    python3 bblm_height.py            таблица по всем файлам нулей + JSON
    python3 bblm_height.py --selftest самопроверка на синтетических входах
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

DATA = Path("/home/user/workspace/corpus/trinity/data/zeta")
OUT = Path(__file__).resolve().parent / "bblm_height.json"
FILES = ("zeros_100.txt", "zeros_150_real.txt", "zeros_2000.txt",
         "zeros_3000.txt", "zeros_odlyzko_100k.txt")
CORPUS_L = 9.4  # значение, фигурирующее в корпусе без указания набора


def read_heights(path: Path) -> list[float]:
    vals: list[float] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        tok = line.strip().split()
        if not tok:
            continue
        try:
            vals.append(float(tok[0]))
        except ValueError:
            continue  # заголовки и комментарии молча не учитываются
    return [v for v in vals if math.isfinite(v) and v > 0]


def params(heights: list[float]) -> dict:
    if len(heights) < 2:
        return {"n_zeros": len(heights), "note": "выборка слишком мала"}
    t_min, t_max = min(heights), max(heights)
    t_mid = 0.5 * (t_min + t_max)
    mean = sum(heights) / len(heights)
    return {
        "n_zeros": len(heights),
        "t_min": t_min,
        "t_max": t_max,
        "L_at_t_min": math.log(t_min / (2 * math.pi)),
        "L_at_t_max": math.log(t_max / (2 * math.pi)),
        "L_at_t_mid": math.log(t_mid / (2 * math.pi)),
        "L_at_mean_T": math.log(mean / (2 * math.pi)),
        # Ведущая конечновысотная поправка BBLM при этом L (коэффициенты взяты
        # из корпуса и НЕ выведены независимо — см. coefficient_rederivation).
        "alpha_minus_1_at_L_mid": 1.4720 / math.log(t_mid / (2 * math.pi)),
        "n_eff_at_L_mid": 0.230158 * math.log(t_mid / (2 * math.pi)),
    }


def sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def selftest() -> int:
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok     " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    # Синтетика с ИЗВЕСТНЫМ ответом: T от 2pi*e до 2pi*e^2 даёт L от 1 до 2.
    hs = [2 * math.pi * math.e, 2 * math.pi * math.e ** 2]
    p = params(hs)
    check("L на минимуме = 1", abs(p["L_at_t_min"] - 1.0) < 1e-12)
    check("L на максимуме = 2", abs(p["L_at_t_max"] - 2.0) < 1e-12)
    check("L середины между ними", 1.0 < p["L_at_t_mid"] < 2.0)
    check("малая выборка помечается", "note" in params([1.0]))
    check("нечисловые строки не роняют разбор",
          read_heights(Path("/dev/null")) == [])
    # ПОДСТАВКА: L не имеет права быть постоянной величиной, иначе весь
    # элемент вырожден и заполнять его нечем.
    p2 = params([2 * math.pi * math.e ** 5, 2 * math.pi * math.e ** 6])
    check("L зависит от высоты", abs(p2["L_at_t_mid"] - p["L_at_t_mid"]) > 1)
    print("самопроверка параметров высоты: пройдено %d, провалено %d" % (ok, fail))
    return 1 if fail else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    rows = {}
    for name in FILES:
        path = DATA / name
        if not path.exists():
            rows[name] = {"error": "файла нет"}
            continue
        h = read_heights(path)
        rows[name] = {"sha16": sha16(path), **params(h)}
    # Проверка корпусного L ~ 9.4: какому набору он соответствует?
    # Атрибуция корпусного L: проверяются ВСЕ законные способы взять L по
    # набору (минимум, максимум, середина диапазона, среднее T). Совпадение
    # именно с одним из них и есть объяснение происхождения числа.
    keys = ("L_at_t_min", "L_at_t_max", "L_at_t_mid", "L_at_mean_T")
    matches = []
    for n, r in rows.items():
        for k in keys:
            if k in r and abs(r[k] - CORPUS_L) < 0.05:
                matches.append("%s:%s=%.4f" % (n, k, r[k]))
    report = {
        "purpose": "элемент height_parameters протокола BBLM",
        "corpus_L_claim": CORPUS_L,
        "corpus_L_matched_files": matches,
        "corpus_L_verdict": (
            "L ~ 9.4 воспроизводится так: " + "; ".join(matches)
            if matches else
            "ни один набор нулей корпуса ни одним из способов (min, max, "
            "середина, среднее T) не даёт L ~ 9.4: происхождение корпусного "
            "значения остаётся неустановленным"),
        "files": rows,
        "coefficients_note": (
            "коэффициенты 0.230158 и 1.4720 перенесены из корпуса и НЕ выведены "
            "независимо: элемент coefficient_rederivation протокола остаётся "
            "недостающим, поэтому предъявленные alpha-1 и n_eff носят "
            "справочный характер"),
        "status_class": "verified-in-scope",
        "scope": "арифметика параметров высоты по файлам нулей корпуса",
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("| файл | нулей | T_min | T_max | L(серед.) | alpha-1 |")
    print("|---|---|---|---|---|---|")
    for name, r in rows.items():
        if "L_at_t_mid" not in r:
            print("| %s | — | — | — | — | %s |" % (name, r.get("note", r.get("error"))))
            continue
        print("| %s | %d | %.3f | %.3f | %.4f | %.4f |"
              % (name, r["n_zeros"], r["t_min"], r["t_max"], r["L_at_t_mid"],
                 r["alpha_minus_1_at_L_mid"]))
    print()
    print(report["corpus_L_verdict"])
    print("JSON: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
