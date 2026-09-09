"""Мутационная проверка детектора тождественности.

Смысл проверки: корпус фикстур сам по себе ничего не доказывает — он мог бы
проходить и при сломанном детекторе, если бы вырождения ловились случайно или
по постороннему признаку. Поэтому в детектор ВНОСЯТСЯ поломки, и от корпуса
требуется поймать КАЖДУЮ: мутант обязан либо пропустить вырождение, либо дать
ложное срабатывание.

Мутация не правит рабочий файл. Текст ``identity_deep.py`` читается, к нему
дописывается переопределение (или в нём заменяется одна строка), мутант
грузится как отдельный модуль и подставляется в ``sys.modules`` под именем
``goldsieve.identity_deep``. ``identity.derives_from`` импортирует ``origin_is``
ВНУТРИ функции, поэтому подстановка действует на реальном пути вызова.

Код возврата 1, если хотя бы одну поломку корпус не обнаружил: такая поломка
означает, что соответствующий класс конструкций проверяется не по существу.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import traceback

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "goldsieve", "identity_deep.py")

# --- каталог поломок --------------------------------------------------------
# Каждая запись: (что сломано, вид, аргументы).
#   "append"  — дописать текст в конец модуля (переопределение имени);
#   "replace" — заменить точную подстроку (поломка внутри функции).
MUTANTS: list[tuple[str, str, tuple[str, ...]]] = [
    ("извлечение глобального состояния (_tainted_globals)", "append", (
        "\n\ndef _tainted_globals(tree, ref_name):\n    return set()\n",)),
    ("наполнители глобального состояния (_tainted_writers)", "append", (
        "\n\ndef _tainted_writers(tree, ref_name, tainted):\n    return set()\n",)),
    ("нормализация functools.partial", "replace", (
        "    if isinstance(obj, functools.partial):",
        "    if False and isinstance(obj, functools.partial):")),
    ("разбор lambda (_node_for)", "append", (
        "\n\n_orig_node_for = _node_for\n\n\ndef _node_for(fn):\n"
        "    node, tree = _orig_node_for(fn)\n"
        "    if isinstance(node, ast.Lambda):\n"
        "        return None, None\n"
        "    return node, tree\n",)),
    ("приёмник связанного объекта (self/cls)", "replace", (
        '            if instance is not None and i == 0 and arg.arg in ("self", "cls"):',
        "            if False:")),
    ("значение по умолчанию от эталона", "replace", (
        "    found_ref = default_from_ref",
        "    found_ref = False")),
    ("чтение захваченного значения (_closure_value)", "append", (
        "\n\ndef _closure_value(fn, name):\n    return _MISSING\n",)),
    ("разбор поля объекта (_field_from_ref)", "append", (
        "\n\ndef _field_from_ref(cls, field, ref_name, instance=None):\n"
        "    return False\n",)),
    # --- мутации тика 41: дескрипторы и глубокие замыкания -----------
    # Без них вновь внесённые фикстуры доказывали бы только то, что на них
    # вернулся True, но не то, что он вернулся ИМЕННО через разбор дескриптора.
    ("разбор дескриптора (_descriptor_origin)", "append", (
        "\n\ndef _descriptor_origin(owner, attr, ref, depth, seen, trail,\n"
        "                       instance=None):\n    return None\n",)),
    ("вложенные определения (_local_defs)", "append", (
        "\n\ndef _local_defs(node):\n    return {}\n",)),
    ("игнор параметров протокола (PROTOCOL_PARAMS)", "replace", (
        "PROTOCOL_PARAMS = frozenset({\"self\", \"cls\", \"obj\", \"owner\", \"objtype\",",
        "PROTOCOL_PARAMS = frozenset({")),
    ("база разобранного атрибута (resolved_bases)", "replace", (
        "        if name in resolved_bases:",
        "        if False:")),
    # --- мутации тика 41б: классы, поддержанные без мутационных целей -------
    # Наблюдение coverage manifest: у классов «callable object», «decorator» и
    # «прямые формы» мутационных целей не было, то есть их прохождение
    # доказывало возврат True, но НЕ то, что он получен именно разбором
    # вызываемого объекта, обёртки или прямого вызова. Молчание проверки на
    # этих классах было непроверенным (урок тика 40).
    ("разбор вызываемого объекта (__call__)", "replace", (
        '    call = getattr(type(obj), "__call__", None)',
        "    call = None")),
    ("разбор обёртки декоратора (__wrapped__)", "replace", (
        '    wrapped = getattr(obj, "__wrapped__", None)',
        "    wrapped = None")),
    # Одноточечное отключение calls детектор ПЕРЕЖИЛ: имя вызываемой функции
    # попадает и в calls (как ast.Call), и в names (как ast.Name в позиции func),
    # то есть прямой вызов покрыт двумя независимыми путями. Это измеренное
    # свойство, а не догадка. Поэтому мутация для этого класса обязана убрать
    # ОБА пути — иначе она не различает наличие разбора от его отсутствия.
    ("разбор прямых вызовов (calls и имя-функция)", "append", (
        "\n\n_orig_value_sources = _value_sources\n\n\n"
        "def _value_sources(node):\n"
        "    calls, dotted, names = _orig_value_sources(node)\n"
        "    return [], dotted, [n for n in names if n not in set(calls)]\n",)),
    # --- мутации тика 42: класс mutable globals ---------------------------
    # Запись в контейнер (`STATE["v"] = _reference()`) и загрязнение из тела
    # функции — ДВА НЕЗАВИСИМЫХ пути покрытия этого класса. Каждый получает
    # свою мутацию с ОБЯЗАТЕЛЬНОЙ привязкой к классу: если поломку видит
    # только чужой класс, значит именно этот класс остался непроверенным.
    # ИЗМЕРЕНО в тике 42: одноточечное отключение ветки `ast.Subscript`
    # в `_tainted_globals` корпус НЕ заметил — и это не дефект корпуса:
    # `ast.walk(tgt)` по цели `STATE["v"]` всё равно выдаёт `ast.Name STATE`,
    # поэтому ветка Subscript избыточна (измерено трассировкой: вердикт
    # приходит через `name in tainted`). Мутация заменена на такую, которая
    # убирает ОБА пути: загрязнять только цели-голые-имена, то есть любая
    # запись в контейнер перестаёт быть видимой.
    ("запись в глобальный контейнер (оба пути)", "replace", (
        "                    for sub in ast.walk(tgt):",
        "                    for sub in ([tgt] if isinstance(tgt, ast.Name)"
        " else []):"), "mutable globals"),
    ("загрязнение из тела функции (обход всего дерева)", "append", (
        "\n\n_orig_tainted_globals = _tainted_globals\n\n\n"
        "def _tainted_globals(tree, ref_name):\n"
        "    shallow = ast.Module(body=[n for n in tree.body\n"
        "                              if not isinstance(n, (ast.FunctionDef,\n"
        "                                                    ast.AsyncFunctionDef,\n"
        "                                                    ast.ClassDef))],\n"
        "                         type_ignores=[])\n"
        "    return _orig_tainted_globals(shallow, ref_name)\n",),
     "mutable globals"),
]


def _mutate(kind: str, args: tuple[str, ...]) -> str:
    text = open(SRC, encoding="utf-8").read()
    if kind == "append":
        return text + args[0]
    old, new = args
    if old not in text:
        raise AssertionError("поломка неприменима: строка не найдена -> " + old)
    return text.replace(old, new, 1)


def _load_mutant(text: str):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                      encoding="utf-8")
    tmp.write(text)
    tmp.close()
    spec = importlib.util.spec_from_file_location("goldsieve.identity_deep_mut",
                                                  tmp.name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _score() -> tuple[int, int, int, list[str]]:
    """Прогон корпуса: (пропущено, ложных, ошибок, имена сработавших).

    Имена нужны для ПРИВЯЗКИ поломки к классу конструкций: агрегатный
    счёт пропусков показывал только то, что поломку вообще кто-то увидел, а не
    то, что её увидели фикстуры проверяемого класса.
    """
    from goldsieve import identity_corpus as C
    from goldsieve.identity import derives_from
    miss = fp = err = 0
    flagged: list[str] = []
    for name, src in C.POSITIVE.items():
        try:
            _m, obs, ref = C.load(name, src)
            same, _c = derives_from(obs, ref)
        except Exception:
            err += 1
            continue
        if not same:
            miss += 1
            flagged.append(name)
    for name, src in C.NEGATIVE.items():
        try:
            _m, obs, ref = C.load(name, src)
            same, _c = derives_from(obs, ref)
        except Exception:
            err += 1
            continue
        if same:
            fp += 1
            flagged.append(name)
    return miss, fp, err, flagged


def run() -> int:
    real = sys.modules.get("goldsieve.identity_deep")
    if real is None:
        import goldsieve.identity_deep as real  # noqa: F401
        real = sys.modules["goldsieve.identity_deep"]

    base_miss, base_fp, base_err, _base_flagged = _score()
    print("исходный детектор: пропусков %d, ложных %d, ошибок %d"
          % (base_miss, base_fp, base_err))
    if base_miss or base_fp:
        print("ОТКАЗ: мутационная проверка определена только на чистом "
              "детекторе (иначе не отличить свою поломку от чужой).")
        return 1

    undetected = []
    print()
    print("=== внесение поломок: %d" % len(MUTANTS))
    for entry in MUTANTS:
        label, kind, args = entry[0], entry[1], entry[2]
        want_class = entry[3] if len(entry) > 3 else None
        try:
            mod = _load_mutant(_mutate(kind, args))
        except Exception:
            print("  ОШИБКА  %-46s %s" % (label,
                  traceback.format_exc().strip().splitlines()[-1][:70]))
            undetected.append(label)
            continue
        sys.modules["goldsieve.identity_deep"] = mod
        try:
            miss, fp, err, flagged = _score()
        finally:
            sys.modules["goldsieve.identity_deep"] = real
        caught = (miss > base_miss) or (fp > base_fp)
        attributed = True
        if caught and want_class:
            # Привязка: среди сработавших фикстур обязана быть хотя бы одна
            # из объявленного класса — иначе класс остался непроверенным.
            attributed = any(n.split(":")[0] == want_class for n in flagged)
        status = "поймана" if caught else "НЕ ВИДНА"
        if caught and not attributed:
            status = "НЕ ТОТКЛ"
        extra = ""
        if want_class:
            extra = " | класс %s: %s" % (
                want_class, "видит" if attributed else "НЕ ВИДИТ")
        print("  %-9s %-46s пропусков %d, ложных %d, ошибок %d%s"
              % (status, label, miss, fp, err, extra))
        if not caught or not attributed:
            undetected.append(label)

    print()
    print("поймано поломок: %d/%d" % (len(MUTANTS) - len(undetected),
                                      len(MUTANTS)))
    for label in undetected:
        print("  НЕ ОБНАРУЖЕНА  " + label)
    return 1 if undetected else 0


if __name__ == "__main__":
    sys.exit(run())
