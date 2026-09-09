# Доклад тика 374 — непрерывный аудит «золотое сито»

## (1) что исправлено в инструменте

Добавлен `json_numeric_type_guard.py`: сторож читает девять машинных JSON-отчётов и отвергает строковое, булево или нефинитное значение в явно числовом поле; научный вердикт он не выносит. Самопроверка дала 3 пройдено и 0 провалено, реальный проход — 9 файлов со статусом `verified-in-scope`. Новый сторож включён в `ci_gate.sh` и описан в `coverage_manifest.yaml`.

**чем этот тик отличается от предыдущего:** предыдущие тики проверяли конечность чисел и повторяющиеся ключи; этот тик добавил отдельный контроль типа числового поля, чтобы строка вроде `"std": "0.4"` не зависела от неявного преобразования потребителя.

Ресурсный сторож завершился кодом 0. Обязательный и финальный гейты завершились кодом 0: 119 `ok`, 2 штатных пропуска без `numpy/pyyaml` в CPython 3.12, 0 провалов. Инкрементальный регресс выбрал 2 кейса, пропустил 114, получил 2 совпадения, 0 изменений ситом, 0 изменений корпусом и 0 несопоставленных; ротация — сегмент 7/8, кэш — 175 попаданий и 0 пересчётов. `tick_aborted_timeout` не увеличивался.

ОС-матрица запуска 33999056048 завершилась шестью из шести заданиями `completed/success`: Ubuntu, macOS и Windows с CPython 3.12 и 3.13. Проверено на указанных версиях CPython, а не объявлено платформонезависимым результатом.

## (2) что установлено о zeta/GUE

Нового научного вердикта о zeta/GUE не установлено. Сторож происхождения прочитал наблюдаемое из `/home/user/workspace/corpus/trinity/data/zeta/zeta_gue_analysis_results.md` и дал `verified-in-scope`. Сторож рецепта прочитал тот же файл и нашёл 11 воспроизводящих вариантов для напечатанного значения 0,4009; однозначность рецепта остаётся `not-evaluated`.

В прочитанном документе 0,4009 сопоставляется с приближением Вигнера—сюрмиса 0,4220; точное значение Fredholm GUE в машинном артефакте — 0,4242576222. Это не превращает наблюдение в подтверждение универсальности GUE: перенос на другие окна и среды, причинность внешних сверок и высотная зависимость остаются недоказанными. Однородность сохранена: `STANDARD_RANGES=20412`, `ACTUAL_RANGES=123201`; каталог = 83 формата; аппаратное объединение около 49–55/83; кремний = «отправлен на изготовление».

Запрет повторов соблюдён: сторож новизны не признал повтором проверяемый набор внешних целей. Сторож внешних целей проверил 22 записи и оставил 3 исторические сверки как `ПУСТО` из-за отсутствующего или несвязанного прочитанного наблюдаемого; это не находка и не ОПРОВЕРГНУТОЕ.

## (3) что осталось недоказанным

BBLM остаётся машинным `ВОПРОСОМ`: протокол заполнен 7 из 8 элементов, а `coefficient_rederivation` остаётся с кодом `analytic_source_absent`. Аналитический источник коэффициентов с формулами и номерами уравнений статьи не предъявлен; проверка типов JSON и разделение формы с масштабом его не заменяют.

Общий `M_eff` остаётся `not-evaluated` для архивов без единого совместного значения. Предпосылка независимости, отдельные χ² и dof и шаровая арифметика Arb остаются `not-evaluated` там, где отсутствуют проверяемые входы; неподдерживаемые случаи маркируются `unsupported`. Криптографическая подпись и область её действия остаются `not-evaluated`, поскольку машинная подпись журнала не предъявлена.

Исторические доклады с неполной машинной сутью остаются `not-evaluated`; молчание проверки не считается покрытием. За пределами завершённой ОС-матрицы переносимость сохраняет `platform-unverified`.

## (4) какие артефакты и тесты это подтверждают

Новый сторож и его чувствительность: `/home/user/workspace/goldsieve/json_numeric_type_guard.py`, `/home/user/workspace/goldsieve/json_numeric_type_guard.json`, `/home/user/workspace/goldsieve/tick374-json-numeric-type-selftest.txt`, `/home/user/workspace/goldsieve/tick374-json-numeric-type-scan.txt`, `/home/user/workspace/goldsieve/ci_gate.sh`, `/home/user/workspace/goldsieve/coverage_manifest.yaml`.

Ресурс, гейт, регресс и снимки: `/home/user/workspace/goldsieve/tick374-gate-final.log`, `/home/user/workspace/goldsieve/tick374-gate-final.rc`, `/home/user/workspace/goldsieve/tick374-regression.log`, `/home/user/workspace/goldsieve/tick374-regression.rc`, `/home/user/workspace/goldsieve/tick374-baseline-snapshot.txt`, `/home/user/workspace/goldsieve/tick374-tri-snapshot.txt`, `/home/user/workspace/cron_tracking/20fee222/tick374-progress-substance.json`; `progress_guard.py --check` дал подпись `7f66b16eb1d92c94`, итог `СОДЕРЖАТЕЛЬНЫЙ`.

ОС-матрица подтверждена `/home/user/workspace/goldsieve/tick374-os-trigger.txt`, `/home/user/workspace/goldsieve/tick374-os-runs.json`, `/home/user/workspace/goldsieve/tick374-os-matrix.json` и запуском `https://github.com/gHashTag/claim-audit-lab/actions/runs/33999056048`; итог — 6 заданий `success`.

Zeta, BBLM и ограничения подтверждены `/home/user/workspace/goldsieve/tick374-zeta-provenance.txt`, `/home/user/workspace/goldsieve/tick374-zeta-ambiguity.txt`, `/home/user/workspace/goldsieve/tick374-bblm-protocol.txt`, `/home/user/workspace/goldsieve/tick374-bblm-analytic-source.txt`, `/home/user/workspace/goldsieve/tick374-bblm-accounting.txt`, `/home/user/workspace/goldsieve/tick374-target-novelty.txt`, `/home/user/workspace/goldsieve/tick374-external-target.txt` и `/home/user/workspace/goldsieve/tick374-reference-tautology.txt`.
