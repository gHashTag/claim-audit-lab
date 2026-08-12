"""CLI золотого сита.

    python -m goldsieve run cases/zeta_gue.py        прогнать задачу
    python -m goldsieve run cases/*.py --json out.json
    python -m goldsieve selftest                     проверить сам инструмент
    python -m goldsieve new cases/my_task.py         заготовка новой задачи

Файл задачи — обычный модуль Python с переменной CLAIMS: список Claim.
"""

import argparse
import importlib.util
import json
import os
import sys

from .sieve import run, CONFIRMED, REFUTED, QUESTION, EMPTY

TEMPLATE = '''"""Задача: <одна строка, что проверяем>.

Правило: ни одно число не цитируется. reference — вычисляемый эталон,
wrong — заведомо неверный ответ той же формы, null_model — шум, который
конвейер обязан отвергнуть.
"""

from goldsieve.sieve import Claim


def reference():
    """Вычислить эталон из определений. Не возвращать литерал из документа."""
    raise NotImplementedError


CLAIMS = [
    Claim(
        name="<утверждение>",
        source="<файл:строка или документ>",
        stated=None,          # что заявлено
        reference=reference,  # вычисляемый эталон
        wrong=None,           # заведомо неверный ответ той же формы
        null_model=None,      # измерение на шуме
        tolerance=0.01,
    ),
]
'''


def load_claims(path):
    spec = importlib.util.spec_from_file_location("case_" + os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    claims = getattr(mod, "CLAIMS", None)
    if not claims:
        raise SystemExit("в %s нет переменной CLAIMS" % path)
    out = []
    for c in claims:
        if callable(getattr(c, "stated", None)):
            c.stated = c.stated()
        out.append(c)
    return out


def cmd_run(args):
    reports = []
    for path in args.files:
        for c in load_claims(path):
            r = run(c)
            reports.append(r)
            print(r.text())
            print()
    tally = {CONFIRMED: 0, REFUTED: 0, QUESTION: 0, EMPTY: 0}
    for r in reports:
        tally[r.verdict] = tally.get(r.verdict, 0) + 1
    print("свод: " + ", ".join("%s %d" % (k, v) for k, v in tally.items() if v))
    if args.json:
        with open(args.json, "w") as f:
            json.dump([json.loads(r.to_json()) for r in reports], f,
                      ensure_ascii=False, indent=1)
        print("json: %s" % args.json)
    # ненулевой код возврата, если есть опровержения или вырожденные проверки —
    # чтобы сито можно было ставить в CI
    return 1 if (tally.get(REFUTED) or tally.get(EMPTY)) else 0


def cmd_selftest(args):
    from .selftest import main
    return 1 if main() else 0


def cmd_new(args):
    if os.path.exists(args.path):
        raise SystemExit("файл уже есть: %s" % args.path)
    os.makedirs(os.path.dirname(os.path.abspath(args.path)), exist_ok=True)
    with open(args.path, "w") as f:
        f.write(TEMPLATE)
    print("создано: %s" % args.path)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="goldsieve", description="золотое сито")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="прогнать файлы задач")
    r.add_argument("files", nargs="+")
    r.add_argument("--json", default=None)
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("selftest", help="проверить сам инструмент")
    s.set_defaults(fn=cmd_selftest)

    n = sub.add_parser("new", help="заготовка новой задачи")
    n.add_argument("path")
    n.set_defaults(fn=cmd_new)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
