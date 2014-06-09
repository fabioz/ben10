from ben10.foundation.platform_ import Platform, UnknownPlatform
import os
import platform
import pytest
import sys



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testPlatform(self):
        p = Platform('win', '32')
        assert p.name == 'win'
        assert p.bits == '32'
        assert p.debug == False
        assert str(p) == 'win32'
        assert p.AsString(False) == 'win32'
        assert p.AsString(True) == 'win32'
        assert p.GetSimplePlatform() == 'i686.win32'
        assert p.GetBaseName() == 'win32'
        assert p.GetLongName() == 'Windows 32-bit'
        assert p.GetPlatformFlavour() == 'windows'
        assert p.GetMneumonic() == 'w32'

        p = Platform('win', '64', True)
        assert p.name == 'win'
        assert p.bits == '64'
        assert p.debug == True
        assert str(p) == 'win64d'
        assert p.AsString(False) == 'win64d'
        assert p.AsString(True) == 'win64'
        assert p.GetSimplePlatform() == 'amd64.win32'
        assert p.GetBaseName() == 'win64'
        assert p.GetLongName() == 'Windows 64-bit DEBUG'
        assert p.GetPlatformFlavour() == 'windows'
        assert p.GetMneumonic() == 'w64'

        with pytest.raises(ValueError):
            p = Platform('INVALID', '32')

        with pytest.raises(ValueError):
            p = Platform('win', 'INVALID')

        p = Platform('win', '32')
        p.name = 'INVALID'
        with pytest.raises(UnknownPlatform):
            p.GetSimplePlatform()

        with pytest.raises(UnknownPlatform):
            p.GetPlatformFlavour()

        with pytest.raises(UnknownPlatform):
            p.GetLongName()

        assert p.GetCurrentFlavour() == p.GetCurrentPlatform().GetPlatformFlavour()


    def testGetValidPlatforms(self):
        assert set(Platform.GetValidPlatforms()) == {
            'darwin32',
            'darwin32d',
            'darwin64',
            'darwin64d',
            'debian32',
            'debian32d',
            'debian64',
            'debian64d',
            'redhat32',
            'redhat32d',
            'redhat64',
            'redhat64d',
            'ubuntu32',
            'ubuntu32d',
            'ubuntu64',
            'ubuntu64d',
            'win32',
            'win32d',
            'win64',
            'win64d',
        }


    def testCreate(self):
        assert str(Platform.Create('win32')) == 'win32'
        assert str(Platform.Create('i686.win32')) == 'win32'
        assert str(Platform.Create(None)) == str(Platform.GetCurrentPlatform())

        plat = Platform.GetCurrentPlatform()
        assert Platform.Create(plat) is plat

        p = Platform.CreateFromString('win32')
        assert str(p) == 'win32'

        p = Platform.CreateFromSimplePlatform('i686.win32')
        assert str(p) == 'win32'

        with pytest.raises(UnknownPlatform):
            Platform.Create(123)

        with pytest.raises(UnknownPlatform):
            Platform.CreateFromSimplePlatform('UNKNOWN')


    def testGetCurrentPlatform(self, monkeypatch):
        '''
        This is a white box test, but I found it necessary to full coverage.
        '''
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(platform, 'python_compiler', lambda:'WINDOWS')
        assert str(Platform.GetCurrentPlatform()) == 'win32'
        assert str(Platform.GetDefaultPlatform()) == 'win32'

        monkeypatch.setattr(platform, 'python_compiler', lambda:'AMD64')
        assert str(Platform.GetCurrentPlatform()) == 'win64'
        assert str(Platform.GetDefaultPlatform()) == 'win32'

        monkeypatch.setattr(sys, 'platform', 'darwin')
        assert str(Platform.GetCurrentPlatform()) == 'darwin64'
        assert str(Platform.GetDefaultPlatform()) == 'darwin64'

        monkeypatch.setattr(sys, 'platform', 'linux2')
        monkeypatch.setattr(platform, 'dist', lambda:['fedora'])
        monkeypatch.setattr(platform, 'machine', lambda:'x86_64')
        assert str(Platform.GetCurrentPlatform()) == 'redhat64'
        assert str(Platform.GetDefaultPlatform()) == 'redhat64'


    def testGetOSPlatform(self, monkeypatch):
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(platform, 'python_compiler', lambda:'WINDOWS')

        monkeypatch.setattr(os, 'environ', {})
        assert str(Platform.GetOSPlatform()) == 'win32'

        monkeypatch.setattr(os, 'environ', {'PROGRAMFILES(X86)':''})
        assert str(Platform.GetOSPlatform()) == 'win64'

        monkeypatch.setattr(sys, 'platform', 'linux2')
        monkeypatch.setattr(platform, 'dist', lambda:['fedora'])
        monkeypatch.setattr(platform, 'machine', lambda:'x86_64')
        assert str(Platform.GetOSPlatform()) == 'redhat64'


    def testFlags(self, monkeypatch):
        assert Platform.GetAllFlags() == {
            'windows', 'linux', 'darwin',
            'win32', 'win32d', 'win64', 'win64d',
            'redhat32', 'redhat32d', 'redhat64', 'redhat64d',
            'darwin32', 'darwin32d', 'darwin64', 'darwin64d',
            'debian64', 'debian32', 'debian64d', 'debian32d',
            'ubuntu64', 'ubuntu32', 'ubuntu32d', 'ubuntu64d',
        }

        platform = Platform.Create('win32')
        assert platform.GetFlags() == {'windows', 'win32'}

        platform = Platform.Create('win32d')
        assert platform.GetFlags() == {'windows', 'win32', 'win32d', 'debug'}

        platform = Platform.Create('redhat64')
        assert platform.GetFlags() == {'linux', 'redhat64'}
