from __future__ import unicode_literals
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    @pytest.mark.skipif("not sys.platform.startswith('win')")
    def testRegistryDict(self):
        from ben10.registry_dict import RegistryDict

        key = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
        invalid_key = r'INVALID'

        reg = RegistryDict()
        try:
            assert reg.has_key(key) == True
            assert key in reg

            value = reg[key]
            assert value['SoftwareType'] == 'System'

            assert invalid_key not in reg
            assert reg.has_key(invalid_key) == False
        finally:
            reg.close()
