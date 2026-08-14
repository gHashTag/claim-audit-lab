"""Корпус фикстур для калибровки детектора тождественности.

Приказ тика 40: довести положительный корпус до 20-30 подтверждённых вырождений,
отдельно покрыв closures, default arguments, bound methods, decorators, callable
objects, nested partial и изменение глобального окружения; и ввести негативный
стресс-корпус, где смысл различается, а форма кода похожа.

Смысл разделения. ПОЛОЖИТЕЛЬНАЯ фикстура — наблюдение, значение которого целиком
происходит из эталона, то есть сравнение вырождено и детектор ОБЯЗАН сработать.
ОТРИЦАТЕЛЬНАЯ фикстура — наблюдение со своим источником данных; детектор обязан
молчать, даже когда форма кода выглядит подозрительно похоже.

Негативный корпус специально составлен из ловушек на наивные признаки:
одинаковое значение при разных путях, равные захваченные значения при разных
идентификаторах объектов, альфа-переименование, перестановка независимых
операций, сериализация вызываемого объекта. Признак, который сработает хотя бы
на одной из них, объявляется негодным.

Каждая фикстура — исходный текст модуля, который загружается НАСТОЯЩИМ
``module_from_spec`` без регистрации в ``sys.modules``: именно так грузит кейсы
CLI, и именно в этих условиях версия детектора из лупа 12 молча отказывала.
Атрибут для проверки — ``_observed``, эталон — ``_reference``.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile

# Общая «данные корпуса» подкладка: фикстуре, которой нужен свой источник,
# нужен файл для чтения. Значение отличается от эталона, поэтому честное
# наблюдение и эталон дают РАЗНЫЕ числа — иначе совпадение чисел можно было бы
# спутать с тождеством пути.
DATA_TEXT = "17.5\n"

_PREAMBLE = '''
import functools
import math
import os
import pickle

DATA = os.environ["GOLDSIEVE_FIXTURE_DATA"]


def _reference():
    """Вычисляемый эталон: замкнутое выражение, не зависящее от файла."""
    return 12.0 * math.sqrt(2.0)


def _read_own():
    """Собственный источник данных: чтение файла корпуса."""
    with open(DATA, encoding="utf-8") as fh:
        return float(fh.read().strip())
'''

# ---------------------------------------------------------------------------
# ПОЛОЖИТЕЛЬНЫЙ КОРПУС: значение наблюдения целиком происходит из эталона
# ---------------------------------------------------------------------------

POSITIVE: dict[str, str] = {}

# --- класс: closures -------------------------------------------------------

POSITIVE["closure: возврат вложенной функции"] = '''
def _make():
    def inner():
        return _reference()
    return inner


_observed = _make()
'''

POSITIVE["closure: захват эталона в переменную"] = '''
def _make():
    ref = _reference
    def inner():
        return ref()
    return inner


_observed = _make()
'''

POSITIVE["closure: захваченное ЗНАЧЕНИЕ эталона"] = '''
def _make():
    value = _reference()
    def inner():
        return value
    return inner


_observed = _make()
'''

# --- класс: default arguments ----------------------------------------------

POSITIVE["default arg: эталон значением по умолчанию"] = '''
def _observed(ref=_reference):
    return ref()
'''

POSITIVE["default arg: готовое число по умолчанию"] = '''
def _observed(value=_reference()):
    return value
'''

POSITIVE["default arg: keyword-only эталон"] = '''
def _observed(*, ref=_reference):
    return ref()
'''

# --- класс: bound methods --------------------------------------------------

POSITIVE["bound method: метод возвращает эталон"] = '''
class Panel:
    def value(self):
        return _reference()


_observed = Panel().value
'''

POSITIVE["bound method: эталон в атрибуте объекта"] = '''
class Panel:
    def __init__(self):
        self.ref = _reference

    def value(self):
        return self.ref()


_observed = Panel().value
'''

POSITIVE["bound method: classmethod через посредника"] = '''
class Panel:
    @classmethod
    def value(cls):
        return _relay()


def _relay():
    return _reference()


_observed = Panel.value
'''

# --- класс: decorators -----------------------------------------------------

POSITIVE["decorator: functools.wraps поверх тавтологии"] = '''
def _passthrough(fn):
    @functools.wraps(fn)
    def wrapper():
        return fn()
    return wrapper


@_passthrough
def _observed():
    return _reference()
'''

POSITIVE["decorator: обёртка сама возвращает эталон"] = '''
def _replace(fn):
    @functools.wraps(fn)
    def wrapper():
        return _reference()
    return wrapper


@_replace
def _observed():
    return _read_own()
'''

POSITIVE["decorator: cache поверх тавтологии"] = '''
@functools.lru_cache(maxsize=None)
def _observed():
    return _reference()
'''

# --- класс: callable objects -----------------------------------------------

POSITIVE["callable object: __call__ возвращает эталон"] = '''
class Meter:
    def __call__(self):
        return _reference()


_observed = Meter()
'''

POSITIVE["callable object: эталон сохранён при создании"] = '''
class Meter:
    def __init__(self, ref):
        self.ref = ref

    def __call__(self):
        return self.ref()


_observed = Meter(_reference)
'''

POSITIVE["callable object: значение эталона в поле"] = '''
class Meter:
    def __init__(self):
        self.value = _reference()

    def __call__(self):
        return self.value


_observed = Meter()
'''

# --- класс: partial и nested partial ---------------------------------------

POSITIVE["partial: прямой partial эталона"] = '''
_observed = functools.partial(_reference)
'''

POSITIVE["partial: partial над partial"] = '''
_observed = functools.partial(functools.partial(_reference))
'''

POSITIVE["partial: partial над посредником"] = '''
def _relay():
    return _reference()


_observed = functools.partial(functools.partial(_relay))
'''

# --- класс: lambda ---------------------------------------------------------

POSITIVE["lambda: прямой вызов эталона"] = '''
_observed = lambda: _reference()
'''

POSITIVE["lambda: цепочка из двух lambda"] = '''
_mid = lambda: _reference()
_observed = lambda: _mid()
'''

POSITIVE["lambda: арифметика над эталоном"] = '''
_observed = lambda: 1.0 * _reference()
'''

# --- класс: изменение глобального окружения --------------------------------

# Мутационная проверка тика 40 показала, что путь чтения ЗАХВАЧЕННОЙ ЯЧЕЙКИ
# (`_closure_value`) корпусом не проверялся: поломка этого пути не давала ни
# одного пропуска. Фикстура ниже закрывает пробел — эталон захвачен как ФУНКЦИЯ,
# а не как значение, поэтому разобрать его можно только через ячейку замыкания.
POSITIVE["closure: захвачена сама функция эталона"] = '''
def _make(fn):
    return lambda: fn()


_observed = _make(_reference)
'''

POSITIVE["globals: эталон пишет кэш, наблюдение читает"] = '''
CACHE = {}


def _fill():
    CACHE["v"] = _reference()


def _observed():
    if "v" not in CACHE:
        _fill()
    return CACHE["v"]
'''

POSITIVE["globals: модульная переменная от эталона"] = '''
VALUE = _reference()


def _observed():
    return VALUE
'''

POSITIVE["globals: список, наполненный эталоном"] = '''
BUF = []
BUF.append(_reference())


def _observed():
    return BUF[0]
'''

# --- класс: прямые формы (регрессия лупов 11-12) ---------------------------

POSITIVE["прямой вызов эталона"] = '''
def _observed():
    return _reference()
'''

POSITIVE["цепочка из двух посредников"] = '''
def _panel():
    return _reference()


def _table():
    r = _panel()
    return dict(v=r)["v"]


def _observed():
    return _table()
'''

POSITIVE["чистая арифметика над эталоном"] = '''
def _observed():
    return math.sqrt(_reference() ** 2)
'''


# --- класс: descriptors (тик 41) -------------------------------------------

# Измерение до правки тика 41: дескрипторы 0/7. Причина — значение приходит
# через доступ к атрибуту объекта, а этот путь не разбирался вовсе.

POSITIVE["descriptor: property возвращает эталон"] = '''
class Panel:
    @property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
'''

POSITIVE["descriptor: data descriptor __get__"] = '''
class Ref:
    def __get__(self, obj, owner=None):
        return _reference()


class Panel:
    value = Ref()


_panel = Panel()


def _observed():
    return _panel.value
'''

POSITIVE["descriptor: cached_property"] = '''
class Panel:
    @functools.cached_property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
'''

POSITIVE["descriptor: __getattr__ отдаёт эталон"] = '''
class Panel:
    def __getattr__(self, name):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.whatever
'''

POSITIVE["descriptor: staticmethod через класс"] = '''
class Panel:
    @staticmethod
    def value():
        return _reference()


def _observed():
    return Panel.value()
'''

POSITIVE["descriptor: property, наблюдение — сам объект"] = '''
class Panel:
    @property
    def value(self):
        return _reference()

    def __call__(self):
        return self.value


_observed = Panel()
'''

# --- класс: closures, глубина (тик 41) --------------------------------------

POSITIVE["closure: три уровня вложенности"] = '''
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_reference)
'''

POSITIVE["closure: значение через два уровня"] = '''
def _outer():
    v = _reference()

    def _mid():
        def _inner():
            return v
        return _inner()
    return _mid


_observed = _outer()
'''

POSITIVE["closure: ячейка через partial"] = '''
def _make(fn):
    return lambda: fn()


_observed = functools.partial(_make(_reference))
'''

POSITIVE["closure: эталон в замкнутом словаре"] = '''
def _make():
    box = {"v": _reference()}
    return lambda: box["v"]


_observed = _make()
'''

# ---------------------------------------------------------------------------
# НЕГАТИВНЫЙ СТРЕСС-КОРПУС: детектор обязан молчать
# ---------------------------------------------------------------------------

NEGATIVE: dict[str, str] = {}

NEGATIVE["тот же смысл, другой AST"] = '''
def _observed():
    total = 0.0
    for _ in range(12):
        total += math.sqrt(2.0)
    return total
'''

NEGATIVE["альфа-переименование локальных имён"] = '''
def _observed():
    qq = DATA
    with open(qq, encoding="utf-8") as zz:
        ww = zz.read().strip()
    return float(ww)
'''

NEGATIVE["перестановка независимых операций"] = '''
def _observed():
    b = 2.0
    a = _read_own()
    c = b * 0.0
    return a + c
'''

NEGATIVE["равные захваченные значения, разные id"] = '''
def _make(v):
    def inner():
        return v
    return inner


_a = _make(float("17.5"))
_b = _make(float("17.5"))
_observed = _b
'''

NEGATIVE["closure: захвачена своя функция чтения"] = '''
def _make(fn):
    return lambda: fn()


_observed = _make(_read_own)
'''

NEGATIVE["сериализация вызываемого объекта"] = '''
class Meter:
    def __init__(self, state):
        self.state = state

    def __call__(self):
        return _read_own() + 0.0 * pickle.loads(self.state)


# Экземпляр класса из модуля, не зарегистрированного в sys.modules, не
# сериализуется в принципе, поэтому через pickle проходит СОСТОЯНИЕ объекта.
# Ловушка сохраняется: путь значения идёт через сериализацию, но источник свой.
_observed = Meter(pickle.dumps(3.0))
'''

NEGATIVE["default arg: путь к файлу, не эталон"] = '''
def _observed(path=DATA):
    with open(path, encoding="utf-8") as fh:
        return float(fh.read().strip())
'''

NEGATIVE["bound method со своим чтением"] = '''
class Panel:
    def value(self):
        return _read_own()


_observed = Panel().value
'''

NEGATIVE["callable object со своим источником"] = '''
class Meter:
    def __call__(self):
        return _read_own()


_observed = Meter()
'''

NEGATIVE["decorator поверх честного наблюдения"] = '''
def _passthrough(fn):
    @functools.wraps(fn)
    def wrapper():
        return fn()
    return wrapper


@_passthrough
def _observed():
    return _read_own()
'''

NEGATIVE["partial над честным разборщиком"] = '''
def _parse(path):
    with open(path, encoding="utf-8") as fh:
        return float(fh.read().strip())


_observed = functools.partial(_parse, DATA)
'''

NEGATIVE["globals: кэш наполняет само наблюдение"] = '''
CACHE = {}


def _observed():
    if "v" not in CACHE:
        CACHE["v"] = _read_own()
    return CACHE["v"]
'''

NEGATIVE["lambda со своим чтением"] = '''
_observed = lambda: _read_own()
'''

NEGATIVE["общий парсер, эталон недостижим"] = '''
def _shared(x):
    return float(x)


def _observed():
    with open(DATA, encoding="utf-8") as fh:
        return _shared(fh.read().strip())
'''

NEGATIVE["наблюдение принимает вход"] = '''
def _observed(raw="17.5"):
    return float(raw)
'''

NEGATIVE["вызвал эталон, вернул своё"] = '''
def _observed():
    _reference()
    return _read_own()
'''


# --- негативные пары к дескрипторам и глубоким замыканиям (тик 41) ----------

NEGATIVE["descriptor: property со своим чтением"] = '''
class Panel:
    @property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEGATIVE["descriptor: __get__ со своим источником"] = '''
class Own:
    def __get__(self, obj, owner=None):
        return _read_own()


class Panel:
    value = Own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEGATIVE["descriptor: cached_property со своим чтением"] = '''
class Panel:
    @functools.cached_property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEGATIVE["descriptor: __getattr__ отдаёт своё"] = '''
class Panel:
    def __getattr__(self, name):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.whatever
'''

NEGATIVE["descriptor: staticmethod со своим чтением"] = '''
class Panel:
    @staticmethod
    def value():
        return _read_own()


def _observed():
    return Panel.value()
'''

NEGATIVE["closure: три уровня над своим чтением"] = '''
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_read_own)
'''

NEGATIVE["closure: замкнутый словарь со своим значением"] = '''
def _make():
    box = {"v": _read_own()}
    return lambda: box["v"]


_observed = _make()
'''

# ---------------------------------------------------------------------------
# ОБЪЯВЛЕННЫЕ ОГРАНИЧЕНИЯ: конструкция не разбирается, и это заявлено
# ---------------------------------------------------------------------------

# Такая фикстура ОБЯЗАНА давать False. Если она начала ловиться — охват вырос, и
# объявление устарело; это расхождение так же обязано быть замечено, как и
# пропуск. Молча выбрасывать непокрытую конструкцию из корпуса запрещено.

LIMITATIONS: dict[str, str] = {}

LIMITATIONS["descriptor: имя атрибута вычисляется в рантайме"] = '''
class Slot:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, obj, owner=None):
        return getattr(obj, self.name)


class Panel:
    value = Slot()

    def __init__(self):
        self._value = _reference()


_panel = Panel()


def _observed():
    return _panel.value
'''

# ---------------------------------------------------------------------------
# загрузка фикстур
# ---------------------------------------------------------------------------

_TMP: str | None = None


def _workdir() -> str:
    global _TMP
    if _TMP is None:
        _TMP = tempfile.mkdtemp(prefix="goldsieve-fixtures-")
        with open(os.path.join(_TMP, "data.txt"), "w", encoding="utf-8") as fh:
            fh.write(DATA_TEXT)
    return _TMP


def load(name: str, src: str):
    """Загрузить фикстуру НАСТОЯЩИМ module_from_spec без sys.modules.

    Возвращает (модуль, наблюдение, эталон). Такой путь загрузки выбран не для
    удобства: именно он вскрыл тихий отказ детектора в лупе 12, поэтому
    калибровка обязана идти через него, а не через exec в текущем модуле.
    """
    work = _workdir()
    os.environ["GOLDSIEVE_FIXTURE_DATA"] = os.path.join(work, "data.txt")
    safe = "".join(c if c.isalnum() else "_" for c in name)
    path = os.path.join(work, "fx_%s.py" % safe)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_PREAMBLE + src)
    spec = importlib.util.spec_from_file_location("fx_%s" % safe, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)          # в sys.modules НЕ регистрируем
    return module, module._observed, module._reference


def classes() -> dict[str, list[str]]:
    """Разбивка положительного корпуса по классам конструкций."""
    out: dict[str, list[str]] = {}
    for name in POSITIVE:
        head = name.split(":")[0] if ":" in name else "прямые формы"
        out.setdefault(head, []).append(name)
    return out


# Причина по каждому объявленному ограничению: печатается в coverage manifest.
LIMITATION_REASONS: dict[str, str] = {
    "descriptor: имя атрибута вычисляется в рантайме":
        "имя читаемого поля собирается в __set_name__ и известно только в "
        "рантайме; статический разбор AST не может связать getattr(obj, "
        "self.name) с полем _value, заполненным в __init__",
}
