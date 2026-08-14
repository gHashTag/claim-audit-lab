"""Измерение детектора тождественности на корпусе фикстур.

Печатает таблицу «класс конструкции -> поймано / пропущено» и метрики.
Код возврата 1, если есть хотя бы один пропуск или ложное срабатывание.
"""

from __future__ import annotations

import sys
import traceback

from goldsieve import identity_corpus as C
from goldsieve.identity import derives_from


def run() -> int:
    pos_hit, pos_miss, errors = [], [], []
    for name, src in C.POSITIVE.items():
        try:
            _mod, obs, ref = C.load(name, src)
            same, chain = derives_from(obs, ref)
        except Exception:
            errors.append((name, traceback.format_exc().strip().splitlines()[-1]))
            continue
        (pos_hit if same else pos_miss).append((name, chain))

    neg_ok, neg_fp = [], []
    for name, src in C.NEGATIVE.items():
        try:
            _mod, obs, ref = C.load(name, src)
            same, chain = derives_from(obs, ref)
        except Exception:
            errors.append((name, traceback.format_exc().strip().splitlines()[-1]))
            continue
        (neg_fp if same else neg_ok).append((name, chain))

    print("=== положительный корпус: %d фикстур" % len(C.POSITIVE))
    for cls, names in sorted(C.classes().items()):
        hit = sum(1 for n, _ in pos_hit if n in names)
        print("  %-28s %d/%d" % (cls, hit, len(names)))
    print()
    print("пропущено вырождений: %d" % len(pos_miss))
    for name, _ in pos_miss:
        print("  ПРОПУСК  " + name)
    print()
    print("=== негативный стресс-корпус: %d фикстур" % len(C.NEGATIVE))
    print("ложных срабатываний: %d" % len(neg_fp))
    for name, chain in neg_fp:
        print("  ЛОЖНОЕ   %s | %s" % (name, chain))
    if errors:
        print()
        print("ошибки загрузки: %d" % len(errors))
        for name, err in errors:
            print("  %s | %s" % (name, err[:100]))
    print()
    npos, nneg = len(C.POSITIVE), len(C.NEGATIVE)
    print("чувствительность: %.4f  [%d/%d]"
          % (len(pos_hit) / npos, len(pos_hit), npos))
    print("специфичность:    %.4f  [%d/%d]"
          % (len(neg_ok) / nneg, len(neg_ok), nneg))
    return 1 if (pos_miss or neg_fp or errors) else 0


if __name__ == "__main__":
    sys.exit(run())
