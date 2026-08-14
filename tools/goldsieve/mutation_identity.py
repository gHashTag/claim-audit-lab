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


def _score() -> tuple[int, int, int]:
    """Прогон корпуса: (пропущено, ложных, ошибок)."""
    from goldsieve import identity_corpus as C
    from goldsieve.identity import derives_from
    miss = fp = err = 0
    for name, src in C.POSITIVE.items():
        try:
            _m, obs, ref = C.load(name, src)
            same, _c = derives_from(obs, ref)
        except Exception:
            err += 1
            continue
        if not same:
            miss += 1
    for name, src in C.NEGATIVE.items():
        try:
            _m, obs, ref = C.load(name, src)
            same, _c = derives_from(obs, ref)
        except Exception:
            err += 1
            continue
        if same:
            fp += 1
    return miss, fp, err


def run() -> int:
    real = sys.modules.get("goldsieve.identity_deep")
    if real is None:
        import goldsieve.identity_deep as real  # noqa: F401
        real = sys.modules["goldsieve.identity_deep"]

    base_miss, base_fp, base_err = _score()
    print("исходный детектор: пропусков %d, ложных %d, ошибок %d"
          % (base_miss, base_fp, base_err))
    if base_miss or base_fp:
        print("ОТКАЗ: мутационная проверка определена только на чистом "
              "детекторе (иначе не отличить свою поломку от чужой).")
        return 1

    undetected = []
    print()
    print("=== внесение поломок: %d" % len(MUTANTS))
    for label, kind, args in MUTANTS:
        try:
            mod = _load_mutant(_mutate(kind, args))
        except Exception:
            print("  ОШИБКА  %-46s %s" % (label,
                  traceback.format_exc().strip().splitlines()[-1][:70]))
            undetected.append(label)
            continue
        sys.modules["goldsieve.identity_deep"] = mod
        try:
            miss, fp, err = _score()
        finally:
            sys.modules["goldsieve.identity_deep"] = real
        caught = (miss > base_miss) or (fp > base_fp)
        print("  %-7s %-46s пропусков %d, ложных %d, ошибок %d"
              % ("поймана" if caught else "НЕ ВИДНА", label, miss, fp, err))
        if not caught:
            undetected.append(label)

    print()
    print("поймано поломок: %d/%d" % (len(MUTANTS) - len(undetected),
                                      len(MUTANTS)))
    for label in undetected:
        print("  НЕ ОБНАРУЖЕНА  " + label)
    return 1 if undetected else 0


if __name__ == "__main__":
    sys.exit(run())
