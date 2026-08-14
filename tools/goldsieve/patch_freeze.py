"""Пункт 1 приказа тика 41: заморозка v12 как квалифицированного baseline.

Различие, которого раньше не было. `baseline/manifest.json` — ПОДВИЖНЫЙ снимок:
он перезаписывается командой snapshot в конце каждого тика, поэтому «сверка с
baseline» отвечает лишь на вопрос «не хуже, чем в прошлый тик». Дрейф на
десять тиков по одному разрешённому шагу такой сверкой не ловится вовсе.

`baseline/frozen-v12.json` — НЕПОДВИЖНАЯ точка: состояние, квалифицированное
приказом («T40 = GREEN, qualified within declared scope»). Она не
перезаписывается snapshot и защищена собственным отпечатком целостности:
`frozen-v12.sha256` считается по каноническому JSON тела, поэтому правка тела
без обновления отпечатка обнаруживается, а обновление отпечатка требует режима
`refreeze`, который печатает предупреждение и требует явного слова.

Режим `frozen` печатает дельту frozen -> current: метрики, отпечатки файлов и
вердиктов, изменившиеся файлы инструмента. Он НЕ падает при отличиях (тик 41 их
и вносит намеренно), но падает при нарушении целостности заморозки.
"""

PATH = "baseline.py"
src = open(PATH, encoding="utf-8").read()

old = '''def main(argv: list[str]) -> int:'''
new = '''FROZEN = os.path.join(DIR, "frozen-v12.json")
FROZEN_SHA = os.path.join(DIR, "frozen-v12.sha256")
FROZEN_LABEL = "v12 (тик 40, quenched)"


def _canon(obj) -> bytes:
    """Каноническая форма для отпечатка: порядок ключей не должен влиять."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()


def _frozen_load() -> tuple[dict, list[str]]:
    """Чтение заморозки с проверкой целостности. Список — найденные нарушения."""
    problems: list[str] = []
    if not os.path.exists(FROZEN):
        return {}, ["заморозка отсутствует: baseline/frozen-v12.json"]
    body = json.load(open(FROZEN, encoding="utf-8"))
    want = hashlib.sha256(_canon(body)).hexdigest()
    if not os.path.exists(FROZEN_SHA):
        problems.append("отпечаток заморозки отсутствует: frozen-v12.sha256")
    else:
        got = open(FROZEN_SHA, encoding="utf-8").read().strip().split()[0]
        if got != want:
            problems.append("ЦЕЛОСТНОСТЬ ЗАМОРОЗКИ НАРУШЕНА: тело даёт %s, "
                            "записано %s" % (want[:16], got[:16]))
    return body, problems


def freeze(force: bool = False) -> int:
    """Зафиксировать ТЕКУЩИЙ подвижный снимок как неподвижную точку."""
    if os.path.exists(FROZEN) and not force:
        print("ОТКАЗ: заморозка уже существует. Перезапись — режим refreeze, "
              "и только после независимого review.")
        return 1
    if not os.path.exists(MANIFEST) or not os.path.exists(VERDICTS_JSON):
        print("ОТКАЗ: подвижный snapshot отсутствует, сначала snapshot")
        return 1
    man = json.load(open(MANIFEST, encoding="utf-8"))
    body = {
        "label": FROZEN_LABEL,
        "frozen_at": _dt.datetime.now(_dt.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "qualified_scope": (
            "детектор косвенной тавтологии: классы конструкций, перечисленные в "
            "coverage_manifest.yaml, на интерпретаторах из versions; вне этого "
            "перечня охват НЕ заявлен"),
        "files": man.get("files", {}),
        "files_digest": man.get("files_digest"),
        "verdicts_digest": man.get("verdicts_digest"),
        "metrics": man.get("metrics", {}),
        "versions": man.get("versions", {}),
        "corpus_head": man.get("corpus_head"),
        "platform": man.get("platform"),
    }
    with open(FROZEN, "w", encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False, indent=2, sort_keys=True)
    # Отпечаток считается по каноническому телу, а не по байтам файла: иначе
    # безобидное переформатирование ломало бы проверку и её начали бы обходить.
    digest = hashlib.sha256(_canon(body)).hexdigest()
    with open(FROZEN_SHA, "w", encoding="utf-8") as fh:
        fh.write(digest + "  frozen-v12.json\\n")
    print("заморожено: %s" % FROZEN_LABEL)
    print("  отпечаток заморозки: " + digest[:16])
    print("  файлов: %d  метрики: %s"
          % (len(body["files"]), json.dumps(body["metrics"],
                                            ensure_ascii=False)))
    return 0


def frozen_delta() -> int:
    """Дельта frozen -> current. Падает только при нарушении целостности."""
    body, problems = _frozen_load()
    if problems:
        print("ГЕЙТ ЗАКРЫТ: заморозка непригодна")
        for p in problems:
            print("  - " + p)
        return 1
    print("заморозка: %s  от %s" % (body.get("label"), body.get("frozen_at")))
    print("объявленный охват: %s" % body.get("qualified_scope"))
    cur_files = {rel: _sha256(os.path.join(ROOT, rel)) for rel in _tool_files()}
    cur_digest = hashlib.sha256(
        json.dumps(cur_files, sort_keys=True).encode()).hexdigest()[:16]
    print()
    print("%-22s %s -> %s" % ("отпечаток файлов", body.get("files_digest"),
                              cur_digest))
    old_files = body.get("files", {})
    changed = sorted(r for r in set(old_files) | set(cur_files)
                     if old_files.get(r) != cur_files.get(r))
    print("изменившихся файлов инструмента: %d" % len(changed))
    for rel in changed[:40]:
        mark = ("новый" if rel not in old_files else
                "удалён" if rel not in cur_files else "правлен")
        print("  %-8s %s" % (mark, rel))
    cur = _metrics()
    print()
    print("метрики заморозки: " + json.dumps(body.get("metrics", {}),
                                             ensure_ascii=False))
    print("метрики сейчас:    " + json.dumps(cur, ensure_ascii=False))
    for key in ("sensitivity", "specificity"):
        old, new = body.get("metrics", {}).get(key), cur.get(key)
        try:
            if old is not None and new is not None and float(new) < float(old):
                print("  ВНИМАНИЕ метрика ниже замороженной: %s %s -> %s"
                      % (key, old, new))
        except ValueError:
            pass
    return 0


def main(argv: list[str]) -> int:'''
assert old in src
src = src.replace(old, new, 1)

old = '''    if mode == "show":
        return show()
    print("режимы: snapshot | check | show")'''
new = '''    if mode == "show":
        return show()
    if mode == "freeze":
        return freeze(force=False)
    if mode == "refreeze":
        if "--i-have-review" not in argv:
            print("ОТКАЗ: refreeze перезаписывает квалифицированную точку. "
                  "Требуется флаг --i-have-review и запись в ведомости о том, "
                  "кто и когда провёл независимый review.")
            return 1
        print("ВНИМАНИЕ: квалифицированная точка перезаписывается.")
        return freeze(force=True)
    if mode == "frozen":
        return frozen_delta()
    print("режимы: snapshot | check | show | freeze | refreeze | frozen")'''
assert old in src
src = src.replace(old, new, 1)

if "import datetime as _dt" not in src:
    src = src.replace("import hashlib", "import datetime as _dt\nimport hashlib", 1)

open(PATH, "w", encoding="utf-8").write(src)
print("правка внесена")
