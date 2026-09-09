"""Чанковая разведка корпуса с продолжением после короткого тайм-аута.

Разведка ``cover`` — это триаж, а не вердикт. Поэтому аварийный тайм-аут
отдельного чанка не должен срывать тик: успешно обработанные файлы сохраняются
в JSON-чекпоинте, а следующий вызов продолжает с последнего файла.

Самопроверка намеренно использует маленький фикстурный корпус, ограничение
числа чанков и мутацию чекпоинта. Так измеряются и чувствительность к
продолжению, и способность заметить пропуск файла.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Callable

from .coverage import scan_file


VERSION = 1
DEFAULT_CHUNK_SIZE = 64
DEFAULT_TIMEOUT_SECONDS = 20.0


def source_files(root: str, exts=(".md", ".rst")) -> list[str]:
    """Детерминированный список текстовых файлов, пригодных для триажа."""
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(
            d for d in dirs
            if d not in (".git", "node_modules", "zig-out",
                         "__pycache__", ".zig-cache")
        )
        for name in sorted(files):
            if name.endswith(exts):
                out.append(os.path.join(base, name))
    return sorted(out)


def _files_digest(files: list[str], root: str) -> str:
    rel = "\n".join(os.path.relpath(p, root) for p in files)
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()


def _new_state(root: str, files: list[str]) -> dict:
    return {
        "version": VERSION,
        "root": os.path.realpath(root),
        "files_digest": _files_digest(files, root),
        "total_files": len(files),
        "last_successful_file": None,
        "next_index": 0,
        "processed_files": 0,
        "timeouts": 0,
        "complete": not files,
        "results": {},
    }


def _load_state(path: str, root: str, files: list[str]) -> dict:
    expected = _new_state(root, files)
    if not path or not os.path.exists(path):
        return expected
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError, TypeError):
        return expected
    if (state.get("version") != VERSION
            or state.get("root") != expected["root"]
            or state.get("files_digest") != expected["files_digest"]):
        return expected
    # Чекпоинт — внутренний артефакт, поэтому недоверенные индексы
    # нормализуются, а не позволяют перескочить за пределы списка.
    state["next_index"] = max(0, min(int(state.get("next_index", 0)),
                                      len(files)))
    state["processed_files"] = max(
        0, min(int(state.get("processed_files", 0)), len(files))
    )
    state["results"] = {
        str(k): v for k, v in (state.get("results") or {}).items()
        if str(k) in files
    }
    # Согласовать указатель с реально сохранёнными результатами. Это guard
    # против мутации, которая сдвигает next_index в конец и тихо пропускает
    # файл в чекпоинте.
    first_missing = next(
        (i for i, path in enumerate(files[:state["next_index"]])
         if path not in state["results"]),
        None,
    )
    if first_missing is not None:
        state["next_index"] = first_missing
        state["processed_files"] = first_missing
        state["complete"] = False
    state["timeouts"] = max(0, int(state.get("timeouts", 0)))
    state["total_files"] = len(files)
    state["complete"] = (
        bool(state.get("complete", False))
        and state["next_index"] >= len(files)
        and len(state["results"]) == len(files)
    )
    return state


def _save_state(path: str, state: dict) -> None:
    if not path:
        return
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def _as_per_file(state: dict) -> dict:
    return {
        path: [tuple(hit) for hit in hits]
        for path, hits in state.get("results", {}).items()
    }


def scan_tree_chunked(
    root: str,
    *,
    checkpoint: str | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_chunks: int | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[dict, dict]:
    """Сканировать корпус чанками и вернуть ``(per_file, state)``.

    Тайм-аут измеряется между файлами. Минимум один файл из начатого чанка
    завершается, чтобы слишком малый лимит не создал бесконечного цикла.
    После тайм-аута функция продолжает следующий вызов чанка; состояние
    записывается после каждого успешно обработанного файла.
    """
    if chunk_size <= 0:
        raise ValueError("размер чанка должен быть положительным")
    if timeout_seconds <= 0:
        raise ValueError("тайм-аут чанка должен быть положительным")
    files = source_files(root)
    state = _load_state(checkpoint, root, files)
    chunks = 0

    while state["next_index"] < len(files):
        if max_chunks is not None and chunks >= max_chunks:
            break
        start = state["next_index"]
        end = min(start + chunk_size, len(files))
        deadline = clock() + timeout_seconds
        progressed = False
        timed_out = False
        while state["next_index"] < end:
            # Проверка до следующего файла делает тайм-аут аварийным для
            # текущего чанка, но не для всей разведки.
            if progressed and clock() >= deadline:
                timed_out = True
                break
            path = files[state["next_index"]]
            state["results"][path] = scan_file(path)
            state["last_successful_file"] = path
            state["next_index"] += 1
            state["processed_files"] = state["next_index"]
            progressed = True
            _save_state(checkpoint, state)
        if timed_out:
            state["timeouts"] += 1
        _save_state(checkpoint, state)
        chunks += 1

    state["complete"] = state["next_index"] >= len(files)
    _save_state(checkpoint, state)
    return _as_per_file(state), state


def selftest() -> int:
    import tempfile

    fail = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal fail
        print("  %s %s%s" % ("ок  " if ok else "FAIL", name,
                             (": " + detail) if detail else ""))
        if not ok:
            fail += 1

    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "corpus")
        os.makedirs(root)
        for i in range(5):
            with open(os.path.join(root, "f%d.md" % i), "w",
                      encoding="utf-8") as fh:
                fh.write("std = %.5f\n" % (1.23456 + i / 100.0))
        checkpoint = os.path.join(d, "checkpoint.json")
        timeout_checkpoint = os.path.join(d, "timeout-checkpoint.json")

        class JumpingClock:
            def __init__(self):
                self.calls = 0

            def __call__(self):
                self.calls += 1
                return self.calls * 10.0

        timed, timeout_state = scan_tree_chunked(
            root, checkpoint=timeout_checkpoint, chunk_size=2,
            timeout_seconds=1.0, max_chunks=1, clock=JumpingClock(),
        )
        check("тайм-аут чанка не срывает разведку",
              len(timed) == 1 and timeout_state["timeouts"] == 1)

        # Чувствительность: один чанк оставляет корпус неполным, а продолжение
        # с последнего успешно обработанного файла восстанавливает все 5 файлов.
        first, state1 = scan_tree_chunked(
            root, checkpoint=checkpoint, chunk_size=2,
            timeout_seconds=60.0, max_chunks=1,
        )
        check("короткий прогон сохраняет частичный результат",
              len(first) == 2 and not state1["complete"])
        check("чекпоинт содержит последний успешный файл",
              state1["last_successful_file"].endswith("f1.md"))
        resumed, state2 = scan_tree_chunked(
            root, checkpoint=checkpoint, chunk_size=2,
            timeout_seconds=60.0,
        )
        check("продолжение обрабатывает остаток корпуса",
              len(resumed) == 5 and state2["complete"])
        check("размер фикстурного корпуса измерен ситом",
              sum(len(v) for v in resumed.values()) == 5)

        # Мутационная цель: если чекпоинт ложно помечен последним файлом,
        # честный результат не должен объявляться полным. Это ловит мутацию,
        # которая меняет next_index на конец списка и молча пропускает файлы.
        with open(checkpoint, encoding="utf-8") as fh:
            mutated = json.load(fh)
        mutated["results"].pop(os.path.join(root, "f4.md"), None)
        mutated["next_index"] = 5
        mutated["complete"] = False
        with open(checkpoint, "w", encoding="utf-8") as fh:
            json.dump(mutated, fh)
        _, state_mut = scan_tree_chunked(
            root, checkpoint=checkpoint, chunk_size=2,
            timeout_seconds=60.0,
        )
        check("мутация пропуска файла не маскируется",
              state_mut["complete"] and state_mut["processed_files"] == 5
              and len(state_mut["results"]) == 5,
              "цель мутации: некорректный next_index")

    print("  итог: %d пройдено, %d провалено" % (6 - fail, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
