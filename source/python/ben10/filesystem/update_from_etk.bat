copy /qes x:\etk\coilib50\source\python\coilib50\filesystem\*.py
copy __init__.extras __init__.py __init__.new
del __init__.py
ren __init__.new __init__.py
call aa.bat .fix_format . --refactor=update_from_etk.ini


