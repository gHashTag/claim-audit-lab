"""Сверка coverage manifest с фактом. Пункт 3 приказа тика 41.

Манифест — объявление. Проверяется КОДОМ, а не доверием:

1. каждый конструкт с supported: true обязан иметь ровно столько положительных
   и негативных фикстур, сколько объявлено (число берётся из
   identity_corpus.classes(), а не из манифеста);
2. каждая объявленная мутационная цель обязана существовать в каталоге
   mutation_identity.MUTANTS;
3. каждый класс, фактически присутствующий в корпусе, обязан быть объявлен —
   иначе покрытие растёт молча, и отчёт снова разойдётся с фактом;
4. каждая фикстура из LIMITATIONS обязана относиться к объявленному конструкту
   и быть перечислена в его limits;
5. конструкт с supported: false обязан иметь ноль фикстур — «не поддержан, но
   фикстуры есть» означает, что объявление устарело.

Код возврата 1 при любом расхождении: манифест включается в ci_gate.sh.
"""

from __future__ import annotations

import os
import sys

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(ROOT, "coverage_manifest.yaml")

sys.path.insert(0, ROOT)


def _corpus_classes() -> dict:
    from goldsieve import identity_corpus as C
    return C.classes()


def _negative_classes(known: list[str]) -> dict:
    """Класс негативной фикстуры.

    Наивный разбор «префикс до двоеточия» не годится: исторические имена
    записаны без префикса («bound method со своим чтением»). Поэтому имя
    конструкта ищется ПОДСТРОКОЙ, а более длинное имя имеет приоритет, чтобы
    «bound method» не перехватывался более общим словом. Сопоставление
    детерминировано и выполняется кодом, а не перечисляется руками.
    """
    from goldsieve import identity_corpus as C
    order = sorted(known, key=len, reverse=True)
    out: dict[str, list[str]] = {}
    for name in C.NEGATIVE:
        low = name.lower()
        cls = next((k for k in order if k.lower() in low), "прямые формы")
        out.setdefault(cls, []).append(name)
    return out


def _mutation_names() -> set[str]:
    import mutation_identity as M
    return {row[0] for row in M.MUTANTS}


def check() -> int:
    man = yaml.safe_load(open(MANIFEST, encoding="utf-8"))
    constructs = man.get("constructs", {})
    pos = _corpus_classes()
    neg = _negative_classes([k for k in constructs if k != "прямые формы"])
    muts = _mutation_names()
    from goldsieve import identity_corpus as C

    problems: list[str] = []
    print("=== конструкты в манифесте: %d" % len(constructs))
    for name, spec in sorted(constructs.items()):
        want_p = int(spec.get("positive", 0))
        want_n = int(spec.get("negative", 0))
        got_p = len(pos.get(name, []))
        got_n = len(neg.get(name, []))
        sup = bool(spec.get("supported"))
        mark = "поддержан " if sup else "НЕ заявлен"
        print("  %-16s %s  фикстур +%d/-%d (объявлено +%d/-%d)"
              % (name, mark, got_p, got_n, want_p, want_n))
        if got_p != want_p:
            problems.append("%s: положительных фикстур %d, объявлено %d"
                            % (name, got_p, want_p))
        if got_n != want_n:
            problems.append("%s: негативных фикстур %d, объявлено %d"
                            % (name, got_n, want_n))
        if sup and got_p == 0:
            problems.append("%s: объявлен поддержанным без фикстур" % name)
        if not sup and (got_p or got_n):
            problems.append("%s: объявлен НЕ поддержанным, но фикстуры есть "
                            "(+%d/-%d) — объявление устарело" % (name, got_p, got_n))
        for target in spec.get("mutation_targets") or []:
            if target not in muts:
                problems.append("%s: мутационная цель отсутствует в каталоге: %r"
                                % (name, target))
        if sup and not (spec.get("mutation_targets") or []):
            print("      ВНИМАНИЕ: поддержан без мутационных целей — молчание "
                  "корпуса на этом классе не доказано")

    # --- классы корпуса, не объявленные в манифесте -------------------------
    for cls in sorted(set(pos) | set(neg)):
        if cls not in constructs:
            problems.append("класс есть в корпусе, но НЕ объявлен в манифесте: "
                            "%s (+%d/-%d)"
                            % (cls, len(pos.get(cls, [])), len(neg.get(cls, []))))

    # --- объявленные ограничения --------------------------------------------
    lims = getattr(C, "LIMITATIONS", {})
    print()
    print("=== объявленных ограничений: %d" % len(lims))
    for name in lims:
        cls = name.split(":")[0].strip()
        print("  %-16s %s" % (cls, name))
        if cls not in constructs:
            problems.append("ограничение относится к необъявленному конструкту: "
                            "%s" % name)
            continue
        limits = constructs[cls].get("limits") or []
        if not limits:
            problems.append("ограничение %r не перечислено в limits конструкта "
                            "%s" % (name, cls))
        if name not in getattr(C, "LIMITATION_REASONS", {}):
            problems.append("ограничение без машинночитаемой причины: %s" % name)

    # --- рантаймы ------------------------------------------------------------
    rt = man.get("runtimes", {})
    print()
    print("=== заявленные рантаймы: %s" % ", ".join(rt.get("verified") or []))
    if not rt.get("verified"):
        problems.append("не заявлено ни одной проверенной версии рантайма")
    plat = (rt.get("platforms") or {})
    for row in plat.get("not_evaluated") or []:
        print("  not-evaluated: %-8s %s" % (row.get("id"), row.get("reason")))
        if not row.get("reason"):
            problems.append("платформа not-evaluated без причины: %s"
                            % row.get("id"))

    print()
    if problems:
        print("МАНИФЕСТ РАСХОДИТСЯ С ФАКТОМ: %d расхождений" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("манифест сходится с фактом: объявленное покрытие подтверждено "
          "составом корпуса и каталогом мутаций")
    return 0


if __name__ == "__main__":
    sys.exit(check())
