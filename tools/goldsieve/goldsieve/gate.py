"""Гейт полезности цели: пускать в каскад только информативные утверждения.

Зачем модуль появился. Тики 18-35 показали устойчивую картину: формулы
семейства n*3^k*pi^m*phi^p*e^q против ГРУБО измеренных величин (космология
Planck, PDG-электрослабое, CKM) дают один и тот же вердикт ПУСТО по сито С16,
потому что ожидаемых случайных попаданий от 2 до 3179. Каждая следующая такая
запись не добавляет знания: реестр растёт, информация в нём — нет. Текстовое
правило «не накапливай новые ПУСТО того же типа» было записано в задание крона
и ПРОИГНОРИРОВАНО тиком 35. Значит правило обязано стать инвариантом кода и
тестов, а не абзацем инструкции.

Чего этот модуль НЕ делает. Он не отбраковывает цель по одной лишь величине
внешней погрешности. Такой фильтр запретил бы законные классы работы: проверку
точного тождества, поиск вычислительной ошибки, проверку внутренней
согласованности корпуса. Вместо порога по погрешности считается ЧЕТЫРЕ
независимых основания полезности, и достаточно ЛЮБОГО одного:

  U_precision      внешняя погрешность мала относительно ОЖИДАЕМОГО ЭФФЕКТА
                   (а не относительно шага решётки семейства);
  U_novelty        класс целей ещё не исчерпан в реестре;
  U_discrimination предсказание различает минимум ДВЕ содержательные модели,
                   а не только «формула против шума»;
  U_independence   независимый источник данных, другой observable либо иной
                   режим параметров.

  U = max(U_precision, U_novelty, U_discrimination, U_independence) >= U_min

Отклонённая цель НЕ исчезает бесследно: она получает статус
SKIPPED_LOW_INFORMATION с причинами по каждой оси, хешем цели и ссылкой на уже
существующий репрезентативный кейс своего класса. Молчаливое исчезновение цели —
та же болезнь, что молчаливый пропуск сита, которую ловит сито С13.

Оси НЕ сливаются в один скаляр усреднением: взвешивание четырёх оснований было
бы назначенной рукой конвенцией, ровно как отменённый в лупе 5 размах декад D.
Берётся максимум — «достаточно одного законного основания», и это решение
объявляется, попадая в отпечаток гейта.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

ADMIT = "ADMIT"
SKIPPED = "SKIPPED_LOW_INFORMATION"

# Цели, для которых гейт неприменим по построению: у них информативность не
# измеряется внешней погрешностью и не исчерпывается семейством.
EXEMPT_PURPOSES = {
    "exact_identity",         # точное тождество: проверяется арифметикой, не опытом
    "arithmetic_check",       # достаточность разрядности вычисления (сито С19)
    "internal_consistency",   # согласованность корпуса с самим собой
    "tool_selftest",          # проверка самого инструмента
}

DEFAULT_U_MIN = 1.0
DEFAULT_REQUIRED_GAIN = 3.0     # во столько раз обязана вырасти точность,
                                # чтобы повторить исчерпанный класс целей


@dataclass
class Target:
    """Паспорт цели аудита. Поля намеренно машинные, без свободного текста.

    claim_family          класс утверждения, напр. external_cosmology
    observable            что именно измеряется, напр. omega_lambda
    measurement_source    источник измерения, напр. planck_2018
    uncertainty_type      statistical | systematic | statistical_plus_systematic
    expected_effect_sigma ожидаемый эффект в сигмах ВНЕШНЕГО измерения
    resolution_sigma      разрешение проверки в тех же сигмах
    novelty_key           ключ класса целей: external_cosmology:rough_target:v1
    information_class     low | medium | high (авторская оценка, не вердикт)
    purpose               назначение проверки; из EXEMPT_PURPOSES снимает гейт
    models                перечень содержательных моделей, которые цель различает
    independent_of        чем цель независима: {"source":..,"observable":..,
                          "regime":..} относительно репрезентативного кейса
    precision_gain        во сколько раз точность выше, чем у репрезентативного
                          кейса класса; задаётся ЗАРАНЕЕ, до прогона
    """

    name: str
    claim_family: str = ""
    observable: str = ""
    measurement_source: str = ""
    uncertainty_type: str = ""
    expected_effect_sigma: Optional[float] = None
    resolution_sigma: Optional[float] = None
    novelty_key: str = ""
    information_class: str = ""
    purpose: str = "external_prediction"
    models: tuple = ()
    independent_of: dict = field(default_factory=dict)
    precision_gain: Optional[float] = None
    # Семантическая предпосылка (тик 48): true | false | unknown |
    # not-declared. Входит в отпечаток паспорта именно потому, что от неё
    # зависит вердикт: подменить её после прогона и не изменить отпечаток было б
    # способом тихо вернуть безусловное ПОДТВЕРЖДЕНО.
    tests_independent: str = "not-declared"

    def hash(self) -> str:
        d = asdict(self)
        d["models"] = list(self.models)
        return hashlib.sha256(
            json.dumps(d, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()[:16]


@dataclass
class Decision:
    status: str
    u: float
    axes: dict
    reasons: list
    target_hash: str
    representative: str = ""

    @property
    def admitted(self) -> bool:
        return self.status == ADMIT

    def line(self) -> str:
        head = "ADMIT   " if self.admitted else "SKIPPED "
        return "%s U=%.2f (%s) %s%s" % (
            head, self.u,
            ", ".join("%s %.2f" % (k, v) for k, v in self.axes.items()),
            "; ".join(self.reasons),
            "" if not self.representative
            else " | репрезентативный кейс: %s" % self.representative,
        )


class FamilyBudget:
    """Бюджет на класс целей: один репрезентативный отрицательный кейс на ключ.

    Повтор класса допускается только при объявленном ЗАРАНЕЕ основании: другой
    источник данных, кратное улучшение точности, другой observable или новый
    различающий механизм. Ключ хранит имя первого кейса, чтобы отклонённая цель
    получала ссылку, а не пустоту.
    """

    def __init__(self, spent: Optional[dict] = None,
                 required_gain: float = DEFAULT_REQUIRED_GAIN):
        # novelty_key -> {"case":..., "source":..., "observable":...,
        #                 "models": [...]}
        self.spent = dict(spent or {})
        self.required_gain = float(required_gain)

    def spend(self, t: Target, case: str) -> None:
        if not t.novelty_key:
            return
        self.spent.setdefault(t.novelty_key, {
            "case": case,
            "source": t.measurement_source,
            "observable": t.observable,
            "models": list(t.models),
        })

    def representative(self, t: Target) -> str:
        rec = self.spent.get(t.novelty_key)
        return rec["case"] if rec else ""

    def novelty(self, t: Target) -> tuple:
        """(U_novelty, причина). 1.0 — класс не исчерпан или повтор оправдан."""
        if not t.novelty_key:
            return 1.0, "ключ новизны не задан: класс не отслеживается"
        rec = self.spent.get(t.novelty_key)
        if rec is None:
            return 1.0, "класс целей %s ещё не представлен в реестре" % t.novelty_key
        if t.measurement_source and t.measurement_source != rec.get("source"):
            return 1.0, ("другой источник измерения: %s против %s"
                         % (t.measurement_source, rec.get("source")))
        if t.observable and t.observable != rec.get("observable"):
            return 1.0, ("другой observable: %s против %s"
                         % (t.observable, rec.get("observable")))
        new_models = [m for m in t.models if m not in rec.get("models", [])]
        if new_models:
            return 1.0, "новый различающий механизм: %s" % ", ".join(new_models)
        if t.precision_gain is not None and t.precision_gain >= self.required_gain:
            return 1.0, ("точность выше в %.1fx при требуемом %.1fx"
                         % (t.precision_gain, self.required_gain))
        return 0.0, ("класс %s исчерпан кейсом %s: тот же источник, тот же "
                     "observable, прироста точности нет"
                     % (t.novelty_key, rec["case"]))


def precision_axis(t: Target) -> tuple:
    """U_precision = ожидаемый эффект / разрешение проверки, в сигмах.

    Ключевое отличие от отменённого фильтра: сравнивается ЭФФЕКТ с РАЗРЕШЕНИЕМ, а
    не погрешность с шагом решётки. Грубое измерение остаётся полезным, если
    ожидаемый эффект тоже крупный.
    """
    if t.expected_effect_sigma is None or t.resolution_sigma is None:
        return 0.0, "ожидаемый эффект или разрешение не объявлены"
    if t.resolution_sigma <= 0:
        return 0.0, "разрешение объявлено нулевым: отношение не определено"
    u = float(t.expected_effect_sigma) / float(t.resolution_sigma)
    if u >= 1.0:
        return u, ("эффект %.2f сигма против разрешения %.2f сигма: различим"
                   % (t.expected_effect_sigma, t.resolution_sigma))
    return u, ("эффект %.2f сигма ниже разрешения %.2f сигма: различить нельзя"
               % (t.expected_effect_sigma, t.resolution_sigma))


def discrimination_axis(t: Target) -> tuple:
    """Различает ли цель минимум две содержательные модели.

    «Формула против шума» содержательной парой не считается: шум — не модель, и
    против него семейство формул побеждает переборoм. Модель «noise» и
    «random» из перечня исключаются намеренно.
    """
    real = [m for m in t.models if m not in ("noise", "random", "шум")]
    if len(real) >= 2:
        return 1.0, "различает модели: %s" % ", ".join(real)
    if len(real) == 1:
        return 0.0, ("одна содержательная модель (%s): против шума перебор "
                     "выигрывает без содержания" % real[0])
    return 0.0, "содержательных моделей не объявлено"


def independence_axis(t: Target) -> tuple:
    keys = [k for k, v in (t.independent_of or {}).items() if v]
    if keys:
        return 1.0, "независимость по: %s" % ", ".join(sorted(keys))
    return 0.0, "независимого источника, observable или режима не объявлено"


def evaluate(t: Target, budget: Optional[FamilyBudget] = None,
             u_min: float = DEFAULT_U_MIN) -> Decision:
    """Решение гейта с обязательным бюджетом повторяющегося класса."""
    budget = budget or FamilyBudget()
    if t.purpose in EXEMPT_PURPOSES:
        return Decision(ADMIT, float("inf"),
                        {"exempt": float("inf")},
                        ["назначение %s: гейт неприменим, информативность не "
                         "измеряется внешней погрешностью" % t.purpose],
                        t.hash())
    up, rp = precision_axis(t)
    un, rn = budget.novelty(t)
    ud, rd = discrimination_axis(t)
    ui, ri = independence_axis(t)
    axes = {"precision": up, "novelty": un, "discrimination": ud,
            "independence": ui}
    u = max(axes.values())
    reasons = [rp, rn, rd, ri]
    # Для уже потраченного паспортизированного класса другие сильные оси не
    # превращают повтор в новую информацию. Разрешение возможно только если
    # сама ось новизны дала основание: иной источник, observable, механизм или
    # объявленный прирост точности.
    if t.novelty_key and un < u_min and up < u_min:
        return Decision(SKIPPED, u, axes, reasons, t.hash(),
                        budget.representative(t))
    if u >= u_min:
        return Decision(ADMIT, u, axes, reasons, t.hash(),
                        budget.representative(t))
    return Decision(SKIPPED, u, axes, reasons, t.hash(),
                    budget.representative(t))


def fingerprint(u_min: float, budget: FamilyBudget) -> str:
    """Отпечаток настроек гейта.

    Порог, требуемый прирост точности и множество исчерпанных ключей входят в
    отпечаток: подкрутить любой из них после того, как результат стал известен,
    незаметно нельзя — отпечаток изменится и baselines потребуют обновления.
    """
    payload = {
        "u_min": float(u_min),
        "required_gain": float(budget.required_gain),
        "novelty_keys": sorted(budget.spent),
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]


# --------------------------------------------------------------------------
# самопроверка модуля: пять обязательных случаев + подставки
# --------------------------------------------------------------------------

def _rough_cosmology_target(**kw) -> Target:
    """Грубо измеренная космологическая цель — типовой источник ПУСТО."""
    base = dict(
        name="формула для Omega_Lambda",
        claim_family="external_cosmology",
        observable="omega_lambda",
        measurement_source="planck_2018",
        uncertainty_type="statistical_plus_systematic",
        expected_effect_sigma=0.3,
        resolution_sigma=1.0,
        novelty_key="external_cosmology:rough_target:v1",
        information_class="low",
        purpose="external_prediction",
        models=("formula", "noise"),
    )
    base.update(kw)
    return Target(**base)


def selftest() -> int:
    fail = 0

    spent = {"external_cosmology:rough_target:v1": {
        "case": "cases/sacred_omega_lambda.py",
        "source": "planck_2018",
        "observable": "omega_lambda",
        "models": ["formula", "noise"]}}

    # 1. Цель с большой неопределённостью блокируется и получает
    #    SKIPPED_LOW_INFORMATION со ссылкой на репрезентативный кейс.
    b = FamilyBudget(spent)
    d = evaluate(_rough_cosmology_target(), b)
    ok = (d.status == SKIPPED and d.u < 1.0
          and d.representative == "cases/sacred_omega_lambda.py")
    print("  %s грубая цель заблокирована: %s" % ("ok  " if ok else "FAIL", d.line()))
    fail += 0 if ok else 1

    # 2. Та же цель проходит при заранее заданном улучшении точности...
    d2 = evaluate(_rough_cosmology_target(precision_gain=5.0), b)
    ok = d2.admitted and d2.axes["novelty"] >= 1.0
    print("  %s прирост точности 5x открывает класс: %s"
          % ("ok  " if ok else "FAIL", d2.line()))
    fail += 0 if ok else 1

    #    ...и при новом независимом observable
    d3 = evaluate(_rough_cosmology_target(
        observable="omega_m",
        independent_of={"observable": "omega_m вместо omega_lambda"}), b)
    ok = d3.admitted
    print("  %s новый observable открывает класс: %s"
          % ("ok  " if ok else "FAIL", d3.line()))
    fail += 0 if ok else 1

    #    подставка: прирост точности НИЖЕ требуемого класс не открывает
    d4 = evaluate(_rough_cosmology_target(precision_gain=1.5), b)
    ok = not d4.admitted
    print("  %s подставка: прирост 1.5x при требуемом 3x не открывает класс"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    # 3. Три почти одинаковых утверждения одного семейства дают ОДИН
    #    репрезентативный кейс, а не три «ПУСТО».
    b2 = FamilyBudget()
    admitted = []
    for i, obs in enumerate(("n_s", "n_s", "n_s"), 1):
        t = _rough_cosmology_target(name="формула %d" % i, observable=obs,
                                    novelty_key="external_cosmology:n_s:v1")
        d = evaluate(t, b2)
        if d.admitted:
            admitted.append(t.name)
            b2.spend(t, "cases/case_%d.py" % i)
    ok = len(admitted) == 1
    print("  %s три однотипных цели дали %d допуск(а) вместо трёх"
          % ("ok  " if ok else "FAIL", len(admitted)))
    fail += 0 if ok else 1

    # 4. Гейт НЕ блокирует точное тождество, проверку арифметики и внутреннюю
    #    согласованность — даже когда все четыре оси нулевые.
    for purpose in ("exact_identity", "arithmetic_check", "internal_consistency"):
        t = Target(name="проверка %s" % purpose, purpose=purpose,
                   novelty_key="external_cosmology:rough_target:v1")
        d = evaluate(t, FamilyBudget(spent))
        ok = d.admitted
        print("  %s назначение %s не блокируется" % ("ok  " if ok else "FAIL", purpose))
        fail += 0 if ok else 1

    #    подставка: цель БЕЗ такого назначения и без оснований обязана падать,
    #    иначе «не блокируем полезное» превратилось бы в «не блокируем ничего»
    t = Target(name="пустая цель", purpose="external_prediction",
               novelty_key="external_cosmology:rough_target:v1")
    ok = not evaluate(t, FamilyBudget(spent)).admitted
    print("  %s подставка: цель без оснований блокируется" % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    # 5. Изменение порога, бюджета семейства или ключа новизны меняет отпечаток.
    f0 = fingerprint(DEFAULT_U_MIN, FamilyBudget(spent))
    f_u = fingerprint(0.5, FamilyBudget(spent))
    f_g = fingerprint(DEFAULT_U_MIN, FamilyBudget(spent, required_gain=10.0))
    more = dict(spent)
    more["external_cosmology:n_s:v1"] = {"case": "c.py", "source": "planck_2018",
                                         "observable": "n_s", "models": []}
    f_k = fingerprint(DEFAULT_U_MIN, FamilyBudget(more))
    ok = len({f0, f_u, f_g, f_k}) == 4
    print("  %s отпечаток гейта различает порог, бюджет и ключи: %s"
          % ("ok  " if ok else "FAIL", [f0, f_u, f_g, f_k]))
    fail += 0 if ok else 1

    #    и подставка: одинаковые настройки дают ОДИН отпечаток
    ok = fingerprint(DEFAULT_U_MIN, FamilyBudget(spent)) == f0
    print("  %s отпечаток устойчив при неизменных настройках" % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    # 6. Ось различения: «формула против шума» не считается парой моделей.
    d = evaluate(Target(name="только шум", models=("formula", "noise"),
                        novelty_key="x:y:v1"), FamilyBudget(
        {"x:y:v1": {"case": "z.py", "source": "", "observable": "",
                    "models": ["formula", "noise"]}}))
    ok = not d.admitted and d.axes["discrimination"] == 0.0
    print("  %s пара «формула против шума» различением не считается"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    d = evaluate(Target(name="две модели", models=("BBLM", "pure_GUE"),
                        novelty_key="x:y:v1"), FamilyBudget(
        {"x:y:v1": {"case": "z.py", "source": "", "observable": "",
                    "models": ["formula", "noise"]}}))
    ok = d.admitted and d.axes["discrimination"] == 1.0
    print("  %s две содержательные модели открывают ось различения"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    # 7. Ось точности: крупный ожидаемый эффект при грубом измерении полезен.
    d = evaluate(_rough_cosmology_target(expected_effect_sigma=8.0,
                                         resolution_sigma=1.0),
                 FamilyBudget(spent))
    ok = d.admitted and d.axes["precision"] >= 1.0
    print("  %s грубое измерение при эффекте 8 сигма допускается"
          % ("ok  " if ok else "FAIL"))
    fail += 0 if ok else 1

    return fail


if __name__ == "__main__":
    print("самопроверка гейта полезности:")
    raise SystemExit(1 if selftest() else 0)
