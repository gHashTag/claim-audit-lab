#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож происхождения артефактов, на которые ссылается доклад.

Наличие в докладе пути ещё не означает, что подтверждение можно прочитать.
Сторож извлекает абсолютные пути рабочего пространства из последнего
доклада, проверяет их принадлежность разрешённым корням и существование.
Он не восстанавливает отсутствующие файлы и не превращает форму доклада в
научное доказательство.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
TRACKING = Path("/home/user/workspace/cron_tracking/8dff7aa3")
WORKSPACE = Path("/home/user/workspace")
ALLOWED_ROOTS = (
    WORKSPACE / "goldsieve",
    WORKSPACE / "cron_tracking" / "8dff7aa3",
    WORKSPACE / "cron_tracking" / "20fee222",
    WORKSPACE / "corpus" / "trinity",
)
OUT = HERE / "report_artifact_provenance_guard.json"
PATH_RE = re.compile(r"/home/user/workspace/[A-Za-z0-9_./-]+")
TRAILING = ".,;:)]}`"


def latest_report(root: Path = TRACKING) -> Path:
    reports = sorted(root.glob("tick*-report.md"))
    if not reports:
        raise FileNotFoundError("доклад tickNNN-report.md не предъявлен")
    return reports[-1]


def extracted_paths(text: str) -> list[str]:
    values = {match.group(0).rstrip(TRAILING) for match in PATH_RE.finditer(text)}
    return sorted(values)


def inside_allowed(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    return any(resolved == root or root in resolved.parents
               for root in ALLOWED_ROOTS)


def inspect(report: Path) -> dict:
    text = report.read_text(encoding="utf-8")
    paths = extracted_paths(text)
    missing = [path for path in paths if not Path(path).exists()]
    outside = [path for path in paths if not inside_allowed(Path(path))]
    status = (
        "verified-in-scope"
        if paths and not missing and not outside
        else "not-evaluated"
    )
    result = {
        "статус": status,
        "доклад": str(report),
        "найдено_путей": len(paths),
        "проверенные_пути": paths,
        "отсутствующие_пути": missing,
        "пути_вне_разрешённых_корней": outside,
        "разрешённые_корни": [str(root) for root in ALLOWED_ROOTS],
        "причина": (
            "каждый предъявленный путь существует и находится в разрешённом "
            "корне"
            if status == "verified-in-scope"
            else "путь отсутствует, находится вне разрешённого корня или пути "
                 "в докладе не предъявлены"
        ),
        "ограничение": (
            "проверка существования и границы пути не доказывает содержание "
            "артефакта или научную истинность доклада"
        ),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return result


def selftest() -> int:
    good = bad = 0

    def check(title: str, condition: bool) -> None:
        nonlocal good, bad
        if condition:
            print("  ок  " + title)
            good += 1
        else:
            print("  ПРОВАЛ  " + title)
            bad += 1

    with tempfile.TemporaryDirectory(prefix="goldsieve-report-path-") as td:
        root = Path(td)
        existing = root / "артефакт.txt"
        existing.write_text("наблюдение\n", encoding="utf-8")
        report = root / "доклад.md"
        report.write_text(
            "# Доклад\n"
            f"артефакт: {existing}\n",
            encoding="utf-8",
        )
        values = extracted_paths(
            "артефакт: /home/user/workspace/goldsieve/fixture.txt"
        )
        check("извлекается абсолютный путь рабочего пространства",
              values == ["/home/user/workspace/goldsieve/fixture.txt"])
        check("внешний временный путь не становится разрешённым артефактом",
              not inside_allowed(existing))
        check("разрешённый путь проходит проверку границы",
              inside_allowed(HERE / "report_artifact_provenance_guard.py"))
        check("отсутствующий путь обнаруживается явно",
              not (root / "нет-такого-файла").exists()
              and not Path(values[0]).exists())

    print("самопроверка происхождения артефактов доклада: пройдено %d, "
          "провалено %d" % (good, bad))
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--selftest"]:
        return selftest()
    if args:
        print("использование: report_artifact_provenance_guard.py [--selftest]")
        return 2
    try:
        result = inspect(latest_report())
    except (OSError, UnicodeError, ValueError) as exc:
        print("сторож происхождения артефактов: not-evaluated; %s" % exc)
        return 1
    print("сторож происхождения артефактов: %s; путей: %d; отсутствует: %d; "
          "вне корней: %d" % (
              result["статус"],
              result["найдено_путей"],
              len(result["отсутствующие_пути"]),
              len(result["пути_вне_разрешённых_корней"]),
          ))
    return 0 if result["статус"] == "verified-in-scope" else 1


if __name__ == "__main__":
    raise SystemExit(main())
