#!/usr/bin/env python3
"""Контракт архива скила: предел записей, порядок, дубликаты, детерминизм.

Зачем. Тик 42 упёрся в отказ сервиса «too many files»: предел в 100 считается
по ЗАПИСЯМ архива, а записи каталогов тоже считаются. Правило было записано
словами в комментарии — то есть держалось на внимательности. Здесь оно
проверяется кодом, вместе с тремя другими свойствами:

  1) записей не больше 100 и записей каталогов нет вовсе;
  2) имена не повторяются (повтор в zip законен, а поведение распаковки —
     последний побеждает — превращает пакет в лотерею);
  3) записи идут в лексикографическом порядке (иначе diff двух сборок
     нечитаем, а сравнение по SHA-256 бессмысленно);
  4) две сборки из ОДНОГО состояния дают одинаковый SHA-256 самого файла
     архива.

Свойство 4 требует отдельной работы: обычный zip кладёт в каждую запись
время изменения файла, а оно у скопированных файлов разное от сборки к
сборке. Поэтому архив собирается детерминированно самим Python: фиксированное
время записи, фиксированные права, сортированный обход.

    python3 archive_contract.py build <каталог> <архив>
    python3 archive_contract.py check <архив>
    python3 archive_contract.py selftest
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import zipfile

MAX_ENTRIES = 100
# Фиксированная отметка времени в архиве. 1980-01-01 — минимально допустимая
# для формата zip; любое другое постоянное значение тоже подошло бы, важно
# лишь чтобы оно не зависело от файловой системы.
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build(src_dir: str, out_zip: str, top: str | None = None) -> str:
    """Детерминированная сборка. Возвращает SHA-256 полученного архива."""
    src_dir = os.path.abspath(src_dir)
    top = top if top is not None else os.path.basename(src_dir)
    files: list[tuple[str, str]] = []
    for root, dirs, names in os.walk(src_dir):
        dirs.sort()
        for name in sorted(names):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, src_dir)
            arc = os.path.join(top, rel) if top else rel
            files.append((arc.replace(os.sep, "/"), full))
    files.sort(key=lambda t: t[0])
    if os.path.exists(out_zip):
        os.remove(out_zip)
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zf:
        for arc, full in files:
            info = zipfile.ZipInfo(arc, date_time=FIXED_TIME)
            # Права фиксируются: у скопированных файлов бит исполнения
            # различается между машинами и ломает сравнение по SHA-256.
            info.external_attr = (0o100644 << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(full, "rb") as fh:
                zf.writestr(info, fh.read())
    return sha256(out_zip)


def check(path: str, max_entries: int = MAX_ENTRIES) -> tuple[int, list[str]]:
    problems: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        dirs = [n for n in names if n.endswith("/")]
        if dirs:
            problems.append("в архиве есть записи каталогов: %d (предел в 100 "
                            "считается по записям, а не по файлам)" % len(dirs))
        if len(names) > max_entries:
            problems.append("записей %d при пределе %d"
                            % (len(names), max_entries))
        seen: set[str] = set()
        for n in names:
            if n in seen:
                problems.append("повтор имени в архиве: %s" % n)
            seen.add(n)
        if names != sorted(names):
            problems.append("записи идут не в лексикографическом порядке")
        times = {i.date_time for i in zf.infolist()}
        if len(times) > 1:
            problems.append("отметки времени различаются: сборка не "
                            "детерминирована (%d разных)" % len(times))
    return (1 if problems else 0), problems


def deterministic(src_dir: str) -> tuple[bool, str, str]:
    """Две сборки подряд из одного состояния. Возвращает (равны, sha1, sha2)."""
    with tempfile.TemporaryDirectory() as tmp:
        a = os.path.join(tmp, "a.zip")
        b = os.path.join(tmp, "b.zip")
        h1 = build(src_dir, a)
        h2 = build(src_dir, b)
        return h1 == h2, h1, h2


def selftest() -> tuple[int, int]:
    ok = fail = 0

    def chk(name: str, cond: bool, note: str = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ок      %s" % name)
        else:
            fail += 1
            print("  ПРОВАЛ  %s %s" % (name, note))

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "pkg")
        os.makedirs(os.path.join(src, "scripts", "cases"))
        for i in range(5):
            open(os.path.join(src, "scripts", "cases", "c%d.py" % i),
                 "w").write("# %d\n" % i)
        open(os.path.join(src, "SKILL.md"), "w").write("---\nname: x\n---\n")
        z = os.path.join(tmp, "pkg.zip")
        build(src, z)
        rc, probs = check(z)
        chk("чистый архив проходит контракт", rc == 0, str(probs))
        same, h1, h2 = deterministic(src)
        chk("две сборки дают одинаковый SHA-256", same, "%s != %s" % (h1, h2))
        # Файл трогается заново: время изменения другое, а SHA-256 архива
        # обязан остаться прежним — иначе детерминизм мнимый.
        os.utime(os.path.join(src, "SKILL.md"), (0, 0))
        h3 = build(src, os.path.join(tmp, "c.zip"))
        chk("изменение времени файла не меняет архив", h3 == h1)
        # А изменение СОДЕРЖИМОГО обязано менять.
        open(os.path.join(src, "SKILL.md"), "a").write("\n# правка\n")
        h4 = build(src, os.path.join(tmp, "d.zip"))
        chk("изменение содержимого меняет архив", h4 != h1)
        # ПОДСТАВКИ: архив, собранный обычным zip с каталогами и предельным
        # числом записей, обязан проваливать контракт.
        bad = os.path.join(tmp, "bad.zip")
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("pkg/", "")
            zf.writestr("pkg/a.txt", "a")
        rc, probs = check(bad)
        chk("записи каталогов ловятся",
            rc == 1 and any("каталог" in p for p in probs))
        many = os.path.join(tmp, "many.zip")
        with zipfile.ZipFile(many, "w") as zf:
            for i in range(101):
                info = zipfile.ZipInfo("pkg/f%03d" % i, date_time=FIXED_TIME)
                zf.writestr(info, "x")
        rc, probs = check(many)
        chk("превышение предела записей ловится",
            rc == 1 and any("предел" in p for p in probs))
        dup = os.path.join(tmp, "dup.zip")
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with zipfile.ZipFile(dup, "w") as zf:
                for _ in range(2):
                    info = zipfile.ZipInfo("pkg/a.txt", date_time=FIXED_TIME)
                    zf.writestr(info, "a")
        rc, probs = check(dup)
        chk("повтор имени ловится",
            rc == 1 and any("повтор" in p for p in probs))
        unsorted = os.path.join(tmp, "uns.zip")
        with zipfile.ZipFile(unsorted, "w") as zf:
            for n in ("pkg/b", "pkg/a"):
                zf.writestr(zipfile.ZipInfo(n, date_time=FIXED_TIME), "x")
        rc, probs = check(unsorted)
        chk("нарушенный порядок записей ловится",
            rc == 1 and any("порядке" in p for p in probs))
        drift = os.path.join(tmp, "drift.zip")
        with zipfile.ZipFile(drift, "w") as zf:
            zf.writestr(zipfile.ZipInfo("pkg/a", date_time=FIXED_TIME), "x")
            zf.writestr(zipfile.ZipInfo("pkg/b", date_time=(2026, 8, 15, 1, 2, 3)), "x")
        rc, probs = check(drift)
        chk("разъехавшиеся отметки времени ловятся",
            rc == 1 and any("детерминир" in p for p in probs))
    print("archive_contract: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "build" and len(argv) >= 3:
        h = build(argv[1], argv[2])
        print("архив собран детерминированно: %s" % argv[2])
        print("  SHA-256: %s" % h)
        rc, probs = check(argv[2])
        for p in probs:
            print("  " + p)
        return rc
    if argv[0] == "check" and len(argv) >= 2:
        rc, probs = check(argv[1])
        if rc == 0:
            with zipfile.ZipFile(argv[1]) as zf:
                print("контракт архива соблюдён: %d записей, каталогов нет, "
                      "порядок и время фиксированы" % len(zf.namelist()))
        else:
            print("НАРУШЕНИЯ КОНТРАКТА: %d" % len(probs))
            for p in probs:
                print("  " + p)
        return rc
    if argv[0] == "selftest":
        return 1 if selftest()[1] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
