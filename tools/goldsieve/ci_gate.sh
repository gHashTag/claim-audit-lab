#!/usr/bin/env bash
# Гейт слияния для золотого сита.
#
# Слияние блокируется при любом из событий:
#   * провал самопроверки каскада;
#   * пропуск подтверждённого вырождения на корпусе фикстур;
#   * ложное срабатывание на негативном стресс-корпусе;
#   * необнаруженная внесённая поломка (мутационная проверка);
#   * ложное срабатывание на реальных кейсах реестра (калибровка);
#   * отклонение от baseline без reason-code;
#   * расхождение coverage manifest с фактическим составом корпуса (тик 41);
#   * провал самопроверки трёхуровневых статусов и линтера «подтверждено» (тик 41);
#   * провал самопроверки pre-filter (тик 41);
#   * нарушение целостности заморозки v12 (тик 41).
#
# Матрица интерпретаторов задаётся переменной GOLDSIEVE_PYTHONS.
set -u
cd "$(dirname "$0")" || exit 2

PYTHONS=${GOLDSIEVE_PYTHONS:-"$(command -v python3) /usr/bin/python3.14 /usr/local/bin/python3.12"}
FAIL=0
declare -a FAILED=()

step() {  # step <имя> <интерпретатор> <аргументы...>
    local name="$1"; shift
    local py="$1"; shift
    local log
    log=$(mktemp)
    if timeout 3600 "$py" "$@" >"$log" 2>&1; then
        echo "  ok      $name  [$($py -V 2>&1)]"
    else
        echo "  ПРОВАЛ  $name  [$($py -V 2>&1)]"
        tail -12 "$log" | sed 's/^/          /'
        FAIL=1
        FAILED+=("$name")
    fi
    rm -f "$log"
}

echo "=== матрица интерпретаторов: $PYTHONS"
for PY in $PYTHONS; do
    [ -x "$PY" ] || { echo "  ПРОПУСК интерпретатор недоступен: $PY"; continue; }
    echo "--- $($PY -V 2>&1)"
    # Пропуск обязан быть ОБЪЯВЛЕН: интерпретатор без numpy/pyyaml физически не
    # может прогнать каскад и калибровку, но разбор конструкций (корпус фикстур
    # и мутации) от этих пакетов не зависит и обязан пройти всюду. Молчаливо
    # выкидывать такой интерпретатор из матрицы нельзя: тогда матрица перестаёт
    # что-либо проверять.
    if "$PY" -c "import numpy, yaml" >/dev/null 2>&1; then
        FULL=1
    else
        FULL=0
        echo "  ПРОПУСК самопроверка каскада: нет numpy/pyyaml в этом интерпретаторе"
        echo "  ПРОПУСК калибровка на реестре: нет numpy/pyyaml в этом интерпретаторе"
    fi
    [ "$FULL" = 1 ] && step "самопроверка каскада"  "$PY" -m goldsieve.selftest
    step "корпус фикстур"            "$PY" measure_identity.py
    step "мутационная проверка"      "$PY" mutation_identity.py
    # Трёхуровневые статусы, линтер и счётчики не зависят от numpy/pyyaml
    # и обязаны проходить на всей матрице интерпретаторов.
    step "трёхуровневые статусы"    "$PY" -m goldsieve.scope
    # Тик 42: разбор AST от numpy/pyyaml не зависит и обязан проходить всюду.
    step "машинный след анализатора" "$PY" -m goldsieve.proof
    step "межмодульный граф"        "$PY" -m goldsieve.modgraph
    step "независимость разметки"   "$PY" independence.py
    step "счётчики тика"             "$PY" tick_counters.py selftest
    [ "$FULL" = 1 ] && step "калибровка на реестре" "$PY" calibrate_identity.py
done

echo "--- сверка с baseline"
BASE_PY=""
for PY in $PYTHONS; do
    if [ -x "$PY" ] && "$PY" -c "import numpy, yaml" >/dev/null 2>&1; then
        BASE_PY="$PY"; break
    fi
done
if [ -z "$BASE_PY" ]; then
    echo "  ПРОВАЛ  гейт baseline: нет интерпретатора с numpy/pyyaml"
    FAIL=1; FAILED+=("гейт baseline: нет пригодного интерпретатора")
else
    step "гейт baseline" "$BASE_PY" baseline.py check
    # Заморозка v12: режим frozen НЕ падает при отличиях от замороженной
    # версии (работа идёт, отличия ожидаются), но падает при НАРУШЕНИИ
    # ЦЕЛОСТНОСТИ самой записи: переписать историю задним числом нельзя.
    step "целостность заморозки v12" "$BASE_PY" baseline.py frozen
    step "coverage manifest"          "$BASE_PY" coverage_manifest.py
    step "pre-filter Golden Chain"    "$BASE_PY" -m goldsieve.prefilter
    # Execution-proof: пустой граф при непустом кейсе — авария, а не тихое
    # отрицательное заключение. Маршрут реальный (подпроцесс CLI), поэтому
    # шаг требует полного окружения.
    step "execution-proof на маршруте CLI" "$BASE_PY" execution_proof.py
    # tri — оболочка тика. Она пишет в ведомость и читает счётчики,
    # поэтому её тихий отказ стоит дороже всего: пропадают именно записи
    # опыта. Проверка идёт на временных файлах, ведомость не трогается.
    step "tri: самопроверка оболочки" "$BASE_PY" tri selftest
fi

echo
if [ "$FAIL" -ne 0 ]; then
    echo "ГЕЙТ ЗАКРЫТ: слияние блокировано (${#FAILED[@]} провалов)"
    for n in "${FAILED[@]}"; do echo "  - $n"; done
    exit 1
fi
echo "ГЕЙТ ОТКРЫТ: слияние разрешено"
