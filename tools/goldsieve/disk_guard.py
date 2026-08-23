#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 215: сторож ресурса песочницы и проверка утечки временных каталогов.

Тик 214 не выполнил ни одного шага: оболочка вернула «No space left on device»
раньше, чем запустился гейт. Диск был занят на 100 %, из них 3,0 ГБ — 5140
каталогов `goldsieve-fixtures-*`, оставленных прошлыми прогонами. Причина в
`goldsieve/identity_corpus.py`: рабочий каталог фикстур создавался один раз на
процесс и не удалялся никогда, а гейт запускает десятки процессов за тик.

Урок шире конкретной утечки: у аудита есть предпосылка, которую сам аудит не
проверял — наличие свободного места. Пока она не проверяется, инструмент
умирает молча и снаружи это выглядит как «тик прерван по таймауту».

Проверки здесь машинные:
  --selftest  чувствительность к утечке измеряется НА ЖИВОМ подпроцессе: он
              грузит фикстуру и завершается, после чего каталогов остаться не
              должно. Мутационная цель — снятая уборка обязана быть замечена.
  (без флага) сторож: считает утёкшие каталоги и свободное место, при нехватке
              возвращает код 1 ДО того, как отработает остальной гейт.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "disk_guard.json"
TMP = Path(tempfile.gettempdir())
PREFIX = "goldsieve-fixtures-"
# Порог не «красивое число»: гейт с полным каскадом и снимками требует места на
# журналы, архив скила (около 2 МБ) и клон репозитория. Измеренный расход одного
# тика — порядка сотен мегабайт, поэтому запас взят с кратностью около трёх.
MIN_FREE_MB = 1024


def leaked_dirs() -> list[Path]:
    try:
        return sorted(p for p in TMP.iterdir()
                      if p.is_dir() and p.name.startswith(PREFIX))
    except OSError:
        return []


def dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def free_mb(path: Path = HERE) -> float:
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 2**20


_PROBE = (
    "import sys; sys.path.insert(0, %r)\n"
    "from goldsieve import identity_corpus as ic\n"
    "%s"
    "ic.load('probe', 'def _observed():\\n    return 1.0\\n"
    "def _reference():\\n    return 1.0\\n')\n"
)

# Мутант: уборка подменяется пустышкой ПОСЛЕ импорта, поэтому каталог,
# созданный при загрузке фикстуры, обязан остаться на диске.
_DISABLE = ("ic._cleanup_workdir = lambda: None\n"
            "import atexit\n")


def probe_leak(disable_cleanup: bool = False) -> int:
    """Запустить подпроцесс, тронувший фикстуры, и посчитать остатки после него.

    Возвращает число каталогов, появившихся и НЕ убранных. При
    `disable_cleanup=True` уборка отключается — это мутант, он обязан оставить
    каталог, иначе проверка ничего не измеряет.
    """
    before = {p.name for p in leaked_dirs()}
    code = _PROBE % (str(HERE), _DISABLE if disable_cleanup else "")
    subprocess.run([sys.executable, "-c", code], check=True,
                   capture_output=True, text=True, encoding="utf-8")
    after = {p.name for p in leaked_dirs()}
    return len(after - before)


def selftest() -> int:
    bad = 0

    def check(name: str, cond: bool) -> None:
        nonlocal bad
        bad += 0 if cond else 1
        print(f"  {'ok    ' if cond else 'ПРОВАЛ'} {name}")

    check("свободное место читается числом", free_mb() > 0)

    # ИСТОРИЧЕСКАЯ ФИКСТУРА: ровно та картина, что убила тик 214.
    stale = [Path(tempfile.mkdtemp(prefix=PREFIX)) for _ in range(3)]
    for d in stale:
        (d / "fx_probe.py").write_text("x = 1\n", encoding="utf-8")
    found = leaked_dirs()
    check("утёкшие каталоги обнаруживаются (%d >= 3)" % len(found),
          len(found) >= 3)
    check("объём утечки измеряется",
          sum(dir_size(d) for d in stale) > 0)
    for d in stale:
        shutil.rmtree(d, ignore_errors=True)
    check("после уборки исторической фикстуры остатков нет",
          all(not d.exists() for d in stale))

    # ЧУВСТВИТЕЛЬНОСТЬ: живой подпроцесс не должен оставлять каталог.
    leaked_now = probe_leak(disable_cleanup=False)
    check("рабочий процесс не оставляет каталог (утечка %d)" % leaked_now,
          leaked_now == 0)

    # МУТАЦИОННАЯ ЦЕЛЬ: со снятой уборкой каталог обязан остаться, иначе
    # проверка выше молчит и покрытием не является.
    before = {p.name for p in leaked_dirs()}
    leaked_mut = probe_leak(disable_cleanup=True)
    check("мутант со снятой уборкой ловится (утечка %d)" % leaked_mut,
          leaked_mut == 1)
    for p in leaked_dirs():
        if p.name not in before:
            shutil.rmtree(p, ignore_errors=True)

    print(f"самопроверка сторожа диска: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    dirs = leaked_dirs()
    size = sum(dir_size(d) for d in dirs)
    cleaned = 0
    if "--clean" in argv:
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)
            cleaned += 1
        dirs = leaked_dirs()
    fm = free_mb()
    report = {
        "free_mb": round(fm, 1),
        "min_free_mb": MIN_FREE_MB,
        "leaked_fixture_dirs": len(dirs),
        "leaked_bytes": size,
        "cleaned": cleaned,
        "root_cause_fixed_at_tick": 215,
        "root_cause": ("goldsieve/identity_corpus.py создавал рабочий каталог "
                       "фикстур на процесс и не удалял его; добавлен atexit-"
                       "уборщик, чувствительность измерена подпроцессом"),
        "why_this_check_exists": ("тик 214 не выполнил ни одного шага: "
                                  "«No space left on device» до гейта"),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if fm < MIN_FREE_MB:
        print("СТОРОЖ ДИСКА: свободно %.0f МБ < порога %d МБ — тик обязан "
              "остановиться и освободить место" % (fm, MIN_FREE_MB))
        return 1
    if len(dirs) > 32:
        print("СТОРОЖ ДИСКА: утёкших каталогов фикстур %d — уборка не "
              "работает" % len(dirs))
        return 1
    print("сторож диска: свободно %.0f МБ, утёкших каталогов %d, убрано %d"
          % (fm, len(dirs), cleaned))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
