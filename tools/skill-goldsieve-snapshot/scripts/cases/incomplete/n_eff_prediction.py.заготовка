"""Задача: <одна строка, что проверяем>.

Правило: ни одно число не цитируется. reference — вычисляемый эталон,
wrong — заведомо неверный ответ той же формы, null_model — шум, который
конвейер обязан отвергнуть.
"""

from goldsieve.sieve import Claim


def reference():
    """Вычислить эталон из определений. Не возвращать литерал из документа."""
    raise NotImplementedError


CLAIMS = [
    Claim(
        name="<утверждение>",
        source="<файл:строка или документ>",
        stated=None,          # что заявлено
        reference=reference,  # вычисляемый эталон
        wrong=None,           # заведомо неверный ответ той же формы
        null_model=None,      # измерение на шуме
        tolerance=0.01,
    ),
]
