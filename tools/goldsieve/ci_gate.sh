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
#   * нарушение целостности заморозки v12 (тик 41);
#   * подпись «exact GUE» на числе 0,4220 — это std Wigner surmise (пункт 1
#     приказа 2026-08-18), вместе с измеренной чувствительностью этого запрета.
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
    step "чувствительность предпосылки независимости" "$PY" independence_assumption_guard.py --selftest
    step "счётчики тика"             "$PY" tick_counters.py selftest
    [ "$FULL" = 1 ] && step "калибровка на реестре" "$PY" calibrate_identity.py
    [ "$FULL" = 1 ] && step "калибровка сит С4 С5 С16" "$PY" calibrate_sieves.py
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
    step "чанкинг cover"              "$BASE_PY" -m goldsieve.cover_chunks
    # Пункт 3 приказа: два последовательных not-evaluated обязаны
    # машинно дать очередь или platform-unverified; verified-in-scope после
    # такого порога запрещён до успешного прогона.
    step "SLA матрицы ОС"             "$BASE_PY" -m goldsieve.platform_sla pending/os-matrix.yaml
    step "pre-filter Golden Chain"    "$BASE_PY" -m goldsieve.prefilter
    # Execution-proof: пустой граф при непустом кейсе — авария, а не тихое
    # отрицательное заключение. Маршрут реальный (подпроцесс CLI), поэтому
    # шаг требует полного окружения.
    step "execution-proof на маршруте CLI" "$BASE_PY" execution_proof.py
    step "кэш отпечатков регресса"        "$BASE_PY" regression_cache_guard.py --selftest
    step "чувствительность неоднозначного ключа реестра" "$BASE_PY" registry_identity_guard.py --selftest
    step "однозначность ключа реестра регресса" "$BASE_PY" registry_identity_guard.py
    # tri — оболочка тика. Она пишет в ведомость и читает счётчики,
    # поэтому её тихий отказ стоит дороже всего: пропадают именно записи
    # опыта. Проверка идёт на временных файлах, ведомость не трогается.
    step "tri: самопроверка оболочки" "$BASE_PY" tri selftest
    # Тик 43. Журнал вызовов: без него отчёт ссылается на артефакты,
    # происхождение которых ничем не подтверждено.
    step "журнал вызовов (run_id)" "$BASE_PY" -m goldsieve.runlog
    # Отдельный контракт парности: хеш-цепочка сохраняет порядок, но не
    # ловит оборванную или продублированную запись одного запуска.
    step "парность записей журнала" "$BASE_PY" runlog_record_guard.py
    step "чувствительность парности записей журнала" "$BASE_PY" runlog_record_guard.py --selftest
    step "связь начала и итога записи журнала" "$BASE_PY" runlog_record_guard.py --identity-selftest
    step "отсутствующий журнал явно not-evaluated" "$BASE_PY" runlog_record_guard_remote_selftest.py
    # Новый риск тика 338: строка artifacts не должна уводить происхождение
    # за пределы разрешённых корней или скрывать относительный путь.
    step "граница путей артефактов" "$BASE_PY" artifact_path_guard.py
    step "чувствительность границы путей артефактов" "$BASE_PY" artifact_path_guard.py --selftest
    # Тик 44. Хеш-цепочка: журнал без связи записей можно править
    # построчно, и ничто этого не обнаружит.
    step "хеш-цепочка журнала" "$BASE_PY" -m goldsieve.chain
    # Хеш-цепочка не является подписью и не доказывает автора записи.
    # Отдельный сторож обязан сохранить этот предел машинно наблюдаемым.
    step "аудит криптографической подписи журнала" "$BASE_PY" journal_signature_guard.py
    step "чувствительность аудита подписи журнала" "$BASE_PY" journal_signature_guard.py --selftest
    # Тик 363: новая неоднозначность — даже предъявленная подпись может
    # покрывать только одну запись. Не объявляем весь журнал покрытым без
    # явной области действия для каждой записи.
    step "область действия подписи журнала" "$BASE_PY" journal_signature_scope_guard.py
    step "чувствительность области действия подписи" "$BASE_PY" journal_signature_scope_guard.py --selftest
    # Цепочка НАСТОЯЩЕГО журнала этой песочницы, а не только
    # игрушечных файлов самопроверки: проверка на синтетике молчит о
    # том, цел ли журнал, на который ссылается отчёт.
    step "цепочка живого журнала" "$BASE_PY" tri log verify
    # Тик 48. Порог при множественных испытаниях двумя независимыми
    # путями (double+scipy против 50 знаков mpmath), границы m=1..1e9,
    # монотонность и разделение Šidák с Бонферрони.
    step "порог множественности: два пути" "$BASE_PY" -m goldsieve.sidak
    # Семантическая предпосылка: unknown или молчание о независимости
    # испытаний НЕ имеют права давать безусловное ПОДТВЕРЖДЕНО.
    step "предпосылка независимости" "$BASE_PY" -m goldsieve.preconditions
    # Отдельный риск: отсутствие поля tests_independent в старом кейсе нельзя
    # принять за независимость. Сторож оставляет такие записи not-evaluated.
    step "аудит предпосылки независимости" "$BASE_PY" independence_assumption_guard.py --scan
    # Несколько целей одного запуска могут делить общий ансамбль попыток.
    # Отсутствие совместного M_eff — машинный not-evaluated, а не скрытое
    # суммирование отдельных оценок.
    step "чувствительность общего M_eff" "$BASE_PY" meff_common_guard.py --selftest
    step "аудит общего M_eff" "$BASE_PY" meff_common_guard.py --scan
    # Контракт χ²/dof: повреждённая таблица не должна молча стать числом.
    # Это проверка входов реконструкции, а не научный вердикт по zeta/GUE.
    step "контракт χ²/dof"          "$BASE_PY" chi2_dof_guard.py --selftest
    # Повторное построение сводки χ²/dof из прочитанной таблицы корпуса:
    # контракт формы без независимого пересчёта не закрывает этот долг.
    step "повторное построение χ²/dof" "$BASE_PY" chi2_dof_rederivation.py --selftest
    # Отдельный риск: готовое отношение χ²/dof не предъявляет автоматически
    # число степеней свободы. Не выдумываем знаменатель и оставляем
    # not-evaluated, пока корпус не даст исходные поля раздельно.
    step "смысл χ²/dof и dof"       "$BASE_PY" chi2_dof_semantics_guard.py --selftest
    # Самопроверка выше ловит поломки классификатора, но не подтверждает,
    # что текущая таблица корпуса действительно прочитана. Отдельный запуск
    # сохраняет наблюдаемый путь и честно оставляет готовое отношение
    # not-evaluated без выдумывания dof.
    step "смысл χ²/dof и dof на корпусе" "$BASE_PY" chi2_dof_semantics_guard.py
    # Отдельный риск: точечное число или слово «интервал» не являются
    # шаровой арифметикой Arb. Требуем прочитанные конечные границы и явно
    # понижаем отсутствие таких данных до not-evaluated.
    step "чувствительность шаровой арифметики Arb" "$BASE_PY" arb_interval_guard.py --selftest
    step "аудит шаровой арифметики Arb" "$BASE_PY" arb_interval_guard.py
    # Проверяемый снимок: SHA-256 входов, отчётов и журналов.
    step "проверяемый снимок" "$BASE_PY" snapshot_manifest.py selftest
    # Контракт архива: предел записей, порядок, детерминизм сборки.
    step "контракт архива скила" "$BASE_PY" archive_contract.py selftest
    step "сборка архива скила: список исключений" "$BASE_PY" build_skill.py selftest
    # Измеритель: проверяется его статистика, а не запускается само
    # измерение: двадцать повторов в гейте стояли бы минуты.
    step "статистика измерителя" "$BASE_PY" bench.py --selftest
    # Тик 44. Измеритель стоимости цепочки: проверяется его статистика
    # и правило «разность меньше разброса — не измерено».
    step "статистика стоимости цепочки" "$BASE_PY" chain_overhead.py --selftest
    # Интеграционные тесты оболочки: фон, замок, падение, обрыв
    # журнала, tick abort. Самопроверка tri зовёт функции напрямую и
    # этих сценариев не видит вовсе.
    step "интеграционные тесты оболочки" "$BASE_PY" tri_integration_test.py
    # Пункт 1 приказа 2026-08-18. Запрет метки exact_gue на числе 0,4220:
    # сначала ИЗМЕРЕННАЯ чувствительность на фикстурах (включая мутанта),
    # затем сам запрет на корпусе и артефактах. Молчание проверки — не покрытие.
    step "чувствительность запрета exact_gue" "$BASE_PY" gue_label_guard.py --selftest
    step "запрет метки exact_gue на 0,4220" "$BASE_PY" gue_label_guard.py
    # Тик 91: скрипты шагов гейта обязаны входить в отпечаток снимка,
    # иначе шаг можно ослабить, не тронув files_digest.
    step "чувствительность охвата гейта" "$BASE_PY" baseline.py gate-coverage --selftest
    step "охват скриптов гейта снимком" "$BASE_PY" baseline.py gate-coverage
    # Пункты 2-4 приказа 2026-08-18.
    step "классификатор токенов срыва"   "$BASE_PY" aborted_audit.py --selftest
    step "очередь межплатформенных прогонов" "$BASE_PY" replay_queue.py --selftest
    # Тик 97: согласованность САМОГО файла очереди: временная причина
    # не имеет права лежать в failed, дублей по id быть не должно.
    step "согласованность очереди повторов" "$BASE_PY" replay_queue.py audit
    step "протокол BBLM: перечень недостающего" "$BASE_PY" bblm_protocol.py --selftest
    step "параметры высоты BBLM"          "$BASE_PY" bblm_height.py --selftest
    step "элементы протокола BBLM"        "$BASE_PY" bblm_elements.py --selftest
    step "чувствительность сторожа внешних целей" "$BASE_PY" external_target_guard.py --selftest
    step "разметка внешних сверок"        "$BASE_PY" external_target_guard.py
    step "чувствительность типа неопределённости" "$BASE_PY" external_uncertainty_type_guard.py --selftest
    step "тип неопределённости внешних сверок" "$BASE_PY" external_uncertainty_type_guard.py
    # Тик 365: новая семантическая граница — одинаковые числа нельзя
    # сопоставлять без проверенной согласованности единиц.
    step "чувствительность согласованности единиц" "$BASE_PY" unit_consistency_guard.py --selftest
    step "согласованность единиц внешних сверок" "$BASE_PY" unit_consistency_guard.py
    # Независимость происхождения: разные имена могут быть одним файлом
    # через относительный путь или символическую ссылку.
    step "чувствительность сторожа происхождения" "$BASE_PY" provenance_guard.py --selftest
    step "происхождение сверки зета" "$BASE_PY" provenance_guard.py --check \
        /home/user/workspace/corpus/trinity/data/zeta/zeta_bin_analysis_update.md \
        /home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt
    # Разные пути ещё не исключают копию observed под именем reference.
    # Сравнение содержимого делает эту тавтологию отдельным машинным риском;
    # различие файлов не объявляется доказательством независимости алгоритмов.
    step "контроль тавтологии observed/reference" "$BASE_PY" reference_tautology_guard.py
    # Наблюдаемое число в паспорте zeta обязано быть прочитано из указанного
    # файла корпуса, а хеши обоих входов должны относиться к той же записи.
    step "чувствительность происхождения паспорта zeta" "$BASE_PY" zeta_passport_provenance_guard.py --selftest
    step "происхождение наблюдаемого паспорта zeta" "$BASE_PY" zeta_passport_provenance_guard.py
    # Новый риск тика 349: несколько законных рецептов могут воспроизвести
    # одно наблюдаемое число. Такое совпадение оставляем not-evaluated, пока
    # рецепт не идентифицирован однозначно; это не находка о GUE.
    step "чувствительность неоднозначности рецепта zeta" "$BASE_PY" zeta_recipe_ambiguity_guard.py --selftest
    step "неоднозначность рецепта zeta" "$BASE_PY" zeta_recipe_ambiguity_guard.py
    # Контракт доклада: форма из четырёх обязательных разделов и отдельная
    # машинная суть. Неполный или оборванный отчёт не является покрытием.
    step "чувствительность контракта доклада" "$BASE_PY" report_contract_guard.py --selftest
    step "контракт последнего доклада" "$BASE_PY" report_contract_guard.py
    step "исторический аудит формы докладов" "$BASE_PY" report_contract_guard.py --history /home/user/workspace/cron_tracking/8dff7aa3
    # Машинная суть — единственный вход запрета холостого тика. Проверяем её
    # размерность и типы отдельно, чтобы испорченное поле не стало молчанием.
    step "чувствительность формы машинной сути" "$BASE_PY" audit_substance_guard.py --selftest
    step "чувствительность сторожа диска" "$BASE_PY" disk_guard.py --selftest
    step "ресурс песочницы и утечка фикстур" "$BASE_PY" disk_guard.py --clean
    step "чувствительность учёта элементов BBLM" "$BASE_PY" bblm_accounting.py --selftest
    step "учёт BBLM: один источник истины"  "$BASE_PY" bblm_accounting.py
    step "чувствительность сторожа формы и масштаба BBLM" "$BASE_PY" bblm_shape_scale_guard.py --selftest
    step "аудит формы и масштаба BBLM" "$BASE_PY" bblm_shape_scale_guard.py
    # Тик 371: стандартный json.loads допускает NaN/Infinity вне стандарта
    # JSON. Такие значения могут скрыть нечисловой результат в машинном
    # отчёте; строгий разбор обязан остановить этот путь.
    step "конечность чисел машинных отчётов" "$BASE_PY" numeric_domain_guard.py
    step "чувствительность конечности чисел" "$BASE_PY" numeric_domain_guard.py --selftest
    # Тик 374: числовое поле, записанное строкой, не должно зависеть от
    # неявного преобразования потребителя машинного отчёта.
    step "типы числовых полей машинных отчётов" "$BASE_PY" json_numeric_type_guard.py
    step "чувствительность типов числовых полей" "$BASE_PY" json_numeric_type_guard.py --selftest
    # Тик 372: обычный json.loads молча оставляет последнее значение
    # повторяющегося ключа. Строгий обработчик пар ключей обязан отвергать
    # неоднозначный машинный отчёт, не смешивая это с научным вердиктом.
    step "однозначность ключей машинных отчётов" "$BASE_PY" json_duplicate_key_guard.py
    step "чувствительность однозначности ключей" "$BASE_PY" json_duplicate_key_guard.py --selftest
    step "чувствительность линтера переносимости" "$BASE_PY" portability_lint.py --selftest
    step "переносимость: кодировки и python3" "$BASE_PY" portability_lint.py
    # Проверка нового риска: успешный общий run не должен скрывать удалённое,
    # незавершённое, дублированное или подменённое задание матрицы.
    step "полнота ОС-матрицы"           "$BASE_PY" os_matrix_audit.py --selftest
    # Ранее неподвижная точка была измерена только для GUE-guard. Эта
    # матрица проверяет, что отчёт не меняет решение остальных проверок, а
    # мутация роли audit_log обнаруживается.
    step "неподвижная точка проверок"     "$BASE_PY" fixed_point_audit.py
    # Тик 261: две предпосылки, которые аудит о себе не проверял. Первая —
    # «сделанное сохранено»: тики 216-260 девять суток отчитывались об
    # исправлениях без единого коммита, os_matrix_audit.py вовсе не был в
    # репозитории. Вторая — «тик содержателен»: прежний запрет холостого тика
    # сравнивал текст доклада, а суть повторялась (измерено: 24 разобранных
    # доклада, 7 различных сутей, 23 доклада в группах повторов).
    step "чувствительность сторожа синхронности" "$BASE_PY" repo_sync_guard.py --selftest
    step "чувствительность сторожа содержательности" "$BASE_PY" progress_guard.py --selftest
    step "повторы сути в исторических докладах" "$BASE_PY" progress_guard.py --history /home/user/workspace/cron_tracking/20fee222
    step "чувствительность сторожа новизны цели" "$BASE_PY" target_novelty_guard.py --selftest
    step "повторы внешних целей против признанного долга" "$BASE_PY" target_novelty_guard.py --gate
fi

echo
if [ "$FAIL" -ne 0 ]; then
    echo "ГЕЙТ ЗАКРЫТ: слияние блокировано (${#FAILED[@]} провалов)"
    for n in "${FAILED[@]}"; do echo "  - $n"; done
    exit 1
fi
echo "ГЕЙТ ОТКРЫТ: слияние разрешено"
