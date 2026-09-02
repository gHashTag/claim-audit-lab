#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тик 215: сторож вырожденных внешних сверок.

Тики 210 и 211 выдали «ровно одну новую содержательную цель» — точностные
сверки постоянной Ридберга (0 сигма) и массы электрона (0,0111 сигма). Разбор
артефактов показал, что ни одна из них НЕ проверяет корпус Trinity: и цель, и
наблюдаемое взяты из одного и того же внешнего источника NIST, поэтому сверка
прошла бы при любом значении корпусных формул. Разрешающая способность нулевая
— тот же дефект, который сито С4 ловит у подставок, но проявившийся на уровне
ВЫБОРА цели, а не внутри каскада.

Отличие честной цели видно машинно. Тик 212 сравнивал с CODATA величину,
ПРОЧИТАННУЮ из корпуса (`corpus/trinity/docs/research/FORMULAS_SUMMARY.md`), и
получил 45,98 сигмы — это измерение о корпусе. Тики 210 и 211 корпусного
наблюдаемого не имеют вовсе.

Правило: артефакт внешней сверки обязан содержать наблюдаемое ИЗ КОРПУСА, путь
к файлу корпуса и отпечаток SHA-256 этого файла. Несовпадение отпечатка делает
класс сверки вырожденным (ПУСТО): наблюдаемое нельзя связать с проверенным
содержимым. Фикстуры этой проверки — настоящие артефакты тиков 210–215 и
временная мутация содержимого при неизменном пути, поэтому чувствительность
измерена на истории и на отрицательной цели, а не на одном позитивном пути.
"""
from __future__ import annotations

import json
import hashlib
import ipaddress
import math
import re
import sys
import tempfile
from urllib.parse import urlsplit
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICKDIR = Path("/home/user/workspace/cron_tracking/20fee222")
OUT = HERE / "external_target_guard.json"
CORPUS_ROOT = Path("/home/user/workspace/corpus/trinity").resolve()

# Ключи, которыми артефакт заявляет корпусное наблюдаемое и его происхождение.
OBSERVED_KEYS = ("наблюдаемое_из_корпуса", "observed_from_corpus")
SOURCE_KEYS = ("источник_наблюдения", "observation_source")
SOURCE_DIGEST_KEYS = ("отпечаток_источника", "source_sha256")
CORPUS_MARK = "corpus/"
EXTERNAL_TARGET_KEYS = ("external_target", "внешняя_цель")
OBSERVATION_TEXT_KEYS = ("строка_наблюдения", "observation_text")
RESERVED_TARGET_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "example.invalid",
}
LOCAL_TARGET_HOSTS = {
    "localhost",
    "localhost.localdomain",
}


def _nonpublic_target_host(hostname: str) -> bool:
    """Отбрасывает локальные и непубличные адреса как внешнюю цель."""
    host = (hostname or "").strip().lower().rstrip(".")
    if host in LOCAL_TARGET_HOSTS:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _external_target_contract(art: dict) -> tuple[bool, list[str]]:
    """Проверяет обязательные поля внешнего измерения.

    Наблюдаемое из корпуса само по себе ещё не является внешней сверкой:
    без численного значения, неопределённости и URL внешний эталон нельзя
    воспроизвести или отличить от молчаливо удалённой цели. Поддерживаются
    обе исторические схемы имён полей.
    """
    key = next((k for k in EXTERNAL_TARGET_KEYS
                if isinstance(art.get(k), dict)), None)
    if key is None:
        return False, ["нет external_target/внешней_цели"]
    target = art[key]
    value_keys = ("value", "значение")
    uncertainty_keys = ("uncertainty", "неопределённость")
    url_keys = ("source", "url")
    missing = []
    value_key = next((k for k in value_keys
                      if k in target and target[k] not in ("", None)), None)
    uncertainty_key = next((k for k in uncertainty_keys
                            if k in target and target[k] not in ("", None)), None)
    if value_key is None:
        missing.append("нет value/значения внешней цели")
    if uncertainty_key is None:
        missing.append("нет uncertainty/неопределённости внешней цели")
    url_key = next((k for k in url_keys
                    if k in target and str(target[k]).strip()), None)
    if url_key is None:
        missing.append("нет URL внешней цели")
    else:
        parsed_url = urlsplit(str(target[url_key]).strip())
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            missing.append("URL внешней цели должен быть абсолютным HTTP(S)-адресом")
        elif parsed_url.username is not None or parsed_url.password is not None:
            missing.append("URL внешней цели содержит учётные данные, "
                           "а не публичный адрес источника")
        elif (parsed_url.hostname or "").lower() in RESERVED_TARGET_HOSTS:
            missing.append("URL внешней цели указывает на зарезервированный "
                           "пример, а не на источник измерения")
        elif _nonpublic_target_host(parsed_url.hostname or ""):
            missing.append("URL внешней цели указывает на локальный или "
                           "непубличный адрес, а не на внешний источник")
    # Наличие ключа не доказывает измерение: NaN, бесконечность, ноль и
    # отрицательная неопределённость превращают нормировку в фиктивную.
    # Разрешаем десятичные строки исторических артефактов, но требуем
    # конечное числовое значение и строго положительную неопределённость.
    if value_key is not None:
        try:
            value = float(target[value_key])
            if not math.isfinite(value):
                missing.append("значение внешней цели не является конечным числом")
        except (TypeError, ValueError):
            missing.append("значение внешней цели не является числом")
    if uncertainty_key is not None:
        try:
            uncertainty = float(target[uncertainty_key])
            if not math.isfinite(uncertainty) or uncertainty <= 0:
                missing.append("неопределённость внешней цели должна быть положительной")
        except (TypeError, ValueError):
            missing.append("неопределённость внешней цели не является числом")
    return not missing, missing


def _sha256(path: Path) -> str:
    """Возвращает отпечаток байтов файла, прочитанного как корпусное наблюдаемое."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _observed_text_present(art: dict, path: Path) -> bool:
    """Проверяет, что заявленное наблюдаемое действительно прочитано из файла.

    Путь и SHA-256 фиксируют, КАКОЙ файл был выбран, но сами по себе не
    связывают поле observed с его содержимым: произвольное число можно было
    бы приписать честному файлу. Для исторических артефактов без отдельной
    строки доказательства используется буквальное представление наблюдаемого;
    новые артефакты могут передавать точную строку таблицы явно.
    """
    observed_key = next((k for k in OBSERVED_KEYS if k in art), None)
    if observed_key is None:
        return False
    evidence_key = next((k for k in OBSERVATION_TEXT_KEYS if k in art), None)
    evidence = art.get(evidence_key) if evidence_key else art.get(observed_key)
    if evidence in (None, ""):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return str(evidence) in text


def _observed_value_present(art: dict) -> bool:
    """Связывает численное наблюдаемое с предъявленной строкой доказательства.

    Отпечаток файла и сама строка ещё не доказывают, что поле
    ``наблюдаемое_из_корпуса`` относится именно к этой строке: можно было
    оставить честную строку и подменить число в JSON.  Сопоставляем число с
    числовыми токенами строки, допуская запятые и завершающие нули.
    """
    observed_key = next((k for k in OBSERVED_KEYS if k in art), None)
    if observed_key is None:
        return False
    evidence_key = next((k for k in OBSERVATION_TEXT_KEYS if k in art), None)
    try:
        observed = float(art[observed_key])
    except (TypeError, ValueError):
        return False
    # Старые артефакты не имели отдельного поля строки наблюдения; для них
    # используется то же числовое поле, которое уже проверяется буквальным
    # поиском в файле корпуса.
    evidence = art[evidence_key] if evidence_key else art[observed_key]
    tokens = re.findall(
        r"(?<![A-Za-z])[-+]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?![A-Za-z])",
        str(evidence),
    )
    for token in tokens:
        try:
            if math.isclose(float(token.replace(",", ".")), observed,
                            rel_tol=1e-12, abs_tol=1e-12):
                return True
        except ValueError:
            continue
    return False


def classify(art: dict) -> dict:
    """Вырожденная сверка или измерение о корпусе — решение по составу полей."""
    observed = next((k for k in OBSERVED_KEYS if k in art), None)
    source = next((k for k in SOURCE_KEYS if k in art), None)
    src_val = str(art.get(source, "")) if source else ""
    # Одной подстроки «corpus/» недостаточно: путь вроде
    # /tmp/corpus/trinity/fake.md создаёт ложное происхождение. Принимается
    # только существующий файл внутри фактического корня корпуса.
    has_corpus_path = False
    resolved_source = None
    source_digest = None
    actual_digest = None
    if src_val:
        candidates = [Path(src_val)]
        if not Path(src_val).is_absolute():
            candidates.append(CORPUS_ROOT.parent.parent / src_val)
        for candidate in candidates:
            resolved = candidate.resolve()
            try:
                resolved.relative_to(CORPUS_ROOT)
            except ValueError:
                continue
            if resolved.is_file():
                has_corpus_path = True
                resolved_source = str(resolved)
                actual_digest = _sha256(resolved)
                break
    supplied_digest_key = next((k for k in SOURCE_DIGEST_KEYS if k in art), None)
    supplied_digest = str(art.get(supplied_digest_key, "")).lower() \
        if supplied_digest_key else ""
    target_ok, target_reasons = _external_target_contract(art)
    observed_in_source = (
        has_corpus_path and resolved_source is not None
        and _observed_text_present(art, Path(resolved_source))
    )
    observed_matches_evidence = _observed_value_present(art)
    if (observed and has_corpus_path and supplied_digest == actual_digest
            and observed_in_source and observed_matches_evidence and target_ok):
        return {"class": "измерение_о_корпусе", "degenerate": False,
                "observed_key": observed, "source": src_val,
                "resolved_source": resolved_source,
                "source_digest": actual_digest,
                "source_digest_key": supplied_digest_key,
                "observed_in_source": "подтверждено",
                "observed_matches_evidence": "подтверждено",
                "source_integrity": "подтверждён",
                "external_target_contract": "подтверждён"}
    reasons = []
    if not observed:
        reasons.append("нет корпусного наблюдаемого: сверяется внешний "
                       "источник сам с собой")
    elif not has_corpus_path:
        reasons.append("наблюдаемое объявлено, но путь к файлу корпуса не "
                       "указан: происхождение непроверяемо")
    elif not supplied_digest:
        reasons.append("у корпусного наблюдаемого нет отпечатка источника: "
                       "целостность содержимого не зафиксирована")
    else:
        reasons.append("отпечаток источника не совпадает с содержимым файла: "
                       "корпусное наблюдаемое нельзя связать с проверенным "
                       "снимком")
    if not observed_in_source:
        reasons.append("наблюдаемое не найдено в тексте указанного файла корпуса")
    if not observed_matches_evidence:
        reasons.append("численное наблюдаемое не найдено в заявленной строке "
                       "наблюдения")
    if not target_ok:
        reasons.extend(target_reasons)
    return {"class": "вырожденная_сверка", "degenerate": True,
            "verdict_if_submitted": "ПУСТО", "reasons": reasons,
            "observed_key": observed, "source": src_val,
            "resolved_source": resolved_source,
            "source_digest": actual_digest,
            "source_digest_key": supplied_digest_key,
            "observed_in_source": "не подтверждено",
            "observed_matches_evidence": "не подтверждено",
            "source_integrity": "не подтверждён",
            "external_target_contract": "не подтверждён"}


def selftest() -> int:
    bad = 0

    def check(name: str, cond: bool) -> None:
        nonlocal bad
        bad += 0 if cond else 1
        print(f"  {'ok    ' if cond else 'ПРОВАЛ'} {name}")

    # ИСТОРИЧЕСКИЕ ФИКСТУРЫ: настоящие артефакты тиков 210–212.
    hist = {}
    for tick in (210, 211, 212):
        p = TICKDIR / ("tick%d_external_measurement.json" % tick)
        if p.exists():
            hist[tick] = json.loads(p.read_text(encoding="utf-8"))
    if len(hist) < 3:
        print("ПРОПУСК самопроверки: исторические артефакты недоступны "
              "(объявленный пропуск, причина — ротация файлов тиков)")
        return 0

    caught = sum(1 for t in (210, 211) if classify(hist[t])["degenerate"])
    check("вырожденные сверки тиков 210 и 211 ловятся (%d/2)" % caught,
          caught == 2)
    check("честная сверка тика 212 НЕ помечена вырожденной",
          not classify(hist[212])["degenerate"])
    check("у вырожденной сверки указана причина",
          all(classify(hist[t]).get("reasons") for t in (210, 211)))

    # МУТАЦИОННАЯ ЦЕЛЬ 1: убрать у честного артефакта путь к корпусу.
    mut = dict(hist[212])
    for k in SOURCE_KEYS:
        mut.pop(k, None)
    check("мутант без источника наблюдения ловится",
          classify(mut)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 2: путь есть, но не в корпус — происхождение подменено.
    mut2 = dict(hist[212])
    mut2["источник_наблюдения"] = "/tmp/scratch/notes.md"
    check("мутант с путём вне корпуса ловится", classify(mut2)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 3: строка содержит «corpus/», но файл не является
    # частью корпуса. Старый подстрочный сторож пропускал бы такой мутант.
    mut3 = dict(hist[212])
    mut3["источник_наблюдения"] = "/tmp/corpus/trinity/fake.md"
    check("мутант с поддельным путём corpus ловится",
          classify(mut3)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 4: корпусное наблюдаемое не может скрыть
    # отсутствующую внешнюю цель, её неопределённость или URL.
    mut4 = dict(hist[212])
    mut4.pop("external_target", None)
    check("мутант без внешней цели ловится", classify(mut4)["degenerate"])
    mut5 = dict(hist[212])
    mut5["external_target"] = dict(hist[212]["external_target"])
    mut5["external_target"].pop("uncertainty", None)
    check("мутант без неопределённости внешней цели ловится",
          classify(mut5)["degenerate"])
    mut6 = dict(hist[212])
    mut6["external_target"] = dict(hist[212]["external_target"])
    mut6["external_target"].pop("source", None)
    check("мутант без URL внешней цели ловится", classify(mut6)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 7: ключи присутствуют, но значение не является
    # измерением. Такой артефакт раньше проходил сторож и мог породить
    # бесконечное или фиктивное число сигм.
    mut7 = dict(hist[212])
    mut7["external_target"] = dict(hist[212]["external_target"])
    mut7["external_target"]["uncertainty"] = 0
    check("мутант с нулевой неопределённостью ловится",
          classify(mut7)["degenerate"])
    mut8 = dict(hist[212])
    mut8["external_target"] = dict(hist[212]["external_target"])
    mut8["external_target"]["uncertainty"] = "не число"
    check("мутант с нечисловой неопределённостью ловится",
          classify(mut8)["degenerate"])
    mut9 = dict(hist[212])
    mut9["external_target"] = dict(hist[212]["external_target"])
    mut9["external_target"]["value"] = "NaN"
    check("мутант с нечисловым значением ловится",
          classify(mut9)["degenerate"])
    mut10 = dict(hist[212])
    mut10["external_target"] = dict(hist[212]["external_target"])
    mut10["external_target"]["source"] = "это не URL"
    check("мутант с поддельным URL ловится",
          classify(mut10)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 11: синтаксически правильный URL всё ещё может быть
    # зарезервированной заглушкой. Такой адрес не является внешним измерением.
    mut_placeholder = dict(hist[212])
    mut_placeholder["external_target"] = dict(hist[212]["external_target"])
    mut_placeholder["external_target"]["source"] = "https://example.invalid/target"
    check("мутант с URL-заглушкой ловится",
          classify(mut_placeholder)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 14: абсолютный URL может указывать на loopback или
    # приватную сеть. Такой адрес не является проверяемым внешним измерением,
    # даже если синтаксис и все числовые поля выглядят правдоподобно.
    mut_local = dict(hist[212])
    mut_local["external_target"] = dict(hist[212]["external_target"])
    mut_local["external_target"]["source"] = "http://127.0.0.1/measurement"
    check("мутант с локальным URL ловится",
          classify(mut_local)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 15: публичный домен с учётными данными в URL нельзя
    # считать публичной внешней целью — секрет мог бы скрывать подменённый
    # источник, а адрес не воспроизводим для независимого читателя.
    mut_credentials = dict(hist[212])
    mut_credentials["external_target"] = dict(hist[212]["external_target"])
    mut_credentials["external_target"]["source"] = (
        "https://reader:secret@physics.nist.gov/cgi-bin/cuu/Value?re"
    )
    check("мутант с учётными данными в URL ловится",
          classify(mut_credentials)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 12: путь и отпечаток остаются честными, но наблюдаемое
    # подменено числом, которого в корпусном файле нет. Один SHA-256 не
    # подтверждает происхождение отдельного поля observed.
    mut12 = dict(hist[212])
    mut12["наблюдаемое_из_корпуса"] = "999999999"
    check("мутант с подменённым наблюдаемым ловится",
          classify(mut12)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 13: строка корпуса и её отпечаток остаются честными,
    # но численное поле меняется на другое значение. Одной ссылки на строку
    # недостаточно — связь наблюдаемого с доказательством должна быть явной.
    mut13 = dict(hist[212])
    mut13["строка_наблюдения"] = hist[212]["наблюдаемое_из_корпуса"]
    mut13["наблюдаемое_из_корпуса"] = "0.0413"
    check("мутант с наблюдаемым, не совпадающим со строкой, ловится",
          classify(mut13)["degenerate"])

    # МУТАЦИОННАЯ ЦЕЛЬ 5: содержимое меняется при неизменном пути. Временный
    # корень корпуса оставляет путь валидным, но меняет его байты после
    # фиксации отпечатка; сторож обязан отвергнуть такой дрейф.
    with tempfile.TemporaryDirectory() as td:
        temp_root = Path(td) / "corpus" / "trinity"
        temp_file = temp_root / "docs" / "source.md"
        temp_file.parent.mkdir(parents=True)
        temp_file.write_text("наблюдаемое до мутации: 1.234\n",
                             encoding="utf-8")
        original_root = CORPUS_ROOT
        try:
            globals()["CORPUS_ROOT"] = temp_root.resolve()
            digest_art = {
                "наблюдаемое_из_корпуса": "1.234",
                "источник_наблюдения": str(temp_file),
                "отпечаток_источника": _sha256(temp_file),
                "external_target": {
                    "value": "1.2",
                    "uncertainty": "0.1",
                    "source": "https://physics.nist.gov/cgi-bin/cuu/Value?re",
                },
            }
            before = classify(digest_art)
            temp_file.write_text("подмена содержимого при том же пути\n",
                                 encoding="utf-8")
            after = classify(digest_art)
        finally:
            globals()["CORPUS_ROOT"] = original_root
    check("мутация содержимого при неизменном пути ловится",
          not before["degenerate"] and after["degenerate"] and
          after.get("source_integrity") == "не подтверждён")

    # ОТРИЦАТЕЛЬНАЯ ПРОВЕРКА: отклонение в сигмах решения НЕ определяет —
    # иначе сторож ловил бы «согласие», а не вырожденность.
    ok_small = dict(hist[212])
    ok_small["отклонение_эталона_от_цели_в_сигмах"] = 0.0
    check("нулевое отклонение при корпусном наблюдаемом вырожденным не "
          "считается", not classify(ok_small)["degenerate"])

    print(f"самопроверка сторожа внешних целей: провалов {bad}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    rows = []
    for p in sorted(TICKDIR.glob("tick*_external_measurement.json")):
        try:
            art = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append({"file": p.name, "error": str(exc)})
            continue
        rows.append({"file": p.name, "target": art.get("цель"),
                     **classify(art)})
    degenerate = [r for r in rows if r.get("degenerate")]
    report = {
        "checked": len(rows),
        "degenerate_count": len(degenerate),
        "degenerate": [r["file"] for r in degenerate],
        "rule": ("артефакт внешней сверки обязан содержать наблюдаемое из "
                 "корпуса и путь к файлу корпуса; иначе сверка проходит при "
                 "любом значении корпусных формул; отпечаток источника "
                 "обязан совпадать с содержимым файла; внешняя цель обязана "
                 "иметь конечное числовое значение, положительную "
                 "неопределённость и публичный URL внешнего источника"),
        "why_this_check_exists": ("тики 210 и 211 подали сверку внешнего "
                                  "источника с самим собой как содержательную "
                                  "цель: 0 и 0,0111 сигмы ни о чём не "
                                  "свидетельствуют"),
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("сторож внешних целей: проверено %d, вырожденных %d"
          % (len(rows), len(degenerate)))
    for r in degenerate:
        print("  ПУСТО  %s — %s" % (r["file"], "; ".join(r["reasons"])))
    # Код возврата 0: это ретроспективная разметка уже сделанного, а не запрет.
    # Отказ гейта здесь означал бы наказание за прошлое; задача сторожа —
    # запретить ПОДАЧУ такой цели в следующем тике.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
