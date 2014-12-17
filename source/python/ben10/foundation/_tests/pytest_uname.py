from __future__ import unicode_literals
from ben10.filesystem import CanonicalPath
from ben10.foundation import is_frozen
from ben10.foundation.platform_ import Platform
from ben10.foundation.pushpop import PushPop
from ben10.foundation.string import Dedent
from ben10.foundation.uname import (GetApplicationDir, GetExecutableDir, GetUserHomeDir,
    IsRunningOn64BitMachine)
import os
import pytest
import sys



#===================================================================================================
# Test
#===================================================================================================
class Test():

    @pytest.mark.skipif('sys.platform != "win32"')
    def testIsRunningOn64BitMachine(self, monkeypatch):
        import ctypes

        def mock_IsWow64Process(a, result):
            print dir(result)
            result = 0

        monkeypatch.setattr(Platform, 'GetCurrentPlatform', classmethod(lambda x:'win64'))
        assert IsRunningOn64BitMachine()

        # When CurrentPlatform returns win32 we fallback the test to IsWow64Process, mocked here to
        # ensure it will return "false" for 64-bits.
        monkeypatch.setattr(ctypes.windll.kernel32, 'IsWow64Process', mock_IsWow64Process)
        monkeypatch.setattr(Platform, 'GetCurrentPlatform', classmethod(lambda x:'win32'))
        assert not IsRunningOn64BitMachine()


    def testGetUserHomeDir(self):
        with PushPop(os, 'environ', dict(HOMEDRIVE='C:/', HOMEPATH='Users/ama', HOME='/home/users/ama')):
            with PushPop(sys, 'platform', 'win32'):
                home_dir = GetUserHomeDir()
                assert isinstance(home_dir, unicode)
                assert home_dir == '%(HOMEDRIVE)s%(HOMEPATH)s' % os.environ
            with PushPop(sys, 'platform', 'linux2'):
                home_dir = GetUserHomeDir()
                assert isinstance(home_dir, unicode)
                assert home_dir == '%(HOME)s' % os.environ


    _SCRIPT = Dedent(r'''# coding: UTF-8
        from ben10.foundation.uname import GetApplicationDir, GetUserHomeDir
        import sys

        option = sys.argv[1]
        if option == 'app':
            dir_name = GetApplicationDir()

        elif option == 'home':
            app_dir = GetApplicationDir()

            import locale
            import os
            if sys.platform == 'win32':
                drive, path = os.path.splitdrive(app_dir)
                os.environ['HOMEDRIVE'] = drive.encode(locale.getpreferredencoding())

                os.environ['HOMEPATH'] = path.encode(locale.getpreferredencoding())

            else:
                os.environ['HOME'] = app_dir.encode(locale.getpreferredencoding())

            dir_name = GetUserHomeDir()

        print dir_name.encode('utf-8')
        ''')


    def testGetUserHomeDirNonAscii(self, embed_data, unicode_samples, script_runner):
        dir_name = embed_data.GetDataFilename(unicode_samples.UNICODE_PREFERRED_LOCALE)
        home_dir = script_runner.ExecuteScript(
            os.path.join(dir_name, 'script.py_'), self._SCRIPT, 'home')
        assert CanonicalPath(home_dir) == CanonicalPath(dir_name)


    def testGetApplicationDir(self):
        was_frozen = is_frozen.SetIsFrozen(False)
        try:
            application_dir = GetApplicationDir()
            assert isinstance(application_dir, unicode)
            assert application_dir == sys.path[0]

            # When in a executable...
            is_frozen.SetIsFrozen(True)
            application_dir = GetApplicationDir()
            assert isinstance(application_dir, unicode)
            assert application_dir == os.path.dirname(os.path.dirname(sys.executable))
        finally:
            is_frozen.SetIsFrozen(was_frozen)


    def testGetApplicationDirNonAscii(self, embed_data, unicode_samples, script_runner):
        dir_name = embed_data.GetDataFilename(unicode_samples.LATIN_1)
        obtained = script_runner.ExecuteScript(os.path.join(dir_name, 'script.py_'), self._SCRIPT, 'app')
        assert CanonicalPath(obtained) == CanonicalPath(dir_name)


    def testGetExecutableDir(self):
        executable_dir = GetExecutableDir()
        assert isinstance(executable_dir, unicode)
        assert executable_dir == os.path.dirname(sys.executable)
