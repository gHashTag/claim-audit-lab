#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сторож криптографического авторства журнала вызовов.

Хеш-цепочка проверяет целостность доступной копии журнала, но сама по себе
не доказывает, кто создал записи. Этот сторож не подменяет отсутствующую
подпись: он различает отсутствие подписи, повреждённый контракт подписи и
непроверенную подпись, а результат сохраняет как машинный ``not-evaluated``
или ``unsupported``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "journal_signature_guard.json"

SIGNATURE_KEYS = ("signature", "подпись", "detached_signature")
REQUIRED_SIGNATURE_FIELDS = ("algorithm", "value", "public_key")
SUPPORTED_ALGORITHMS = {"ed25519", "minisign", "openpgp"}
DETACHED_SUFFIXES = (".sig", ".asc", ".minisig", ".signature")


def _detached_candidates(path: Path) -> list[Path]:
    """Найти соседние файлы detached-подписи без признания их валидными."""
    candidates = []
    for suffix in DETACHED_SUFFIXES:
        candidates.append(path.with_name(path.name + suffix))
        candidates.append(path.with_suffix(suffix))
    return list(dict.fromkeys(candidates))


def _read_jsonl(path: Path) -> tuple[list[dict], list[str]]:
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


def audit(path: Path) -> dict:
    """Вернуть статус авторства, не называя цепочку подписью."""
    if not path.is_file():
        return {
            "status": "not-evaluated",
            "reason": "журнал вызовов отсутствует",
            "journal": str(path),
            "records": 0,
            "signatures": 0,
        }

    records, errors = _read_jsonl(path)
    if errors:
        return {
            "status": "unsupported",
            "reason": "журнал содержит повреждённые записи",
            "details": errors,
            "journal": str(path),
            "records": len(records),
            "signatures": 0,
        }

    signatures: list[object] = []
    for record in records:
        for key in SIGNATURE_KEYS:
            if key in record:
                signatures.append(record[key])

    detached = [candidate for candidate in _detached_candidates(path)
                if candidate.is_file()]
    signature_count = len(signatures) + len(detached)

    if detached:
        return {
            "status": "not-evaluated",
            "reason": (
                "отдельная подпись предъявлена, но проверяющий алгоритм и "
                "доверенный открытый ключ не закреплены в инструменте"
            ),
            "journal": str(path),
            "records": len(records),
            "signatures": signature_count,
            "inline_signatures": len(signatures),
            "detached_signatures": len(detached),
            "detached_paths": [str(item) for item in detached],
        }

    if not signatures:
        return {
            "status": "not-evaluated",
            "reason": (
                "криптографическая подпись не предъявлена; "
                "хеш-цепочка не доказывает авторство"
            ),
            "journal": str(path),
            "records": len(records),
            "signatures": 0,
            "inline_signatures": 0,
            "detached_signatures": 0,
        }

    malformed = [
        item for item in signatures
        if not isinstance(item, dict)
        or any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in REQUIRED_SIGNATURE_FIELDS
        )
    ]
    if malformed:
        return {
            "status": "unsupported",
            "reason": "контракт подписи неполон",
            "journal": str(path),
            "records": len(records),
            "signatures": signature_count,
            "inline_signatures": len(signatures),
            "detached_signatures": 0,
        }

    unknown_algorithms = sorted({
        item["algorithm"].strip().lower()
        for item in signatures
        if item["algorithm"].strip().lower() not in SUPPORTED_ALGORITHMS
    })
    if unknown_algorithms:
        return {
            "status": "unsupported",
            "reason": "алгоритм подписи не входит в закреплённый словарь",
            "algorithms": unknown_algorithms,
            "journal": str(path),
            "records": len(records),
            "signatures": signature_count,
            "inline_signatures": len(signatures),
            "detached_signatures": 0,
        }

    return {
        "status": "not-evaluated",
        "reason": (
            "подпись предъявлена, но проверяющий алгоритм и доверенный "
            "открытый ключ не закреплены в инструменте"
        ),
        "journal": str(path),
        "records": len(records),
        "signatures": signature_count,
        "inline_signatures": len(signatures),
        "detached_signatures": 0,
    }


def selftest() -> tuple[int, int]:
    ok = failed = 0

    def check(name: str, condition: bool) -> None:
        nonlocal ok, failed
        if condition:
            ok += 1
            print("  ок      %s" % name)
        else:
            failed += 1
            print("  ПРОВАЛ  %s" % name)

    with tempfile.TemporaryDirectory(prefix="goldsieve-signature-") as td:
        root = Path(td)
        missing = root / "missing.jsonl"
        check("отсутствие подписи различается", audit(missing)["status"] == "not-evaluated")

        unsigned = root / "unsigned.jsonl"
        unsigned.write_text('{"seq": 1, "entry_hash": "abc"}\n', encoding="utf-8")
        result = audit(unsigned)
        check(
            "неподписанный журнал не считается подписанным",
            result["status"] == "not-evaluated"
            and "авторство" in result["reason"],
        )

        detached = root / "detached.jsonl"
        detached.write_text('{"seq": 1}\n', encoding="utf-8")
        detached.with_name(detached.name + ".sig").write_text(
            "подпись без проверяющего\n", encoding="utf-8")
        result = audit(detached)
        check(
            "отдельная подпись не теряется при поиске",
            result["status"] == "not-evaluated"
            and result["detached_signatures"] == 1
            and "отдельная подпись" in result["reason"],
        )

        malformed = root / "malformed.jsonl"
        malformed.write_text(
            '{"seq": 1, "signature": {"algorithm": "ed25519"}}\n',
            encoding="utf-8",
        )
        check("неполный контракт подписи отвергается",
              audit(malformed)["status"] == "unsupported")

        typed = root / "typed.jsonl"
        typed.write_text(
            '{"seq": 1, "signature": {"algorithm": "ed25519", '
            '"value": 7, "public_key": "key"}}\n',
            encoding="utf-8",
        )
        check("нетекстовое поле подписи отвергается",
              audit(typed)["status"] == "unsupported")

        unknown = root / "unknown.jsonl"
        unknown.write_text(
            '{"seq": 1, "signature": {"algorithm": "rsa2048", '
            '"value": "sig", "public_key": "key"}}\n',
            encoding="utf-8",
        )
        check("неизвестный алгоритм подписи отвергается",
              audit(unknown)["status"] == "unsupported")

        broken = root / "broken.jsonl"
        broken.write_text('{"seq": 1}\nне JSON\n', encoding="utf-8")
        check("повреждённая запись не становится покрытием",
              audit(broken)["status"] == "unsupported")

    print("самопроверка подписи журнала: пройдено %d, провалено %d"
          % (ok, failed))
    return ok, failed


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        ok, failed = selftest()
        return 1 if failed else 0

    try:
        from goldsieve import runlog
        path = Path(runlog.runs_path())
    except Exception as exc:
        result = {
            "status": "not-evaluated",
            "reason": "путь журнала не определён: %s" % exc,
        }
        path = Path("<не определён>")
    else:
        result = audit(path)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("сторож криптографической подписи журнала: %s; причина: %s"
          % (result["status"], result["reason"]))
    print("журнал: %s; записей: %s; подписей: %s"
          % (result.get("journal", path), result.get("records", 0),
             result.get("signatures", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
