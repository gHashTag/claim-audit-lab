"""Неизменяемый baseline инструмента и гейт отклонений.

Зачем. Метрика без привязки к состоянию инструмента ничего не значит: «28/28»
верно только для конкретного текста детектора, конкретного интерпретатора и
конкретной платформы. Baseline фиксирует это состояние целиком, поэтому
следующий тик не может незаметно изменить условие измерения.

Три режима:

  python3 baseline.py snapshot   собрать baseline (перезаписывает файлы)
  python3 baseline.py check      сверить текущее состояние с baseline
  python3 baseline.py show       напечатать сводку baseline

Гейт (`check`) даёт ненулевой код возврата, если:
  * ухудшилась любая метрика корпуса (пропуск, ложное срабатывание, поломка);
  * вердикт из реестра изменился и НЕ имеет reason-code в reasons.yaml;
  * изменился текст инструмента при неизменной сводке метрик, а reason-code
    отсутствует (молчаливая правка).

Reason-code обязателен для КАЖДОГО отклонения: без него отличие превращается в
«молчаливое исключение», а именно так теряются найденные дефекты.
"""

from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "baseline")
MANIFEST = os.path.join(DIR, "manifest.json")
VERDICTS_JSON = os.path.join(DIR, "verdicts.json")
VERDICTS_CSV = os.path.join(DIR, "verdicts.csv")
REASONS = os.path.join(DIR, "reasons.yaml")
SEED = int(os.environ.get("GOLDSIEVE_SEED", "20260814"))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _tool_files() -> list[str]:
    out = []
    for sub in ("goldsieve", "cases"):
        base = os.path.join(ROOT, sub)
        for dirpath, _dirs, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for name in sorted(files):
                if name.endswith(".py"):
                    out.append(os.path.relpath(os.path.join(dirpath, name), ROOT))
    # Тик 41: гейт, манифест покрытия и счётчики ОБЯЗАНЫ входить в отпечаток.
    # До этой правки правку ci_gate.sh (например, удаление шага) отпечаток не
    # замечал: можно было ослабить гейт, не тронув ни один охваченный файл.
    for name in ("claims.yaml", "measure_identity.py", "mutation_identity.py",
                 "calibrate_identity.py", "calibrate_sieves.py",
                 "baseline.py", "ci_gate.sh",
                 "coverage_manifest.py", "coverage_manifest.yaml",
                 "tick_counters.py",
                 # Тик 43: оболочка и её обвязка. Отпечаток обязан замечать
                 # правку tri и ослабление интеграционных тестов.
                 "tri", "tri_integration_test.py", "snapshot_manifest.py",
                 "archive_contract.py", "bench.py",
                 # Тик 44: измеритель стоимости журналирования.
                 "chain_overhead.py"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            out.append(name)
    # Тик 91: дыра охвата. Реализации шагов гейта, лежащие в КОРНЕ
    # (gue_label_guard.py, bblm_protocol.py, prefilter.py, aborted_audit.py,
    # replay_queue.py и т.п.), в отпечаток НЕ входили: правка запрета
    # (включая его ослабление) не меняла files_digest. Ставим весь корень
    # под отпечаток, лишнего там нет: одноразовые patch_*/debug_* тоже
    # влияют на состояние рабочей копии и должны быть видны в диффе.
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".py") and os.path.isfile(os.path.join(ROOT, name)):
            out.append(name)
    return sorted(set(out))


def _gate_missing(root: str, covered: set[str]) -> tuple[set[str], list[str]]:
    with open(os.path.join(root, "ci_gate.sh"), encoding="utf-8") as fh:
        text = fh.read()
    refs = set(re.findall(r"[\w./-]+\.py", text))
    missing = sorted(r for r in refs
                     if os.path.exists(os.path.join(root, r)) and r not in covered)
    return refs, missing


def gate_coverage_selftest() -> int:
    """Измеренная чувствительность проверки охвата: молчание ≠ покрытие.

    Фикстуры: (1) скрипт шага вне отпечатка ОБЯЗАН быть найден;
    (2) полный охват даёт пустой список; (3) ссылка на НЕСУЩЕСТВУЮЩИЙ файл
    не считается пробелом охвата (иначе комментарий в гейте ломает проверку).
    """
    import tempfile
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "covered.py"), "w").close()
        open(os.path.join(td, "nocover.py"), "w").close()
        with open(os.path.join(td, "ci_gate.sh"), "w", encoding="utf-8") as fh:
            fh.write("step a python3 covered.py\nstep b python3 nocover.py\n"
                     "# упоминание ghost.py в комментарии\n")
        cases = [
            ({"covered.py"}, ["nocover.py"], "неохваченный шаг находится"),
            ({"covered.py", "nocover.py"}, [], "полный охват молчит"),
        ]
        for covered, want, label in cases:
            _refs, missing = _gate_missing(td, covered)
            ok = missing == want
            bad += 0 if ok else 1
            print("  %s %s: ожидалось %s, получено %s"
                  % ("ok " if ok else "ПРОВАЛ", label, want, missing))
        refs, missing = _gate_missing(td, {"covered.py", "nocover.py"})
        ok = "ghost.py" in refs and "ghost.py" not in missing
        bad += 0 if ok else 1
        print("  %s ссылка на несуществующий файл не ломает проверку"
              % ("ok " if ok else "ПРОВАЛ"))
    print("самопроверка охвата гейта: провалов %d" % bad)
    return 1 if bad else 0


def gate_coverage() -> int:
    """Тик 91: каждый скрипт, который ЗАПУСКАЕТ гейт, обязан быть в отпечатке.

    Список берётся КОДОМ из ci_gate.sh, а не поддерживается руками: иначе
    новый шаг гейта снова окажется вне отпечатка и его можно будет ослабить
    незаметно для снимка. Код возврата 1 при любом неохваченном скрипте.
    """
    gate = os.path.join(ROOT, "ci_gate.sh")
    if not os.path.exists(gate):
        print("ОТКАЗ: ci_gate.sh не найден")
        return 1
    refs, missing = _gate_missing(ROOT, set(_tool_files()))
    print("скриптов в гейте: %d, охвачено отпечатком: %d"
          % (len(refs), len(refs) - len(missing)))
    if missing:
        print("НЕ ОХВАЧЕНО СНИМКОМ: " + ", ".join(missing))
        return 1
    print("охват соблюдён: все скрипты шагов гейта входят в files_digest")
    return 0


def _versions() -> dict:
    out = {"python": sys.version.split()[0],
           "python_implementation": platform.python_implementation()}
    for mod in ("numpy", "scipy", "mpmath", "yaml"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "?")
        except Exception:
            out[mod] = None
    return out


def _run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="backslashreplace",
                       timeout=3600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _metrics() -> dict:
    """Сводка корпуса: получается ПРОГОНОМ, не переписыванием чисел руками."""
    m = {}
    code, out = _run([sys.executable, "measure_identity.py"])
    m["measure_exit"] = code
    for line in out.splitlines():
        if line.startswith("чувствительность:"):
            m["sensitivity"] = line.split()[1]
            m["positive"] = line.split()[2].strip("[]")
        if line.startswith("специфичность:"):
            m["specificity"] = line.split()[1]
            m["negative"] = line.split()[2].strip("[]")
    code, out = _run([sys.executable, "mutation_identity.py"])
    m["mutation_exit"] = code
    for line in out.splitlines():
        if line.startswith("поймано поломок:"):
            m["mutants_caught"] = line.split(":")[1].strip()
    code, out = _run([sys.executable, "-m", "goldsieve.selftest"])
    m["selftest_exit"] = code
    for line in out.splitlines():
        if "итог:" in line:
            m["selftest"] = line.split("итог:")[1].strip()
    return m


def _verdicts() -> list[dict]:
    import yaml
    with open(os.path.join(ROOT, "claims.yaml"), encoding="utf-8") as fh:
        reg = yaml.safe_load(fh) or {}
    rows = []
    for e in reg.get("claims", []):
        rows.append({"case": e.get("case", ""),
                     "claim": " ".join(str(e.get("claim", "")).split()),
                     "verdict": e.get("verdict"),
                     "source": e.get("source", ""),
                     "inputs_digest": e.get("inputs_digest", "")})
    return sorted(rows, key=lambda r: (r["case"], r["claim"]))


def _corpus_head() -> str:
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"],
                           cwd="/home/user/workspace/corpus/trinity",
                           capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", timeout=60)
        return p.stdout.strip() or "?"
    except Exception:
        return "?"


def _reasons() -> dict:
    if not os.path.exists(REASONS):
        return {}
    import yaml
    with open(REASONS, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    out = {}
    for e in data.get("deviations", []):
        key = (e.get("case", ""), " ".join(str(e.get("claim", "")).split()))
        out[key] = e
    return out


def snapshot() -> int:
    os.makedirs(DIR, exist_ok=True)
    files = {rel: _sha256(os.path.join(ROOT, rel)) for rel in _tool_files()}
    man = {
        "seed": SEED,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "versions": _versions(),
        "corpus_head": _corpus_head(),
        "files": files,
        "files_digest": hashlib.sha256(
            json.dumps(files, sort_keys=True).encode()).hexdigest()[:16],
        "metrics": _metrics(),
    }
    rows = _verdicts()
    man["verdicts_digest"] = hashlib.sha256(
        json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2, sort_keys=True)
    with open(VERDICTS_JSON, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
    with open(VERDICTS_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["case", "claim", "verdict",
                                           "source", "inputs_digest"])
        w.writeheader()
        w.writerows(rows)
    print("baseline записан: %d файлов инструмента, %d вердиктов"
          % (len(files), len(rows)))
    print("  отпечаток файлов:    " + man["files_digest"])
    print("  отпечаток вердиктов: " + man["verdicts_digest"])
    print("  метрики: " + json.dumps(man["metrics"], ensure_ascii=False))
    return 0


def show() -> int:
    if not os.path.exists(MANIFEST):
        print("baseline отсутствует")
        return 1
    man = json.load(open(MANIFEST, encoding="utf-8"))
    for key in ("seed", "platform", "machine", "corpus_head",
                "files_digest", "verdicts_digest"):
        print("%-18s %s" % (key, man.get(key)))
    print("%-18s %s" % ("versions", json.dumps(man["versions"],
                                               ensure_ascii=False)))
    print("%-18s %s" % ("metrics", json.dumps(man["metrics"],
                                              ensure_ascii=False)))
    print("файлов инструмента: %d" % len(man.get("files", {})))
    return 0


def check() -> int:
    if not os.path.exists(MANIFEST):
        print("ОТКАЗ: baseline отсутствует, сначала snapshot")
        return 1
    man = json.load(open(MANIFEST, encoding="utf-8"))
    base_rows = json.load(open(VERDICTS_JSON, encoding="utf-8"))
    reasons = _reasons()
    problems: list[str] = []

    # --- 1. метрики корпуса: ухудшение блокирует ----------------------------
    cur = _metrics()
    print("метрики сейчас:  " + json.dumps(cur, ensure_ascii=False))
    print("метрики baseline:" + json.dumps(man.get("metrics", {}),
                                           ensure_ascii=False))
    for key in ("measure_exit", "mutation_exit", "selftest_exit"):
        if cur.get(key) != 0:
            problems.append("прогон не прошёл: %s = %s" % (key, cur.get(key)))
    for key in ("sensitivity", "specificity"):
        old, new = man["metrics"].get(key), cur.get(key)
        try:
            if new is not None and old is not None and float(new) < float(old):
                problems.append("метрика ухудшилась: %s %s -> %s"
                                % (key, old, new))
        except ValueError:
            problems.append("метрика нечитаема: %s = %r" % (key, new))
    old_m, new_m = man["metrics"].get("mutants_caught"), cur.get("mutants_caught")
    if old_m and new_m:
        def frac(s):
            a, b = s.split("/")
            return int(a), int(b)
        oa, ob = frac(old_m)
        na, nb = frac(new_m)
        if na - nb < oa - ob or (nb >= ob and na < oa):
            problems.append("мутанты: %s -> %s" % (old_m, new_m))

    # --- 2. вердикты: каждое отклонение обязано иметь reason-code -----------
    cur_rows = {(r["case"], r["claim"]): r for r in _verdicts()}
    base_map = {(r["case"], r["claim"]): r for r in base_rows}
    unclassified = 0
    for key, old in base_map.items():
        new = cur_rows.get(key)
        if new is None:
            if key not in reasons:
                problems.append("запись исчезла без reason-code: %s :: %s"
                                % (key[0], key[1][:60]))
                unclassified += 1
            continue
        if new["verdict"] != old["verdict"]:
            rc = reasons.get(key)
            if not rc or not rc.get("reason_code"):
                problems.append("вердикт изменился без reason-code: %s :: %s "
                                "(%s -> %s)" % (key[0], key[1][:50],
                                                old["verdict"], new["verdict"]))
                unclassified += 1
            else:
                print("  классифицировано [%s] %s :: %s -> %s"
                      % (rc["reason_code"], key[0], old["verdict"],
                         new["verdict"]))
    for key in cur_rows:
        if key not in base_map and key not in reasons:
            print("  новая запись (не отклонение): %s :: %s"
                  % (key[0], key[1][:50]))

    print()
    print("неклассифицированных отклонений: %d" % unclassified)
    if problems:
        print("ГЕЙТ ЗАКРЫТ: %d причин" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("ГЕЙТ ОТКРЫТ: ухудшений нет, все отклонения классифицированы")
    return 0


FROZEN = os.path.join(DIR, "frozen-v12.json")
FROZEN_SHA = os.path.join(DIR, "frozen-v12.sha256")
FROZEN_LABEL = "v12 (тик 40, quenched)"


def _canon(obj) -> bytes:
    """Каноническая форма для отпечатка: порядок ключей не должен влиять."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()


def _frozen_load() -> tuple[dict, list[str]]:
    """Чтение заморозки с проверкой целостности. Список — найденные нарушения."""
    problems: list[str] = []
    if not os.path.exists(FROZEN):
        return {}, ["заморозка отсутствует: baseline/frozen-v12.json"]
    body = json.load(open(FROZEN, encoding="utf-8"))
    want = hashlib.sha256(_canon(body)).hexdigest()
    if not os.path.exists(FROZEN_SHA):
        problems.append("отпечаток заморозки отсутствует: frozen-v12.sha256")
    else:
        got = open(FROZEN_SHA, encoding="utf-8").read().strip().split()[0]
        if got != want:
            problems.append("ЦЕЛОСТНОСТЬ ЗАМОРОЗКИ НАРУШЕНА: тело даёт %s, "
                            "записано %s" % (want[:16], got[:16]))
    return body, problems


def freeze(force: bool = False) -> int:
    """Зафиксировать ТЕКУЩИЙ подвижный снимок как неподвижную точку."""
    if os.path.exists(FROZEN) and not force:
        print("ОТКАЗ: заморозка уже существует. Перезапись — режим refreeze, "
              "и только после независимого review.")
        return 1
    if not os.path.exists(MANIFEST) or not os.path.exists(VERDICTS_JSON):
        print("ОТКАЗ: подвижный snapshot отсутствует, сначала snapshot")
        return 1
    man = json.load(open(MANIFEST, encoding="utf-8"))
    body = {
        "label": FROZEN_LABEL,
        "frozen_at": _dt.datetime.now(_dt.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "qualified_scope": (
            "детектор косвенной тавтологии: классы конструкций, перечисленные в "
            "coverage_manifest.yaml, на интерпретаторах из versions; вне этого "
            "перечня охват НЕ заявлен"),
        "files": man.get("files", {}),
        "files_digest": man.get("files_digest"),
        "verdicts_digest": man.get("verdicts_digest"),
        "metrics": man.get("metrics", {}),
        "versions": man.get("versions", {}),
        "corpus_head": man.get("corpus_head"),
        "platform": man.get("platform"),
    }
    with open(FROZEN, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2, sort_keys=True)
    # Отпечаток считается по каноническому телу, а не по байтам файла: иначе
    # безобидное переформатирование ломало бы проверку и её начали бы обходить.
    digest = hashlib.sha256(_canon(body)).hexdigest()
    with open(FROZEN_SHA, "w", encoding="utf-8") as fh:
        fh.write(digest + "  frozen-v12.json\n")
    print("заморожено: %s" % FROZEN_LABEL)
    print("  отпечаток заморозки: " + digest[:16])
    print("  файлов: %d  метрики: %s"
          % (len(body["files"]), json.dumps(body["metrics"],
                                            ensure_ascii=False)))
    return 0


def frozen_delta() -> int:
    """Дельта frozen -> current. Падает только при нарушении целостности."""
    body, problems = _frozen_load()
    if problems:
        print("ГЕЙТ ЗАКРЫТ: заморозка непригодна")
        for p in problems:
            print("  - " + p)
        return 1
    print("заморозка: %s  от %s" % (body.get("label"), body.get("frozen_at")))
    print("объявленный охват: %s" % body.get("qualified_scope"))
    cur_files = {rel: _sha256(os.path.join(ROOT, rel)) for rel in _tool_files()}
    cur_digest = hashlib.sha256(
        json.dumps(cur_files, sort_keys=True).encode()).hexdigest()[:16]
    print()
    print("%-22s %s -> %s" % ("отпечаток файлов", body.get("files_digest"),
                              cur_digest))
    old_files = body.get("files", {})
    changed = sorted(r for r in set(old_files) | set(cur_files)
                     if old_files.get(r) != cur_files.get(r))
    print("изменившихся файлов инструмента: %d" % len(changed))
    for rel in changed[:40]:
        mark = ("новый" if rel not in old_files else
                "удалён" if rel not in cur_files else "правлен")
        print("  %-8s %s" % (mark, rel))
    cur = _metrics()
    print()
    print("метрики заморозки: " + json.dumps(body.get("metrics", {}),
                                             ensure_ascii=False))
    print("метрики сейчас:    " + json.dumps(cur, ensure_ascii=False))
    for key in ("sensitivity", "specificity"):
        old, new = body.get("metrics", {}).get(key), cur.get(key)
        try:
            if old is not None and new is not None and float(new) < float(old):
                print("  ВНИМАНИЕ метрика ниже замороженной: %s %s -> %s"
                      % (key, old, new))
        except ValueError:
            pass
    return 0


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "show"
    if mode == "snapshot":
        return snapshot()
    if mode == "check":
        return check()
    if mode == "show":
        return show()
    if mode == "freeze":
        return freeze(force=False)
    if mode == "refreeze":
        if "--i-have-review" not in argv:
            print("ОТКАЗ: refreeze перезаписывает квалифицированную точку. "
                  "Требуется флаг --i-have-review и запись в ведомости о том, "
                  "кто и когда провёл независимый review.")
            return 1
        print("ВНИМАНИЕ: квалифицированная точка перезаписывается.")
        return freeze(force=True)
    if mode == "frozen":
        return frozen_delta()
    if mode == "gate-coverage":
        if "--selftest" in argv:
            return gate_coverage_selftest()
        return gate_coverage()
    print("режимы: snapshot | check | show | freeze | refreeze | frozen | gate-coverage")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
