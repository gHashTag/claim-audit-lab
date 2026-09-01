#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 261: сторож синхронности рабочей копии с разрешённой ветвью.

Что измерено, а не предположено. Последний коммит ветви
`tools/goldsieve-v3-2026-08-13` — тик 215 (2026-08-23 10:52 UTC). Тики 216–260
работали девять суток и не сделали ни одного коммита. Файл
`os_matrix_audit.py` (28 577 байт), который правили почти в каждом тике этого
отрезка, НИКОГДА не существовал в репозитории: `git log -- <файл>` даёт нуль
коммитов. Ещё шесть файлов инструмента разошлись с ветвью.

Смысл проверки: у аудита была непроверяемая предпосылка «сделанное сохранено».
Песочница эфемерна, поэтому тик, который отчитался об исправлении и не отправил
его в ветвь, оставил работу в единственном экземпляре. Доклад при этом честен
построчно и всё равно вводит в заблуждение: он говорит «исправлено», а вне
песочницы исправления нет.

Решение по СОСТАВУ фактов, а не по величине: любое расхождение файла
инструмента с HEAD разрешённой ветви — код 1. Отсутствие клона — код 2 с
причиной `clone_absent`, а не молчаливый PASS: отсутствие возможности проверить
не является проверкой.

  --selftest  чувствительность на временных парах каталогов: пропущенный файл,
              изменённый файл, совпадающий набор, а также мутационная цель —
              сторож со снятым сравнением содержимого обязан быть замечен.
  (без флага) сторож: сравнить /home/user/workspace/goldsieve с ветвью в клоне.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "repo_sync_guard.json"
CLONE = Path("/tmp/cal")
SUBDIR = "tools/goldsieve"
BRANCH = "tools/goldsieve-v3-2026-08-13"
# Расширения, которые составляют инструмент. Данные корпуса и журналы тиков
# сюда не входят: они живут вне репозитория по отдельному решению.
SUFFIXES = (".py", ".sh", ".yaml")
# Файлы, которые заведомо не отправляются: сборочный мусор и локальные отчёты
# сторожей (их содержимое меняется каждым прогоном и не является исходником).
EXCLUDE = {
    "disk_guard.json", "repo_sync_guard.json", "external_target_guard.json",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_files(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in SUFFIXES:
            continue
        rel = p.relative_to(root).as_posix()
        if p.name in EXCLUDE:
            continue
        out[rel] = p.read_bytes()
    return out


def branch_files(clone: Path, branch: str, subdir: str) -> dict[str, bytes]:
    """Содержимое файлов инструмента в HEAD ветви, читается из объектов git."""
    cmd = ["git", "-C", str(clone), "ls-tree", "-r", "--name-only", branch,
           "--", subdir + "/"]
    res = subprocess.run(cmd, capture_output=True, text=True,
                         encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError("git ls-tree: " + res.stderr.strip())
    out: dict[str, bytes] = {}
    for line in res.stdout.splitlines():
        prefix = subdir.rstrip("/") + "/"
        name = line[len(prefix):] if line.startswith(prefix) else line
        if not name or Path(name).suffix not in SUFFIXES or Path(name).name in EXCLUDE:
            continue
        blob = subprocess.run(
            ["git", "-C", str(clone), "cat-file", "blob", branch + ":" + line],
            capture_output=True)
        if blob.returncode != 0:
            raise RuntimeError("git cat-file: " + line)
        out[name] = blob.stdout
    return out


def compare(local: dict[str, bytes], remote: dict[str, bytes],
            compare_content: bool = True) -> dict:
    """Сравнение наборов. `compare_content=False` — мутационная цель."""
    missing = sorted(n for n in local if n not in remote)
    extra = sorted(n for n in remote if n not in local)
    differs = []
    if compare_content:
        for n in sorted(set(local) & set(remote)):
            if local[n] != remote[n]:
                differs.append(n)
    return {
        "отсутствует_в_ветви": missing,
        "нет_в_песочнице": extra,
        "различается": differs,
        "расхождений": len(missing) + len(differs),
    }


def _selftest() -> int:
    passed = failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal passed, failed
        if ok:
            passed += 1
        else:
            failed += 1
            print("ПРОВАЛ: " + name)

    a = {"x.py": b"1", "y.py": b"2"}
    check("совпадающий набор даёт 0", compare(a, dict(a))["расхождений"] == 0)

    b = dict(a)
    del b["y.py"]
    r = compare(a, b)
    check("пропущенный в ветви файл пойман", r["расхождений"] == 1
          and r["отсутствует_в_ветви"] == ["y.py"])

    c = dict(a)
    c["y.py"] = "2 изменено".encode("utf-8")
    r = compare(a, c)
    check("изменённый файл пойман",
          r["расхождений"] == 1 and r["различается"] == ["y.py"])

    # Мутационная цель: сторож, не сравнивающий содержимое, обязан пропустить
    # именно тот случай, который рабочий сторож ловит. Если мутант тоже даёт
    # расхождение, проверка содержимого ничего не решает и молчит.
    mut = compare(a, c, compare_content=False)
    check("мутант со снятым сравнением содержимого пропускает случай",
          mut["расхождений"] == 0)

    # Живой контроль на настоящем git: два коммита, второй файл изменён локально.
    with tempfile.TemporaryDirectory(prefix="goldsieve-reposync-") as td:
        repo = Path(td) / "repo"
        (repo / SUBDIR).mkdir(parents=True)
        env_git = ["git", "-C", str(repo)]
        subprocess.run(env_git + ["init", "-q", "-b", BRANCH], check=True)
        subprocess.run(env_git + ["config", "user.email", "t@t"], check=True)
        subprocess.run(env_git + ["config", "user.name", "t"], check=True)
        (repo / SUBDIR / "a.py").write_bytes(b"print(1)\n")
        subprocess.run(env_git + ["add", "-A"], check=True)
        subprocess.run(env_git + ["commit", "-qm", "1"], check=True)

        sand = Path(td) / "sand"
        sand.mkdir()
        (sand / "a.py").write_bytes(b"print(1)\n")
        rf = branch_files(repo, BRANCH, SUBDIR)
        check("чтение ветви даёт файл", rf == {"a.py": b"print(1)\n"})
        check("живой контроль: копии равны",
              compare(local_files(sand), rf)["расхождений"] == 0)

        (sand / "a.py").write_bytes(b"print(2)\n")
        (sand / "новый.py").write_bytes(b"x\n")
        r = compare(local_files(sand), rf)
        check("живой контроль: правка и неотправленный файл пойманы",
              r["расхождений"] == 2 and r["различается"] == ["a.py"]
              and r["отсутствует_в_ветви"] == ["новый.py"])

    print("самопроверка сторожа синхронности: %d пройдено, %d провалено"
          % (passed, failed))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()

    if not (CLONE / ".git").is_dir():
        report = {"статус": "НЕ ПРОВЕРЕНО", "причина": "clone_absent",
                  "клон": str(CLONE)}
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("СТОРОЖ СИНХРОННОСТИ: клона %s нет — проверить невозможно, "
              "это НЕ PASS" % CLONE)
        return 2

    local = local_files(HERE)
    try:
        remote = branch_files(CLONE, BRANCH, SUBDIR)
    except RuntimeError as exc:
        report = {"статус": "НЕ ПРОВЕРЕНО", "причина": "branch_unreadable",
                  "сообщение": str(exc)}
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("СТОРОЖ СИНХРОННОСТИ: ветвь %s не читается: %s" % (BRANCH, exc))
        return 2

    res = compare(local, remote)
    head = subprocess.run(
        ["git", "-C", str(CLONE), "rev-parse", "--short", BRANCH],
        capture_output=True, text=True,
                         encoding="utf-8").stdout.strip()
    report = {
        "ветвь": BRANCH,
        "коммит_ветви": head,
        "файлов_в_песочнице": len(local),
        "файлов_в_ветви": len(remote),
        "почему_проверка_существует": (
            "тики 216-260 девять суток отчитывались об исправлениях, не "
            "отправив ни одного коммита; os_matrix_audit.py не существовал в "
            "репозитории вовсе"),
        **res,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if res["расхождений"]:
        print("СТОРОЖ СИНХРОННОСТИ: расхождений %d — не отправлено в ветвь: "
              "%s; различается: %s"
              % (res["расхождений"], ", ".join(res["отсутствует_в_ветви"]),
                 ", ".join(res["различается"])))
        return 1
    print("сторож синхронности: %d файлов совпадают с %s (%s)"
          % (len(local), BRANCH, head))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
