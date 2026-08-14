"""Происхождение значения вызываемого объекта: глубокий разбор.

Зачем модуль. Луп 12 закрыл тавтологию через цепочку ОБЫЧНЫХ функций. Тик 40
измерил корпус из 27 вырожденных фикстур и получил чувствительность 0,1852:
детектор ловил только прямые формы. Пропускались целые классы конструкций —
замыкания, значения по умолчанию, связанные методы, декораторы, вызываемые
объекты, `functools.partial`, а также передача значения через глобальное
состояние модуля.

Вопрос, на который отвечает модуль, тот же: **есть ли у наблюдения СВОЙ
источник значения**. Меняется только полнота разбора того, откуда значение
может прийти:

  * прямой вызов эталона или прозрачной обёртки;
  * свободная переменная замыкания (сам эталон или его значение);
  * значение параметра по умолчанию;
  * атрибут связанного объекта (`self.ref`, `self.value`);
  * `functools.partial` любой вложенности и `__wrapped__` от декоратора;
  * глобальное имя модуля, «испачканное» эталоном на уровне модуля или
    функцией, которая пишет в него значение эталона.

Правило разрешения сомнений не меняется: **неизвестный источник СНИМАЕТ
подозрение**. Всё, что не удалось доказать как производное от эталона,
считается собственным источником данных наблюдения. Ошибка в сторону молчания
безопасна (вердикт останется содержательным), ошибка в сторону срабатывания
уничтожает верные вердикты — за это уже пришлось платить в лупе 11, когда
признак «ровное нулевое расхождение» перевернул 17 корректных вердиктов.
"""

from __future__ import annotations

import ast
import functools
import types

from . import proof
from .identity import PURE_BUILTINS, PURE_MODULES

MAX_DEPTH = 12


# ---------------------------------------------------------------------------
# разбор исходника: поиск узла AST по объекту кода
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=256)
def _parse_file(path: str) -> ast.Module | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return ast.parse(fh.read())
    except (OSError, SyntaxError):
        return None


def _node_for(fn) -> tuple[ast.AST | None, ast.Module | None]:
    """AST-узел функции (в том числе lambda) и модуль, где она объявлена.

    Поиск идёт по номеру первой строки объекта кода, а не по имени: у lambda
    имя `<lambda>`, а у вложенных функций имена совпадают между фабриками.
    """
    code = getattr(fn, "__code__", None)
    if code is None:
        proof.note_unsupported("no-code-object", type(fn).__name__)
        return None, None
    tree = _parse_file(code.co_filename)
    if tree is None:
        proof.note_unsupported("syntax-error", code.co_filename)
        return None, None
    # След пишется ПОСЛЕ разбора и без учёта кэша: измеряется работа
    # анализатора, а не число промахов lru_cache.
    proof.bump("files_parsed")
    proof.bump("functions_seen")
    want = code.co_firstlineno
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if getattr(node, "lineno", None) == want:
                best = node
                break
    if best is None:
        # у декорированной функции co_firstlineno может указывать на строку
        # декоратора: ищем ближайшее объявление, начинающееся не позже
        cands = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.Lambda))
                 and getattr(n, "lineno", 10 ** 9) >= want]
        if cands:
            best = min(cands, key=lambda n: n.lineno)
    if best is None:
        proof.note_unsupported("node-not-found", getattr(fn, "__name__", "?"))
    return best, tree


def _enclosing(tree: ast.Module, node: ast.AST) -> ast.AST | None:
    """Ближайшая объемлющая функция для узла (нужна для свободных переменных)."""
    parent = None
    for cand in ast.walk(tree):
        if isinstance(cand, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for sub in ast.walk(cand):
                if sub is node and cand is not node:
                    if parent is None or cand.lineno > parent.lineno:
                        parent = cand
    return parent


def _body_of(node: ast.AST) -> list[ast.AST]:
    body = getattr(node, "body", [])
    return body if isinstance(body, list) else [body]


# ---------------------------------------------------------------------------
# источники значения внутри одного узла
# ---------------------------------------------------------------------------

def _value_sources(node: ast.AST) -> tuple[list[str], list[str], list[str]]:
    """Имена, из которых узел может взять значение.

    Возвращает (вызовы по имени, вызовы через точку, прочитанные имена).
    Присваиваемые имена в «прочитанные» не попадают: это локальные ярлыки.
    """
    calls, dotted, names = [], [], []
    assigned: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            assigned.add(sub.id)
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            f = sub.func
            if isinstance(f, ast.Name):
                calls.append(f.id)
            elif isinstance(f, ast.Attribute):
                root = f
                parts = []
                while isinstance(root, ast.Attribute):
                    parts.append(root.attr)
                    root = root.value
                base = root.id if isinstance(root, ast.Name) else "?"
                dotted.append(base + "." + ".".join(reversed(parts)))
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            if sub.id not in assigned:
                names.append(sub.id)
        elif isinstance(sub, ast.Attribute) and isinstance(sub.ctx, ast.Load):
            root = sub
            parts = []
            while isinstance(root, ast.Attribute):
                parts.append(root.attr)
                root = root.value
            if isinstance(root, ast.Name):
                names.append(root.id + "." + ".".join(reversed(parts)))
    return calls, dotted, names


def _tainted_globals(tree: ast.Module, ref_name: str) -> set[str]:
    """Глобальные имена модуля, значение которых происходит от эталона.

    Два пути: присваивание на уровне модуля (`VALUE = _reference()`) и запись
    внутри любой функции (`CACHE["v"] = _reference()`, `BUF.append(...)`).
    Второй путь важен: значение эталона попадает в контейнер, а наблюдение
    читает контейнер и формально эталон не вызывает.
    """
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        marks = {ref_name} | tainted
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                value = getattr(node, "value", None)
                if value is None:
                    continue
                calls, _dotted, names = _value_sources(value)
                if not (set(calls) & marks or set(names) & marks):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) \
                    else [node.target]
                for tgt in targets:
                    for sub in ast.walk(tgt):
                        if isinstance(sub, ast.Name):
                            if sub.id not in tainted:
                                tainted.add(sub.id)
                                changed = True
                        elif isinstance(sub, ast.Subscript):
                            root = sub.value
                            while isinstance(root, (ast.Subscript, ast.Attribute)):
                                root = root.value
                            if isinstance(root, ast.Name) and root.id not in tainted:
                                tainted.add(root.id)
                                changed = True
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                f = call.func
                if not isinstance(f, ast.Attribute):
                    continue
                root = f.value
                if not isinstance(root, ast.Name):
                    continue
                for arg in call.args:
                    calls, _d, names = _value_sources(arg)
                    if set(calls) & marks or set(names) & marks:
                        if root.id not in tainted:
                            tainted.add(root.id)
                            changed = True
    return tainted


# ---------------------------------------------------------------------------
# главный разбор
# ---------------------------------------------------------------------------

def _tainted_writers(tree: ast.Module, ref_name: str,
                     tainted: set[str]) -> set[str]:
    """Функции, которые ЗАПИСЫВАЮТ значение эталона в глобальное состояние.

    Такая функция ничего не возвращает (`CACHE["v"] = _reference()`), поэтому
    обёрткой по возвращаемому значению не является — и прежний разбор считал
    её вызов «неизвестным источником», снимая подозрение. На самом деле она
    переносит значение эталона в контейнер, из которого читает наблюдение.
    """
    out: set[str] = set()
    dirty: set[str] = set()
    if not ref_name:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        writes_tainted = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    root = tgt
                    while isinstance(root, (ast.Subscript, ast.Attribute)):
                        root = root.value
                    # Контейнер не обязан быть загрязнён НА УРОВНЕ МОДУЛЯ:
                    # запись `CACHE["v"] = _reference()` внутри функции делает
                    # его загрязнённым в момент вызова. Прежнее требование
                    # `root.id in tainted` этот случай пропускало.
                    if isinstance(root, ast.Name) and (
                            root.id in tainted or _is_module_level(tree,
                                                                  root.id)):
                        calls, _d, names = _value_sources(sub.value)
                        if ref_name in calls or ref_name in names:
                            writes_tainted = True
                            dirty.add(root.id)
        if not writes_tainted:
            continue
        # ПОДСТАВКА: наполнитель, который берёт данные откуда-то ещё, следом
        # эталона не считается — иначе честное наблюдение с кэшем попало бы
        # под подозрение.
        calls, dotted, _names = _value_sources(node)
        foreign = [c for c in calls
                   if c not in PURE_BUILTINS and c != ref_name]
        foreign += [d for d in dotted
                    if d.split(".")[0] not in PURE_MODULES
                    and d.split(".")[0] not in tainted]
        if not foreign:
            out.add(node.name)
    tainted |= dirty
    return out


def _is_module_level(tree: ast.Module, name: str) -> bool:
    """Имя объявлено на уровне модуля (а не локальная переменная функции)."""
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return True
    return False


def origin_is(obj, ref, _depth: int = 0, _seen: set[int] | None = None,
              _trail: list[str] | None = None) -> tuple[bool, list[str]]:
    """Значение `obj` целиком происходит от `ref`.

    Возвращает (вердикт, путь). Путь печатается в вердикте сита, чтобы
    вырождение проверялось руками.
    """
    trail = list(_trail or [])
    proof.bump("chains_expanded")
    if obj is None or ref is None:
        return False, trail
    if _depth > MAX_DEPTH:
        proof.note_unsupported("depth-limit", str(_depth))
        return False, trail
    seen = set(_seen or set())
    if id(obj) in seen:
        return False, trail
    seen.add(id(obj))

    if obj is ref:
        return True, trail + ["эталон"]

    # --- functools.partial любой вложенности --------------------------------
    if isinstance(obj, functools.partial):
        ok, tr = origin_is(obj.func, ref, _depth + 1, seen,
                           trail + ["partial"])
        return ok, tr

    # --- связанный метод ----------------------------------------------------
    if isinstance(obj, types.MethodType):
        inst = obj.__self__
        ok, tr = _origin_function(obj.__func__, ref, _depth + 1, seen,
                                  trail + ["метод %s" % obj.__func__.__name__],
                                  instance=inst)
        return ok, tr

    # --- обёртка от декоратора / lru_cache ----------------------------------
    wrapped = getattr(obj, "__wrapped__", None)
    if wrapped is not None and not isinstance(obj, types.FunctionType):
        ok, tr = origin_is(wrapped, ref, _depth + 1, seen,
                           trail + ["обёртка"])
        if ok:
            return True, tr

    # --- обычная функция или lambda ----------------------------------------
    if isinstance(obj, types.FunctionType):
        return _origin_function(obj, ref, _depth, seen, trail)

    # --- вызываемый объект --------------------------------------------------
    call = getattr(type(obj), "__call__", None)
    if isinstance(call, types.FunctionType):
        return _origin_function(call, ref, _depth + 1, seen,
                                trail + ["__call__ %s" % type(obj).__name__],
                                instance=obj)
    return False, trail


def _resolve_attr(instance, dotted: str):
    """Разрешить `self.a.b` на конкретном экземпляре."""
    parts = dotted.split(".")[1:]
    cur = instance
    for part in parts:
        cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


def _origin_function(fn, ref, depth: int, seen: set[int],
                     trail: list[str], instance=None,
                     protocol: bool = False) -> tuple[bool, list[str]]:
    """Разбор одной функции: все ли её источники значения ведут к эталону."""
    node, tree = _node_for(fn)
    if node is None or tree is None:
        return False, trail
    return _origin_node(node, tree, fn, ref, depth, seen, trail, instance,
                        protocol)


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
                                    instance=inst, protocol=True)
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
                                instance=descr, protocol=True)
    return None


# Параметры протоколов Python, которые не приносят данных извне разбора.
PROTOCOL_PARAMS = frozenset({"self", "cls", "obj", "owner", "objtype",
                             "instance", "name"})


def _origin_node(node, tree, fn, ref, depth: int, seen: set[int],
                 trail: list[str], instance=None,
                 protocol: bool = False) -> tuple[bool, list[str]]:
    proof.bump("nodes_visited")
    ref_name = getattr(ref, "__name__", None)
    globals_ = getattr(fn, "__globals__", {}) or {}
    tainted = _tainted_globals(tree, ref_name) if ref_name else set()
    writers = _tainted_writers(tree, ref_name, tainted) if ref_name else set()

    local_defs = _local_defs(node)
    body = _body_of(node)
    calls, dotted, names = [], [], []
    for stmt in body:
        c, d, n = _value_sources(stmt)
        calls += c
        dotted += d
        names += n

    # Возврат обязателен: функция без возвращаемого значения обёрткой не бывает.
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        has_return = any(isinstance(s, ast.Return) and s.value is not None
                         for s in ast.walk(node))
        if not has_return:
            return False, trail
        # ПОДСТАВКА: вызвал эталон, а вернул константу — не обёртка.
        rets = [s for s in ast.walk(node)
                if isinstance(s, ast.Return) and s.value is not None]
        if all(isinstance(r.value, ast.Constant) for r in rets):
            return False, trail

    # --- параметры: собственный вход снимает подозрение, кроме случая, когда
    #     значением по умолчанию стоит сам эталон или его значение ------------
    args = getattr(node, "args", None)
    defaults_ok = True
    default_from_ref = False
    param_names: set[str] = set()
    if args is not None:
        positional = list(args.posonlyargs) + list(args.args)
        defaults = list(args.defaults)
        pad = len(positional) - len(defaults)
        for i, arg in enumerate(positional):
            param_names.add(arg.arg)
            # Приёмник связанного объекта (`self`, `cls`) данных извне не
            # приносит: он УЖЕ разрешён в конкретный экземпляр, и его поля
            # разбираются отдельно. Без этого исключения связанные методы и
            # вызываемые объекты молча выпадали из разбора.
            if instance is not None and i == 0 and arg.arg in ("self", "cls"):
                continue
            # Метод протокола (__get__, __getattr__ и подобные): служебные
            # аргументы собственным источником данных не являются.
            if protocol and arg.arg in PROTOCOL_PARAMS:
                continue
            default = defaults[i - pad] if i >= pad else None
            if not _default_from_ref(default, ref, ref_name, globals_,
                                     tainted, depth, seen):
                defaults_ok = False
            else:
                default_from_ref = True
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            param_names.add(arg.arg)
            if protocol and arg.arg in PROTOCOL_PARAMS:
                continue
            if not _default_from_ref(default, ref, ref_name, globals_,
                                     tainted, depth, seen):
                defaults_ok = False
            else:
                default_from_ref = True
        if args.vararg or args.kwarg:
            defaults_ok = False
    if not defaults_ok:
        return False, trail

    # Значение по умолчанию, взятое от эталона, — это уже след эталона, даже
    # если в теле стоит только `return value`.
    found_ref = default_from_ref
    # --- вызовы по имени ----------------------------------------------------
    for name in calls:
        if name in PURE_BUILTINS or name in param_names:
            if name in param_names:
                found_ref = True      # параметр с дефолтом-эталоном
            continue
        if name in writers:
            found_ref = True
            continue
        target = _lookup(name, fn, globals_, instance)
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
            return False, trail       # неизвестный источник — подозрение снято
        if target is ref:
            found_ref = True
            continue
        ok, tr = origin_is(target, ref, depth + 1, seen, trail + [name])
        if not ok:
            return False, trail
        trail = tr
        found_ref = True

    # --- вызовы через точку -------------------------------------------------
    dotted_bases: set[str] = set()
    for label in dotted:
        base = label.split(".")[0]
        if base in PURE_MODULES:
            continue
        mod = globals_.get(base)
        if isinstance(mod, types.ModuleType) and mod.__name__ in PURE_MODULES:
            continue
        if base == "self" and instance is not None:
            target = _resolve_attr(instance, label)
            if target is ref:
                found_ref = True
                continue
            if callable(target):
                ok, tr = origin_is(target, ref, depth + 1, seen,
                                   trail + [label])
                if not ok:
                    return False, trail
                trail = tr
                found_ref = True
                continue
            return False, trail
        if base in tainted:
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
            dotted_bases.add(base)
            continue
        return False, trail

    # --- прочитанные имена: свободные переменные, глобальные, self.атрибуты --
    # Порядок не случаен: имена С ТОЧКОЙ разбираются первыми. Значение приходит
    # через атрибут (`_panel.value`), а чтение самого имени объекта (`_panel`)
    # данных не приносит — иначе разобранный дескриптор тут же перекрывался бы
    # вердиктом «объект не callable, источник неизвестен».
    resolved_bases: set[str] = set(dotted_bases)
    for name in [x for x in names if "." in x] + [x for x in names if "." not in x]:
        if name in param_names or name in PURE_BUILTINS:
            continue
        if name in resolved_bases:
            continue
        # Имя функции-наполнителя попадает и в список ПРОЧИТАННЫХ имён (её надо
        # разрешить, чтобы вызвать). Само чтение имени данных не приносит.
        if name in writers:
            found_ref = True
            continue
        # Имя вложенной функции читается только чтобы её вызвать; сам вызов
        # разобран выше в списке вызовов, поэтому данных чтение не приносит.
        if name in local_defs:
            continue
        if "." in name:
            base = name.split(".")[0]
            if base == "self" and instance is not None:
                value = _resolve_attr(instance, name)
                if value is ref:
                    found_ref = True
                    continue
                if callable(value):
                    ok, tr = origin_is(value, ref, depth + 1, seen,
                                       trail + [name])
                    if ok:
                        trail = tr
                        found_ref = True
                        continue
                    return False, trail
                # значение поля: происхождение ищется в __init__ класса
                if _field_from_ref(type(instance), name.split(".")[1],
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
                return False, trail
            if base in tainted:
                found_ref = True
                resolved_bases.add(base)
                continue
            if base in PURE_MODULES:
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
                resolved_bases.add(base)
                continue
            return False, trail
        if name == ref_name:
            found_ref = True
            continue
        if name in tainted:
            found_ref = True
            continue
        cell = _closure_value(fn, name)
        if cell is not _MISSING:
            if cell is ref:
                found_ref = True
                continue
            if callable(cell):
                ok, tr = origin_is(cell, ref, depth + 1, seen, trail + [name])
                if ok:
                    trail = tr
                    found_ref = True
                    continue
                return False, trail
            # захвачено ЗНАЧЕНИЕ: происхождение ищется в объемлющей функции
            if _freevar_from_ref(fn, name, ref_name, tree, globals_):
                found_ref = True
                continue
            return False, trail
        looked = _lookup(name, fn, globals_, instance)
        if looked is ref:
            found_ref = True
            continue
        if looked is None or isinstance(looked, types.ModuleType):
            if name in tainted:
                found_ref = True
                continue
            return False, trail
        if callable(looked):
            ok, tr = origin_is(looked, ref, depth + 1, seen, trail + [name])
            if ok:
                trail = tr
                found_ref = True
                continue
        return False, trail

    if not found_ref:
        return False, trail
    return True, trail + [getattr(fn, "__name__", "?")]


_MISSING = object()


def _closure_value(fn, name):
    """Значение свободной переменной замыкания или _MISSING."""
    code = getattr(fn, "__code__", None)
    cells = getattr(fn, "__closure__", None)
    if code is None or not cells:
        return _MISSING
    freevars = list(code.co_freevars)
    if name not in freevars:
        return _MISSING
    try:
        return cells[freevars.index(name)].cell_contents
    except (IndexError, ValueError):
        return _MISSING


def _lookup(name, fn, globals_, instance):
    """Разрешить имя: замыкание -> globals -> атрибут экземпляра."""
    cell = _closure_value(fn, name)
    if cell is not _MISSING:
        proof.bump("edges_resolved")
        return cell
    if name in globals_:
        proof.bump("edges_resolved")
        return globals_[name]
    if instance is not None:
        return getattr(instance, name, None)
    return None


def _default_from_ref(default, ref, ref_name, globals_, tainted,
                      depth, seen) -> bool:
    """Значение по умолчанию происходит от эталона (или параметра нет)."""
    if default is None:
        return False           # параметр без дефолта = собственный вход
    calls, _dotted, names = _value_sources(default)
    if ref_name and (ref_name in calls or ref_name in names):
        return True
    for nm in list(calls) + list(names):
        if nm in tainted:
            return True
        target = globals_.get(nm)
        if target is ref:
            return True
        if callable(target):
            ok, _tr = origin_is(target, ref, depth + 1, seen, [])
            if ok:
                return True
    return False


def _freevar_from_ref(fn, name, ref_name, tree, globals_) -> bool:
    """Свободная переменная получила ЗНАЧЕНИЕ от эталона в объемлющей функции.

    Разбирается объемлющая функция-фабрика: присваивание `value = _reference()`
    делает захваченное значение производным от эталона. Присваивание из
    параметра фабрики — НЕ делает: значение приходит снаружи, и негативная
    фикстура «равные захваченные значения, разные id» обязана остаться чистой.
    """
    if not ref_name:
        return False
    node, _tree = _node_for(fn)
    if node is None:
        return False
    parent = _enclosing(tree, node)
    if parent is None:
        return False
    parent_params = {a.arg for a in
                     list(getattr(parent.args, "posonlyargs", []))
                     + list(parent.args.args)
                     + list(parent.args.kwonlyargs)}
    for sub in ast.walk(parent):
        if not isinstance(sub, ast.Assign):
            continue
        targets = [t.id for t in sub.targets if isinstance(t, ast.Name)]
        if name not in targets:
            continue
        calls, _dotted, names = _value_sources(sub.value)
        if ref_name in calls or ref_name in names:
            return True
        if set(names) & parent_params or set(calls) & parent_params:
            return False
    return False


def _field_from_ref(cls, field, ref_name, instance) -> bool:
    """Поле экземпляра получило значение от эталона в __init__."""
    if not ref_name:
        return False
    init = getattr(cls, "__init__", None)
    node, _tree = _node_for(init)
    if node is None:
        return False
    init_params = set()
    args = getattr(node, "args", None)
    if args is not None:
        init_params = {a.arg for a in
                       list(getattr(args, "posonlyargs", []))
                       + list(args.args) + list(args.kwonlyargs)} - {"self"}
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Assign):
            continue
        hit = False
        for tgt in sub.targets:
            if isinstance(tgt, ast.Attribute) and tgt.attr == field:
                hit = True
        if not hit:
            continue
        calls, _dotted, names = _value_sources(sub.value)
        if ref_name in calls or ref_name in names:
            return True
        if set(names) & init_params or set(calls) & init_params:
            # значение пришло аргументом конструктора: смотрим сам объект
            value = getattr(instance, field, None)
            return value is not None and getattr(
                value, "__name__", None) == ref_name
    return False
