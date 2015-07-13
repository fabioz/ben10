from __future__ import unicode_literals
from ben10.esss_http_protocol import EsssHttpProtocol
from ben10.filesystem import CreateFile
from ben10.phony_http_server import PhonyHTTPServer, ProxyHandler
from urllib2 import HTTPError
import os
import pytest


class _FixRegex(object):
    '''
    Applies a list of fixes (subn patterns) in a list of lines.

    This is used as shortcut for AssertEqualFiles fix_callback parameter.
    '''

    def __init__(self, fixes):
        self.__fixes = fixes

    def __call__(self, lines):
        import re
        contents = '\n'.join(lines)
        for i_pattern, i_repl in self.__fixes:
            contents = re.subn(i_pattern, i_repl, contents)[0]
        return contents.split('\n')



def _DoTestDownloadFile(embed_data, expected_filename, additional_user_agent_params=[]):
    server, port = PhonyHTTPServer.CreateAndStart()
    try:
        protocol = EsssHttpProtocol()
        protocol.DownloadFile(
            'http://127.0.0.1:%s/anyfile.txt' % port,
            embed_data['testDownloadFile.txt'],
            additional_user_agent_params=additional_user_agent_params,
        )
        #self.FixFile(embed_data['testDownloadFile.txt'], [('\:\d+', ':XXXXX')])
        embed_data.AssertEqualFiles(
            embed_data['testDownloadFile.txt'],
            embed_data[expected_filename],
            _FixRegex([('\:\d+', ':XXXXX')])
        )
        # self.assertContentsEqual(
        #     embed_data['testDownloadFile.txt'],
        #     embed_data[expected_filename]
        # )
    finally:
        server.stop()
        ProxyHandler.Reset()


def testOpenURLWithPostData():
    server, port = PhonyHTTPServer.CreateAndStart()
    try:
        protocol = EsssHttpProtocol()
        post_dict = {
            'project_id' : 110,  # Simentar project ID
            'category' : 'Rework',
            'target_version': 'Future',
            'summary' : 'Test error summary',
            'description' : 'Test error description...',
            'steps_to_reproduce' : 'Test steps to reproduce',
            'additional_information' : 'Test additional information'
        }
        protocol.URLOpen('http://127.0.0.1:%s/anyfile.txt' % port, post_dict=post_dict)
    finally:
        server.stop()
        ProxyHandler.Reset()



def testFileContents(embed_data):
    server, port = PhonyHTTPServer.CreateAndStart()
    try:
        obtained_filename = embed_data['testFileContents.txt']
        expected_filename = embed_data['anyfile.expected.txt']

        protocol = EsssHttpProtocol()
        contents = protocol.GetFileContents('http://127.0.0.1:%s/anyfile.txt' % port)
        CreateFile(obtained_filename, contents)
        embed_data.AssertEqualFiles(
            obtained_filename,
            expected_filename,
            _FixRegex([('\:\d+', ':XXXXX')]),
        )
    finally:
        server.stop()
        ProxyHandler.Reset()


def testDownloadFile(embed_data):
    _DoTestDownloadFile(embed_data, 'anyfile.expected.txt')


def testDownloadFileWithReportHook(embed_data):
    report_hook = []

    def MyHttpGet(path):
        '''
        Returns the contents that will be returned by the PhonyHTTPServer.
        '''
        return "123456789\n" * 100

    def MyReportHook(read_size, total_size):
        '''
        Implements a report hook that just add the information in the self.report_hook list
        '''
        report_hook.append((read_size, total_size))
        return True

    def MyReportHookWithCancel(read_size, total_size):
        '''
        Implements a report hook that cancels the download (returning False) when the read size
        is greater than 450
        '''
        report_hook.append((read_size, total_size))
        return read_size < 500

    server, port = PhonyHTTPServer.CreateAndStart()
    server.http_get_callback = MyHttpGet
    try:
        protocol = EsssHttpProtocol()
        assert protocol.DownloadFile(
            'http://127.0.0.1:%s/anyfile.txt' % port,
            embed_data['testDownloadFile.txt'],
            report_hook=MyReportHook,
            block_size=100,
        ) == True

        # The number of reports is total size (100 *10) divided by block_size (100) plus one
        # (the first call with read_size == 0)
        assert report_hook[0] == (0, 1000)
        assert len(report_hook) == 11

        # Check the number of lines to match the value implement in "MyHttpGet"
        assert os.path.isfile(embed_data['testDownloadFile.txt']) == True
        obtained_file = file(embed_data['testDownloadFile.txt'], 'r')
        try:
            assert len(obtained_file.readlines()) == 100
        finally:
            obtained_file.close()

        # >>> Test cancel via report_hook
        report_hook = []
        assert protocol.DownloadFile(
                'http://127.0.0.1:%s/anyfile.txt' % port,
                embed_data['testDownloadFile.txt'],
                report_hook=MyReportHookWithCancel,
                block_size=100,
            ) == False
        assert os.path.isfile(embed_data['testDownloadFile.txt']) == False

        assert report_hook[0] == (0, 1000)
        assert report_hook[-1] == (500, 1000)
        assert len(report_hook) == 6

    finally:
        server.stop()
        ProxyHandler.Reset()


def testRequestsBehindProxy(embed_data):
    '''
    Check the ESSS HTTP protocol behavior behind a proxy with authentication.
    '''

    def OnProxyAddressRequest(*args, **kwargs):
        return 'http://127.0.0.1:%s' % port

    _allow_proxy_authentication = False
    def OnProxyAuthenticationRequest(request):
        login = 'john_doe'
        password = '123456'

        if _allow_proxy_authentication:
            ProxyHandler.login = login
            ProxyHandler.password = password

        return login, password

    server, port = PhonyHTTPServer.CreateAndStart(request_handler=ProxyHandler)
    try:
        protocol = EsssHttpProtocol(OnProxyAddressRequest, OnProxyAuthenticationRequest)

        # Testing exception with GetFileContents
        with pytest.raises(HTTPError):
            protocol.GetFileContents('http://127.0.0.1:%s/invalid_file.txt' % port,)

        # Testing exception with DownloadFile
        with pytest.raises(HTTPError):
            protocol.DownloadFile('http://127.0.0.1:%s/invalid_file.txt' % port,
            embed_data['testDownloadFile.txt'],)

        _allow_proxy_authentication = True
        protocol.GetFileContents('http://127.0.0.1:%s/anyfile.txt' % port)  # Not raises HTTPError
        protocol.DownloadFile('http://127.0.0.1:%s/anyfile.txt' % port, embed_data['testDownloadFile.txt'])  # Not raises HTTPError

    finally:
        server.stop()
        ProxyHandler.Reset()


def testDownloadFileWithUserAgent(embed_data):
    _DoTestDownloadFile(
        embed_data,
        'anyfile_with_user_agent.expected.txt',
        additional_user_agent_params=['User', 'Company', 'Other'],
    )
