#!/usr/bin/env python3
"""Калибровка открытых сит С4, С5 и С16.

Это отдельная проверка инструмента, а не вердикт корпуса. Фикстуры заранее
размечены по ожидаемому статусу, а мутационные цели заменяют различающий
ввод на совпадающий или на сломанный контроль. Реальный кейс загружается
через module_from_spec без регистрации в sys.modules — тот же маршрут, что
использует CLI.
"""

from __future__ import annotations

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from goldsieve.sieve import (  # noqa: E402
    Claim,
    FAIL,
    PASS,
    SKIP,
    VOID,
    sieve_discriminates,
    sieve_multiplicity,
    sieve_null_model,
)


def _проверить(имя: str, условие: bool) -> None:
    if not условие:
        raise AssertionError(имя)
    print("  ок  " + имя)


def _число(значение):
    return lambda: значение


def _загрузить_реальный_кейс():
    путь = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "cases",
        "golden_chain_v240_train_ppl_20260815.py",
    )
    имя = "калибровка_реальный_кейс"
    spec = importlib.util.spec_from_file_location(имя, путь)
    if spec is None or spec.loader is None:
        raise AssertionError("не создан spec реального кейса")
    модуль = importlib.util.module_from_spec(spec)
    # Явный guard: loader не должен получать кейс через sys.modules.
    _проверить("module_from_spec без регистрации в sys.modules", имя not in sys.modules)
    spec.loader.exec_module(модуль)
    _проверить("реальный кейс экспортирует CLAIMS", bool(getattr(модуль, "CLAIMS", None)))
    return модуль.CLAIMS[0]


def main() -> int:
    реальный = _загрузить_реальный_кейс()
    _проверить("С4 реально вызывается или объявленно пропускается",
               sieve_discriminates(реальный).status in (PASS, FAIL, VOID, SKIP))
    _проверить("С5 реально вызывается или объявленно пропускается",
               sieve_null_model(реальный).status in (PASS, FAIL, VOID, SKIP))
    # С16 может быть честно пропущено конкретным кейсом; важен сам guard
    # вызова и отсутствие молчаливой подмены результата.
    _проверить("С16 реально вызывается или объявленно пропускается",
               sieve_multiplicity(реальный).status in (PASS, FAIL, VOID, SKIP))

    # С4: живое различение, точная мутация в вырождение и граница допуска.
    def с4(неверный):
        return Claim(
            name="фикстура С4",
            reference=_число(10.0),
            wrong=_число(неверный),
            tolerance=0.01,
        )

    _проверить("С4 отклоняет дальнюю подставку",
               sieve_discriminates(с4(11.0)).status == PASS)
    _проверить("мутация С4 в точное совпадение даёт VOID",
               sieve_discriminates(с4(10.0)).status == VOID)
    _проверить("С4 фиксирует границу терпимости",
               sieve_discriminates(с4(10.1)).status == VOID)

    # С5: negative и positive controls имеют разные ожидаемые смыслы.
    def с5(контроль, вид, ожидание=None):
        return Claim(
            name="фикстура С5",
            reference=_число(10.0),
            null_model=_число(контроль),
            null_expect=ожидание,
            null_kind=вид,
            tolerance=0.01,
        )

    _проверить("С5 negative отличается от сигнала",
               sieve_null_model(с5(12.0, "negative")).status == PASS)
    _проверить("мутация С5 negative в сигнал даёт VOID",
               sieve_null_model(с5(10.0, "negative")).status == VOID)
    _проверить("С5 positive воспроизводит эталон",
               sieve_null_model(с5(10.0, "positive")).status == PASS)
    _проверить("мутация С5 positive в промах даёт FAIL",
               sieve_null_model(с5(12.0, "positive")).status == FAIL)

    # С16: проверяем три области решения, включая отдельную мутацию p_global.
    def с16(ожидаемые, глобальная, доля=None):
        данные = {"expected_hits": ожидаемые, "p_global": глобальная}
        if доля is not None:
            данные["fraction_random_targets_hit"] = доля
        return Claim(
            name="фикстура С16",
            multiplicity=lambda данные=данные: данные,
            alpha=0.05,
        )

    _проверить("С16 пропускает редкое попадание",
               sieve_multiplicity(с16(0.1, 0.03)).status == PASS)
    _проверить("мутация С16 в ожидаемое попадание даёт VOID",
               sieve_multiplicity(с16(1.0, 0.9)).status == VOID)
    _проверить("мутация С16 p_global выше alpha даёт FAIL",
               sieve_multiplicity(с16(0.2, 0.1)).status == FAIL)

    print("  итог калибровки: 15 пройдено, 0 провалено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
