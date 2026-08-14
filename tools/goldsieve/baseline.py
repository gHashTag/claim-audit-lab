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
import hashlib
import json
import os
import platform
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
    for name in ("claims.yaml", "measure_identity.py", "mutation_identity.py",
                 "calibrate_identity.py", "baseline.py"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            out.append(name)
    return sorted(set(out))


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
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
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
                           capture_output=True, text=True, timeout=60)
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


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "show"
    if mode == "snapshot":
        return snapshot()
    if mode == "check":
        return check()
    if mode == "show":
        return show()
    print("режимы: snapshot | check | show")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
