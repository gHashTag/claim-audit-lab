"""Правка тика 41: вложенные def и дескрипторы в разборе происхождения.

Приказ тика 41, пункт 4: закрыть зону риска ГЛУБИНОЙ, а не шириной — довести
closures и descriptors до позитивных, негативных и мутационных доказательств.

Измерение до правки (probe_descriptors.py): дескрипторы 0/7, глубокие
замыкания 2/4. Причины:
  * имя вложенной функции (`def _l3(): ...` внутри тела) не разрешается ни в
    globals, ни в ячейке замыкания, поэтому считалось «неизвестным источником»
    и снимало подозрение;
  * доступ к атрибуту глобального объекта (`_panel.value`) не разбирался: если
    база не `self` и не помечена как загрязнённая, разбор возвращал False. У
    property, cached_property, data descriptor и `__getattr__` значение
    приходит именно так.
"""

import re

PATH = "goldsieve/identity_deep.py"
src = open(PATH, encoding="utf-8").read()

# ---------------------------------------------------------------------------
# 1. Ядро разбора выносится в _origin_node, чтобы его можно было вызвать и для
#    вложенного def, у которого нет собственного объекта функции.
# ---------------------------------------------------------------------------
old_head = '''def _origin_function(fn, ref, depth: int, seen: set[int],
                     trail: list[str], instance=None) -> tuple[bool, list[str]]:
    """Разбор одной функции: все ли её источники значения ведут к эталону."""
    node, tree = _node_for(fn)
    if node is None or tree is None:
        return False, trail
    ref_name'''
new_head = '''def _origin_function(fn, ref, depth: int, seen: set[int],
                     trail: list[str], instance=None) -> tuple[bool, list[str]]:
    """Разбор одной функции: все ли её источники значения ведут к эталону."""
    node, tree = _node_for(fn)
    if node is None or tree is None:
        return False, trail
    return _origin_node(node, tree, fn, ref, depth, seen, trail, instance)


def _local_defs(node: ast.AST) -> dict[str, ast.AST]:
    """Функции, определённые ВНУТРИ тела разбираемого узла.

    Такое имя не лежит ни в globals, ни в ячейке замыкания, поэтому прежний
    разбор считал его неизвестным источником и снимал подозрение. На самом деле
    это ближайший разбираемый узел: `def _l3(): return fn()` внутри `_l2`.
    Учитываются только определения ПЕРВОГО уровня вложенности: определения
    глубже разбираются рекурсивно, когда до них дойдёт разбор.
    """
    out: dict[str, ast.AST] = {}
    for stmt in _body_of(node):
        for sub in ast.walk(stmt):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.setdefault(sub.name, sub)
            elif isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Lambda):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Name):
                        out.setdefault(tgt.id, sub.value)
    return out


def _descriptor_origin(owner, attr: str, ref, depth: int, seen: set[int],
                       trail: list[str]) -> tuple[bool, list[str]] | None:
    """Происхождение значения атрибута `owner.attr` через дескриптор.

    Возвращает (вердикт, путь) либо None, если разобрать нечем — тогда решение
    принимает вызывающий по общему правилу «неизвестный источник снимает
    подозрение».

    Разбираются: property (fget), functools.cached_property (func),
    staticmethod и classmethod (__func__), произвольный дескриптор с методом
    __get__, и падение в __getattr__ класса, когда атрибута нет в mro.
    """
    if owner is None or isinstance(owner, types.ModuleType):
        return None
    cls = owner if isinstance(owner, type) else type(owner)
    inst = None if isinstance(owner, type) else owner
    descr = None
    for base in getattr(cls, "__mro__", (cls,)):
        if attr in getattr(base, "__dict__", {}):
            descr = base.__dict__[attr]
            break

    if descr is None:
        getattr_fn = getattr(cls, "__getattr__", None)
        if isinstance(getattr_fn, types.FunctionType):
            return _origin_function(getattr_fn, ref, depth + 1, seen,
                                    trail + ["__getattr__ %s" % cls.__name__],
                                    instance=inst)
        return None

    if isinstance(descr, property):
        if descr.fget is None:
            return None
        return _origin_function(descr.fget, ref, depth + 1, seen,
                                trail + ["property %s.%s" % (cls.__name__, attr)],
                                instance=inst)

    if isinstance(descr, functools.cached_property):
        func = getattr(descr, "func", None)
        if not isinstance(func, types.FunctionType):
            return None
        return _origin_function(func, ref, depth + 1, seen,
                                trail + ["cached_property %s.%s"
                                         % (cls.__name__, attr)],
                                instance=inst)

    if isinstance(descr, (staticmethod, classmethod)):
        func = getattr(descr, "__func__", None)
        if not isinstance(func, types.FunctionType):
            return None
        return origin_is(func, ref, depth + 1, seen,
                         trail + ["%s %s.%s" % (type(descr).__name__,
                                                cls.__name__, attr)])

    get = getattr(type(descr), "__get__", None)
    if isinstance(get, types.FunctionType):
        return _origin_function(get, ref, depth + 1, seen,
                                trail + ["дескриптор %s.%s"
                                         % (cls.__name__, attr)],
                                instance=descr)
    return None


def _origin_node(node, tree, fn, ref, depth: int, seen: set[int],
                 trail: list[str], instance=None) -> tuple[bool, list[str]]:
    ref_name'''
assert old_head in src
src = src.replace(old_head, new_head, 1)

# ---------------------------------------------------------------------------
# 2. Вложенные определения: собрать таблицу.
# ---------------------------------------------------------------------------
old = '''    body = _body_of(node)
    calls, dotted, names = [], [], []'''
new = '''    local_defs = _local_defs(node)
    body = _body_of(node)
    calls, dotted, names = [], [], []'''
assert old in src
src = src.replace(old, new, 1)

# ---------------------------------------------------------------------------
# 3. Вызов по имени: имя вложенной функции разбирается, а не снимает подозрение.
# ---------------------------------------------------------------------------
old = '''        target = _lookup(name, fn, globals_, instance)
        if target is None:
            if name in tainted:
                found_ref = True
                continue
            return False, trail       # неизвестный источник — подозрение снято'''
new = '''        target = _lookup(name, fn, globals_, instance)
        if target is None:
            if name in tainted:
                found_ref = True
                continue
            if name in local_defs:
                ok, tr = _origin_node(local_defs[name], tree, fn, ref,
                                      depth + 1, seen, trail + [name],
                                      instance)
                if not ok:
                    return False, trail
                trail = tr
                found_ref = True
                continue
            return False, trail       # неизвестный источник — подозрение снято'''
assert old in src
src = src.replace(old, new, 1)

# ---------------------------------------------------------------------------
# 4. Вызов через точку: разбор дескриптора на объекте-владельце.
# ---------------------------------------------------------------------------
old = '''        if base in tainted:
            found_ref = True
            continue
        return False, trail

    # --- прочитанные имена'''
new = '''        if base in tainted:
            found_ref = True
            continue
        owner = _lookup(base, fn, globals_, instance)
        got = _descriptor_origin(owner, label.split(".")[-1], ref, depth,
                                 seen, trail) if owner is not None else None
        if got is not None:
            ok, tr = got
            if not ok:
                return False, trail
            trail = tr
            found_ref = True
            continue
        return False, trail

    # --- прочитанные имена'''
assert old in src
src = src.replace(old, new, 1)

# ---------------------------------------------------------------------------
# 5. Чтение атрибута: то же для `_panel.value` без вызова.
# ---------------------------------------------------------------------------
old = '''            if base in PURE_MODULES:
                continue
            if base in tainted:
                found_ref = True
                continue
            return False, trail'''
new = '''            if base in PURE_MODULES:
                continue
            if base in tainted:
                found_ref = True
                continue
            owner = _lookup(base, fn, globals_, instance)
            got = _descriptor_origin(owner, name.split(".")[-1], ref, depth,
                                     seen, trail) if owner is not None else None
            if got is not None:
                ok, tr = got
                if not ok:
                    return False, trail
                trail = tr
                found_ref = True
                continue
            return False, trail'''
assert old in src
src = src.replace(old, new, 1)

open(PATH, "w", encoding="utf-8").write(src)
print("правка внесена")
print(re.search(r"def _origin_node", src) is not None)
