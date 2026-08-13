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


def cmd_power(args):
    """Минимально различимое отклонение: вносим сдвиг и смотрим, когда сорвётся.

    Отвечает на вопрос, который иначе остаётся без ответа: проверка есть — а
    эффекты какой величины она вообще видит.
    """
    from .sieve import run, CONFIRMED, _as_dict, Claim
    import copy
    for path in args.files:
        for c in load_claims(path):
            if c.reference is None:
                print("%s: эталона нет, мощность не определена" % c.name)
                continue
            base = run(c)
            print("утверждение: %s" % c.name)
            print("  исходный вердикт: %s" % base.verdict)
            found = None
            for k in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20):
                m = copy.copy(c)
                ref = _as_dict(c.reference())
                shifted = {kk: v * (1.0 + k) for kk, v in ref.items()}
                m.stated = shifted if isinstance(c.stated, dict) else \
                    list(shifted.values())[0]
                m.observed = (lambda s=shifted: s) if c.observed is not None else None
                m.sample = None
                m.statistics = None
                m.bins = None
                m.estimators = None
                m.skip_reasons = {"С%d" % i: "прогон мощности" for i in range(1, 15)}
                v = run(m).verdict
                mark = "срыв" if v != CONFIRMED else "проходит"
                print("  сдвиг %+6.2f%% -> %-13s %s" % (100 * k, v, mark))
                if v != CONFIRMED and found is None:
                    found = k
            if found is not None:
                print("  минимально различимое отклонение: %.2f%%" % (100 * found))
            else:
                print("  ВНИМАНИЕ: не сорвалось даже на +20%% — проверка слепая")
            print()
    return 0


def cmd_cover(args):
    from .coverage import report
    print(report(args.root, args.registry))
    return 0


def cmd_regress(args):
    """Перепрогон всего реестра: новый цикл не имеет права молча ломать старое.

    После каждого усиления каскада ранее выданные вердикты обязаны быть
    перепроверены: усиление МЕНЯЕТ вердикты, и это нормально, но изменение
    должно быть замечено и объяснено, а не пройти незаметно. Команда сверяет
    свежий прогон с записанным в реестре и возвращает ненулевой код при любом
    расхождении.
    """
    import yaml
    with open(args.registry) as f:
        reg = yaml.safe_load(f) or {}
    entries = reg.get("claims", [])
    recorded = {}
    for e in entries:
        recorded.setdefault(e.get("case", ""), {})[e.get("claim", "")] = e.get("verdict")

    changed, same, missing = [], [], []
    root = os.path.dirname(os.path.abspath(args.registry))
    for case, by_claim in sorted(recorded.items()):
        path = case if os.path.isabs(case) else os.path.join(root, case)
        if not os.path.exists(path):
            missing.append(case)
            continue
        try:
            fresh = {c.name: run(c).verdict for c in load_claims(path)}
        except Exception as exc:  # noqa: BLE001
            missing.append("%s (упал: %r)" % (case, exc))
            continue
        for claim_text, old in by_claim.items():
            new = None
            # сопоставление без учёта регистра и лишних пробелов: расхождение
            # в одной заглавной букве не должно выглядеть как потерянная запись
            def norm(s):
                return " ".join(str(s).split()).lower()
            want = norm(claim_text)
            for name, verdict in fresh.items():
                got = norm(name)
                if got == want or got in want or want in got:
                    new = verdict
                    break
            if new is None:
                missing.append("%s :: %s" % (case, claim_text))
            elif new != old:
                changed.append((case, claim_text, old, new))
            else:
                same.append((case, claim_text, old))

    print("перепрогон реестра: %d совпало, %d изменилось, %d не сопоставлено"
          % (len(same), len(changed), len(missing)))
    for case, claim_text, old, new in changed:
        print("  ИЗМЕНЁН %s -> %s | %s | %s" % (old, new, claim_text, case))
    for m in missing:
        print("  НЕ СОПОСТАВЛЕНО %s" % m)
    if args.update and changed:
        for e in entries:
            for case, claim_text, old, new in changed:
                if e.get("case") == case and e.get("claim") == claim_text:
                    e["verdict"] = new
                    e["verdict_was"] = old
        with open(args.registry, "w") as f:
            yaml.safe_dump(reg, f, allow_unicode=True, sort_keys=False)
        print("реестр обновлён: %s" % args.registry)
    return 1 if (changed or missing) else 0


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

    pw = sub.add_parser("power", help="минимально различимое отклонение")
    pw.add_argument("files", nargs="+")
    pw.set_defaults(fn=cmd_power)

    cv = sub.add_parser("cover", help="триаж: покрытие корпуса утверждениями")
    cv.add_argument("root")
    cv.add_argument("--registry", default="claims.yaml")
    cv.set_defaults(fn=cmd_cover)

    rg = sub.add_parser("regress", help="перепрогон реестра: искать изменения вердиктов")
    rg.add_argument("--registry", default="claims.yaml")
    rg.add_argument("--update", action="store_true",
                    help="записать новые вердикты в реестр, сохранив прежний")
    rg.set_defaults(fn=cmd_regress)

    n = sub.add_parser("new", help="заготовка новой задачи")
    n.add_argument("path")
    n.set_defaults(fn=cmd_new)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
