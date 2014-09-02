copy /qe %AA_SYSTEM_PROJECTS_DIR%\sharedscripts10\source\python\sharedscripts10\_execute_impl.py execute.py

copy /qe %AA_SYSTEM_PROJECTS_DIR%\etk\sharedscripts10\source\python\sharedscripts10\_tests\pytest_execute.py _tests
copy /qes %AA_SYSTEM_PROJECTS_DIR%\sharedscripts10\source\python\sharedscripts10\_tests\pytest_execute _tests\pytest_execute

call aa.bat .fix_format _tests\pytest_execute.py --refactor=%AA_SYSTEM_PROJECTS_DIR%\ben10\terraforming.ini
call aa.bat .fix_format execute.py --refactor=%AA_SYSTEM_PROJECTS_DIR%\ben10\terraforming.ini
