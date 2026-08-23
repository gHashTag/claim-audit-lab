#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 215: сторож вырожденных внешних сверок.

Тики 210 и 211 выдали «ровно одну новую содержательную цель» — точностные
сверки постоянной Ридберга (0 сигма) и массы электрона (0,0111 сигма). Разбор
артефактов показал, что ни одна из них НЕ проверяет корпус Trinity: и цель, и
наблюдаемое взяты из одного и того же внешнего источника NIST, поэтому сверка
прошла бы при любом значении корпусных формул. Разрешающая способность нулевая
— тот же дефект, который сито С4 ловит у подставок, но проявившийся на уровне
ВЫБОРА цели, а не внутри каскада.

Отличие честной цели видно машинно. Тик 212 сравнивал с CODATA величину,
ПРОЧИТАННУЮ из корпуса (`corpus/trinity/docs/research/FORMULAS_SUMMARY.md`), и
получил 45,98 сигмы — это измерение о корпусе. Тики 210 и 211 корпусного
наблюдаемого не имеют вовсе.

Правило: артефакт внешней сверки обязан содержать наблюдаемое ИЗ КОРПУСА и путь
к файлу корпуса. Иначе класс сверки — вырожденная (ПУСТО), и подавать её как
содержательную цель нельзя. Фикстуры этой проверки — три настоящих артефакта
тиков 210, 211 и 212, поэтому чувствительность и специфичность измерены на
истории, а не на придуманных примерах.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICKDIR = Path("/home/user/workspace/cron_tracking/20fee222")
OUT = HERE / "external_target_guard.json"

# Ключи, которыми артефакт заявляет корпусное наблюдаемое и его происхождение.
OBSERVED_KEYS = ("наблюдаемое_из_корпуса", "observed_from_corpus")
SOURCE_KEYS = ("источник_наблюдения", "observation_source")
CORPUS_MARK = "corpus/"


def classify(art: dict) -> dict:
    """Вырожденная сверка или измерение о корпусе — решение по составу полей."""
    observed = next((k for k in OBSERVED_KEYS if k in art), None)
    source = next((k for k in SOURCE_KEYS if k in art), None)
    src_val = str(art.get(source, "")) if source else ""
    has_corpus_path = CORPUS_MARK in src_val
    if observed and has_corpus_path:
        return {"class": "измерение_о_корпусе", "degenerate": False,
                "observed_key": observed, "source": src_val}
    reasons = []
    if not observed:
        reasons.append("нет корпусного наблюдаемого: сверяется внешний "
                       "источник сам с собой")
    elif not has_corpus_path:
        reasons.append("наблюдаемое объявлено, но путь к файлу корпуса не "
                       "указан: происхождение непроверяемо")
    return {"class": "вырожденная_сверка", "degenerate": True,
            "verdict_if_submitted": "ПУСТО", "reasons": reasons,
            "observed_key": observed, "source": src_val}


def selftest() -> int:
    bad = 0

    def check(name: str, cond: bool) -> None:
        nonlocal bad
        bad += 0 if cond else 1
        print(f"  {'ok    ' if cond else 'ПРОВАЛ'} {name}")

    # ИСТОРИЧЕСКИЕ ФИКСТУРЫ: настоящие артефакты тиков 210–212.
    hist = {}
    for tick in (210, 211, 212):
        p = TICKDIR / ("tick%d_external_measurement.json" % tick)
        if p.exists():
            hist[tick] = json.loads(p.read_text(encoding="utf-8"))
    if len(hist) < 3:
        print("ПРОПУСК самопроверки: исторические артефакты недоступны "
              "(объявленный пропуск, причина — ротация файлов тиков)")
        return 0

    caught = sum(1 for t in (210, 211) if classify(hist[t])["degenerate"])
    check("вырожденные сверки тиков 210 и 211 ловятся (%d/2)" % caught,
          caught == 2)
    check("честная сверка тика 212 НЕ помечена вырожденной",
          not classify(hist[212])["degenerate"])
    check("у вырожденной сверки указана причина",
          all(classify(hist[t]).get("reasons") for t in (210, 211)))

    # МУТАЦИОННАЯ ЦЕЛЬ 1: убрать у честного артефакта путь к корпусу.
    mut = dict(hist[212])
    for k in SOURCE_KEYS:
        mut.pop(k, None)
    check("мутант без источника наблюдения ловится",
          classify(mut)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 2: путь есть, но не в корпус — происхождение подменено.
    mut2 = dict(hist[212])
    mut2["источник_наблюдения"] = "/tmp/scratch/notes.md"
    check("мутант с путём вне корпуса ловится", classify(mut2)["degenerate"])

    # ОТРИЦАТЕЛЬНАЯ ПРОВЕРКА: отклонение в сигмах решения НЕ определяет —
    # иначе сторож ловил бы «согласие», а не вырожденность.
    ok_small = dict(hist[212])
    ok_small["отклонение_эталона_от_цели_в_сигмах"] = 0.0
    check("нулевое отклонение при корпусном наблюдаемом вырожденным не "
          "считается", not classify(ok_small)["degenerate"])

    print(f"самопроверка сторожа внешних целей: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    rows = []
    for p in sorted(TICKDIR.glob("tick*_external_measurement.json")):
        try:
            art = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append({"file": p.name, "error": str(exc)})
            continue
        rows.append({"file": p.name, "target": art.get("цель"),
                     **classify(art)})
    degenerate = [r for r in rows if r.get("degenerate")]
    report = {
        "checked": len(rows),
        "degenerate_count": len(degenerate),
        "degenerate": [r["file"] for r in degenerate],
        "rule": ("артефакт внешней сверки обязан содержать наблюдаемое из "
                 "корпуса и путь к файлу корпуса; иначе сверка проходит при "
                 "любом значении корпусных формул"),
        "why_this_check_exists": ("тики 210 и 211 подали сверку внешнего "
                                  "источника с самим собой как содержательную "
                                  "цель: 0 и 0,0111 сигмы ни о чём не "
                                  "свидетельствуют"),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("сторож внешних целей: проверено %d, вырожденных %d"
          % (len(rows), len(degenerate)))
    for r in degenerate:
        print("  ПУСТО  %s — %s" % (r["file"], "; ".join(r["reasons"])))
    # Код возврата 0: это ретроспективная разметка уже сделанного, а не запрет.
    # Отказ гейта здесь означал бы наказание за прошлое; задача сторожа —
    # запретить ПОДАЧУ такой цели в следующем тике.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
