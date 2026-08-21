# -*- coding: utf-8 -*-
"""Пакет «золотое сито».

Тик 171: размещённые исполнители Windows (py3.12 и py3.13) показали настоящий
дефект переносимости — поток вывода там открывается в кодировке cp1252, а весь
вывод инструмента русский, поэтому первая же строка «самопроверка сита:» роняла
прогон с UnicodeEncodeError ещё до первой проверки. Дефект не был бы найден на
Linux никогда. Кодировка потоков задаётся здесь, один раз для всего пакета.
"""
import sys as _sys

for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, ValueError, OSError):
        pass   # поток подменён или не поддерживает reconfigure — не мешаем
