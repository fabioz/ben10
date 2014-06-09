copy /qe x:\etk\sharedscripts10\source\python\sharedscripts10\platform_.py platform_.py
copy /qe x:\etk\sharedscripts10\source\python\sharedscripts10\_tests\pytest_platform.py _tests\pytest_platform.py

call aa.bat .fix_format platform_.py --refactor=x:\ben10\terraforming.ini
call aa.bat .fix_format _tests\pytest_platform.py --refactor=x:\ben10\terraforming.ini
