"""Правка тика 41 (продолжение 2): протокол дескриптора и вложенные имена.

Три причины пропусков, найденные отладкой:

1. Методы протокола (`__get__(self, obj, owner=None)`, `__getattr__(self, name)`)
   принимают параметры, которые НЕ являются собственным входом данных: это
   служебные аргументы протокола. Прежний разбор видел параметр без дефолта и
   снимал подозрение. Игнорирование таких параметров не открывает дорогу ложным
   срабатываниям: вердикт True требует НАЙДЕННОГО пути к эталону (found_ref), а
   не отсутствия входов.

2. Имя вложенной функции попадает и в список ПРОЧИТАННЫХ имён (его надо
   разрешить, чтобы вызвать). Само чтение данных не приносит — ровно как у
   функции-наполнителя из тика 40.

3. Значение поля, полученное через дескриптор класса, не находится в `__init__`;
   когда `_field_from_ref` не нашёл источник, остаётся попытка разобрать
   дескриптор.
"""

PATH = "goldsieve/identity_deep.py"
src = open(PATH, encoding="utf-8").read()

# --- 1. параметры протокола -------------------------------------------------
old = '''def _origin_node(node, tree, fn, ref, depth: int, seen: set[int],
                 trail: list[str], instance=None) -> tuple[bool, list[str]]:
    ref_name'''
new = '''# Параметры протоколов Python, которые не приносят данных извне разбора.
PROTOCOL_PARAMS = frozenset({"self", "cls", "obj", "owner", "objtype",
                             "instance", "name"})


def _origin_node(node, tree, fn, ref, depth: int, seen: set[int],
                 trail: list[str], instance=None,
                 protocol: bool = False) -> tuple[bool, list[str]]:
    ref_name'''
assert old in src
src = src.replace(old, new, 1)

old = '''            if instance is not None and i == 0 and arg.arg in ("self", "cls"):
                continue'''
new = '''            if instance is not None and i == 0 and arg.arg in ("self", "cls"):
                continue
            # Метод протокола (__get__, __getattr__ и подобные): служебные
            # аргументы собственным источником данных не являются.
            if protocol and arg.arg in PROTOCOL_PARAMS:
                continue'''
assert old in src
src = src.replace(old, new, 1)

old = '''        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            param_names.add(arg.arg)'''
new = '''        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            param_names.add(arg.arg)
            if protocol and arg.arg in PROTOCOL_PARAMS:
                continue'''
assert old in src
src = src.replace(old, new, 1)

# протокольный флаг протаскивается через _origin_function
old = '''def _origin_function(fn, ref, depth: int, seen: set[int],
                     trail: list[str], instance=None) -> tuple[bool, list[str]]:
    """Разбор одной функции: все ли её источники значения ведут к эталону."""
    node, tree = _node_for(fn)
    if node is None or tree is None:
        return False, trail
    return _origin_node(node, tree, fn, ref, depth, seen, trail, instance)'''
new = '''def _origin_function(fn, ref, depth: int, seen: set[int],
                     trail: list[str], instance=None,
                     protocol: bool = False) -> tuple[bool, list[str]]:
    """Разбор одной функции: все ли её источники значения ведут к эталону."""
    node, tree = _node_for(fn)
    if node is None or tree is None:
        return False, trail
    return _origin_node(node, tree, fn, ref, depth, seen, trail, instance,
                        protocol)'''
assert old in src
src = src.replace(old, new, 1)

for call, repl in (
    ('''            return _origin_function(getattr_fn, ref, depth + 1, seen,
                                    trail + ["__getattr__ %s" % cls.__name__],
                                    instance=inst)''',
     '''            return _origin_function(getattr_fn, ref, depth + 1, seen,
                                    trail + ["__getattr__ %s" % cls.__name__],
                                    instance=inst, protocol=True)'''),
    ('''        return _origin_function(get, ref, depth + 1, seen,
                                trail + ["дескриптор %s.%s"
                                         % (cls.__name__, attr)],
                                instance=descr)''',
     '''        return _origin_function(get, ref, depth + 1, seen,
                                trail + ["дескриптор %s.%s"
                                         % (cls.__name__, attr)],
                                instance=descr, protocol=True)'''),
):
    assert call in src
    src = src.replace(call, repl, 1)

# --- 2. имя вложенной функции в списке прочитанных --------------------------
old = '''        if name in writers:
            found_ref = True
            continue
        if "." in name:'''
new = '''        if name in writers:
            found_ref = True
            continue
        # Имя вложенной функции читается только чтобы её вызвать; сам вызов
        # разобран выше в списке вызовов, поэтому данных чтение не приносит.
        if name in local_defs:
            continue
        if "." in name:'''
assert old in src
src = src.replace(old, new, 1)

# --- 3. поле, приходящее через дескриптор -----------------------------------
old = '''                if _field_from_ref(type(instance), name.split(".")[1],
                                   ref_name, instance):
                    found_ref = True
                    continue
                return False, trail'''
new = '''                if _field_from_ref(type(instance), name.split(".")[1],
                                   ref_name, instance):
                    found_ref = True
                    continue
                # Поля нет в __init__: значение могло прийти через дескриптор
                # класса (property, cached_property, свой __get__).
                got = _descriptor_origin(instance, name.split(".")[-1], ref,
                                         depth, seen, trail)
                if got is not None:
                    ok, tr = got
                    if not ok:
                        return False, trail
                    trail = tr
                    found_ref = True
                    resolved_bases.add(base)
                    continue
                return False, trail'''
assert old in src
src = src.replace(old, new, 1)

open(PATH, "w", encoding="utf-8").write(src)
print("правка внесена")
