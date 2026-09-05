#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож области действия подписи журнала.

Даже предъявленная подпись не покрывает весь журнал автоматически: одна
подпись на одной строке может относиться только к этой строке. Этот сторож
различает наличие подписи и доказанную область её действия. Он не объявляет
криптографическую проверку выполненной и сохраняет консервативный статус
``not-evaluated`` до появления проверяемого контракта.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "journal_signature_scope_guard.json"
SIGNATURE_KEYS = ("signature", "подпись", "detached_signature")


def _read(path: Path) -> tuple[list[dict], list[str]]:
    records: list[dict] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], ["ошибка чтения журнала: %s" % exc]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            errors.append("строка %d не является JSON" % number)
            continue
        if not isinstance(item, dict):
            errors.append("строка %d не является объектом" % number)
            continue
        records.append(item)
    return records, errors


def _scope(signature: object, records: list[dict]) -> set[int] | None:
    """Извлечь явно заявленную область, не принимая её за доказательство."""
    if not isinstance(signature, dict):
        return None
    covers = signature.get("covers")
    if covers == "all":
        return set(range(1, len(records) + 1))
    if not isinstance(covers, list) or not all(
            isinstance(item, int) and not isinstance(item, bool) and item > 0
            for item in covers):
        return None
    return set(covers)


def _scope_out_of_range(signature: object, records: list[dict]) -> bool:
    """Обнаружить ссылки на записи, которых в журнале нет.

    Простое пересечение с ``expected`` скрывало бы подменённую область:
    ``covers: [1, 999]`` выглядело как частичное покрытие, хотя 999 не может
    относиться к прочитанному журналу. Это повреждённая форма контракта, а не
    честно неоценённая область.
    """
    if not isinstance(signature, dict):
        return False
    covers = signature.get("covers")
    if not isinstance(covers, list):
        return False
    return any(
        isinstance(item, int) and not isinstance(item, bool)
        and (item < 1 or item > len(records))
        for item in covers
    )


def audit(path: Path) -> dict:
    if not path.is_file():
        return {
            "статус": "not-evaluated",
            "причина": "журнал вызовов отсутствует",
            "журнал": str(path),
            "записей": 0,
            "подписей": 0,
        }
    records, errors = _read(path)
    if errors:
        return {
            "статус": "unsupported",
            "причина": "журнал содержит повреждённые записи",
            "подробности": errors,
            "журнал": str(path),
            "записей": len(records),
            "подписей": 0,
        }
    signatures = [
        record[key]
        for record in records
        for key in SIGNATURE_KEYS
        if key in record
    ]
    if not signatures:
        return {
            "статус": "not-evaluated",
            "причина": "подпись и область её действия не предъявлены",
            "журнал": str(path),
            "записей": len(records),
            "подписей": 0,
            "покрытие": 0,
        }
    covered: set[int] = set()
    for item in signatures:
        if _scope_out_of_range(item, records):
            return {
                "статус": "unsupported",
                "причина": (
                    "область действия подписи содержит номер записи вне "
                    "прочитанного журнала"
                ),
                "журнал": str(path),
                "записей": len(records),
                "подписей": len(signatures),
                "покрытие": len(covered),
            }
        part = _scope(item, records)
        if part is not None:
            covered.update(part)
    expected = set(range(1, len(records) + 1))
    if covered != expected:
        return {
            "статус": "not-evaluated",
            "причина": (
                "область действия подписи не покрывает все записи; "
                "сама подпись не заменяет проверку алгоритма и ключа"
            ),
            "журнал": str(path),
            "записей": len(records),
            "подписей": len(signatures),
            "покрытие": len(covered & expected),
        }
    return {
        "статус": "not-evaluated",
        "причина": (
            "область действия заявлена для всех записей, но проверяющий "
            "алгоритм и доверенный ключ не закреплены"
        ),
        "журнал": str(path),
        "записей": len(records),
        "подписей": len(signatures),
        "покрытие": len(expected),
    }


def selftest() -> tuple[int, int]:
    good = failed = 0

    def check(name: str, condition: bool) -> None:
        nonlocal good, failed
        if condition:
            good += 1
            print("  ок      %s" % name)
        else:
            failed += 1
            print("  ПРОВАЛ  %s" % name)

    with tempfile.TemporaryDirectory(prefix="goldsieve-signature-scope-") as td:
        root = Path(td)
        missing = root / "нет.jsonl"
        check("отсутствующий журнал не считается покрытием",
              audit(missing)["статус"] == "not-evaluated")

        partial = root / "частичное.jsonl"
        partial.write_text(
            '{"seq": 1, "signature": {"covers": [1]}}\n'
            '{"seq": 2}\n',
            encoding="utf-8",
        )
        result = audit(partial)
        check("частичная область подписи остаётся not-evaluated",
              result["статус"] == "not-evaluated"
              and result["покрытие"] == 1)

        full = root / "полное.jsonl"
        full.write_text(
            '{"seq": 1, "signature": {"covers": "all"}}\n'
            '{"seq": 2}\n',
            encoding="utf-8",
        )
        result = audit(full)
        check("полная область без ключа не объявляется проверенной",
              result["статус"] == "not-evaluated"
              and result["покрытие"] == 2
              and "ключ" in result["причина"])

        out_of_range = root / "вне-диапазона.jsonl"
        out_of_range.write_text(
            '{"seq": 1, "signature": {"covers": [1, 9]}}\n',
            encoding="utf-8",
        )
        result = audit(out_of_range)
        check("ссылка за пределами журнала получает unsupported",
              result["статус"] == "unsupported"
              and "вне" in result["причина"])

        malformed = root / "повреждено.jsonl"
        malformed.write_text('не JSON\n', encoding="utf-8")
        check("повреждённый журнал получает unsupported",
              audit(malformed)["статус"] == "unsupported")

    print("самопроверка области подписи журнала: пройдено %d, провалено %d"
          % (good, failed))
    return good, failed


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        good, failed = selftest()
        return 1 if failed else 0
    try:
        from goldsieve import runlog
        path = Path(runlog.runs_path())
    except Exception as exc:
        result = {
            "статус": "not-evaluated",
            "причина": "путь журнала не определён: %s" % exc,
        }
    else:
        result = audit(path)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож области подписи журнала: %s; причина: %s"
          % (result["статус"], result["причина"]))
    print("журнал: %s; записей: %s; покрытие: %s"
          % (result.get("журнал", "<не определён>"),
             result.get("записей", 0), result.get("покрытие", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
