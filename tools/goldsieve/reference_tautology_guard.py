#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож содержательной независимости observed/reference.

Разные имена файлов ещё не доказывают независимое сравнение: копия
наблюдаемого файла может быть названа reference. Сторож сравнивает
канонические байты, inode и SHA-256 двух явно предъявленных файлов. Совпадение
любого из этих признаков понижает результат до ``not-evaluated``. Он не
утверждает независимость алгоритмов и не подменяет проверку происхождения.

Команды:
    python3 reference_tautology_guard.py --selftest
    python3 reference_tautology_guard.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

CORPUS = Path("/home/user/workspace/corpus/trinity")
OBSERVED = CORPUS / "data/zeta/zeros_odlyzko_100k.txt"
REFERENCE = CORPUS / "data/zeta/zeta_gue_analysis_results.md"
OUT = Path(__file__).resolve().parent / "reference_tautology_guard.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_pair(observed: Path, reference: Path) -> dict:
    """Проверить явно предъявленную пару, не выводя научный вердикт."""
    observed = observed.resolve(strict=True)
    reference = reference.resolve(strict=True)
    observed_digest = _digest(observed)
    reference_digest = _digest(reference)
    same_inode = os.stat(observed).st_ino == os.stat(reference).st_ino
    same_bytes = observed_digest == reference_digest
    same_path = observed == reference
    if same_path or same_inode or same_bytes:
        status = "not-evaluated"
        reason = (
            "observed и reference совпадают по пути, inode или содержимому; "
            "сравнение тавтологично и не считается покрытием"
        )
    else:
        status = "verified-in-scope"
        reason = (
            "предъявлены разные существующие файлы с разными inode и SHA-256; "
            "алгоритмическая независимость отдельно не доказана"
        )
    return {
        "статус": status,
        "наблюдаемое": str(observed),
        "эталон": str(reference),
        "sha256_наблюдаемого": observed_digest,
        "sha256_эталона": reference_digest,
        "inode_совпадает": same_inode,
        "содержимое_совпадает": same_bytes,
        "путь_совпадает": same_path,
        "причина": reason,
        "ограничение": (
            "разные файлы не доказывают независимость формул, библиотек или "
            "вычислительных путей"
        ),
    }


def scan() -> dict:
    return inspect_pair(OBSERVED, REFERENCE)


def selftest() -> int:
    good = failed = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, failed
        if condition:
            good += 1
            print("  ок  " + name)
        else:
            failed += 1
            print("  ПРОВАЛ  " + name)

    with tempfile.TemporaryDirectory(prefix="reference-tautology-") as tmp:
        root = Path(tmp)
        observed = root / "observed.txt"
        reference = root / "reference.txt"
        copied = root / "reference-copy.txt"
        observed.write_text("наблюдаемое\n", encoding="utf-8")
        reference.write_text("эталон\n", encoding="utf-8")
        copied.write_bytes(observed.read_bytes())

        different = inspect_pair(observed, reference)
        check(
            "разные байты получают verified-in-scope",
            different["статус"] == "verified-in-scope"
            and not different["содержимое_совпадает"],
        )
        identical = inspect_pair(observed, copied)
        check(
            "копия с тем же содержимым получает not-evaluated",
            identical["статус"] == "not-evaluated"
            and identical["содержимое_совпадает"],
        )
        same = inspect_pair(observed, observed)
        check(
            "один путь получает not-evaluated",
            same["статус"] == "not-evaluated" and same["путь_совпадает"],
        )
        missing = root / "missing.txt"
        try:
            inspect_pair(observed, missing)
        except FileNotFoundError:
            check("отсутствующий reference не принимается", True)
        else:
            check("отсутствующий reference не принимается", False)

    print(
        "самопроверка сторожа тавтологии observed/reference: "
        "%d пройдено, %d провалено" % (good, failed)
    )
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if argv not in ([], ["--scan"]):
        print("использование: --selftest или --scan")
        return 2
    report = scan()
    OUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "сторож тавтологии observed/reference: %s"
        % report["статус"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
