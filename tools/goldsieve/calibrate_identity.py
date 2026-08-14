"""Калибровка ложных срабатываний детектора тождественности.

Разметка не назначается на глаз: каждый кейс реестра загружается, из него
берутся РЕАЛЬНЫЕ функции `observed` / `reference_alt` / `reference` объекта
Claim, и детектор применяется к ним. Ожидание фиксируется заранее: помечен
должен быть только кейс тика 37, где `_observed` возвращает `_reference()`.
Любое иное срабатывание — ложноположительное и требует разбора.
"""

import glob
import re
import importlib.util
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from goldsieve.identity import derives_from  # noqa: E402

# Разметка строится НЕЗАВИСИМЫМ путём — текстовым разбором самих кейсов, без
# участия детектора. Первая версия задавала её вручную одним файлом и оказалась
# неверна в обе стороны: пропустила два кейса с `observed=<то же имя, что
# reference>` и записала как «ложное срабатывание» настоящее вырождение.
# Ручная разметка проверяющего инструмента — сама источник ошибки.
ASSIGN = re.compile(r"^\s*(observed|reference_alt|reference)\s*=\s*([A-Za-z_][\w.]*)\s*,?\s*$")


def marked_by_text(path):
    """Пары «поле → функция» в одном Claim, совпадающие с reference.

    Ищется ровно то, что можно увидеть глазами: в одном блоке Claim(...) поле
    observed или reference_alt указывает на ТУ ЖЕ функцию, что reference, либо
    указанная функция имеет тело из единственного `return <reference>()`.
    """
    src = open(path, encoding="utf-8").read()
    hits = set()
    # 1) одно и то же имя в одном блоке Claim
    for block in re.findall(r"Claim\((.*?)\n\s*\)", src, flags=re.S):
        fields = {}
        for line in block.splitlines():
            m = ASSIGN.match(line)
            if m:
                fields[m.group(1)] = m.group(2)
        ref = fields.get("reference")
        if not ref:
            continue
        for field in ("observed", "reference_alt"):
            if fields.get(field) == ref:
                hits.add((field, ref))
    # 2) тело функции — единственный возврат вызова эталона (прямой или через
    #    посредника: цепочка раскрывается по тексту)
    # Тела функций собираются построчно, а не одним regex: жадный вариант
    # съедал пустые строки перед следующим `def` и молча терял функцию —
    # калибровка тогда показала «ложное срабатывание» на настоящем вырождении.
    bodies = {}
    cur = None
    for line in src.splitlines(keepends=True):
        m = re.match(r"def (\w+)\(\):", line)
        if m:
            cur = m.group(1)
            bodies[cur] = ""
            continue
        if cur is not None:
            if line.strip() and not line.startswith((" ", "\t")):
                cur = None
                continue
            bodies[cur] += line

    def resolves_to(fname, target, depth=0):
        if depth > 6:
            return False
        body = bodies.get(fname, "")
        lines = [l.strip() for l in body.splitlines()
                 if l.strip() and not l.strip().startswith(('"""', "#"))]
        lines = [l for l in lines if not l.startswith('"')]
        if len(lines) != 1 or not lines[0].startswith("return "):
            return False
        expr = lines[0][len("return "):]
        m = re.fullmatch(r"(\w+)\(\)", expr)
        if not m:
            return False
        return m.group(1) == target or resolves_to(m.group(1), target, depth + 1)

    for block in re.findall(r"Claim\((.*?)\n\s*\)", src, flags=re.S):
        fields = {}
        for line in block.splitlines():
            m = ASSIGN.match(line)
            if m:
                fields[m.group(1)] = m.group(2)
        ref = fields.get("reference")
        if not ref:
            continue
        for field in ("observed", "reference_alt"):
            fn = fields.get(field)
            if fn and fn != ref and resolves_to(fn, ref):
                hits.add((field, fn))
    return hits


def load_claims(path):
    spec = importlib.util.spec_from_file_location("case_" + os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    claims = getattr(mod, "CLAIMS", None)
    if claims is None:
        c = getattr(mod, "CLAIM", None)
        claims = [c] if c is not None else []
    return list(claims)


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(root, "cases", "*.py")))
    detected, expected, broken = {}, {}, []
    for f in files:
        base = os.path.basename(f)
        expected[base] = marked_by_text(f)
        try:
            claims = load_claims(f)
        except Exception:
            broken.append((base, traceback.format_exc().strip().splitlines()[-1]))
            continue
        hits = set()
        for c in claims:
            for field in ("observed", "reference_alt"):
                fn = getattr(c, field, None)
                same, chain = derives_from(fn, getattr(c, "reference", None))
                if same:
                    hits.add((field, getattr(fn, "__name__", "?"), chain))
        if hits:
            detected[base] = hits

    n = len(files)
    exp_pos = {b for b, h in expected.items() if h}
    det_pos = set(detected)
    false_pos = sorted(det_pos - exp_pos)
    missed = sorted(exp_pos - det_pos)
    true_neg = n - len(exp_pos)

    print("кейсов разобрано: %d (не загрузились: %d)" % (n, len(broken)))
    print("разметка по тексту (независимо от детектора): %d вырожденных"
          % len(exp_pos))
    for b in sorted(exp_pos):
        print("  %s | %s" % (b, sorted(expected[b])))
    print()
    print("детектор пометил: %d" % len(det_pos))
    for b in sorted(det_pos):
        mark = "совпало" if b in exp_pos else "ЛОЖНОЕ СРАБАТЫВАНИЕ"
        print("  [%s] %s" % (mark, b))
        for field, name, chain in sorted(detected[b]):
            print("      %s=%s | %s" % (field, name, chain))
    print()
    print("ложных срабатываний: %d" % len(false_pos))
    for b in false_pos:
        print("  " + b)
    print("пропущено вырождений: %d" % len(missed))
    for b in missed:
        print("  %s | %s" % (b, sorted(expected[b])))
    denom = true_neg + len(false_pos)
    print("специфичность (доля честных кейсов без срабатывания): %.4f  [%d/%d]"
          % (true_neg / denom if denom else 1.0, true_neg, denom))
    rec_d = len(exp_pos)
    print("чувствительность на размеченных: %.4f  [%d/%d]"
          % ((rec_d - len(missed)) / rec_d if rec_d else 1.0,
             rec_d - len(missed), rec_d))
    if broken:
        print("\nне загрузились (вне зоны детектора):")
        for b, err in broken:
            print("  %s | %s" % (b, err[:90]))
    return 1 if (false_pos or missed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
