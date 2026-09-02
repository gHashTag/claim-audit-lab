#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 261: сторож содержательного отличия тика (запрет холостого тика v2).

Прежний запрет холостого тика сравнивал sha256 ТЕКСТА доклада. Этот признак
тривиально обходится: достаточно иного абзаца. Измерено на настоящих докладах
тиков 215-259: все отпечатки текста различны, но машинная СУТЬ повторяется.
Суть — только числа, которые тик обязан предъявить: итог гейта, четвёрка
регресса, итог ОС-матрицы, состояние учёта BBLM и множество изменённых файлов
инструмента. Проза в подпись не входит намеренно.

Второй признак застоя — предмет правки. Почти каждый тик отрезка 226-259 правил
один и тот же файл, парсер ответа GitHub API, добавляя по одной микромутации
(`run_attempt`, `total_count`, `run.id`, HTML против API URL, путь workflow).
Каждая правка по отдельности законна, но предмет аудита — корпус Trinity и
каскад сит, а не клиент чужого API. Правило: один и тот же файл не может быть
единственным изменённым больше двух тиков подряд.

  --history <каталог>  измерить повторы сути на настоящих докладах tickNNN-report.md
  --check <файл.json>  проверить суть текущего тика против журнала
  --record <файл.json> записать суть текущего тика в журнал
  --selftest           чувствительность на фикстурах и мутационных целях
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = Path("/home/user/workspace/cron_tracking/20fee222/progress-log.jsonl")
OUT = HERE / "progress_guard.json"
# Сколько прошлых тиков сравнивать. Три — не «красивое число»: приказ уже
# требует ревизии молчащих проверок после трёх тиков без изменений, порог здесь
# согласован с ним, чтобы два правила не противоречили друг другу.
WINDOW = 3
SOLE_FILE_LIMIT = 2

FIELDS = ("гейт", "регресс", "ос_матрица", "bblm", "изменённые_файлы")


def parse_report(text: str) -> dict:
    """Суть доклада: только машинные числа, проза отбрасывается."""
    out: dict = {}

    m = re.search(r"(\d+)\s+(?:шаг\w*\s+)?`?ok`?[\s\S]{0,160}?(\d+)\s+штатн\w*\s+"
                  r"пропуск\w*[\s\S]{0,160}?(\d+)\s+провал", text)
    if not m:
        m = re.search(r"гейт[\s\S]{0,160}?(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", text,
                      re.IGNORECASE)
    if not m:
        # Новые доклады иногда пишут машинный итог без обратных кавычек:
        # «69 ok, 2 штатных пропуска, 0 провалов». Это тот же наблюдаемый
        # тройной счётчик; значения не восстанавливаются из соседних тиков.
        m = re.search(r"(\d+)\s+ok[\s\S]{0,100}?(\d+)\s+штатн\w*\s+"
                      r"пропуск\w*[\s\S]{0,100}?(\d+)\s+провал", text,
                      re.IGNORECASE)
    if m:
        out["гейт"] = [int(m.group(1)), int(m.group(2)), int(m.group(3))]

    m = re.search(r"(\d+)\s+совпа\w+[\s\S]{0,60}?(\d+)\s+измен\w+\s+ситом"
                  r"[\s\S]{0,80}?(\d+)\s+измен\w+", text)
    if not m:
        m = re.search(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*/\s*0", text)
    if m:
        out["регресс"] = [int(m.group(1)), int(m.group(2)), int(m.group(3))]

    m = re.search(r"(\d+)\s*(?:из|/)\s*(\d+)\s+задани", text)
    if m:
        out["ос_матрица"] = [int(m.group(1)), int(m.group(2))]
    elif re.search(r"\bпять\s+задани\w*\s+пять\s+заверш|"
                   r"\bиз\s+шести\s+задани\w*\s+пять\s+заверш", text,
                   re.IGNORECASE):
        out["ос_матрица"] = [5, 6]
    elif re.search(r"(?:успешно\s+)?все\s+6\s+задани\w*|"
                   r"6\s+задани\w*\s+завершен\w*\s+успешно", text,
                   re.IGNORECASE):
        # Исторические доклады иногда не писали дробь «6 из 6», но
        # сообщали тот же наблюдаемый итог словами. Число заданий
        # восстанавливается из самой строки, без подстановки результата
        # соседнего тика.
        out["ос_матрица"] = [6, 6]
    elif re.search(r"шесть\s+заданий|6/6", text):
        out["ос_матрица"] = [6, 6]

    m = re.search(r"(\d+)\s+элемент\w*,?\s+закрыт\w*\s+кодом", text)
    if not m:
        m = re.search(r"кодом\s+закрыт\w*\s+(\d+)", text)
    if not m:
        # В докладе тика 261 порядок слов был обратным: «закрыто кодом
        # 4 элемента». Это всё ещё наблюдаемый счётчик, поэтому разбор можно
        # расширить без восстановления отсутствующих значений.
        m = re.search(r"закрыт\w*\s+кодом\s+(\d+)\s+элемент", text,
                      re.IGNORECASE)
    if not m:
        # В некоторых новых докладах машинный счётчик заключён в обратные
        # кавычки: «закрыто кодом `4` элемента из `8`». Кавычки не меняют
        # наблюдаемое число и не должны делать доклад неразбираемым.
        m = re.search(r"закрыт\w*\s+кодом\s+`?(\d+)`?\s+элемент", text,
                      re.IGNORECASE)
    # Старые доклады до введения обязательной машинной сути писали только
    # неполный счётчик протокола: «заполнены 3 из 8 элементов». Это не
    # позволяет восстановить полный протокол, но число закрытых элементов и
    # код отсутствующего аналитического источника наблюдаемы и пригодны для
    # честного сравнения истории.
    if not m:
        m = re.search(r"(?:заполнен\w*|присутств\w*)\s+(\d+)\s+из\s+8\s+"
                      r"(?:обязательных\s+)?элемент", text,
                      re.IGNORECASE)
    if not m:
        # Историческая форма: «из 8 обязательных элементов присутствуют 7».
        m = re.search(r"из\s+8\s+обязательных\s+элемент\w*\s+"
                      r"присутств\w*\s+(\d+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"BBLM[\s\S]{0,80}?(\d+)\s+(?:закрыт|элемент)", text)
    closed = int(m.group(1)) if m else None
    if closed is not None:
        out["bblm"] = [closed, "analytic_source_absent" in text]

    return out


def signature(substance: dict) -> str:
    payload = {k: substance.get(k) for k in FIELDS}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def read_log(path: Path = LOG) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def verdict(substance: dict, history: list[dict],
            window: int = WINDOW,
            sole_limit: int = SOLE_FILE_LIMIT) -> dict:
    """Решение по СОСТАВУ фактов: повтор сути либо застревание на одном файле."""
    sig = signature(substance)
    recent = history[-window:]
    repeats = [h for h in recent if h.get("подпись") == sig]

    files = substance.get("изменённые_файлы") or []
    sole = files[0] if len(files) == 1 else None
    streak = 0
    if sole is not None:
        streak = 1
        for h in reversed(history):
            hf = h.get("суть", {}).get("изменённые_файлы") or []
            if len(hf) == 1 and hf[0] == sole:
                streak += 1
            else:
                break

    reasons = []
    if repeats:
        reasons.append("substance_repeat")
    if not files and repeats:
        reasons.append("no_tool_change")
    if sole is not None and streak > sole_limit:
        reasons.append("single_file_streak:" + sole)

    return {
        "подпись": sig,
        "повторов_в_окне": len(repeats),
        "единственный_файл": sole,
        "длина_серии": streak,
        "причины": reasons,
        "итог": "ХОЛОСТОЙ" if reasons else "СОДЕРЖАТЕЛЬНЫЙ",
    }


def history_scan(root: Path) -> dict:
    reports = sorted(root.glob("tick*-report.md"))
    groups: dict[str, list[str]] = {}
    unparsable = []
    unparsed_reasons = []
    for p in reports:
        text = p.read_text(encoding="utf-8", errors="replace")
        sub = parse_report(text)
        if len(sub) < 3:
            unparsable.append(p.name)
            missing = [field for field in FIELDS if field not in sub]
            unparsed_reasons.append({
                "имя": p.name,
                "недостающие_поля": missing,
                "причина": (
                    "старый доклад не содержит машинных итогов "
                    + ", ".join(missing)
                    + "; значения не восстанавливаются из соседних тиков"
                ),
            })
            continue
        groups.setdefault(signature(sub), []).append(p.name)
    collisions = {k: v for k, v in groups.items() if len(v) > 1}
    return {
        "докладов": len(reports),
        "разобрано": len(reports) - len(unparsable),
        "не_разобрано": unparsable,
        "различных_сутей": len(groups),
        "групп_повторов": len(collisions),
        "повторяющихся_докладов": sum(len(v) for v in collisions.values()),
        "повторы": collisions,
        "неразобрано_с_причинами": unparsed_reasons,
    }


def _selftest() -> int:
    passed = failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
            print("ПРОВАЛ: " + name)

    text = ("Гейт открыт: 66 шагов `ok`, 2 штатных пропуска, 0 провалов. "
            "Регрессия: 150 совпало, 0 изменилось ситом, 3 изменилось из-за "
            "корпуса, 0 не сопоставлено. ОС-матрица: все 6 из 6 заданий "
            "завершились успешно. BBLM: 4 элемента, закрытых кодом, и один "
            "машинный вопрос analytic_source_absent.")
    sub = parse_report(text)
    check("разбор гейта", sub.get("гейт") == [66, 2, 0])
    check("разбор регресса", sub.get("регресс") == [150, 0, 3])
    check("разбор ОС-матрицы", sub.get("ос_матрица") == [6, 6])
    check("разбор BBLM", sub.get("bblm") == [4, True])

    legacy = ("Протокол BBLM остаётся машинным вопросом: заполнены 3 из 8 "
              "элементов; код analytic_source_absent.")
    check("разбор неполного старого BBLM",
          parse_report(legacy).get("bblm") == [3, True])

    # Иная проза, те же числа — подпись обязана совпасть.
    other = ("Совершенно другой текст доклада. Регрессия дала 150 совпало, "
             "0 изменилось ситом, 3 изменилось из-за корпуса. Гейт: 66 шагов "
             "`ok`, 2 штатных пропуска, 0 провалов. Задания ОС-матрицы: 6 из 6 "
             "заданий успешны. BBLM: 4 элемента, закрытых кодом, "
             "analytic_source_absent.")
    check("иная проза при тех же числах даёт ту же подпись",
          signature(parse_report(text)) == signature(parse_report(other)))
    # Иные числа — подпись обязана отличаться.
    changed = text.replace("150 совпало", "151 совпало")
    check("изменение числа меняет подпись",
          signature(parse_report(text)) != signature(parse_report(changed)))

    base = dict(sub)
    base["изменённые_файлы"] = ["os_matrix_audit.py"]
    hist = [{"подпись": signature(base), "суть": base} for _ in range(3)]
    v = verdict(base, hist)
    check("повтор сути пойман", "substance_repeat" in v["причины"])
    check("серия одного файла поймана",
          any(r.startswith("single_file_streak") for r in v["причины"]))
    check("итог холостой", v["итог"] == "ХОЛОСТОЙ")

    fresh = dict(base)
    fresh["регресс"] = [151, 0, 3]
    fresh["изменённые_файлы"] = ["repo_sync_guard.py", "ci_gate.sh"]
    v2 = verdict(fresh, hist)
    check("содержательный тик проходит", v2["итог"] == "СОДЕРЖАТЕЛЬНЫЙ")

    # Мутационная цель: сторож, сравнивающий текст вместо чисел, обязан
    # пропустить именно тот случай, который рабочий сторож ловит.
    mut_a = hashlib.sha256(text.encode("utf-8")).hexdigest()
    mut_b = hashlib.sha256(other.encode("utf-8")).hexdigest()
    check("мутант по тексту доклада пропускает повтор сути", mut_a != mut_b)

    # Отрицательная фикстура: пустая история не может дать ХОЛОСТОЙ.
    check("пустая история не наказывает",
          verdict(base, [])["итог"] == "СОДЕРЖАТЕЛЬНЫЙ")

    # Порог серии проверяем на границе: ровно предел — ещё проходит.
    hist2 = [{"подпись": "иная", "суть": base}]
    v3 = verdict(dict(base, регресс=[999, 0, 3]), hist2)
    check("серия ровно на пределе проходит",
          not any(r.startswith("single_file_streak") for r in v3["причины"]))

    print("самопроверка сторожа содержательности: %d пройдено, %d провалено"
          % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()

    if "--history" in argv:
        root = Path(argv[argv.index("--history") + 1])
        rep = history_scan(root)
        OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("докладов %d, разобрано %d, различных сутей %d, групп повторов "
              "%d, докладов в повторах %d"
              % (rep["докладов"], rep["разобрано"], rep["различных_сутей"],
                 rep["групп_повторов"], rep["повторяющихся_докладов"]))
        for sig, names in rep["повторы"].items():
            print("  %s: %s" % (sig, ", ".join(names)))
        # Неполные старые доклады нельзя честно восстановить из соседних
        # тиков.  Раньше CLI сохранял причины только в JSON, поэтому
        # обязательный P5 выглядел как «разобрано», хотя имена долгов в
        # стандартном выводе отсутствовали.  Показываем только наблюдаемые
        # пропуски и их причины; значения машинной сути не подставляем.
        for item in rep.get("неразобрано_с_причинами", []):
            print("  НЕРАЗОБРАНО %s: %s"
                  % (item["имя"], item["причина"]))
        return 0

    for flag in ("--check", "--record"):
        if flag in argv:
            path = Path(argv[argv.index(flag) + 1])
            sub = json.loads(path.read_text(encoding="utf-8"))
            hist = read_log()
            v = verdict(sub, hist)
            OUT.write_text(json.dumps({"суть": sub, **v}, ensure_ascii=False,
                                      indent=1), encoding="utf-8")
            print("подпись %s, итог %s, причины: %s"
                  % (v["подпись"], v["итог"], ", ".join(v["причины"]) or "нет"))
            if flag == "--record":
                LOG.parent.mkdir(parents=True, exist_ok=True)
                with LOG.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"подпись": v["подпись"], "суть": sub},
                                        ensure_ascii=False) + "\n")
            return 1 if v["итог"] == "ХОЛОСТОЙ" else 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
