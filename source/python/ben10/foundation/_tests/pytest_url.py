from __future__ import unicode_literals
from ben10.foundation.platform_ import Platform
from ben10.foundation.url import HideURLPassword, IsUrlEqual



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testUrlCompare(self, monkeypatch):

        # Remote protocols
        for protocol in ['http', 'https', 'ftp']:
            # Check if ignoring case
            assert IsUrlEqual(protocol + '://HERE', protocol + '://here') == False
            assert IsUrlEqual(protocol + '://here', protocol + '://here') == True
            assert IsUrlEqual(protocol + '://here', protocol + '://nothere') == False

        protocol = 'file'
        monkeypatch.setattr(Platform, 'GetCurrentFlavour', classmethod(lambda x:'windows'))
        # Check if ignoring case
        assert IsUrlEqual(protocol + '://HERE', protocol + '://here') == True
        assert IsUrlEqual(protocol + '://here', protocol + '://here') == True
        assert IsUrlEqual(protocol + '://here', protocol + '://nothere') == False

        # Local file protocol, not windows
        protocol = 'file'
        monkeypatch.setattr(Platform, 'GetCurrentFlavour', classmethod(lambda x:'linux'))
        # Check if ignoring case
        assert IsUrlEqual(protocol + '://HERE', protocol + '://here') == False
        assert IsUrlEqual(protocol + '://here', protocol + '://here') == True
        assert IsUrlEqual(protocol + '://here', protocol + '://nothere') == False


    def testHideURLPassword(self):
        # No username nor password
        assert HideURLPassword('ftp://host/dir') == 'ftp://host/dir'

        # Username
        assert HideURLPassword('ftp://user@host/dir') == 'ftp://USERNAME:PASSWORD@host/dir'

        # Username and password
        assert HideURLPassword('ftp://user:pass@host/dir') == 'ftp://USERNAME:PASSWORD@host/dir'

        # Other URLS
        assert HideURLPassword('http://user:pass@host/dir') == 'http://USERNAME:PASSWORD@host/dir'
        assert HideURLPassword('https://user:pass@host/dir') == 'https://USERNAME:PASSWORD@host/dir'
        assert HideURLPassword('file://user:pass@host/dir') == 'file://USERNAME:PASSWORD@host/dir'
