# Доклад тика 382 — непрерывный аудит «золотое сито»

## (1) что исправлено в инструменте

Добавлен `scope_provenance_guard.py`: запись реестра со статусом `verified-in-scope` теперь обязана разрешать каждый локальный фрагмент `source` именно внутри `/home/user/workspace/corpus/trinity`. Существующий файл рабочей копии, внешний URL и отсутствующий файл получают `not-evaluated`, а не доказательство корпусного наблюдения. Самопроверка нового сторожа дала 4 пройдено и 0 провалено; на реестре проверены 30 записей `verified-in-scope`, неподтверждённых источников нет. Проверка подключена к `ci_gate.sh` и объявлена в `coverage_manifest.yaml`.

**чем этот тик отличается от предыдущего:** тик 381 закрывал границу символических ссылок и переходов в локальном `source`; этот тик закрывает иной класс риска — безопасный путь ещё не доказывает, что источник принадлежит корпусу, а не рабочей копии инструмента. Обязательный и финальный гейт завершены кодом 0: 131 `ok`, 2 штатных пропуска без `numpy/pyyaml` на CPython 3.12, 0 провалов. Инкрементальный регресс завершён кодом 0: выбрано 1, пропущено 115, совпало 1, изменений ситом 0, изменений из-за корпуса 0, несопоставленных 0; ротация — сегмент 7/8, кэш — 175 попаданий и 0 пересчётов. `tick_aborted_timeout` не увеличивался.

ОС-матрица запуска 34019776669 завершилась шестью из шести заданий успешно на ветви `tools/goldsieve-v3-2026-08-13`, SHA запуска `99d69eb81a71db1cffff9ea46ebfff11bad6efcb`. Она проверяет состояние до локальной правки этого тика, поэтому переносимость именно нового `scope_provenance_guard.py` имеет статус `platform-unverified`; проверено на указанных версиях CPython, а не объявлено платформонезависимым.

## (2) что установлено о zeta/GUE

Нового научного вердикта о zeta/GUE не установлено. Проверка происхождения связала наблюдаемое `/home/user/workspace/corpus/trinity/data/zeta/zeta_bin_analysis_update.md` и эталон `/home/user/workspace/corpus/trinity/data/zeta/zeros_odlyzko_100k.txt`; результат `PASS`, файлы различны. Неоднозначность рецепта остаётся `not-evaluated`: сторож воспроизводит 11 вариантов для напечатанного значения 0,4009 из `/home/user/workspace/corpus/trinity/data/zeta/zeta_gue_analysis_results.md`.

В корпусном документе 0,4009 сопоставлено с приближением Вигнера—сюрмиса 0,4220, а машинный отчёт предъявляет точный эталон GUE 0,4242576222. Это не доказывает точность закона, универсальность GUE, перенос результата на другие окна и среды или причинность внешних сверок. Новые внешние константы и цели не добавлялись; долг повторов сохранён на 7 группах при признанном долге 7, три исторические записи остаются `ПУСТО`.

## (3) что осталось недоказанным

BBLM остаётся машинным `ВОПРОСОМ`: предъявлено 7 из 8 элементов, а `coefficient_rederivation` имеет код `analytic_source_absent`. Аналитический источник коэффициентов с формулой и номером уравнения статьи не предъявлен; это не находка и не опровержение.

Общий `M_eff` остаётся `not-evaluated` для 12 архивов; предпосылка независимости остаётся `not-evaluated` для 132 из 133 кейсов и `unsupported` для одного. Смысл χ²/dof остаётся `not-evaluated`, потому что число степеней свободы отдельно не предъявлено. Шаровая арифметика Arb остаётся `not-evaluated`: прочитаны 3 файла, интервалов 0. Криптографическая подпись журнала и область её действия остаются `not-evaluated`, подписей 0.

Не доказаны однозначность рецепта zeta, независимость наблюдаемого и эталонного вычислительных путей, переносимость новой локальной правки за пределы указанных версий CPython и научная универсальность GUE. Молчание проверки не считается покрытием; сохранены статусы `not-evaluated`, `unsupported` и `platform-unverified`. Границы протокола сохранены: `STANDARD_RANGES=20412`, `ACTUAL_RANGES=123201`; каталог = 83 формата; аппаратное объединение около 49–55/83; кремний = отправлен на изготовление.

## (4) какие артефакты и тесты это подтверждают

Новый сторож и его машинный результат: `/home/user/workspace/goldsieve/scope_provenance_guard.py`, `/home/user/workspace/goldsieve/scope_provenance_guard.json`, `/home/user/workspace/cron_tracking/20fee222/tick382-coverage-update.txt`; самопроверка — 4/0, проверка реестра — `verified-in-scope`, 30/30 записей. Финальный гейт подтверждён `/home/user/workspace/cron_tracking/20fee222/tick382-gate-final.log` и `/home/user/workspace/cron_tracking/20fee222/tick382-gate-final.rc`; итог — 131/2/0. Инкрементальный регресс подтверждён `/home/user/workspace/cron_tracking/20fee222/tick382-regression.log` и `/home/user/workspace/cron_tracking/20fee222/tick382-regression.rc`; итог — 1/115/0/0/0/0. Снимки подтверждены `/home/user/workspace/cron_tracking/20fee222/tick382-baseline-snapshot.txt` и `/home/user/workspace/cron_tracking/20fee222/tick382-tri-snapshot.txt`.

ОС-матрица подтверждена `/home/user/workspace/cron_tracking/20fee222/tick382-os-audit.json` и `/home/user/workspace/cron_tracking/20fee222/tick382-os-payload.json`: 6/6 заданий, `PASS`, 0 пропущено, 0 неуспешно; из-за SHA до локальной правки область нового сторожа `platform-unverified`. BBLM подтверждён `/home/user/workspace/cron_tracking/20fee222/tick382-bblm-protocol.txt`, `/home/user/workspace/cron_tracking/20fee222/tick382-bblm-accounting.txt` и `/home/user/workspace/goldsieve/bblm_protocol.json`. Запрет повторов и корпусная наблюдаемость подтверждены `/home/user/workspace/cron_tracking/20fee222/tick382-target-novelty.txt` и `/home/user/workspace/cron_tracking/20fee222/tick382-external-target.txt`; zeta — `/home/user/workspace/cron_tracking/20fee222/tick382-zeta-provenance.txt` и `/home/user/workspace/cron_tracking/20fee222/tick382-zeta-ambiguity.txt`. Машинная суть сохранена в `/home/user/workspace/cron_tracking/8dff7aa3/tick382-progress-substance.json`.
Синхронность подтверждена `/home/user/workspace/cron_tracking/20fee222/tick382-repo-sync-guard.txt`: 230 файлов совпадают с ветвью после коммита `8142b47`; отправка выполнена только в `tools/goldsieve-v3-2026-08-13`.
