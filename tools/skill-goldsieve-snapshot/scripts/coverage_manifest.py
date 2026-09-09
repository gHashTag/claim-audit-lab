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
    from goldsieve import platform_sla as _platform_sla
    for level in ("not_evaluated", "platform_unverified"):
      for row in plat.get(level) or []:
        print("  %-19s %-8s %s" %
              (level, row.get("id"), row.get("reason")))
        if not row.get("reason"):
            problems.append("платформа %s без причины: %s" %
                            (level, row.get("id")))
        # Ссылка на ожидающую задачу обязана вести на файл с владельцем
        # и бюджетом повторов: иначе «выведено в очередь» — только слова.
        ref = row.get("pending")
        if ref:
            path = os.path.join(ROOT, ref)
            if not os.path.exists(path):
                problems.append("ожидающая задача не найдена: %s" % ref)
                continue
            with open(path, encoding="utf-8") as fh:
                task = yaml.safe_load(fh) or {}
            miss = [k for k in ("owner", "retry_budget", "acceptance",
                                "status") if not task.get(k)]
            if miss:
                problems.append("ожидающая задача %s без полей: %s"
                                % (ref, ", ".join(miss)))
            rb = task.get("retry_budget") or {}
            if not isinstance(rb.get("total_attempts_left"), int):
                problems.append("ожидающая задача %s: бюджет повторов не "
                                "число" % ref)
            if level == "platform_unverified":
                good, message = _platform_sla.validate_task(task)
                if not good:
                    problems.append("SLA %s: %s" % (ref, message))
                print("  SLA: %s — %s" % (ref, message))
            print("  ожидает: %s — %s, попыток осталось %s"
                  % (ref, task.get("status"), rb.get("total_attempts_left")))

    # --- статусы задач (тик 43) --------------------------------------
    # Словарь статусов ЗАКРЫТ: свободное слово в поле status делает
    # очередь несравнимой от тика к тику — именно так «waiting» жило рядом
    # с «pending» и никто этого не заметил. Проверяются ВСЕ файлы очереди,
    # а не только те, на кого есть ссылка из манифеста: забытый файл в
    # pending/ — такая же невидимая задача, как и ненаписанная.
    from goldsieve import runlog as _runlog
    pend_dir = os.path.join(ROOT, "pending")
    tasks = sorted(f for f in os.listdir(pend_dir)) if os.path.isdir(pend_dir) \
        else []
    print()
    print("=== задач в очереди: %d, словарь статусов: %s"
          % (len(tasks), ", ".join(_runlog.STATUSES)))
    for fname in tasks:
        if not fname.endswith((".yaml", ".yml")):
            continue
        with open(os.path.join(pend_dir, fname), encoding="utf-8") as fh:
            task = yaml.safe_load(fh) or {}
        st = task.get("status")
        print("  %-20s %s" % (fname, st))
        if st not in _runlog.STATUSES:
            problems.append("задача %s: статус %r вне закрытого словаря %s"
                            % (fname, st, list(_runlog.STATUSES)))
        # Правило приказа: pending без владельца, бюджета и критериев
        # приёмки — провал гейта, а не заметка на потом.
        if st == "pending":
            miss = [k for k in ("owner", "retry_budget", "acceptance")
                    if not task.get(k)]
            if miss:
                problems.append("задача %s в статусе pending без полей: %s"
                                % (fname, ", ".join(miss)))

    # --- оболочка и её обвязка (тик 43) ---------------------------
    # Проверяется три вещи: файл в составе отпечатка baseline, шаг есть
    # в гейте, число утверждений совпадает с объявленным. Проверка, не
    # включённая в гейт, никого не блокирует — это и есть молчание
    # проверки вместо покрытия.
    import subprocess
    from baseline import _tool_files
    sh = man.get("shell_checks", {})
    covered = set(_tool_files())
    gate_text = open(os.path.join(ROOT, "ci_gate.sh"), encoding="utf-8").read()
    print()
    print("=== проверок оболочки: %d" % len(sh))
    for name, spec in sorted(sh.items()):
        if name not in covered:
            problems.append("проверка %s вне состава отпечатка baseline"
                            % name)
        stepname = spec.get("gate_step") or ""
        # Искать ПОДСТРОКУ недостаточно: переименование шага в
        # «…_отключено» подстроку сохраняет, и подставка прошла бы.
        # Проверяется точный вызов step с этим именем.
        if ('step "%s"' % stepname) not in gate_text:
            problems.append("проверка %s: шаг гейта %r не найден в "
                            "ci_gate.sh" % (name, stepname))
        cmd = spec.get("selftest_cmd")
        want = int(spec.get("selftest_checks", 0))
        if cmd is None:
            if not spec.get("skip_run_reason"):
                problems.append("проверка %s без запуска и без объявленной "
                                "причины" % name)
            print("  %-26s шаг есть, запуск пропущен по объявленной "
                  "причине" % name)
            continue
        res = subprocess.run([sys.executable, *cmd], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", errors="backslashreplace", timeout=300)
        got = res.stdout.count("  ок  ")
        print("  %-26s самопроверка %d (объявлено %d)" % (name, got, want))
        if res.returncode != 0:
            problems.append("проверка %s вернула код %d"
                            % (name, res.returncode))
        if got != want:
            problems.append("проверка %s: утверждений %d, объявлено %d"
                            % (name, got, want))

    # --- анализаторы (тик 42) ------------------------------------------
    ana = man.get("analyzers", {})
    print()
    print("=== объявленных анализаторов: %d" % len(ana))
    for name, spec in sorted(ana.items()):
        try:
            mod = __import__("goldsieve." + name, fromlist=["selftest"])
        except Exception as exc:
            problems.append("анализатор %s не импортируется: %s" % (name, exc))
            continue
        st = getattr(mod, "selftest", None)
        if st is None:
            problems.append("анализатор %s без самопроверки" % name)
            continue
        got_ok, got_fail = st()
        want = int(spec.get("selftest_checks", 0))
        print("  %-10s самопроверка %d/%d (объявлено %d)"
              % (name, got_ok, got_ok + got_fail, want))
        if got_fail:
            problems.append("анализатор %s: провалов %d" % (name, got_fail))
        if got_ok != want:
            problems.append("анализатор %s: проверок %d, объявлено %d"
                            % (name, got_ok, want))
        if spec.get("affects_verdict") is not False:
            problems.append("анализатор %s обязан быть объявлен как не "
                            "влияющий на вердикт" % name)

    # --- границы применимости: считаются ЗДЕСЬ, а не переписываются -
    # руками. Правило трёх (Hanley & Lippman-Hand 1983): при нуле событий на N
    # наблюдениях грубая 95 %-верхняя граница доли равна 3/N.
    b = man.get("bounds", {})
    n_neg = len(C.NEGATIVE)
    print()
    print("=== границы: негативных фикстур %d" % n_neg)
    if int(b.get("negative_fixtures", -1)) != n_neg:
        problems.append("границы: объявлено %s негативных фикстур, фактически %d"
                        % (b.get("negative_fixtures"), n_neg))
    fp = int(b.get("false_positives", -1))
    if fp != 0:
        problems.append("границы: объявлено %s ложных — гейт не пропускает "
                        "ненулевое число" % b.get("false_positives"))
    want_upper = float(b.get("rule_of_three_upper", -1))
    calc_upper = 3.0 / n_neg if n_neg else 1.0
    print("  правило трёх: 3/%d = %.4f (объявлено %.4f)"
          % (n_neg, calc_upper, want_upper))
    if abs(calc_upper - want_upper) > 5e-5:
        problems.append("границы: верхняя оценка объявлена %.4f, считается %.4f"
                        % (want_upper, calc_upper))
    note = str(b.get("note", ""))
    for banned in ("полностью верен", "нулевая вероятность ложн"):
        if banned in note.replace("«", "").replace("»", "") and "запрещ" not in note:
            problems.append("границы: запрещённая формулировка в note")

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
