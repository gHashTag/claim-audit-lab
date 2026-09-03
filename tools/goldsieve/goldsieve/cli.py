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
import re
import sys

from .sieve import run, CONFIRMED, REFUTED, QUESTION, EMPTY
from . import preconditions as _pre

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
    # Вердикты предпосылки (тик 48) перечислены явно: без них свод показал бы
    # их только при ненулевом счёте и в конце списка.
    tally = {CONFIRMED: 0, REFUTED: 0, QUESTION: 0, EMPTY: 0,
             _pre.ASSUMPTION: 0, _pre.NOT_APPLICABLE: 0}
    for r in reports:
        tally[r.verdict] = tally.get(r.verdict, 0) + 1
    print("свод: " + ", ".join("%s %d" % (k, v) for k, v in tally.items() if v))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
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

    НАЙДЕННЫЙ ДЕФЕКТ (луп 6). Прежняя версия объявляла пропуски только для сит
    С1..С14, поэтому в мутанте сита С15..С19 оставались НЕобъявленными, мета-сито
    С13 честно давало FAIL, и вердикт мутанта был ВОПРОС при ЛЮБОМ сдвиге —
    включая нулевой. «Срыв» фиксировался на первой же точке сетки, и команда
    печатала первое значение сетки как ответ. Из-за этого 28 записей в ведомости
    получили одинаковое «0,10 %», которое не измеряло ничего.

    Отсюда два обязательных изменения: пропуски объявляются для всех сит, а
    перед сканированием стоит КАЛИБРОВКА нулевым сдвигом. Если при нулевом
    сдвиге вердикт мутанта не совпал с базовым, число не печатается вообще:
    сначала надо понять, почему конвейер мутанта отличается от исходного.
    """
    from .sieve import run, CONFIRMED, _as_dict, Claim, sieve_numbers
    import copy

    def mutate(c, k):
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
        # пропуски объявляются для ВСЕХ сит, иначе С13 сорвёт мутанта сам
        m.skip_reasons = {"С%d" % i: "прогон мощности"
                          for i in sieve_numbers()}
        return m

    # Сетка спускается на девять порядков: печатная точность корпуса доходит до
    # шестой значащей цифры, а погрешность CODATA — до 1e-11, поэтому останов
    # на 0,1 % не измерил бы ни то, ни другое.
    GRID = (1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3,
            0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20)
    rc = 0
    for path in args.files:
        for c in load_claims(path):
            if c.reference is None:
                print("%s: эталона нет, мощность не определена" % c.name)
                continue
            base = run(c)
            print("утверждение: %s" % c.name)
            print("  исходный вердикт: %s" % base.verdict)
            # Порядок проверок важен, и первая попытка калибровки его нарушала.
            # Мутация ЗАМЕНЯЕТ заявленное значение на сдвинутый эталон, поэтому
            # при нулевом сдвиге заявленное совпадает с эталоном по построению —
            # и у опровергнутого утверждения расхождение исчезает. Калибровка
            # честно сообщала «не прошла» для шести опровержений, но это была
            # претензия не по адресу: мощность в такой постановке определена
            # только для подтверждённого утверждения. Сначала отсечь, потом
            # калибровать.
            if base.verdict != CONFIRMED:
                print("  исходный вердикт %s: мощность в этой постановке не "
                      "определена — мутация заменяет заявленное значение "
                      "эталоном и сама устраняет расхождение" % base.verdict)
                print()
                continue
            # КАЛИБРОВКА: нулевой сдвиг обязан дать тот же вердикт
            zero = run(mutate(c, 0.0)).verdict
            if zero != base.verdict:
                print("  КАЛИБРОВКА НЕ ПРОШЛА: при нулевом сдвиге вердикт %s "
                      "вместо %s — конвейер мощности не равен исходному, "
                      "число не выводится" % (zero, base.verdict))
                print()
                rc = 1
                continue
            print("  калибровка: нулевой сдвиг даёт %s" % zero)
            # Нулевой допуск: сито требует ТОЧНОГО совпадения, поэтому любой
            # сдвиг его ломает, и сканирование вернёт нижнюю границу сетки —
            # то есть свойство сетки, а не проверки. Такое разрешение задаётся
            # арифметикой, и об этом надо сказать словами, а не числом сетки.
            tol = c.tolerance() if callable(c.tolerance) else c.tolerance
            if tol == 0.0:
                print("  допуск нулевой: требуется точное совпадение, "
                      "разрешение ограничено только арифметикой "
                      "(2,2e-16 относительных); сканирование сеткой смысла "
                      "не имеет и не проводится")
                print()
                continue
            found = None
            for k in GRID:
                v = run(mutate(c, k)).verdict
                mark = "срыв" if v != CONFIRMED else "проходит"
                print("  сдвиг %+10.7f%% -> %-13s %s" % (100 * k, v, mark))
                if v != CONFIRMED and found is None:
                    found = k
                    break      # дальше сканировать нечего: сита монотонны
            if found is not None:
                print("  минимально различимое отклонение: %.3g%% "
                      "(нижняя граница сетки %.3g%%)"
                      % (100 * found, 100 * GRID[0]))
                if found == GRID[0]:
                    print("  ВНИМАНИЕ: срыв на первой точке сетки — истинное "
                          "разрешение может быть лучше, сетку надо продлить вниз")
            else:
                print("  ВНИМАНИЕ: не сорвалось даже на +20%% — проверка слепая")
            print()
    return rc


def cmd_cover(args):
    from .coverage import report
    from .cover_chunks import scan_tree_chunked
    per_file, state = scan_tree_chunked(
        args.root,
        checkpoint=args.checkpoint,
        chunk_size=args.chunk_size,
        timeout_seconds=args.chunk_timeout,
    )
    print(report(args.root, args.registry, per_file=per_file))
    if not state["complete"]:
        print("  разведка прервана лимитом чанка; продолжение с %s" %
              (state.get("last_successful_file") or "начала"))
    return 0


def _inputs_digest(report):
    """Свёрнутый отпечаток входных файлов прогона.

    Нужен, чтобы перепрогон реестра отличал «сито стало строже» от «корпус
    исправлен»: во втором случае прежний вердикт не является регрессией.
    """
    import hashlib
    inputs = (report.prov or {}).get("inputs") or {}
    if not isinstance(inputs, dict) or not inputs:
        return None
    parts = ["%s=%s" % (k, inputs[k]) for k in sorted(inputs)]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


REGRESSION_BASELINE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "baseline", "regression-fingerprints.json")
TRINITY_CORPUS = os.environ.get(
    "TRINITY_CORPUS", "/home/user/workspace/corpus/trinity")


def _file_sha256(path):
    import hashlib
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _source_file(root, source):
    """Найти наблюдаемый файл корпуса без чтения внешнего URL."""
    text = str(source or "").strip()
    if text.startswith(("http://", "https://")):
        return None
    rel = text.split(":", 1)[0]
    candidates = []
    if os.path.isabs(rel):
        candidates.append(rel)
    else:
        candidates.extend((
            os.path.join(TRINITY_CORPUS, rel),
            os.path.join(root, rel),
        ))
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def _source_files(root, source):
    """Найти все локальные файлы в составной ссылке на наблюдение.

    В старом снимке строка вроде ``a.json; b.csv`` становилась одним
    неразрешённым путём и затем могла навсегда остаться «неизменившейся»:
    инкрементальный регресс пропускал кейс даже при изменении ``a.json`` или
    ``b.csv``.  Разделители здесь относятся только к реестровому описанию
    источника; URL по-прежнему не читаются как локальные входы.
    """
    text = str(source or "").strip()
    if not text or text.startswith(("http://", "https://")):
        return []
    paths = []
    # В реестре составные наблюдения разделяются точкой с запятой или
    # запятой. Повторяющиеся пути сохраняем один раз в исходном порядке.
    for fragment in re.split(r"[;,]", text):
        rel = fragment.strip()
        if not rel:
            continue
        path = _source_file(root, rel)
        if path and path not in paths:
            paths.append(path)
    return paths


def _regression_fingerprints(entries, root):
    """Снимок файлов кейсов и их наблюдаемых входов.

    Снимок не запускает кейсы: он предназначен именно для выбора малого
    инкрементального регресса. Файл кейса покрывает изменение рецепта, а
    отпечатки файлов, прочитанных из корпуса, покрывают дрейф наблюдаемого.
    """
    by_case = {}
    for entry in entries:
        case = str(entry.get("case", ""))
        if not case:
            continue
        path = case if os.path.isabs(case) else os.path.join(root, case)
        sources = {}
        source_key = str(entry.get("source", ""))
        source_paths = _source_files(root, source_key)
        if len(source_paths) <= 1:
            source_path = source_paths[0] if source_paths else None
            sources[source_key] = {
                "path": source_path,
                "sha256": _file_sha256(source_path) if source_path else None,
            }
        else:
            # Сохраняем прежние path/sha256 для совместимости со снимками и
            # добавляем полный список только там, где реестр действительно
            # описывает несколько локальных входов.
            sources[source_key] = {
                "path": source_paths[0],
                "sha256": _file_sha256(source_paths[0]),
                "paths": source_paths,
                "sha256s": [_file_sha256(item) for item in source_paths],
            }
        row = by_case.setdefault(case, {
            "case_sha256": _file_sha256(path),
            "sources": {},
        })
        row["sources"].update(sources)
    import hashlib
    for row in by_case.values():
        payload = json.dumps(
            {"case_sha256": row["case_sha256"],
             "sources": row["sources"]},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        row["recipe_fingerprint"] = hashlib.sha256(
            payload.encode("utf-8")).hexdigest()[:16]
    return by_case


def _load_regression_baseline():
    try:
        with open(REGRESSION_BASELINE, encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("cases", {})
    except (OSError, ValueError, AttributeError):
        return {}


def _save_regression_baseline(fingerprints):
    os.makedirs(os.path.dirname(REGRESSION_BASELINE), exist_ok=True)
    payload = {
        "version": 1,
        "corpus": TRINITY_CORPUS,
        "cases": fingerprints,
    }
    with open(REGRESSION_BASELINE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)


def cmd_regress(args):
    """Перепрогон всего реестра: новый цикл не имеет права молча ломать старое.

    После каждого усиления каскада ранее выданные вердикты обязаны быть
    перепроверены: усиление МЕНЯЕТ вердикты, и это нормально, но изменение
    должно быть замечено и объяснено, а не пройти незаметно. Команда сверяет
    свежий прогон с записанным в реестре и возвращает ненулевой код при любом
    расхождении.
    """
    import yaml
    with open(args.registry, encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    entries = reg.get("claims", [])
    recorded = {}
    for e in entries:
        recorded.setdefault(e.get("case", ""), {})[e.get("claim", "")] = e.get("verdict")

    root = os.path.dirname(os.path.abspath(args.registry))
    all_fingerprints = _regression_fingerprints(entries, root)
    previous_fingerprints = _load_regression_baseline()
    if args.changed_only:
        selected_cases = {
            case for case, current in all_fingerprints.items()
            if case not in previous_fingerprints
            or current != previous_fingerprints.get(case)
            # Неразрешённый локальный source — не покрытие. Даже если такой
            # пропуск уже попал в старый снимок, кейс надо выбрать снова, чтобы
            # регресс не маскировал потерю входного файла. Внешний URL здесь не
            # считается локальным входом и намеренно остаётся вне отбора.
            or any(
                meta.get("path") is None
                and not str(source).startswith(("http://", "https://"))
                for source, meta in current.get("sources", {}).items()
            )
        }
    else:
        selected_cases = set(recorded)
    changed, same, missing, corpus_moved = [], [], [], []
    _all_digests = {}
    for case, by_claim in sorted(recorded.items()):
        if case not in selected_cases:
            continue
        path = case if os.path.isabs(case) else os.path.join(root, case)
        if not os.path.exists(path):
            missing.append(case)
            continue
        try:
            reports = [run(c) for c in load_claims(path)]
        except Exception as exc:  # noqa: BLE001
            missing.append("%s (упал: %r)" % (case, exc))
            continue
        fresh = {r.claim: r.verdict for r in reports}
        digests = {r.claim: _inputs_digest(r) for r in reports}
        _all_digests[case] = digests
        e_superseded = {}
        for e in entries:
            if e.get("case") == case and e.get("superseded_by"):
                e_superseded[" ".join(str(e.get("claim")).split()).lower()] = \
                    str(e["superseded_by"])
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
                # Отделяем регрессию сита от исправленного корпуса: если
                # отпечатки входных файлов не совпадают с записанными, вердикт
                # изменился потому, что изменились ДАННЫЕ, а не инструмент.
                # Смешивать эти два случая нельзя: первый — дефект, который надо
                # разбирать, второй — ожидаемое следствие принятой правки.
                rec_digest = None
                for e in entries:
                    if e.get("case") == case and norm(e.get("claim")) == want:
                        rec_digest = e.get("inputs_digest")
                        break
                got_digest = None
                for name, dig in digests.items():
                    if norm(name) == want or norm(name) in want or want in norm(name):
                        got_digest = dig
                        break
                if e_superseded.get(want):
                    # Утверждение уже исправлено в корпусе принятой правкой:
                    # свежий прогон читает исправленный текст, поэтому прежний
                    # вердикт не воспроизводится по построению. Это не
                    # регрессия сита и не требует разбора.
                    corpus_moved.append((case, claim_text, old, new,
                                         "исправлено " + e_superseded[want],
                                         "текущий корпус"))
                elif rec_digest and got_digest and rec_digest != got_digest:
                    corpus_moved.append((case, claim_text, old, new,
                                         rec_digest, got_digest))
                else:
                    changed.append((case, claim_text, old, new))
            else:
                same.append((case, claim_text, old))

    skipped = max(0, len(recorded) - len(selected_cases))
    mode = "инкрементальный" if args.changed_only else "полный"
    print("%s регресс реестра: выбрано %d, пропущено %d; %d совпало, "
          "%d изменилось ситом, "
          "%d изменилось из-за корпуса, %d не сопоставлено"
          % (mode, len(selected_cases), skipped, len(same), len(changed),
             len(corpus_moved), len(missing)))
    for case, claim_text, old, new, was, now in corpus_moved:
        print("  КОРПУС ИЗМЕНИЛСЯ %s -> %s | %s | %s | %s -> %s"
              % (old, new, claim_text, case, was, now))
    for case, claim_text, old, new in changed:
        print("  ИЗМЕНЁН %s -> %s | %s | %s" % (old, new, claim_text, case))
    for m in missing:
        print("  НЕ СОПОСТАВЛЕНО %s" % m)
    if args.update:
        # Отпечаток входов пишется всегда: без него следующий перепрогон не
        # сможет отличить исправленный корпус от ужесточённого сита.
        for e in entries:
            case = e.get("case", "")
            for name, dig in _all_digests.get(case, {}).items():
                if " ".join(str(name).split()).lower() == \
                        " ".join(str(e.get("claim")).split()).lower() and dig:
                    e["inputs_digest"] = dig
        for e in entries:
            for case, claim_text, old, new in changed + [
                    (c, t_, o, n) for c, t_, o, n, _w, _g in corpus_moved]:
                if e.get("case") == case and e.get("claim") == claim_text:
                    e["verdict"] = new
                    e["verdict_was"] = old
        with open(args.registry, "w", encoding="utf-8") as f:
            yaml.safe_dump(reg, f, allow_unicode=True, sort_keys=False)
        print("реестр обновлён: %s" % args.registry)
    _save_regression_baseline(all_fingerprints)
    return 1 if (changed or missing) else 0


def cmd_selftest(args):
    from .selftest import main
    return 1 if main() else 0


def cmd_new(args):
    if os.path.exists(args.path):
        raise SystemExit("файл уже есть: %s" % args.path)
    os.makedirs(os.path.dirname(os.path.abspath(args.path)), exist_ok=True)
    with open(args.path, "w", encoding="utf-8") as f:
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
    cv.add_argument("--checkpoint", default=None,
                    help="JSON-чекпоинт продолжения разведки")
    cv.add_argument("--chunk-size", type=int, default=64)
    cv.add_argument("--chunk-timeout", type=float, default=20.0)
    cv.set_defaults(fn=cmd_cover)

    rg = sub.add_parser("regress", help="перепрогон реестра: искать изменения вердиктов")
    rg.add_argument("--registry", default="claims.yaml")
    rg.add_argument("--changed-only", action="store_true",
                    help="проверить только изменившиеся кейсы и входы корпуса")
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
