"""Правка тика 41 (продолжение): имя объекта, чей атрибут уже разобран.

Симптом: `_descriptor_origin` давал верный вердикт True для `_panel.value`, но
в списке прочитанных имён есть и само имя `_panel`; оно разрешается в экземпляр,
который не callable, и разбор возвращал False. Чтение имени объекта данных не
приносит — данные приходят через атрибут, который уже разобран.

Поэтому имена с точкой обрабатываются ПЕРВЫМИ, и база успешно разобранного
атрибута заносится в множество resolved_bases; чистое имя из этого множества
пропускается.
"""

PATH = "goldsieve/identity_deep.py"
src = open(PATH, encoding="utf-8").read()

old = '''    # --- прочитанные имена: свободные переменные, глобальные, self.атрибуты --
    for name in names:
        if name in param_names or name in PURE_BUILTINS:
            continue'''
new = '''    # --- прочитанные имена: свободные переменные, глобальные, self.атрибуты --
    # Порядок не случаен: имена С ТОЧКОЙ разбираются первыми. Значение приходит
    # через атрибут (`_panel.value`), а чтение самого имени объекта (`_panel`)
    # данных не приносит — иначе разобранный дескриптор тут же перекрывался бы
    # вердиктом «объект не callable, источник неизвестен».
    resolved_bases: set[str] = set()
    for name in [x for x in names if "." in x] + [x for x in names if "." not in x]:
        if name in param_names or name in PURE_BUILTINS:
            continue
        if name in resolved_bases:
            continue'''
assert old in src
src = src.replace(old, new, 1)

# База успешно разобранного атрибута — и для self.*, и для внешнего объекта.
old = '''                if _field_from_ref(type(instance), name.split(".")[1],
                                   ref_name, instance):
                    found_ref = True
                    continue
                return False, trail'''
new = '''                if _field_from_ref(type(instance), name.split(".")[1],
                                   ref_name, instance):
                    found_ref = True
                    continue
                return False, trail
            if base in tainted:
                found_ref = True
                resolved_bases.add(base)
                continue'''
assert old in src
src = src.replace(old, new, 1)

old = '''            owner = _lookup(base, fn, globals_, instance)
            got = _descriptor_origin(owner, name.split(".")[-1], ref, depth,
                                     seen, trail) if owner is not None else None
            if got is not None:
                ok, tr = got
                if not ok:
                    return False, trail
                trail = tr
                found_ref = True
                continue
            return False, trail'''
new = '''            owner = _lookup(base, fn, globals_, instance)
            got = _descriptor_origin(owner, name.split(".")[-1], ref, depth,
                                     seen, trail) if owner is not None else None
            if got is not None:
                ok, tr = got
                if not ok:
                    return False, trail
                trail = tr
                found_ref = True
                resolved_bases.add(base)
                continue
            return False, trail'''
assert old in src
src = src.replace(old, new, 1)

# То же для вызовов через точку: `Panel.value()`.
old = '''        owner = _lookup(base, fn, globals_, instance)
        got = _descriptor_origin(owner, label.split(".")[-1], ref, depth,
                                 seen, trail) if owner is not None else None
        if got is not None:
            ok, tr = got
            if not ok:
                return False, trail
            trail = tr
            found_ref = True
            continue
        return False, trail'''
new = '''        owner = _lookup(base, fn, globals_, instance)
        got = _descriptor_origin(owner, label.split(".")[-1], ref, depth,
                                 seen, trail) if owner is not None else None
        if got is not None:
            ok, tr = got
            if not ok:
                return False, trail
            trail = tr
            found_ref = True
            dotted_bases.add(base)
            continue
        return False, trail'''
assert old in src
src = src.replace(old, new, 1)

old = '''    # --- вызовы через точку -------------------------------------------------
    for label in dotted:'''
new = '''    # --- вызовы через точку -------------------------------------------------
    dotted_bases: set[str] = set()
    for label in dotted:'''
assert old in src
src = src.replace(old, new, 1)

old = '''    resolved_bases: set[str] = set()'''
new = '''    resolved_bases: set[str] = set(dotted_bases)'''
assert old in src
src = src.replace(old, new, 1)

open(PATH, "w", encoding="utf-8").write(src)
print("правка внесена")
