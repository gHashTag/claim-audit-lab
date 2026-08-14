"""Межмодульный граф: ТОЛЬКО статически разрешимые импорты (пункт 1 тика 42).

Зачем отдельный модуль. Разбор происхождения значения (`identity_deep`) работает
внутри ОДНОГО файла: дерево берётся из `fn.__code__.co_filename`. Если эталон
объявлен в одном модуле, а наблюдение читает загрязнённое имя из другого, разбор
не находит связи — и молчит. Молчание неотличимо от «связи нет». Именно этот
класс тихого отказа приказ тика 42 требует сделть наблюдаемым.

Устройство. Граф строится по файлам, а не по объектам модулей: кейсы и фикстуры
грузятся через `module_from_spec` БЕЗ регистрации в `sys.modules`, поэтому
опираться на `sys.modules` нельзя (та же ловушка, что сорвала луп 12).

Разрешаются РОВНО два случая, и оба — по файловой системе рядом с исходным
файлом:

  * `<dir>/<name>.py`            — модуль-сосед;
  * `<dir>/<name>/__init__.py`   — пакет-сосед.

Всё остальное объявляется явно через `proof.note_unsupported` и попадает в
список `unsupported` графа с причиной. Никакого «наверное, это stdlib» —
причина `external-module` тоже пишется.

Что граф НЕ делает (границы, зафиксированные в манифесте):

  * не исполняет код и не импортирует модули (иначе побочные эффекты кейса
    попали бы в анализ);
  * не разрешает `import a.b.c` глубже первого уровня — `a.b` объявляется
    `external-module`, если `a` не сосед;
  * не разрешает импорт внутри функции или ветки `if` — причина
    `conditional-import`;
  * `from x import *` — причина `star-import`;
  * `importlib.import_module(...)`, `__import__(...)` — `dynamic-import`.
"""

from __future__ import annotations

import ast
import functools
import os

from . import proof


@functools.lru_cache(maxsize=256)
def _parse(path: str) -> ast.Module | None:
    """Разбор файла в AST. Свой кэш: модуль не зависит от `identity_deep`."""
    try:
        with open(path, encoding="utf-8") as fh:
            return ast.parse(fh.read())
    except (OSError, SyntaxError):
        return None


def _resolve_sibling(base_dir: str, name: str) -> str | None:
    """Файл модуля-соседа или None. Только первый уровень имени."""
    head = name.split(".")[0]
    if head != name:
        return None                      # пакетный путь: см. external-module
    cand = os.path.join(base_dir, head + ".py")
    if os.path.isfile(cand):
        return cand
    pkg = os.path.join(base_dir, head, "__init__.py")
    if os.path.isfile(pkg):
        return pkg
    return None


def _module_level_imports(tree: ast.Module):
    """Импорты РОВНО на уровне модуля (тело, без вложенности)."""
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node


def _nested_imports(tree: ast.Module):
    """Импорты внутри функций и ветвей: статически не разрешаем."""
    top = set(id(n) for n in _module_level_imports(tree))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and id(node) not in top:
            yield node


def _dynamic_import_calls(tree: ast.Module):
    """Вызовы, порождающие модуль в рантайме."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id == "__import__":
            yield "__import__"
        elif isinstance(f, ast.Attribute) and f.attr == "import_module":
            yield "importlib.import_module"


class ModuleGraph:
    """Вершины — файлы, рёбра — статически разрешённые импорты.

    `bindings[(file, local_name)] = (target_file, target_name)` — что именно
    локальное имя означает в другом файле. Это и есть межмодульное ребро,
    пригодное для разбора происхождения.
    """

    __slots__ = ("nodes", "edges", "bindings", "unsupported", "files_scanned")

    def __init__(self) -> None:
        self.nodes: set[str] = set()
        self.edges: set[tuple[str, str]] = set()
        self.bindings: dict[tuple[str, str], tuple[str, str]] = {}
        self.unsupported: list[tuple[str, str]] = []
        self.files_scanned = 0

    def note(self, reason: str, detail: str) -> None:
        self.unsupported.append((reason, detail))
        proof.note_unsupported(reason, detail)

    def target_of(self, path: str, local_name: str) -> tuple[str, str] | None:
        return self.bindings.get((path, local_name))

    def reasons(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r, _d in self.unsupported:
            out[r] = out.get(r, 0) + 1
        return out

    def render(self) -> str:
        line = "граф: вершин %d, рёбер %d, связей имён %d, файлов %d" % (
            len(self.nodes), len(self.edges), len(self.bindings),
            self.files_scanned)
        if self.unsupported:
            line += "; unsupported: " + ", ".join(
                "%s×%d" % (k, v) for k, v in sorted(self.reasons().items()))
        return line

    def as_dict(self) -> dict:
        return {
            "nodes": sorted(self.nodes),
            "edges": sorted(list(e) for e in self.edges),
            "bindings": {"%s::%s" % k: list(v)
                         for k, v in sorted(self.bindings.items())},
            "unsupported": [{"reason": r, "detail": d}
                            for r, d in self.unsupported],
            "files_scanned": self.files_scanned,
        }


def build(entry_path: str, max_files: int = 64) -> ModuleGraph:
    """Построить граф от файла `entry_path` вглубь по соседним модулям."""
    graph = ModuleGraph()
    entry_path = os.path.abspath(entry_path)
    queue = [entry_path]
    seen: set[str] = set()
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        if len(seen) > max_files:
            graph.note("external-module", "предел обхода %d файлов" % max_files)
            break
        tree = _parse(path)
        graph.files_scanned += 1
        proof.bump("files_parsed")
        if tree is None:
            graph.note("syntax-error", path)
            continue
        graph.nodes.add(path)
        base_dir = os.path.dirname(path)

        for kind in _dynamic_import_calls(tree):
            graph.note("dynamic-import", "%s в %s" % (kind, os.path.basename(path)))
        for node in _nested_imports(tree):
            names = [a.name for a in getattr(node, "names", [])] or ["?"]
            graph.note("conditional-import",
                       "%s в %s" % (",".join(names), os.path.basename(path)))

        for node in _module_level_imports(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _resolve_sibling(base_dir, alias.name)
                    local = alias.asname or alias.name.split(".")[0]
                    if target is None:
                        graph.note("external-module" if "." in alias.name
                                   or _looks_installed(alias.name)
                                   else "module-not-found", alias.name)
                        continue
                    graph.edges.add((path, target))
                    proof.bump("edges_resolved")
                    graph.bindings[(path, local)] = (target, "*module*")
                    queue.append(target)
            else:  # ImportFrom
                if node.level and node.level > 0:
                    # относительный импорт: поднимаемся на level-1 каталогов
                    up = base_dir
                    for _ in range(node.level - 1):
                        up = os.path.dirname(up)
                    if not os.path.isdir(up):
                        graph.note("relative-beyond-root",
                                   "level=%d в %s" % (node.level,
                                                      os.path.basename(path)))
                        continue
                    src_dir = up
                    modname = node.module
                else:
                    src_dir = base_dir
                    modname = node.module
                target = _resolve_sibling(src_dir, modname) if modname else None
                if modname is None and node.level:
                    # from . import x — цель ищется как сосед по имени
                    for alias in node.names:
                        t = _resolve_sibling(src_dir, alias.name)
                        if t is None:
                            graph.note("module-not-found", alias.name)
                            continue
                        graph.edges.add((path, t))
                        proof.bump("edges_resolved")
                        graph.bindings[(path, alias.asname or alias.name)] = (
                            t, "*module*")
                        queue.append(t)
                    continue
                if target is None:
                    graph.note("external-module" if _looks_installed(modname or "")
                               or (modname and "." in modname)
                               else "module-not-found", modname or "?")
                    continue
                graph.edges.add((path, target))
                proof.bump("edges_resolved")
                queue.append(target)
                for alias in node.names:
                    if alias.name == "*":
                        graph.note("star-import", modname or "?")
                        continue
                    graph.bindings[(path, alias.asname or alias.name)] = (
                        target, alias.name)
    return graph


_STDLIB_HINT = {
    "ast", "os", "sys", "math", "json", "functools", "itertools", "types",
    "typing", "pickle", "re", "time", "random", "importlib", "pathlib",
    "collections", "decimal", "fractions", "statistics", "tempfile",
    "threading", "subprocess", "hashlib", "numpy", "scipy", "mpmath", "yaml",
}


def _looks_installed(name: str) -> bool:
    return name.split(".")[0] in _STDLIB_HINT


# ---------------------------------------------------------------------------
# межмодульное происхождение: одно применение графа
# ---------------------------------------------------------------------------

def transparent_relay(path: str, func_name: str, target_name: str,
                      depth: int = 0) -> bool:
    """Функция `func_name` в файле `path` прозрачно возвращает `target_name`.

    Разбор статический: нужен там, где объект модуля недоступен (кейс загружен
    без регистрации в sys.modules). Глубина ограничена: цепочка длиннее трёх
    звеньев объявляется unsupported, а не «нет связи».
    """
    if depth > 3:
        proof.note_unsupported("depth-limit", "modgraph relay %d" % depth)
        return False
    tree = _parse(path)
    if tree is None:
        proof.note_unsupported("syntax-error", path)
        return False
    proof.bump("nodes_visited")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != func_name:
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                if sub.func.id == target_name:
                    proof.bump("chains_expanded")
                    return True
                # звено: локальная функция того же файла
                if transparent_relay(path, sub.func.id, target_name, depth + 1):
                    proof.bump("chains_expanded")
                    return True
    return False


# ---------------------------------------------------------------------------
# самопроверка: позитивные и негативные случаи + подставки
# ---------------------------------------------------------------------------

_FIXTURES = {
    "mg_ref.py": "def reference():\n    return 12.0\n",
    "mg_relay.py": (
        "import mg_ref\n"
        "from mg_ref import reference\n\n\n"
        "def relay():\n    return reference()\n"
    ),
    "mg_own.py": (
        "import os\n\n\n"
        "def own():\n    return float(os.environ.get('MG', '1'))\n"
    ),
    "mg_dyn.py": (
        "import importlib\n\n\n"
        "def get(name):\n    return importlib.import_module(name)\n"
    ),
    "mg_star.py": "from mg_ref import *\n",
    "mg_cond.py": (
        "def lazy():\n    import mg_ref\n    return mg_ref.reference()\n"
    ),
    "mg_missing.py": "import mg_nonexistent_module_xyz\n",
}


def selftest() -> tuple[int, int]:
    import tempfile

    ok = fail = 0

    def check(name: str, cond: bool) -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("  FAIL %s" % name)

    with tempfile.TemporaryDirectory() as d:
        for fname, text in _FIXTURES.items():
            with open(os.path.join(d, fname), "w", encoding="utf-8") as fh:
                fh.write(text)
        _parse.cache_clear()

        relay = os.path.join(d, "mg_relay.py")
        g = build(relay)
        check("вершины включают точку входа", relay in g.nodes)
        check("сосед разрешён в файл",
              os.path.join(d, "mg_ref.py") in g.nodes)
        check("ребро построено",
              (relay, os.path.join(d, "mg_ref.py")) in g.edges)
        check("связь имени построена",
              g.target_of(relay, "reference")
              == (os.path.join(d, "mg_ref.py"), "reference"))
        check("stdlib не выдаётся за сосед", not any(
            os.path.basename(n).startswith("os.") for n in g.nodes))

        # применение: прозрачное межмодульное звено
        check("прозрачное звено найдено",
              transparent_relay(relay, "relay", "reference"))
        own = os.path.join(d, "mg_own.py")
        check("честное наблюдение звеном не считается",
              not transparent_relay(own, "own", "reference"))

        # ЯВНЫЕ отказы вместо тишины
        gd = build(os.path.join(d, "mg_dyn.py"))
        check("динамический импорт объявлен",
              gd.reasons().get("dynamic-import", 0) >= 1)
        gs = build(os.path.join(d, "mg_star.py"))
        check("звёздный импорт объявлен",
              gs.reasons().get("star-import", 0) == 1)
        gc = build(os.path.join(d, "mg_cond.py"))
        check("импорт внутри функции объявлен",
              gc.reasons().get("conditional-import", 0) == 1)
        gm = build(os.path.join(d, "mg_missing.py"))
        check("ненайденный модуль объявлен",
              gm.reasons().get("module-not-found", 0) == 1)
        go = build(own)
        check("stdlib объявлен как внешний",
              go.reasons().get("external-module", 0) >= 1)

        # ПОДСТАВКА 1: отказ обязан иметь ИМЯ из закрытого списка proof.REASONS.
        bad = [r for r, _d in (gd.unsupported + gs.unsupported
                               + gc.unsupported + gm.unsupported)
               if r not in proof.REASONS]
        check("все причины из закрытого списка", not bad)

        # ПОДСТАВКА 2: граф не смеет исполнять код фикстуры. Если бы исполнял,
        # mg_dyn.get() поднял бы ImportError на несуществующем имени; строим
        # граф файла, чей импорт заведомо падает при исполнении.
        boom = os.path.join(d, "mg_boom.py")
        with open(boom, "w", encoding="utf-8") as fh:
            fh.write("import mg_ref\nraise SystemExit('исполнение запрещено')\n")
        _parse.cache_clear()
        try:
            gb = build(boom)
            check("граф не исполняет код", boom in gb.nodes)
        except SystemExit:
            check("граф не исполняет код", False)

        # ПОДСТАВКА 3: след обязан наполняться при построении графа.
        _parse.cache_clear()
        with proof.scope("modgraph") as pr:
            build(relay)
        check("след непустой при построении графа", not pr.is_trivial())
        check("след содержит рёбра", pr.counters["edges_resolved"] >= 1)

        # ПОДСТАВКА 4: у пустого файла граф — одна вершина, ноль рёбер, и это
        # НЕ должно выглядеть как успешный межмодульный разбор.
        empty = os.path.join(d, "mg_empty.py")
        open(empty, "w").close()
        _parse.cache_clear()
        ge = build(empty)
        check("пустой файл даёт ноль рёбер", not ge.edges)

    print("  modgraph: %d пройдено, %d провалено" % (ok, fail))
    return ok, fail


if __name__ == "__main__":
    import sys
    _ok, _fail = selftest()
    sys.exit(1 if _fail else 0)
