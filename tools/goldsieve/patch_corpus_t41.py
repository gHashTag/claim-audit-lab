"""Внесение фикстур тика 41: дескрипторы и глубокие замыкания.

Приказ тика 41, пункт 4: глубина вместо ширины. Класс выбран приказом —
closures + descriptors, и доводится до позитивных, негативных и мутационных
доказательств, прежде чем брать exec/eval, генераторы и корутины.

Отдельно вводится банк LIMITATIONS: конструкция, которую детектор НЕ разбирает,
и это ЗАЯВЛЕНО. Такая фикстура обязана давать False; если она внезапно начала
ловиться — это тоже расхождение с объявленным охватом, и его надо заметить, а не
радоваться. Молча удалять непокрытую конструкцию из корпуса запрещено: именно
так и появляется «молчаливое исключение», из-за которого тик 39 отчитался о
покрытии, которого не было.
"""

PATH = "goldsieve/identity_corpus.py"
src = open(PATH, encoding="utf-8").read()

NEW_POSITIVE = '''
# --- класс: descriptors (тик 41) -------------------------------------------

# Измерение до правки тика 41: дескрипторы 0/7. Причина — значение приходит
# через доступ к атрибуту объекта, а этот путь не разбирался вовсе.

POSITIVE["descriptor: property возвращает эталон"] = \'\'\'
class Panel:
    @property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

POSITIVE["descriptor: data descriptor __get__"] = \'\'\'
class Ref:
    def __get__(self, obj, owner=None):
        return _reference()


class Panel:
    value = Ref()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

POSITIVE["descriptor: cached_property"] = \'\'\'
class Panel:
    @functools.cached_property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

POSITIVE["descriptor: __getattr__ отдаёт эталон"] = \'\'\'
class Panel:
    def __getattr__(self, name):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.whatever
\'\'\'

POSITIVE["descriptor: staticmethod через класс"] = \'\'\'
class Panel:
    @staticmethod
    def value():
        return _reference()


def _observed():
    return Panel.value()
\'\'\'

POSITIVE["descriptor: property, наблюдение — сам объект"] = \'\'\'
class Panel:
    @property
    def value(self):
        return _reference()

    def __call__(self):
        return self.value


_observed = Panel()
\'\'\'

# --- класс: closures, глубина (тик 41) --------------------------------------

POSITIVE["closure: три уровня вложенности"] = \'\'\'
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_reference)
\'\'\'

POSITIVE["closure: значение через два уровня"] = \'\'\'
def _outer():
    v = _reference()

    def _mid():
        def _inner():
            return v
        return _inner()
    return _mid


_observed = _outer()
\'\'\'

POSITIVE["closure: ячейка через partial"] = \'\'\'
def _make(fn):
    return lambda: fn()


_observed = functools.partial(_make(_reference))
\'\'\'

POSITIVE["closure: эталон в замкнутом словаре"] = \'\'\'
def _make():
    box = {"v": _reference()}
    return lambda: box["v"]


_observed = _make()
\'\'\'

'''

anchor = '''# ---------------------------------------------------------------------------
# НЕГАТИВНЫЙ СТРЕСС-КОРПУС: детектор обязан молчать
# ---------------------------------------------------------------------------'''
assert anchor in src
src = src.replace(anchor, NEW_POSITIVE + anchor, 1)

NEW_NEGATIVE = '''
# --- негативные пары к дескрипторам и глубоким замыканиям (тик 41) ----------

NEGATIVE["descriptor: property со своим чтением"] = \'\'\'
class Panel:
    @property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

NEGATIVE["descriptor: __get__ со своим источником"] = \'\'\'
class Own:
    def __get__(self, obj, owner=None):
        return _read_own()


class Panel:
    value = Own()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

NEGATIVE["descriptor: cached_property со своим чтением"] = \'\'\'
class Panel:
    @functools.cached_property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
\'\'\'

NEGATIVE["descriptor: __getattr__ отдаёт своё"] = \'\'\'
class Panel:
    def __getattr__(self, name):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.whatever
\'\'\'

NEGATIVE["descriptor: staticmethod со своим чтением"] = \'\'\'
class Panel:
    @staticmethod
    def value():
        return _read_own()


def _observed():
    return Panel.value()
\'\'\'

NEGATIVE["closure: три уровня над своим чтением"] = \'\'\'
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_read_own)
\'\'\'

NEGATIVE["closure: замкнутый словарь со своим значением"] = \'\'\'
def _make():
    box = {"v": _read_own()}
    return lambda: box["v"]


_observed = _make()
\'\'\'

# ---------------------------------------------------------------------------
# ОБЪЯВЛЕННЫЕ ОГРАНИЧЕНИЯ: конструкция не разбирается, и это заявлено
# ---------------------------------------------------------------------------

# Такая фикстура ОБЯЗАНА давать False. Если она начала ловиться — охват вырос, и
# объявление устарело; это расхождение так же обязано быть замечено, как и
# пропуск. Молча выбрасывать непокрытую конструкцию из корпуса запрещено.

LIMITATIONS: dict[str, str] = {}

LIMITATIONS["descriptor: имя атрибута вычисляется в рантайме"] = \'\'\'
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
\'\'\'

'''

anchor2 = '''# ---------------------------------------------------------------------------
# загрузка фикстур
# ---------------------------------------------------------------------------'''
assert anchor2 in src
src = src.replace(anchor2, NEW_NEGATIVE + anchor2, 1)

# причина ограничения — машинночитаемо, рядом с фикстурой
src += '''

# Причина по каждому объявленному ограничению: печатается в coverage manifest.
LIMITATION_REASONS: dict[str, str] = {
    "descriptor: имя атрибута вычисляется в рантайме":
        "имя читаемого поля собирается в __set_name__ и известно только в "
        "рантайме; статический разбор AST не может связать getattr(obj, "
        "self.name) с полем _value, заполненным в __init__",
}
'''

open(PATH, "w", encoding="utf-8").write(src)
print("фикстуры внесены")
