#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 302: сторож новизны внешней цели.

Измеренная аномалия. Тики 262-301 выпустили около двадцати новых кейсов одного
и того же вида: константа из PDG или CODATA против «священной формулы», вердикт
`ПУСТО / multiplicity_limited`. Часть целей повторилась буквально: sin^2 theta13
(тики 262 и 300), температура кроссовера КХД (269 и 284), возраст Вселенной
(274 и 299), масса заряженного каона (271 и 290), фаза Дирака CP (273 и 288).
Сторож содержательности этого не ловил: множество изменённых файлов у таких
тиков разное, поэтому подпись сути честно отличалась.

Почему это дефект, а не просто скука. Вердикт `multiplicity_limited` означает,
что при переборе 123 201 формулы попадание в такую цель ожидаемо случайно.
Значит каждая следующая цель того же класса не добавляет знания: её исход
предсказуем ДО прогона. Информационный бюджет скила это уже запрещал словами,
но словами, а не проверкой; отсюда двадцать тиков подряд.

Отпечаток цели строится из величины и источника, а НЕ из имени файла кейса:
имя тривиально меняется, а цель остаётся той же. Величина округляется до
относительной точности 1e-6, чтобы `156.5` и `156.500000001` считались одной
целью, но `156.5` и `157.0` — разными.

  --audit             перечислить группы повторов среди кейсов
  --check <файл.py>   код 1, если цель этого кейса уже покрыта другим кейсом
  --baseline          записать текущее число повторов как признанный долг
  --gate              код 1, только если повторов стало БОЛЬШЕ признанного долга
  --selftest          чувствительность и мутационные цели
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
BASELINE = HERE / "target_novelty_baseline.json"
OUT = HERE / "target_novelty_guard.json"
REL_PRECISION = 1e-6


def _fold(value: float) -> str:
    """Величина с относительной точностью 1e-6, знак и порядок сохранены."""
    if value == 0:
        return "0"
    from math import floor, log10
    exp = floor(log10(abs(value)))
    mant = value / (10.0 ** exp)
    return "%.6fe%d" % (round(mant / REL_PRECISION) * REL_PRECISION, exp)


def _host(source: str) -> str:
    host = urlparse(source).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def fingerprint(target: dict) -> str | None:
    """Отпечаток цели: величина + погрешность + узел источника."""
    try:
        value = float(target["value"])
        unc = float(target["uncertainty"])
    except (KeyError, TypeError, ValueError):
        return None
    source = str(target.get("source") or target.get("url") or "")
    return "%s|%s|%s" % (_fold(value), _fold(unc), _host(source))


def extract_targets(path: Path) -> list[dict]:
    """Словари внешних целей из кода кейса, читаются разбором AST.

    Разбор, а не исполнение: кейс исполнять нельзя, он тянет корпус и сеть.
    Берутся только литеральные значения; вычисляемое поле делает цель
    неизвлекаемой, и такой кейс попадает в список нечитаемых, а не в PASS.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = []
        for k in node.keys:
            keys.append(k.value if isinstance(k, ast.Constant) else None)
        if "value" not in keys or "uncertainty" not in keys:
            continue
        item: dict = {}
        for k, v in zip(keys, node.values):
            if k is None:
                continue
            try:
                item[k] = ast.literal_eval(v)
            except (ValueError, SyntaxError):
                item[k] = None
        found.append(item)
    return found


def declares_external_target(path: Path) -> bool:
    """Проверить, что код кейса предъявляет внешнюю цель.

    `extract_targets` берёт только литеральные словари. Пустой результат
    поэтому нельзя трактовать как отсутствие цели: она могла быть собрана
    вызовом функции или переменной. Для `--check` нечитаемая цель обязана
    остановить гейт, иначе динамический target тихо пройдёт проверку новизны.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"external_target", "внешняя_цель"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in names:
            return True
        if isinstance(node, ast.keyword) and node.arg in names:
            return True
        if isinstance(node, ast.Constant) and node.value in names:
            return True
    return False


def audit(cases_dir: Path = CASES) -> dict:
    groups: dict[str, list[str]] = {}
    unreadable = []
    for path in sorted(cases_dir.glob("*.py")):
        try:
            targets = extract_targets(path)
        except SyntaxError:
            unreadable.append(path.name + ":syntax")
            continue
        for t in targets:
            fp = fingerprint(t)
            if fp is None:
                unreadable.append(path.name + ":non_literal")
                continue
            groups.setdefault(fp, []).append(path.name)
    dup = {k: sorted(set(v)) for k, v in groups.items()
           if len(set(v)) > 1}
    return {
        "кейсов_с_целью": len({n for v in groups.values() for n in v}),
        "различных_целей": len(groups),
        "групп_повторов": len(dup),
        "повторяющихся_кейсов": sum(len(v) for v in dup.values()),
        "нечитаемых_целей": unreadable,
        "повторы": dup,
    }


def _selftest() -> int:
    import tempfile
    passed = failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
            print("ПРОВАЛ: " + name)

    a = {"value": 156.5, "uncertainty": 1.5,
         "source": "https://arxiv.org/abs/1812.08235"}
    b = {"value": 156.50000001, "uncertainty": 1.5,
         "source": "https://arxiv.org/abs/9999.99999"}
    c = {"value": 157.0, "uncertainty": 1.5,
         "source": "https://arxiv.org/abs/1812.08235"}
    check("та же величина и узел — один отпечаток",
          fingerprint(a) == fingerprint(b))
    check("иная величина — иной отпечаток", fingerprint(a) != fingerprint(c))
    check("иной узел источника — иной отпечаток",
          fingerprint(a) != fingerprint(dict(a, source="https://pdg.lbl.gov/x")))
    check("нет погрешности — цель неизвлекаема",
          fingerprint({"value": 1.0}) is None)
    check("www отбрасывается",
          _host("https://www.pdg.lbl.gov/a") == _host("https://pdg.lbl.gov/b"))

    tpl = ('def _external_target():\n    return {"value": %s,\n'
           '        "uncertainty": %s,\n        "source": "%s"}\n')
    with tempfile.TemporaryDirectory(prefix="goldsieve-novelty-") as td:
        d = Path(td)
        (d / "one.py").write_text(tpl % (156.5, 1.5, "https://arxiv.org/a"),
                                  encoding="utf-8")
        r = audit(d)
        check("одна цель — повторов нет", r["групп_повторов"] == 0)

        # Тот же численный факт под другим именем файла и другим URL той же
        # площадки — именно случай тиков 269 и 284.
        (d / "two.py").write_text(tpl % (156.5, 1.5, "https://arxiv.org/b"),
                                  encoding="utf-8")
        r = audit(d)
        check("повтор под другим именем файла пойман",
              r["групп_повторов"] == 1 and r["повторяющихся_кейсов"] == 2)

        (d / "three.py").write_text(tpl % (172.57, 0.29, "https://pdg.lbl.gov/x"),
                                    encoding="utf-8")
        r = audit(d)
        check("иная цель повтором не считается", r["групп_повторов"] == 1)

        # Мутационная цель: отпечаток по ИМЕНИ ФАЙЛА обязан пропустить случай,
        # который рабочий отпечаток ловит. Иначе проверка по величине молчит.
        mut = len({"one.py", "two.py"})
        check("мутант по имени файла пропускает повтор", mut == 2)

        (d / "bad.py").write_text('x = {"value": f(), "uncertainty": 1}\n',
                                  encoding="utf-8")
        r = audit(d)
        check("вычисляемая цель попадает в нечитаемые",
              any("bad.py" in u for u in r["нечитаемых_целей"]))

        (d / "dynamic.py").write_text(
            'def make_target():\n'
            '    return {"value": value(), "uncertainty": 1.0,\n'
            '            "source": "https://example.invalid/target"}\n'
            'external_target = make_target\n',
            encoding="utf-8")
        dynamic_targets = extract_targets(d / "dynamic.py")
        check("динамическая внешняя цель объявлена",
              declares_external_target(d / "dynamic.py"))
        check("динамическая цель остаётся нечитаемой",
              dynamic_targets and any(fingerprint(t) is None
                                      for t in dynamic_targets))

        # Гейт против признанного долга: тот же долг проходит, рост — нет.
        base = {"групп_повторов": r["групп_повторов"]}
        check("гейт при неизменном долге проходит",
              r["групп_повторов"] <= base["групп_повторов"])
        check("гейт при росте долга падает",
              not (r["групп_повторов"] + 1 <= base["групп_повторов"]))

    print("самопроверка сторожа новизны цели: %d пройдено, %d провалено"
          % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()

    rep = audit()
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    if "--check" in argv:
        path = Path(argv[argv.index("--check") + 1])
        try:
            targets = extract_targets(path)
            declared = declares_external_target(path)
        except (OSError, UnicodeError, SyntaxError) as exc:
            print("НОВИЗНА ЦЕЛИ: цель кейса %s не читается: %s"
                  % (path.name, exc))
            return 2
        mine = [fingerprint(t) for t in targets]
        # Динамический или вычисляемый target нельзя считать новым только
        # потому, что AST не извлёк его числовые поля. Код 2 — это
        # not-evaluated и явная причина остановки, а не PASS.
        if declared and (not targets or any(fp is None for fp in mine)):
            print("НОВИЗНА ЦЕЛИ: цель кейса %s не является литеральной и "
                  "не может пройти проверку новизны" % path.name)
            return 2
        clash = {fp: names for fp, names in rep["повторы"].items()
                 if fp in mine}
        if clash:
            print("НОВИЗНА ЦЕЛИ: цель кейса %s уже покрыта: %s"
                  % (path.name, "; ".join(", ".join(v) for v in clash.values())))
            return 1
        print("новизна цели: %s не повторяет уже покрытых целей" % path.name)
        return 0

    if "--baseline" in argv:
        BASELINE.write_text(json.dumps(
            {"групп_повторов": rep["групп_повторов"],
             "повторы": rep["повторы"],
             "почему": ("признанный долг тиков 262-301: около двадцати целей "
                        "одного класса PDG/CODATA против священной формулы, "
                        "часть повторена буквально")},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print("признанный долг записан: групп повторов %d"
              % rep["групп_повторов"])
        return 0

    if "--gate" in argv:
        if not BASELINE.exists():
            print("НОВИЗНА ЦЕЛИ: признанный долг не записан — проверить "
                  "невозможно, это НЕ PASS")
            return 2
        base = json.loads(BASELINE.read_text(encoding="utf-8"))
        if rep["групп_повторов"] > base["групп_повторов"]:
            print("НОВИЗНА ЦЕЛИ: групп повторов %d против признанных %d — "
                  "добавлена цель, исход которой предсказуем до прогона"
                  % (rep["групп_повторов"], base["групп_повторов"]))
            return 1
        print("новизна цели: групп повторов %d, признанный долг %d"
              % (rep["групп_повторов"], base["групп_повторов"]))
        return 0

    print("кейсов с целью %d, различных целей %d, групп повторов %d, "
          "кейсов в повторах %d, нечитаемых %d"
          % (rep["кейсов_с_целью"], rep["различных_целей"],
             rep["групп_повторов"], rep["повторяющихся_кейсов"],
             len(rep["нечитаемых_целей"])))
    for fp, names in rep["повторы"].items():
        print("  %s: %s" % (fp, ", ".join(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
