"""Пробник: как детектор ведёт себя на дескрипторах и глубоких замыканиях.

Скрипт разведочный: он НЕ часть гейта. Задача — до внесения фикстур в корпус
измерить, какие конструкции ловятся, а какие дают тихий отказ.
"""

from __future__ import annotations

import traceback

from goldsieve import identity_corpus as C
from goldsieve.identity import derives_from

POS: dict[str, str] = {}
NEG: dict[str, str] = {}

# --- дескрипторы -----------------------------------------------------------

POS["descriptor: property возвращает эталон"] = '''
class Panel:
    @property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
'''

POS["descriptor: data descriptor __get__"] = '''
class Ref:
    def __get__(self, obj, owner=None):
        return _reference()


class Panel:
    value = Ref()


_panel = Panel()


def _observed():
    return _panel.value
'''

POS["descriptor: __set_name__ и хранение эталона"] = '''
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

POS["descriptor: cached_property"] = '''
class Panel:
    @functools.cached_property
    def value(self):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.value
'''

POS["descriptor: __getattr__ отдаёт эталон"] = '''
class Panel:
    def __getattr__(self, name):
        return _reference()


_panel = Panel()


def _observed():
    return _panel.whatever
'''

POS["descriptor: staticmethod через класс"] = '''
class Panel:
    @staticmethod
    def value():
        return _reference()


def _observed():
    return Panel.value()
'''

POS["descriptor: property, наблюдение — сам объект"] = '''
class Panel:
    @property
    def value(self):
        return _reference()

    def __call__(self):
        return self.value


_observed = Panel()
'''

# --- глубокие замыкания ----------------------------------------------------

POS["closure: три уровня вложенности"] = '''
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_reference)
'''

POS["closure: значение через два уровня"] = '''
def _outer():
    v = _reference()

    def _mid():
        def _inner():
            return v
        return _inner()
    return _mid


_observed = _outer()
'''

POS["closure: ячейка через partial"] = '''
def _make(fn):
    return lambda: fn()


_observed = functools.partial(_make(_reference))
'''

POS["closure: эталон в замкнутом словаре"] = '''
def _make():
    box = {"v": _reference()}
    return lambda: box["v"]


_observed = _make()
'''

# --- негативные пары -------------------------------------------------------

NEG["descriptor: property со своим чтением"] = '''
class Panel:
    @property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEG["descriptor: __get__ со своим источником"] = '''
class Own:
    def __get__(self, obj, owner=None):
        return _read_own()


class Panel:
    value = Own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEG["descriptor: cached_property со своим чтением"] = '''
class Panel:
    @functools.cached_property
    def value(self):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.value
'''

NEG["descriptor: __getattr__ отдаёт своё"] = '''
class Panel:
    def __getattr__(self, name):
        return _read_own()


_panel = Panel()


def _observed():
    return _panel.whatever
'''

NEG["closure: три уровня над своим чтением"] = '''
def _l1(fn):
    def _l2():
        def _l3():
            return fn()
        return _l3()
    return _l2


_observed = _l1(_read_own)
'''

NEG["closure: замкнутый словарь со своим значением"] = '''
def _make():
    box = {"v": _read_own()}
    return lambda: box["v"]


_observed = _make()
'''


def main() -> None:
    for title, bank, want in (("ПОЛОЖИТЕЛЬНЫЕ (ожидается срабатывание)", POS, True),
                              ("НЕГАТИВНЫЕ (ожидается молчание)", NEG, False)):
        print("=== " + title)
        for name, src in bank.items():
            try:
                _m, obs, ref = C.load(name, src)
                same, chain = derives_from(obs, ref)
            except Exception:
                last = traceback.format_exc().strip().splitlines()[-1]
                print("  ОШИБКА   %-46s %s" % (name, last[:70]))
                continue
            mark = "ok     " if same is want else "ПРОБЕЛ "
            print("  %s %-46s same=%-5s %s" % (mark, name, same, (chain or "")[:60]))
        print()


if __name__ == "__main__":
    main()
