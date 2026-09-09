import importlib.util
p='/home/user/workspace/goldsieve/cases/sacred_table_audit_20260813.py'
spec=importlib.util.spec_from_file_location('case',p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print('extended',m.extended_reference(),m.extended_reference_alt(),m.extended_observed(),m.extended_negative_control())
rows=m._established_rows()
print('rows',len(rows),'exact',m.exact_reference(),'alt',m.exact_reference_alt(),'control',m.exact_negative_control())
for name,params,target in rows:
    err=abs(m._formula(params)-target)/abs(target)*100
    if err < .011 or err > .01:
        print(name, params, target, m._formula(params), err)
