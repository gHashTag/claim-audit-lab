"""Детектор тождественности наблюдения и эталона по ГРАФУ ВЫЗОВОВ.

Зачем модуль. Луп 11 закрыл прямую тавтологию `def _observed(): return
_reference()`. Оставался пропуск: та же тавтология через посредника

    def _observed():
        return _table()          # посредник

    def _table():
        return _reference()      # эталон

Строчный признак такое не видит. Здесь разбирается AST модуля, в котором
объявлено наблюдение, и строится ответ на вопрос: получаются ли ВСЕ значения,
которые возвращает наблюдение, из вызова эталона — возможно через цепочку
посредников — и ниоткуда больше.

Чего модуль НЕ делает и почему. Он не объявляет вырождением сам факт
достижимости эталона из наблюдения. Законно, когда наблюдение и эталон
пользуются ОБЩИМ парсером: тогда у них общий предок в графе, но эталон из
наблюдения не достижим, и сравнение содержательно. Также законно, когда
наблюдение читает данные само: появление любого собственного источника данных
снимает подозрение, даже если эталон где-то рядом вызывается.

Критерий: функция — «прозрачная обёртка» эталона, если

  1. у неё нет параметров (иначе значение зависит от входа, а не от эталона);
  2. каждый её `return` содержит вызов эталона или другой прозрачной обёртки;
  3. в её теле нет НИ ОДНОГО другого источника значений: ни вызова функции вне
     белого списка чистых операций, ни чтения файла, ни обращения к модулям
     ввода-вывода.

Белый список чистых операций умышленно узкий: это структурные и арифметические
builtins, которые не могут принести данные извне. `open`, `numpy.loadtxt`,
`Path.read_text` в него не входят, поэтому наблюдение, читающее корпус,
подозрением не становится.
"""

from __future__ import annotations

import ast
import inspect
import types

# Чистые операции: не приносят данных извне, лишь переупаковывают уже
# полученное значение. Список узкий намеренно: любое неизвестное имя трактуется
# как самостоятельный источник данных и СНИМАЕТ подозрение в тождественности.
PURE_BUILTINS = frozenset({
    "abs", "bool", "dict", "divmod", "enumerate", "float", "frozenset", "int",
    "len", "list", "max", "min", "pow", "range", "reversed", "round", "set",
    "sorted", "str", "sum", "tuple", "zip",
})

# Модули чистой математики: math.sqrt(reference()) остаётся производной эталона.
PURE_MODULES = frozenset({"math", "cmath", "decimal", "fractions"})


class _CallCollector(ast.NodeVisitor):
    """Собирает имена всего, что вызывается в теле функции."""

    def __init__(self) -> None:
        self.plain: set[str] = set()      # прямые вызовы: f(...)
        self.attribute: list[str] = []    # вызовы через точку: m.f(...)
        self.has_comprehension_source = False

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        f = node.func
        if isinstance(f, ast.Name):
            self.plain.add(f.id)
        elif isinstance(f, ast.Attribute):
            root = f
            while isinstance(root, ast.Attribute):
                root = root.value
            base = root.id if isinstance(root, ast.Name) else "?"
            self.attribute.append("%s.%s" % (base, f.attr))
        self.generic_visit(node)


def _functions_of(module_src: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(module_src)
    out: dict[str, ast.FunctionDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node  # type: ignore[assignment]
    return out


def _returns(fn: ast.FunctionDef) -> list[ast.Return]:
    found = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and node.value is not None:
            found.append(node)
    return found


def _foreign_source(fn: ast.FunctionDef, allowed: set[str]) -> str | None:
    """Есть ли у функции собственный источник значений, кроме `allowed`.

    Возвращает имя найденного источника или None. Наличие источника означает,
    что наблюдение делает свою работу и подозрение снимается.
    """
    if fn.args.args or fn.args.posonlyargs or fn.args.kwonlyargs \
            or fn.args.vararg or fn.args.kwarg:
        return "параметры функции"
    col = _CallCollector()
    for stmt in fn.body:
        col.visit(stmt)
    for name in sorted(col.plain):
        if name in allowed or name in PURE_BUILTINS:
            continue
        return name
    for dotted in col.attribute:
        base = dotted.split(".")[0]
        if base in PURE_MODULES or base in allowed:
            continue
        return dotted
    return None


def transparent_wrappers(module_src: str, target: str) -> set[str]:
    """Функции модуля, чьё значение целиком происходит из `target`.

    Замыкание считается до неподвижной точки, поэтому цепочка посредников
    любой длины раскрывается: observed -> table -> panel -> reference.
    """
    funcs = _functions_of(module_src)
    wrappers: set[str] = set()
    changed = True
    while changed:
        changed = False
        allowed = {target} | wrappers
        for name, fn in funcs.items():
            if name in wrappers or name == target:
                continue
            rets = _returns(fn)
            if not rets:
                continue
            if _foreign_source(fn, allowed) is not None:
                continue
            # Значение цели может прийти в return через локальную переменную
            # (r = _panel(); return dict(r)), поэтому вызов ищется по ВСЕМУ
            # телу, а не только внутри return. Это безопасно: чужие источники
            # уже исключены выше, значит данных взять больше негде.
            body_calls = set()
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    body_calls.add(sub.func.id)
            uses_target = bool(body_calls & allowed)
            # ПОДСТАВКА в самом критерии: функция, которая вызвала эталон и
            # вернула не связанную с ним константу, обёрткой не является.
            returns_value = any(
                not isinstance(r.value, ast.Constant) for r in rets)
            if uses_target and returns_value:
                wrappers.add(name)
                changed = True
    return wrappers


def derives_from(fn, ref) -> tuple[bool, str]:
    """Наблюдение `fn` целиком производно от эталона `ref`.

    Возвращает (вердикт, объяснение). Объяснение попадает в текст сита, чтобы
    вырождение можно было проверить руками, а не поверить на слово.
    """
    if fn is None or ref is None:
        return False, ""
    if fn is ref:
        return True, "наблюдение и эталон — одна и та же функция"
    # Глубокий разбор происхождения значения (тик 40). Закрывает классы
    # конструкций, которые прямой разбор графа вызовов не видел: замыкания,
    # значения по умолчанию, связанные методы, декораторы, вызываемые объекты,
    # functools.partial и передачу значения через глобальное состояние модуля.
    # Стоит ПЕРЕД проверкой имён: у lambda, partial и вызываемого объекта
    # атрибута __name__ может не быть вообще, и прежний код на них молча
    # возвращал False — тот же тихий отказ, что был найден в лупе 12.
    try:
        from .identity_deep import origin_is
        deep_ok, trail = origin_is(fn, ref)
    except Exception:
        deep_ok, trail = False, []
    if deep_ok:
        return True, "происхождение значения: " + " <- ".join(
            reversed(trail)) if trail else "значение производно от эталона"
    ref_name = getattr(ref, "__name__", None)
    fn_name = getattr(fn, "__name__", None)
    if not ref_name or not fn_name:
        return False, ""
    # ФАЙЛ, а не sys.modules. Найдено калибровкой: CLI загружает кейсы через
    # importlib.util.module_from_spec БЕЗ регистрации в sys.modules, поэтому
    # inspect.getmodule() возвращает None и детектор молча отключался — тихий
    # отказ, худший вид дефекта проверки. Имя файла берётся из объекта кода и
    # от регистрации модуля не зависит.
    fn_file = getattr(getattr(fn, "__code__", None), "co_filename", None)
    ref_file = getattr(getattr(ref, "__code__", None), "co_filename", None)
    if not fn_file or fn_file != ref_file:
        # Межмодульная цепочка требует разрешать реальные объекты из globals,
        # а не сравнивать только имена. Это важно для module_from_spec: такой
        # модуль не обязан быть зарегистрирован в sys.modules.
        same, chain = _derives_cross_module(fn, ref)
        if same:
            return True, chain
        return False, ""
    try:
        with open(fn_file, encoding="utf-8") as fh:
            src = fh.read()
    except OSError:
        return False, ""
    try:
        wrappers = transparent_wrappers(src, ref_name)
    except SyntaxError:
        return False, ""
    if fn_name not in wrappers:
        return False, ""
    chain = _explain_chain(src, fn_name, ref_name, wrappers)
    return True, chain


def _called_functions(fn) -> tuple[list[object], list[str]]:
    """Вернуть реальные вызываемые объекты и неизвестные вызовы функции.

    Объекты разрешаются из ``fn.__globals__``. Для атрибута ``m.f()`` сначала
    разрешается модуль или объект ``m``, после чего берётся ``f``. Возврат
    неизвестного вызова отдельно нужен, чтобы не превратить любую функцию с
    побочным эффектом в «обёртку» эталона.
    """
    code = getattr(fn, "__code__", None)
    if code is None:
        return [], ["объект без тела функции"]
    try:
        src = open(code.co_filename, encoding="utf-8").read()
        funcs = _functions_of(src)
        ast_fn = funcs.get(getattr(fn, "__name__", ""))
        if ast_fn is None:
            return [], ["тело функции не найдено"]
    except (OSError, SyntaxError):
        return [], ["исходник функции недоступен"]

    globals_ = getattr(fn, "__globals__", {})
    calls: list[object] = []
    foreign: list[str] = []
    for node in ast.walk(ast_fn):
        if not isinstance(node, ast.Call):
            continue
        called = None
        label = None
        if isinstance(node.func, ast.Name):
            label = node.func.id
            if label in PURE_BUILTINS:
                continue
            called = globals_.get(label)
        elif isinstance(node.func, ast.Attribute):
            parts = []
            root = node.func
            while isinstance(root, ast.Attribute):
                parts.append(root.attr)
                root = root.value
            if isinstance(root, ast.Name):
                base = globals_.get(root.id)
                label = root.id + "." + ".".join(reversed(parts))
                try:
                    called = base
                    for attr in reversed(parts):
                        called = getattr(called, attr)
                except AttributeError:
                    called = None
                if isinstance(base, types.ModuleType) and base.__name__ in PURE_MODULES:
                    continue
        if callable(called):
            calls.append(called)
        else:
            foreign.append(label or "?")
    return calls, foreign


def _derives_cross_module(fn, ref) -> tuple[bool, str]:
    """Проверить прозрачную цепочку, даже если функции живут в разных файлах.

    Для каждого звена требуются отсутствие параметров, наличие возврата и
    отсутствие неизвестных вызовов. Разрешаются только чистые операции,
    вызов самого эталона или следующего звена, найденные по реальным
    объектам в ``__globals__``. Поэтому совпадение имён в разных модулях не
    является доказательством тождества.
    """
    seen: set[int] = set()
    path: list[str] = []

    def visit(cur) -> bool:
        ident = id(cur)
        if ident in seen:
            return False
        seen.add(ident)
        code = getattr(cur, "__code__", None)
        if code is None:
            return False
        try:
            src = open(code.co_filename, encoding="utf-8").read()
            ast_fn = _functions_of(src).get(getattr(cur, "__name__", ""))
        except (OSError, SyntaxError):
            return False
        if ast_fn is None:
            return False
        if (ast_fn.args.args or ast_fn.args.posonlyargs
                or ast_fn.args.kwonlyargs or ast_fn.args.vararg
                or ast_fn.args.kwarg):
            return False
        returns = _returns(ast_fn)
        if not returns:
            return False
        calls, foreign = _called_functions(cur)
        if foreign:
            return False
        if not calls:
            return False
        path.append(getattr(cur, "__name__", "?"))
        for called in calls:
            if called is ref:
                return True
            if not visit(called):
                path.pop()
                return False
        return True

    ok = visit(fn)
    if not ok:
        return False, ""
    path.append(getattr(ref, "__name__", "?"))
    return True, "межмодульная цепочка вызовов: " + " -> ".join(path)


def _explain_chain(src: str, start: str, target: str,
                   wrappers: set[str]) -> str:
    """Кратчайший путь от наблюдения к эталону — для текста вердикта."""
    funcs = _functions_of(src)
    queue = [[start]]
    seen = {start}
    while queue:
        path = queue.pop(0)
        node = funcs.get(path[-1])
        if node is None:
            continue
        called = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                called.add(sub.func.id)
        if target in called:
            return "цепочка вызовов: " + " -> ".join(path + [target])
        for nxt in sorted(called & wrappers):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(path + [nxt])
    return "наблюдение производно от эталона"


# --------------------------------------------------------------------------
# самопроверка модуля: обязательна по правилу «у каждого модуля-эталона свой
# guard на подставленный неверный ответ»
# --------------------------------------------------------------------------

_POSITIVE = {
    "прямой вызов": '''
def _reference():
    return 1.0

def _observed():
    return _reference()
''',
    "через одного посредника": '''
def _reference():
    return 1.0

def _table():
    return _reference()

def _observed():
    return _table()
''',
    "через двух посредников и упаковку": '''
def _reference():
    return {"mean": 1.0}

def _panel():
    return _reference()

def _table():
    r = _panel()
    return dict(r)

def _observed():
    return _table()
''',
    "чистая арифметика над эталоном": '''
import math

def _reference():
    return 4.0

def _observed():
    return math.sqrt(_reference()) ** 2
''',
}

_NEGATIVE = {
    "наблюдение читает файл": '''
def _reference():
    return 1.0

def _observed():
    with open("data.txt") as fh:
        return float(fh.read())
''',
    "общий парсер, эталон не достижим": '''
def _parse():
    with open("t.md") as fh:
        return fh.read()

def _reference():
    return len(_parse()) * 2

def _observed():
    return len(_parse()) * 2 + 1
''',
    "свой источник рядом с эталоном": '''
import numpy

def _reference():
    return 1.0

def _observed():
    data = numpy.loadtxt("zeros.txt")
    return float(data.mean()) + 0.0 * _reference()
''',
    "наблюдение принимает вход": '''
def _reference():
    return 1.0

def _observed(sample):
    return sum(sample) / len(sample)
''',
    "вызов чужой функции корпуса": '''
def _reference():
    return 1.0

def _measure_zeros():
    return 0.5

def _observed():
    return _measure_zeros()
''',
    "вызвал эталон, вернул константу": '''
def _reference():
    return 1.0

def _observed():
    _reference()
    return 3.14
''',
}


def selftest() -> int:
    """Возвращает число провалов. Позитивные И негативные случаи обязательны."""
    fail = 0

    def check(name, ok):
        nonlocal fail
        print("  %s %s" % ("ok  " if ok else "FAIL", name))
        if not ok:
            fail += 1

    for name, src in _POSITIVE.items():
        w = transparent_wrappers(src, "_reference")
        check("ловит тавтологию: %s" % name, "_observed" in w)

    for name, src in _NEGATIVE.items():
        w = transparent_wrappers(src, "_reference")
        check("НЕ срабатывает: %s" % name, "_observed" not in w)

    # ПОДСТАВКА на сам разбор цепочки: объяснение обязано называть посредника,
    # иначе вердикт невозможно проверить руками.
    src = _POSITIVE["через одного посредника"]
    w = transparent_wrappers(src, "_reference")
    chain = _explain_chain(src, "_observed", "_reference", w)
    check("объяснение называет посредника", "_table" in chain)

    # ПОДСТАВКА: эталон не должен объявляться обёрткой самого себя.
    check("эталон не считается обёрткой себя", "_reference" not in w)

    # ГЛАВНЫЙ guard на тихий отказ. Кейсы загружаются CLI через
    # module_from_spec без регистрации в sys.modules; ранняя версия опиралась
    # на inspect.getmodule() и в этих условиях просто возвращала False.
    # Проверяется сквозь настоящую загрузку файла, а не имитацию.
    import importlib.util
    import os
    import tempfile

    case_src = _POSITIVE["через одного посредника"]
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "case_unregistered.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(case_src)
    spec = importlib.util.spec_from_file_location("case_unregistered", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # в sys.modules НЕ регистрируем
    assert "case_unregistered" not in __import__("sys").modules
    same, chain = derives_from(mod._observed, mod._reference)
    check("работает на модуле вне sys.modules (тихий отказ)", same)
    check("объяснение цепочки доступно и там", "_table" in chain)

    # ПОДСТАВКА к тому же guard: честное наблюдение в тех же условиях не
    # помечается, то есть проверка не превратилась в «всегда True».
    honest = os.path.join(tmp, "case_honest.py")
    with open(honest, "w", encoding="utf-8") as fh:
        fh.write(_NEGATIVE["вызов чужой функции корпуса"])
    spec2 = importlib.util.spec_from_file_location("case_honest", honest)
    mod2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(mod2)
    same2, _ = derives_from(mod2._observed, mod2._reference)
    check("честный кейс вне sys.modules не помечается", not same2)

    # Межмодульный guard: case-файл также не регистрируется в sys.modules, а
    # звено и эталон живут в отдельном реально импортированном модуле.
    helper_src = '''\
def reference():
    return 7

def relay():
    return reference()

def read_file():
    with open(DATA_FILE, encoding="utf-8") as fh:
        return int(fh.read())
'''
    helper_path = os.path.join(tmp, "identity_helper.py")
    data_path = os.path.join(tmp, "identity_data.txt")
    with open(helper_path, "w", encoding="utf-8") as fh:
        fh.write(helper_src)
    with open(data_path, "w", encoding="utf-8") as fh:
        fh.write("7")
    spec_h = importlib.util.spec_from_file_location("identity_helper", helper_path)
    helper = importlib.util.module_from_spec(spec_h)
    helper.DATA_FILE = data_path
    spec_h.loader.exec_module(helper)
    cross_src = '''\
def observed():
    return h.relay()
'''
    cross_path = os.path.join(tmp, "case_cross.py")
    with open(cross_path, "w", encoding="utf-8") as fh:
        fh.write(cross_src)
    spec3 = importlib.util.spec_from_file_location("case_cross", cross_path)
    mod3 = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(mod3)
    # Обе функции остаются вне sys.modules; зависимость передаётся в globals
    # так же, как это делают загрузчики плагинов.
    mod3.h = helper
    mod3.reference = helper.reference
    same3, chain3 = derives_from(mod3.observed, mod3.reference)
    check("ловит межмодульную цепочку", same3)
    check("объяснение межмодульной цепочки доступно",
          "межмодульная цепочка" in chain3 and "relay" in chain3)

    honest_cross_src = '''\
def observed():
    return h.read_file()
'''
    honest_cross_path = os.path.join(tmp, "case_cross_honest.py")
    with open(honest_cross_path, "w", encoding="utf-8") as fh:
        fh.write(honest_cross_src)
    spec4 = importlib.util.spec_from_file_location(
        "case_cross_honest", honest_cross_path)
    mod4 = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(mod4)
    mod4.h = helper
    mod4.reference = helper.reference
    same4, _ = derives_from(mod4.observed, mod4.reference)
    check("межмодульное чтение данных не помечается", not same4)
    return fail


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(1 if selftest() else 0)
