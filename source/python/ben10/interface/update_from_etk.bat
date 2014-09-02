:: This script does not fully updates ben10's code, but it gives a hint if
:: we have any new changes in the original code.
copy /qes %AA_SYSTEM_PROJECTS_DIR%\etk\coilib50\source\python\coilib50\basic\interface\_adaptable_interface.py
::_interface: Removed ScalarAttribute on ben10.
call aa.bat .fix_format . --refactor=update_from_etk.ini
call aa.bat .fix_format . --refactor=%AA_SYSTEM_PROJECTS_DIR%\ben10\terraforming.ini


