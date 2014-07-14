copy /qe x:\etk\coilib50\source\python\coilib50\basic\bunch.py bunch.py
:: callback: from coilib50.messages.callback/
copy /qe x:\etk\coilib50\source\python\coilib50\basic\debug.py debug.py
:: decorators: joins more than one module from coilib50
:: enum: Improved on ben10
copy /qe x:\etk\coilib50\source\python\coilib50\basic\fifo.py fifo.py
:: immutable: Improved on ben10
:: is_frozen:
copy /qe x:\etk\coilib50\source\python\coilib50\basic\klass.py klass.py
:: log:
:: copy /qe x:\etk\coilib50\source\python\coilib50\basic\log.py log.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\lru.py lru.py
copy /qe x:\etk\coilib50\source\python\coilib50\cache\memoize.py memoize.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\odict\__init__.py odict.py
copy /qe x:\etk\sharedscripts10\source\python\sharedscripts10\platform_.py platform_.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\pushpop.py pushpop.py
::copy /qe x:\etk\coilib50\source\python\coilib50\basic\redirect_output.py redirect_output.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\_reraise.py reraise.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\singleton.py singleton.py
copy /qe x:\etk\coilib50\source\python\coilib50\basic\string.py string.py
::translation: no equivalency
::types_: this is a mix of many coilib50's modules
::uname: Most of the code was replaced by Platform class.
copy /qe x:\etk\coilib50\source\python\coilib50\basic\url.py url.py
::weak_ref: from coilib50.basic.weak_ref/


copy /qe x:\etk\sharedscripts10\source\python\sharedscripts10\_tests\pytest_platform.py _tests\pytest_platform.py

call aa.bat .fix_format . --refactor=x:\ben10\terraforming.ini
::call aa.bat .fix_format platform_.py --refactor=x:\ben10\terraforming.ini
::call aa.bat .fix_format _tests\pytest_platform.py --refactor=x:\ben10\terraforming.ini
