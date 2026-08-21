#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 171: линтер переносимости — класс дефектов, невидимый на Linux.

Размещённые исполнители Windows (py3.12, py3.13) отвергли самопроверку три раза
подряд по ОДНОЙ и той же причине разного вида: текст на русском проходил через
поток или файл, открытый в локальной кодировке (cp1252), и падал с
UnicodeEncodeError/UnicodeDecodeError. На Linux локальная кодировка utf-8,
поэтому дефект не наблюдаем в принципе — его нашла только вторая платформа.

Линтер закрывает КЛАСС, а не отдельные места: любая новая текстовая файловая
операция без явного encoding и любой вызов подпроцесса с text=True без
encoding — нарушение. Плюс запрет литерала "python3" в аргументах команд:
на Windows такого исполняемого файла нет, нужен sys.executable.

Режим --fix правит найденное машинно, --selftest измеряет чувствительность.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

try:
    import goldsieve as _gs  # noqa: F401   (utf-8 для потоков)
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
TEXT_CALLS = {"open", "write_text", "read_text"}


def _targets(root: Path) -> list[Path]:
    files = sorted(root.glob("*.py"))
    pkg = root / "goldsieve"
    if pkg.is_dir():
        files += sorted(p for p in pkg.rglob("*.py")
                        if "__pycache__" not in p.parts)
    return [p for p in files if p.name != Path(__file__).name]


def scan_source(src: str, name: str = "<строка>") -> list[dict]:
    """Находки в одном исходнике. Чистая функция: годится для фикстур."""
    out: list[dict] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [{"file": name, "line": exc.lineno or 0, "kind": "syntax_error",
                 "detail": str(exc)}]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        fname = getattr(fn, "id", None) or getattr(fn, "attr", None)
        # os.open — низкоуровневый дескриптор, аргумента encoding не принимает.
        # Тик 171: первая версия линтера пометила его и сломала журнал, поэтому
        # исключение зафиксировано фикстурой ниже.
        if fname == "open" and isinstance(fn, ast.Attribute) \
                and getattr(fn.value, "id", None) == "os":
            continue
        kw = {k.arg for k in node.keywords}
        if fname in TEXT_CALLS and "encoding" not in kw:
            # бинарный режим кодировки не требует
            binary = (fname == "open" and len(node.args) > 1
                      and isinstance(node.args[1], ast.Constant)
                      and "b" in str(node.args[1].value))
            if not binary:
                out.append({"file": name, "line": node.lineno,
                            "kind": "text_io_without_encoding",
                            "detail": f"{fname}() без encoding="})
        if "text" in kw and "encoding" not in kw:
            for k in node.keywords:
                if k.arg == "text" and isinstance(k.value, ast.Constant) \
                        and k.value.value is True:
                    out.append({"file": name, "line": node.lineno,
                                "kind": "subprocess_text_without_encoding",
                                "detail": "text=True без encoding="})
        for arg in ast.walk(node):
            if isinstance(arg, ast.Constant) and arg.value == "python3":
                out.append({"file": name, "line": node.lineno,
                            "kind": "hardcoded_python3",
                            "detail": 'литерал "python3": нужен sys.executable'})
                break
    return out


def scan_tree(root: Path) -> list[dict]:
    found: list[dict] = []
    for p in _targets(root):
        found += scan_source(p.read_text(encoding="utf-8"),
                             str(p.relative_to(root)))
    return found


def fix_source(src: str) -> tuple[str, int]:
    """Вставить encoding="utf-8" в текстовые вызовы. Правка по позициям AST."""
    tree = ast.parse(src)
    edits: list[tuple[int, int]] = []          # (строка, столбец конца вызова)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        fname = getattr(fn, "id", None) or getattr(fn, "attr", None)
        kw = {k.arg for k in node.keywords}
        if fname == "open" and isinstance(fn, ast.Attribute) \
                and getattr(fn.value, "id", None) == "os":
            continue
        need = False
        if fname in TEXT_CALLS and "encoding" not in kw:
            binary = (fname == "open" and len(node.args) > 1
                      and isinstance(node.args[1], ast.Constant)
                      and "b" in str(node.args[1].value))
            need = not binary
        if not need and "text" in kw and "encoding" not in kw:
            need = any(k.arg == "text" and isinstance(k.value, ast.Constant)
                       and k.value.value is True for k in node.keywords)
        if need and node.end_lineno is not None:
            edits.append((node.end_lineno, node.end_col_offset))
    lines = src.split("\n")
    # правки применяются от конца к началу: смещения не сдвигаются
    for ln, col in sorted(set(edits), reverse=True):
        line = lines[ln - 1]
        close = line.rfind(")", 0, col)
        if close < 0:
            continue
        head = line[:close].rstrip()
        sep = "" if head.endswith("(") else ", "
        lines[ln - 1] = head + sep + 'encoding="utf-8"' + line[close:]
    return "\n".join(lines), len(set(edits))


def selftest() -> int:
    bad = 0
    dirty = ('open("a.txt", "w").write("x")\n'
             'import subprocess\n'
             'subprocess.run(["python3", "-c", "1"], text=True)\n')
    found = scan_source(dirty, "фикстура")
    kinds = {f["kind"] for f in found}
    ok = kinds == {"text_io_without_encoding",
                   "subprocess_text_without_encoding", "hardcoded_python3"}
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} грязная фикстура: три класса найдены "
          f"({sorted(kinds)})")

    clean = ('open("a.txt", "w", encoding="utf-8").write("x")\n'
             'import subprocess, sys\n'
             'subprocess.run([sys.executable, "-c", "1"], text=True,\n'
             '               encoding="utf-8")\n')
    found_clean = scan_source(clean, "фикстура")
    ok = found_clean == []
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} чистая фикстура молчит: "
          f"находок {len(found_clean)}")

    # бинарный режим не обязан объявлять кодировку — иначе линтер шумит
    ok = scan_source('open("a.bin", "rb").read()\n', "ф") == []
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} бинарный режим не считается нарушением")

    # os.open не принимает encoding: первая версия линтера пометила его и
    # сломала блокировку журнала. Фикстура закрепляет исключение.
    ok = scan_source('import os\nos.open(p, os.O_CREAT | os.O_WRONLY)\n', "ф") == []
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} os.open исключён из требования кодировки")
    fixed_os, n_os = fix_source('import os\nos.open(p, os.O_WRONLY)\n')
    ok = n_os == 0
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} --fix не трогает os.open: правок {n_os}")

    # мутационная цель: правка обязана делать грязную фикстуру чистой
    fixed, n = fix_source('open("a.txt", "w").write("x")\n')
    ok = n == 1 and scan_source(fixed, "ф") == []
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} --fix закрывает находку: правок {n}")

    # неподвижная точка: повторная правка ничего не меняет
    again, n2 = fix_source(fixed)
    ok = n2 == 0 and again == fixed
    bad += 0 if ok else 1
    print(f"  {'ok ' if ok else 'ПРОВАЛ'} неподвижная точка правки: правок {n2}")

    print(f"самопроверка линтера переносимости: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--fix" in argv:
        total = 0
        for p in _targets(ROOT):
            src = p.read_text(encoding="utf-8")
            out, n = fix_source(src)
            if n:
                ast.parse(out)          # правка не имеет права ломать разбор
                p.write_text(out, encoding="utf-8")
                total += n
                print(f"  {p.relative_to(ROOT)}: правок {n}")
        print(f"правок всего: {total}")
        return 0
    found = scan_tree(ROOT)
    # литерал "python3" остаётся допустимым в bench.py: там он ИМЯ исторической
    # раскладки команд в отчёте измерителя, а не исполняемый файл.
    found = [f for f in found
             if not (f["kind"] == "hardcoded_python3"
                     and f["file"] == "bench.py")]
    if found:
        print(f"НАРУШЕНИЯ ПЕРЕНОСИМОСТИ: {len(found)}")
        for f in found[:40]:
            print(f"  [{f['kind']}] {f['file']}:{f['line']}: {f['detail']}")
        return 1
    print("переносимость: явная кодировка везде, литерала python3 нет")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
