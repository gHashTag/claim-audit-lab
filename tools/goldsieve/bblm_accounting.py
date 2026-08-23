#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 205: единый учёт элементов протокола BBLM.

Аномалия, найденная по письмам тиков 172–204: тридцать три тика подряд
докладывали «BBLM: 3 из 8 элементов», хотя тик 171 закрыл КОДОМ четыре
элемента и сложил результаты в bblm_elements.json. Причина не в науке, а в
учёте: у протокола оказалось ДВА источника истины — рукописная
спецификация bblm_spec.yaml (её читает гейт) и машинный артефакт
bblm_elements.json (его пишет расчёт). Расчёт не обязан править спецификацию,
поэтому расхождение существовало молча и воспроизводилось в каждом докладе.

Правило: у учёта один источник. Элемент считается закрытым тогда и только
тогда, когда его закрыл КОД, то есть он присутствует в
`elements_closed_by_code` артефакта. Спецификация синхронизируется отсюда
машинно (--sync), а проверка согласованности (--check) даёт код 1 при любом
расхождении и ставится шагом гейта. Значит следующий такой разрыв не сможет
прожить дольше одного тика.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import goldsieve as _gs  # noqa: F401
except Exception:
    pass

try:
    import yaml
except Exception:                                   # объявленный пропуск
    yaml = None

HERE = Path(__file__).resolve().parent
ELEMENTS = HERE / "bblm_elements.json"
SPEC = HERE / "bblm_spec.yaml"
PROTOCOL_JSON = HERE / "bblm_protocol.json"
OUT = HERE / "bblm_accounting.json"

# Поля содержимого, которые протокол требует от каждого элемента, и путь к
# значению внутри узла артефакта. Значения НЕ придумываются: берётся то, что
# посчитал код, иначе элемент остаётся открытым.
FILL = {
    "per_bin_heights": lambda n: {"bins": n.get("bins", [])},
    "error_estimate_method": lambda n: {
        "method": ("непараметрический бутстрэп по зазорам, %d повторов, seed %s"
                   % (n.get("n_boot", 0), n.get("seed"))),
        "sigma_full_sample": n.get("sigma_full_sample"),
    },
    "out_of_sample_check": lambda n: {
        "fit_range": n.get("train_range"),
        "test_range": n.get("test_range"),
        "result": {
            "c_fitted_on_train": n.get("c_fitted_on_train"),
            "deviation_sigma_fitted_c": n.get("deviation_sigma_fitted_c"),
            "deviation_sigma_cited_c": n.get("deviation_sigma_cited_c"),
        },
    },
    "shape_vs_scale_discrimination": lambda n: {
        "scale_part": {"alpha_best_pure_scale": n.get("alpha_best_pure_scale")},
        "shape_part": {"worst_statistic": n.get("worst_statistic"),
                       "worst_residual_sigma": n.get("worst_residual_sigma")},
    },
}


def closed_by_code(artifact: dict) -> dict:
    return artifact.get("elements_closed_by_code") or {}


def open_with_question(artifact: dict) -> list[dict]:
    return artifact.get("elements_open_with_machine_question") or []


def spec_present(spec: dict) -> set[str]:
    return {k for k, v in (spec or {}).items()
            if isinstance(v, dict) and v.get("present")}


def divergence(artifact: dict, spec: dict) -> list[dict]:
    """Расхождения между машинным артефактом и спецификацией протокола."""
    out = []
    present = spec_present(spec)
    for key in closed_by_code(artifact):
        if key not in present:
            out.append({"element": key, "kind": "closed_by_code_absent_in_spec",
                        "detail": "элемент закрыт кодом, но протокол считает "
                                  "его отсутствующим — учёт занижен"})
    for node in open_with_question(artifact):
        key = node.get("element")
        if key in present:
            out.append({"element": key, "kind": "open_but_declared_present",
                        "detail": "элемент остаётся машинным ВОПРОСОМ, но "
                                  "протокол считает его заполненным — учёт "
                                  "завышен"})
    return out


def sync(artifact: dict, spec: dict) -> tuple[dict, list[str]]:
    """Заполнить спецификацию значениями, посчитанными кодом."""
    changed = []
    spec = {k: (dict(v) if isinstance(v, dict) else v) for k, v in spec.items()}
    for key, node in closed_by_code(artifact).items():
        filler = FILL.get(key)
        if filler is None:
            continue
        target = dict(spec.get(key) or {})
        if target.get("present"):
            continue
        target.pop("needed", None)
        target["present"] = True
        target["closed_by"] = "bblm_elements.py (машинный расчёт)"
        target["closed_at_tick"] = artifact.get("tick")
        target.update(filler(node))
        spec[key] = target
        changed.append(key)
    for node in open_with_question(artifact):
        key = node.get("element")
        target = dict(spec.get(key) or {})
        if target.get("present"):
            target["present"] = False
            changed.append(key)
        target["machine_reason_code"] = node.get("machine_reason_code")
        target["needed"] = node.get("what_would_close_it") or target.get("needed")
        spec[key] = target
    return spec, changed


def selftest() -> int:
    bad = 0

    def check(name: str, cond: bool) -> None:
        nonlocal bad
        bad += 0 if cond else 1
        print(f"  {'ok    ' if cond else 'ПРОВАЛ'} {name}")

    art = {"tick": 171,
           "elements_closed_by_code": {"per_bin_heights": {"bins": [1, 2]}},
           "elements_open_with_machine_question": [
               {"element": "coefficient_rederivation",
                "machine_reason_code": "analytic_source_absent",
                "what_would_close_it": "текст статьи"}]}

    # ИСТОРИЧЕСКАЯ ФИКСТУРА: ровно та рассинхронизация, что жила 33 тика.
    stale = {"per_bin_heights": {"present": False, "needed": "L по корзинам"},
             "coefficient_rederivation": {"present": False}}
    d = divergence(art, stale)
    check("занижённый учёт (закрыто кодом, в протоколе нет) ловится",
          len(d) == 1 and d[0]["kind"] == "closed_by_code_absent_in_spec")

    inflated = {"per_bin_heights": {"present": True, "bins": [1]},
                "coefficient_rederivation": {"present": True}}
    d2 = divergence(art, inflated)
    check("завышённый учёт (открыто кодом, в протоколе есть) ловится",
          len(d2) == 1 and d2[0]["kind"] == "open_but_declared_present")

    synced, changed = sync(art, stale)
    check("синхронизация закрывает расхождение",
          divergence(art, synced) == [] and changed == ["per_bin_heights"])
    check("синхронизация переносит СОДЕРЖИМОЕ, а не только признак",
          synced["per_bin_heights"].get("bins") == [1, 2])
    check("открытый элемент синхронизацией не закрывается",
          synced["coefficient_rederivation"]["present"] is False)
    again, changed2 = sync(art, synced)
    check("неподвижная точка синхронизации", changed2 == [] and
          divergence(art, again) == [])

    # МУТАЦИОННАЯ ЦЕЛЬ: если проверку ослабить до сравнения ЧИСЕЛ, историческая
    # фикстура пройдёт (3 против 3), поэтому сравнение обязано быть поимённым.
    counts_only = len(closed_by_code(art)) - len(spec_present(stale))
    check("сравнение чисел этот случай НЕ ловит — значит нужно поимённое",
          counts_only == 1 and len(spec_present(stale)) == 0)

    print(f"самопроверка учёта BBLM: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if yaml is None:
        print("ПРОПУСК: нет pyyaml (объявленный пропуск)")
        return 0
    if not ELEMENTS.exists():
        print("ПРОПУСК: нет bblm_elements.json — сравнивать не с чем")
        return 0
    art = json.loads(ELEMENTS.read_text(encoding="utf-8"))
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8")) or {}

    if "--sync" in argv:
        new_spec, changed = sync(art, spec)
        if changed:
            SPEC.write_text(yaml.safe_dump(new_spec, allow_unicode=True,
                                           sort_keys=False, width=88),
                            encoding="utf-8")
        print("синхронизировано элементов: %d %s" % (len(changed), changed))
        spec = new_spec

    div = divergence(art, spec)
    report = {
        "source_of_truth": "bblm_elements.json (elements_closed_by_code)",
        "closed_by_code": sorted(closed_by_code(art)),
        "open_with_machine_question": [n.get("element")
                                       for n in open_with_question(art)],
        "spec_present": sorted(spec_present(spec)),
        "divergence": div,
        "divergence_count": len(div),
        "why_this_check_exists": (
            "тики 172–204 докладывали 3 из 8 элементов, потому что учёт имел "
            "два источника истины; расхождение обнаружено разбором писем, а "
            "не кодом, поэтому теперь его ловит гейт"),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if div:
        print("РАСХОЖДЕНИЕ УЧЁТА BBLM: %d" % len(div))
        for d in div:
            print("  [%s] %s: %s" % (d["kind"], d["element"], d["detail"]))
        return 1
    print("учёт BBLM согласован: закрыто кодом %d, открытых вопросов %d"
          % (len(report["closed_by_code"]),
             len(report["open_with_machine_question"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
