#!/usr/bin/env python3
"""Семантический сторож чисел инкрементального регресса.

Форма машинной сути уже проверяет длину списка. Этот сторож проверяет
смысловые инварианты результата: выбранные записи должны быть полностью
разложены по исходам, а пропущенные записи не могут быть отрицательными.
Старый четырёхполный формат не объявляется доказанным и получает
``not-evaluated``.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


ROOT = Path("/home/user/workspace/cron_tracking/8dff7aa3")
FIELDS = (
    "выбрано",
    "пропущено",
    "совпало",
    "изменилось_ситом",
    "изменилось_из-за_корпуса",
    "не_сопоставлено",
)


def validate(value: Any) -> dict[str, Any]:
    if not isinstance(value, list):
        return {"статус": "unsupported", "причина": "регресс не является списком"}
    if len(value) == 4:
        return {
            "статус": "not-evaluated",
            "причина": "старый четырёхполный формат не различает выбранные и пропущенные записи",
        }
    if len(value) != 6:
        return {
            "статус": "unsupported",
            "причина": "регресс обязан содержать шесть счётчиков",
        }
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0
           for item in value):
        return {
            "статус": "unsupported",
            "причина": "счётчики регресса обязаны быть неотрицательными целыми",
        }
    selected, skipped, same, changed, corpus, unmatched = value
    outcomes = same + changed + corpus + unmatched
    if outcomes != selected:
        return {
            "статус": "unsupported",
            "причина": (
                "исходы регресса не разлагают все выбранные записи: "
                f"{outcomes} вместо {selected}"
            ),
        }
    return {
        "статус": "verified-in-scope",
        "причина": "выбранные записи полностью разложены по исходам регресса",
        "поля": dict(zip(FIELDS, value)),
    }


def _latest() -> Path | None:
    paths = [Path(p) for p in glob.glob(str(ROOT / "tick*-progress-substance.json"))]
    if not paths:
        return None
    return max(paths, key=lambda p: int(p.name[4:p.name.index("-")]))


def inspect(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"статус": "unsupported", "причина": f"не удалось прочитать машинную суть: {exc}"}
    result = validate(document.get("регресс"))
    result["источник_наблюдения"] = str(path)
    return result


def selftest() -> int:
    cases = [
        ("полная форма согласована", [2, 4, 2, 0, 0, 0], "verified-in-scope"),
        ("разные исходы согласованы", [5, 0, 2, 1, 1, 1], "verified-in-scope"),
        ("старый формат не объявляется покрытием", [2, 1, 0, 0], "not-evaluated"),
        ("неполная форма отвергается", [2, 0, 2], "unsupported"),
        ("отрицательное число отвергается", [2, -1, 2, 0, 0, 0], "unsupported"),
        ("исходы не покрывают выборку", [3, 0, 2, 0, 0, 0], "unsupported"),
        ("булево значение отвергается", [True, 0, 0, 0, 0, 0], "unsupported"),
    ]
    failed = 0
    for name, value, expected in cases:
        actual = validate(value)["статус"]
        if actual == expected:
            print("  ок      " + name)
        else:
            failed += 1
            print("  ПРОВАЛ  " + name)
    print("самопроверка семантики результата регресса: пройдено %d, провалено %d"
          % (len(cases) - failed, failed))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--check", type=Path)
    parser.add_argument("--scan", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    path = args.check or (_latest() if args.scan else None)
    if path is None:
        print("семантика результата регресса: not-evaluated; машинная суть отсутствует")
        return 0
    result = inspect(path)
    print("семантика результата регресса: %s; %s" %
          (result["статус"], result["причина"]))
    print("источник наблюдения: %s" % result["источник_наблюдения"])
    return 0 if result["статус"] != "unsupported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
