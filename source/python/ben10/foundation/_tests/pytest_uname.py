from ben10.foundation import is_frozen
from ben10.foundation.platform_ import Platform
from ben10.foundation.pushpop import PushPop
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
        with PushPop(os, 'environ', dict(HOMEDRIVE='C:/',HOMEPATH='Users/ama',HOME='/home/users/ama')):
            with PushPop(sys, 'platform', 'win32'):
                assert GetUserHomeDir() == '%(HOMEDRIVE)s%(HOMEPATH)s' % os.environ
            with PushPop(sys, 'platform', 'linux2'):
                assert GetUserHomeDir() == '%(HOME)s' % os.environ


    def testGetApplicationDir(self):
        was_frozen = is_frozen.SetIsFrozen(False)
        try:
            assert GetApplicationDir() == sys.path[0]

            # When in a executable...
            is_frozen.SetIsFrozen(True)
            assert GetApplicationDir() == os.path.dirname(os.path.dirname(sys.executable))
        finally:
            is_frozen.SetIsFrozen(was_frozen)


    def testGetExecutableDir(self):
        assert GetExecutableDir() == os.path.dirname(sys.executable)
