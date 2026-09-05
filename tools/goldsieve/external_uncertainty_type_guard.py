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
COMBINED_LABELS = {
    "both",
    "statistical+systematic",
    "statistical_plus_systematic",
}


def _target_entry(artifact: dict) -> tuple[bool, dict | None, str | None]:
    """Вернуть наличие, содержимое и имя поля внешней цели.

    Отсутствие поля и повреждённая форма — разные наблюдения. Раньше строка
    или список в ``external_target`` выглядели как отсутствие цели и могли
    тихо выпасть из свода.
    """
    for key in ("external_target", "внешняя_цель"):
        if key not in artifact:
            continue
        value = artifact[key]
        if isinstance(value, dict):
            return True, value, key
        return True, None, key
    return False, None, None


def _target(artifact: dict) -> dict | None:
    """Совместимый помощник для вызовов, которым нужна только цель."""
    found, value, _key = _target_entry(artifact)
    return value if found else None


def _combined_components(target: dict) -> tuple[str, str]:
    """Проверить составную неопределённость, не подменяя её одной цифрой.

    Метка ``both`` семантически сильнее положительного числа: без двух
    предъявленных компонент и их объединения нельзя воспроизвести, что именно
    было нормировано. Поэтому отсутствие компонент — ``not-evaluated``, а
    повреждённая арифметика — ``unsupported``.
    """
    raw = target.get("uncertainty_components",
                     target.get("компоненты_неопределённости"))
    if raw is None:
        return ("not-evaluated",
                "для составной неопределённости не предъявлены "
                "статистическая и систематическая компоненты")
    if not isinstance(raw, dict):
        return ("unsupported",
                "компоненты неопределённости не являются объектом")
    stat = raw.get("statistical", raw.get("статистическая"))
    syst = raw.get("systematic", raw.get("систематическая"))
    combined = target.get("combined_uncertainty",
                          target.get("объединённая_неопределённость"))
    try:
        stat = float(stat)
        syst = float(syst)
        combined = float(combined)
    except (TypeError, ValueError):
        return ("unsupported",
                "компоненты и объединённая неопределённость должны быть числами")
    if (not math.isfinite(stat) or not math.isfinite(syst)
            or not math.isfinite(combined) or stat <= 0 or syst <= 0
            or combined <= 0):
        return ("unsupported",
                "компоненты и объединённая неопределённость должны быть "
                "положительными конечными числами")
    expected = math.hypot(stat, syst)
    if not math.isclose(combined, expected, rel_tol=1e-12, abs_tol=1e-12):
        return ("unsupported",
                "объединённая неопределённость не равна sqrt(stat² + syst²)")
    return ("verified-in-scope", "")


def inspect(artifact: dict, path: str) -> dict:
    """Разобрать одну запись без вывода вердикта о научной гипотезе."""
    found, target, key = _target_entry(artifact)
    if not found:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "not-evaluated",
            "причина": "в артефакте нет внешней цели",
        }
    if target is None:
        return {
            "путь": path,
            "прочитано": True,
            "статус": "unsupported",
            "причина": "поле внешней цели не является объектом",
            "поле": key,
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
    if label in COMBINED_LABELS:
        component_status, component_reason = _combined_components(target)
        if component_status != "verified-in-scope":
            return {
                "путь": path,
                "прочитано": True,
                "статус": component_status,
                "причина": component_reason,
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
        if not isinstance(artifact, dict):
            reports.append({
                "путь": str(path),
                "прочитано": True,
                "статус": "unsupported",
                "причина": "корень внешнего артефакта не является объектом",
            })
            continue
        found, _target_value, _target_key = _target_entry(artifact)
        if found:
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
    combined = inspect(
        {"external_target": {
            "value": 1, "uncertainty": math.hypot(0.08, 0.06),
            "uncertainty_type": "both",
            "uncertainty_components": {
                "statistical": 0.08, "systematic": 0.06},
            "combined_uncertainty": 0.1,
        }},
        "фикстура/составная",
    )
    check("составная неопределённость с компонентами проходит",
          combined["статус"] == "verified-in-scope")
    missing_components = inspect(
        {"external_target": {
            "value": 1, "uncertainty": 0.1, "uncertainty_type": "both"}},
        "фикстура/составная-без-компонент",
    )
    check("составная неопределённость без компонент остаётся not-evaluated",
          missing_components["статус"] == "not-evaluated")
    inconsistent = inspect(
        {"external_target": {
            "value": 1, "uncertainty": 0.1, "uncertainty_type": "both",
            "uncertainty_components": {
                "statistical": 0.08, "systematic": 0.06},
            "combined_uncertainty": 0.2,
        }},
        "фикстура/составная-рассогласована",
    )
    check("несогласованная составная неопределённость отклоняется",
          inconsistent["статус"] == "unsupported")
    malformed = inspect({"external_target": ["value", 1]},
                         "фикстура/неверная-форма")
    check("неверная форма цели не выдаётся за отсутствие",
          malformed["статус"] == "unsupported")
    malformed_alias = inspect({"внешняя_цель": "строка"},
                              "фикстура/неверная-форма-алиаса")
    check("неверная форма русской цели отклоняется",
          malformed_alias["статус"] == "unsupported")
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
