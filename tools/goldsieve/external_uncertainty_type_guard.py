"""Сторож семантики неопределённости внешних сверок.

Число ``uncertainty`` без указания, является ли оно статистическим,
систематическим или объединённым, не задаёт воспроизводимую нормировку.
Основной сторож внешних целей проверяет наличие положительной величины, но
не должен молча считать её тип. Этот сторож оставляет такой случай
``not-evaluated`` и сохраняет путь реально прочитанного артефакта.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "external_uncertainty_type_guard.json"
ALLOWED = {
    "statistical": "статистическая",
    "systematic": "систематическая",
    "both": "статистическая и систематическая",
    "statistical+systematic": "статистическая и систематическая",
    "statistical_plus_systematic": "статистическая и систематическая",
}


def _target(artifact: dict) -> dict | None:
    for key in ("external_target", "внешняя_цель"):
        value = artifact.get(key)
        if isinstance(value, dict):
            return value
    return None


def inspect(artifact: dict, path: str) -> dict:
    """Разобрать одну запись без вывода вердикта о научной гипотезе."""
    target = _target(artifact)
    if target is None:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "not-evaluated",
            "причина": "в артефакте нет внешней цели",
        }
    raw = target.get("uncertainty_type", target.get("тип_неопределённости"))
    label = str(raw or "").strip().lower()
    if not label:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "not-evaluated",
            "причина": "тип неопределённости не предъявлен",
        }
    if label not in ALLOWED:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "unsupported",
            "причина": "тип неопределённости не входит в разрешённый перечень",
            "значение_типа": str(raw),
        }
    try:
        uncertainty = float(target.get("uncertainty",
                                       target.get("неопределённость")))
    except (TypeError, ValueError):
        uncertainty = float("nan")
    if not math.isfinite(uncertainty) or uncertainty <= 0:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "unsupported",
            "причина": "неопределённость не является положительным конечным числом",
        }
    return {
        "путь": path,
        "прочитано": True,
        "статус": "verified-in-scope",
        "тип": ALLOWED[label],
    }


def collect(root: Path = HERE) -> dict:
    reports = []
    for path in sorted(root.glob("tick*_external*.json")):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            reports.append({
                "путь": str(path),
                "прочитано": False,
                "статус": "unsupported",
                "причина": "артефакт нельзя прочитать как JSON",
            })
            continue
        if isinstance(artifact, dict) and _target(artifact) is not None:
            reports.append(inspect(artifact, str(path)))
    counts = {}
    for report in reports:
        counts[report["статус"]] = counts.get(report["статус"], 0) + 1
    if counts.get("unsupported"):
        status = "unsupported"
        reason = "найдены записи с неподдержанным типом или числом неопределённости"
    elif counts.get("not-evaluated"):
        status = "not-evaluated"
        reason = "часть внешних сверок не предъявляет тип неопределённости"
    else:
        status = "verified-in-scope"
        reason = "тип неопределённости и положительная величина предъявлены"
    result = {
        "статус": status,
        "причина": reason,
        "прочитано_артефактов": len(reports),
        "сводка": counts,
        "разрешённые_типы": sorted(set(ALLOWED.values())),
        "наблюдения": reports,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return result


def selftest() -> int:
    checks = 0
    failures = 0

    def check(name: str, condition: bool) -> None:
        nonlocal checks, failures
        checks += 1
        if condition:
            print("  ок   " + name)
        else:
            failures += 1
            print("  ПРОВАЛ " + name)

    missing = inspect({"external_target": {"value": 1, "uncertainty": 0.1}},
                      "фикстура/нет-типа")
    check("отсутствующий тип даёт not-evaluated",
          missing["статус"] == "not-evaluated")
    valid = inspect({"external_target": {"value": 1, "uncertainty": 0.1,
                                         "uncertainty_type": "statistical"}},
                    "фикстура/статистический")
    check("статистический тип проходит",
          valid["статус"] == "verified-in-scope")
    bad = inspect({"external_target": {"value": 1, "uncertainty": 0.1,
                                       "uncertainty_type": "приближённый"}},
                  "фикстура/неизвестный")
    check("неизвестный тип даёт unsupported",
          bad["статус"] == "unsupported")
    zero = inspect({"external_target": {"value": 1, "uncertainty": 0,
                                        "uncertainty_type": "both"}},
                   "фикстура/нулевая-погрешность")
    check("нулевая неопределённость отклоняется",
          zero["статус"] == "unsupported")
    print("самопроверка типа неопределённости: %d пройдено, %d провалено"
          % (checks - failures, failures))
    return failures


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--selftest":
        return selftest()
    result = collect()
    print("сторож типа неопределённости: %s; прочитано артефактов %d; "
          "сводка %s" % (result["статус"], result["прочитано_артефактов"],
                         json.dumps(result["сводка"], ensure_ascii=False,
                                    sort_keys=True)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
