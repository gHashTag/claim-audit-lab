# Доклад тика 398 — непрерывный аудит «золотое сито»

## (1) что исправлено в инструменте

Добавлен `bblm_coefficient_rederivation_guard.py` — точечный машинный сторож открытого элемента `coefficient_rederivation`. Он читает `/home/user/workspace/goldsieve/bblm_protocol.json`, требует ровно один элемент и сохраняет отсутствие аналитического источника с формулой и номером уравнения как статус `not-evaluated` с кодом вопроса `analytic_source_absent`. Противоречивое объявление и дублирование элемента получают `unsupported`; это не научная находка и не новая внешняя константа. Самопроверка дала 4/4.

Новый сторож подключён в `/home/user/workspace/goldsieve/ci_gate.sh` и описан в `/home/user/workspace/goldsieve/coverage_manifest.yaml`. Обязательный гейт завершён кодом 0: 147 успешных проверок, 2 штатных пропуска в CPython 3.12 без `numpy/pyyaml`, 0 провалов. Инкрементальный регресс выбрал 7 записей, пропустил 163 неизменившиеся записи, получил 7 совпадений, 0 изменений ситом, 0 изменений корпусом и 0 несопоставленных; кэш дал 175 попаданий и 0 пересчётов. Полный регресс не запускался.

**чем этот тик отличается от предыдущего:** после проверки контракта `skip_reasons` в тике 397 этот тик вынес именно долг аналитического вывода коэффициентов BBLM в отдельный машинный вопрос с кодом `analytic_source_absent`, вместо повторения внешней цели или выдачи `ВОПРОС` за результат. Окна опроса не увеличивались, `os_matrix_audit.py` не изменялся, долг повторов внешних целей остался 7 группами.

ОС-матрица GitHub Actions `34066644619` завершила 6 из 6 заданий успешно: Ubuntu, Windows и macOS с CPython 3.12 и 3.13. Запуск выполнен на SHA `1309ccf6c8e59803083cf16d51a16da1ba434d24`, до локальной правки тика; поэтому переносимость нового сторожа имеет статус `platform-unverified`, а не `verified-in-scope`. Инструмент проверен на указанных версиях CPython, но это не утверждение о платформенной универсальности. Постоянные параметры сохранены: `STANDARD_RANGES=20412`, `ACTUAL_RANGES=123201`; каталог = 83 формата; аппаратное объединение около 49–55/83; кремний = отправлен на изготовление.

## (2) что установлено о zeta/GUE

Нового научного вердикта о zeta/GUE не установлено. Наблюдаемое прочитано из `/home/user/workspace/corpus/trinity/data/zeta/zeta_gue_analysis_results.md`: 100000 нулей, стандартное отклонение зазоров около 0,4009, 95-й процентиль 1,7189 и 99-й процентиль 2,0680. В том же файле 0,4220 названо приближением Вигнера—сюрмиса, а вычисленный точный эталон GUE указан как 0,4242576222440628. Паспорт происхождения наблюдаемого получил `verified-in-scope`; неоднозначность рецепта остаётся `not-evaluated` при 11 воспроизводящих вариантах.

Новые внешние константы в этом тике не брались. Сторож новизны целей подтвердил 7 групп повторов при признанном долге 7; сторож внешних целей вновь показал 3 исторические вырожденные сверки со статусом ПУСТО, которые не выдавались за находки. Это подтверждает контроль инструмента, а не универсальность GUE.

## (3) что осталось недоказанным

Независимый аналитический вывод коэффициентов BBLM остаётся `not-evaluated` с кодом `analytic_source_absent`: файл с формулой и номером уравнения не предъявлен. Общий `M_eff` остаётся `not-evaluated` для 12 архивов. Предпосылка независимости остаётся `not-evaluated` для 132 из 133 кейсов и `unsupported` для одного. Смысл `χ²/dof` остаётся `not-evaluated`, потому что корпус предъявляет готовое отношение без отдельного числа степеней свободы. Шаровая арифметика Arb остаётся `not-evaluated`: прочитаны 3 файла, интервалов 0.

Криптографическая подпись журнала и область её действия остаются `not-evaluated`: подписей 0. Исторический аудит формы классифицирует 63 доклада: 28 имеют `verified-in-scope`, 35 остаются `not-evaluated`; старые записи не восстанавливались. Однозначность рецепта zeta, независимость наблюдаемого и эталонного путей, научная универсальность GUE и переносимость новой правки после SHA до правки за пределы указанной ОС-матрицы не доказаны. Молчание проверки не считается покрытием; сохранены статусы `verified-in-scope`, `not-evaluated`, `unsupported` и `platform-unverified`.

## (4) какие артефакты и тесты это подтверждают

Новая правка и её результат: `/home/user/workspace/goldsieve/bblm_coefficient_rederivation_guard.py`, `/home/user/workspace/goldsieve/bblm_coefficient_rederivation_guard.json`, `/home/user/workspace/goldsieve/ci_gate.sh`, `/home/user/workspace/goldsieve/coverage_manifest.yaml`. Самопроверка нового сторожа — 4/4; машинный вопрос записан с `analytic_source_absent` и путём `/home/user/workspace/goldsieve/bblm_protocol.json`.

Финальный гейт подтверждён `/home/user/workspace/cron_tracking/20fee222/tick398-gate-final.log` и `/home/user/workspace/cron_tracking/20fee222/tick398-gate-final.rc`, код 0, итог 147/2/0. Регресс подтверждён `/home/user/workspace/cron_tracking/20fee222/tick398-regression.log` и `/home/user/workspace/cron_tracking/20fee222/tick398-regression.rc`. ОС-матрица подтверждена `/home/user/workspace/cron_tracking/20fee222/tick398-os-matrix.json`, новизна целей — `/home/user/workspace/cron_tracking/20fee222/tick398-target-novelty.txt`, внешние сверки — `/home/user/workspace/cron_tracking/20fee222/tick398-external-target.txt`.

Снимки подтверждены `/home/user/workspace/cron_tracking/20fee222/tick398-baseline-snapshot.txt` и `/home/user/workspace/cron_tracking/20fee222/tick398-tri-snapshot.txt`. Содержательная проверка тика прошла кодом 0 и записана в `/home/user/workspace/cron_tracking/20fee222/tick398-progress-check.txt` и `/home/user/workspace/cron_tracking/20fee222/tick398-progress-record.txt`; синхронность после коммита `fa3b403` подтверждена кодом 0 в `/home/user/workspace/cron_tracking/20fee222/tick398-repo-sync-guard.txt`. Правка отправлена только в ветвь `tools/goldsieve-v3-2026-08-13`.
