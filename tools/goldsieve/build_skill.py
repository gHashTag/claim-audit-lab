#!/usr/bin/env python3
"""Сборка архива скила с явным списком исключений.

Зачем отдельный шаг. Предел сервиса — 100 записей архива, и он достигнут.
Значит каждый новый файл требует решения «что не кладём». Решение, принятое в
голове, однажды выбросит модуль инструмента вместо кейса-примера. Здесь оно
берётся из файла skill_exclude.txt, а сборка отказывается работать, если:

  1) в списке исключений есть путь, которого нет в источнике — список
     разошёлся с рабочей копией и молча перестал что-то исключать;
  2) в списке есть файл из пакета goldsieve/ либо один из контрактов —
     исключать инструмент запрещено правилом отбора;
  3) после исключений записей всё ещё больше предела — тогда надо принимать
     решение, а не собирать битый пакет.

Проверяется кодом, а не комментарием: см. selftest().
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archive_contract as ac

# Пути, которые НИКОГДА не исключаются: без них скил не проверяет ничего.
PROTECTED_PREFIXES = ("scripts/goldsieve/", "SKILL.md")
PROTECTED_FILES = (
    "scripts/claims.yaml", "scripts/ci_gate.sh", "scripts/baseline.py",
    "scripts/tri", "scripts/archive_contract.py",
    "scripts/coverage_manifest.yaml", "scripts/coverage_manifest.py",
    "scripts/snapshot_manifest.py",
)


def read_exclude(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def validate(src: str, excluded: list[str]) -> list[str]:
    """Список проблем. Пусто — список исключений законен."""
    problems = []
    for rel in excluded:
        full = os.path.join(src, rel)
        if not os.path.exists(full):
            problems.append("нет в источнике: %s" % rel)
        if rel.startswith(PROTECTED_PREFIXES) or rel in PROTECTED_FILES:
            problems.append("запрещено исключать инструмент: %s" % rel)
    return problems


def staged_copy(src: str, excluded: set[str], dst: str) -> int:
    """Копия источника без исключённых файлов и без __pycache__."""
    count = 0
    for root, dirs, names in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(names):
            if name.endswith(".pyc"):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, src).replace(os.sep, "/")
            if rel in excluded:
                continue
            target = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(full, target)
            count += 1
    return count


def build(src: str, out_zip: str, exclude_file: str) -> tuple[str, int]:
    src = os.path.abspath(src)
    excluded = read_exclude(exclude_file)
    problems = validate(src, excluded)
    if problems:
        for p in problems:
            print("  ОТКАЗ: " + p)
        raise SystemExit(2)
    with tempfile.TemporaryDirectory() as tmp:
        stage = os.path.join(tmp, os.path.basename(src))
        os.makedirs(stage)
        n = staged_copy(src, set(excluded), stage)
        if n > ac.MAX_ENTRIES:
            print("  ОТКАЗ: записей %d при пределе %d — нужно исключить ещё %d"
                  % (n, ac.MAX_ENTRIES, n - ac.MAX_ENTRIES))
            raise SystemExit(2)
        digest = ac.build(stage, out_zip)
    rc, probs = ac.check(out_zip)
    for p in probs:
        print("  " + p)
    if rc:
        raise SystemExit(rc)
    return digest, n


def selftest() -> int:
    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok   " + name)
        else:
            fail += 1
            print("  ПРОВАЛ " + name)

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "skill")
        os.makedirs(os.path.join(src, "scripts", "goldsieve"))
        os.makedirs(os.path.join(src, "scripts", "cases"))
        for rel in ("SKILL.md", "scripts/goldsieve/sieve.py",
                    "scripts/cases/a.py", "scripts/cases/b.py"):
            with open(os.path.join(src, rel), "w") as fh:
                fh.write("x\n")

        exc = os.path.join(tmp, "exc.txt")
        with open(exc, "w") as fh:
            fh.write("# комментарий\n\nscripts/cases/b.py\n")
        check("комментарии и пустые строки не попадают в список",
              read_exclude(exc) == ["scripts/cases/b.py"])
        check("законный список исключений принят",
              validate(src, ["scripts/cases/b.py"]) == [])
        check("отсутствующий путь отвергнут",
              any("нет в источнике" in p
                  for p in validate(src, ["scripts/cases/zzz.py"])))
        check("исключение модуля инструмента отвергнуто",
              any("запрещено исключать" in p
                  for p in validate(src, ["scripts/goldsieve/sieve.py"])))
        check("исключение реестра отвергнуто",
              any("запрещено исключать" in p
                  for p in validate(src, ["scripts/claims.yaml"])))

        z1 = os.path.join(tmp, "a.zip")
        d1, n1 = build(src, z1, exc)
        check("исключённый файл отсутствует в архиве", n1 == 3)
        import zipfile
        with zipfile.ZipFile(z1) as zf:
            names = zf.namelist()
        check("исключённого имени нет среди записей",
              not any(x.endswith("cases/b.py") for x in names))
        check("оставленное имя есть среди записей",
              any(x.endswith("cases/a.py") for x in names))
        z2 = os.path.join(tmp, "b.zip")
        d2, _ = build(src, z2, exc)
        check("сборка детерминирована", d1 == d2)

        # Подставка: __pycache__ не должен попадать в архив, иначе предел
        # записей съедается мусором, а SHA-256 перестаёт совпадать.
        pc = os.path.join(src, "scripts", "goldsieve", "__pycache__")
        os.makedirs(pc)
        with open(os.path.join(pc, "sieve.cpython-314.pyc"), "wb") as fh:
            fh.write(b"\x00")
        z3 = os.path.join(tmp, "c.zip")
        d3, n3 = build(src, z3, exc)
        check("__pycache__ не попадает в архив", n3 == 3 and d3 == d1)

    print("  итог: %d провалов" % fail)
    return fail


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "selftest":
        raise SystemExit(1 if selftest() else 0)
    here = os.path.dirname(os.path.abspath(__file__))
    src = argv[0] if argv else "/home/user/workspace/skills/user/goldsieve"
    out = argv[1] if len(argv) > 1 else \
        "/home/user/workspace/skills-build/goldsieve.zip"
    exc = os.path.join(here, "skill_exclude.txt")
    digest, n = build(src, out, exc)
    print("архив собран: %s" % out)
    print("  записей: %d (предел %d)" % (n, ac.MAX_ENTRIES))
    print("  SHA-256: %s" % digest[:16])
