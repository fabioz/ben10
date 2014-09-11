from __future__ import unicode_literals
from urllib2 import HTTPError, HTTPPasswordMgrWithDefaultRealm, ProxyBasicAuthHandler
import urllib
import urllib2



#===================================================================================================
# EsssHttpProtocol
#===================================================================================================
class EsssHttpProtocol(object):
    '''
    Implements ESSS HTTP Protocol variations.

    This protocol is used instead of the default HTTP protocol to communicate with ESSS server,
    performing the security communication if necessary.

    Currently, the security is performed by checking the user agent.
    '''

    DEFAULT_BLOCK_SIZE = 8 * 1024

    def __init__(self, on_proxy_settings_request=None, on_proxy_authentication_request=None):
        '''
        :param callable on_proxy_address_request:
            Callable responsible for return the full proxy address.
            E.g.: fenix.fln.esss.com.br:3128

        :param callable on_proxy_authentication_request:
            Callable responsible for return the user and password.
            Both values must be a string.
        '''
        self._user_agent = "ESSS"
        self._on_proxy_address_request = on_proxy_settings_request
        self._on_proxy_authentication_request = on_proxy_authentication_request


    def _CreateRequest(self, url, additional_user_agent_params=[]):
        '''
        Create a Request with our user agent in it.

        :param str url:
            The url to be opened.

        :type additional_user_agent_params: list( str )
        :param additional_user_agent_params:
            The "User-Agent" request header at HTTP protocol contains information about the user
            agent originating the request. By default the User-Agent is ESSS but additional tokens
            and comments can be added to identify the agent and/or any subproduct of it.

        :rtype: Request
        :returns:
            The url request.
        '''
        user_agent = self._user_agent
        user_agent = '/'.join([user_agent] + additional_user_agent_params)

        headers = {'User-Agent':user_agent}
        return urllib2.Request(url, headers=headers)


    def _URLOpenBehindProxyAuthentication(self, request, post_dict):
        '''
        Open the given request providing support for proxy authentication.

        :param Request request:
            The URL request.

        :param str post_dict:
            String with a sequence of two-element tuples or dict encoded for POST requests.
            See urllib.urlencode.

        :rtype: file
        :returns:
            The file containing the url request contents.
        '''
        user, password = self._on_proxy_authentication_request(request)

        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, self._on_proxy_address_request(), user, password)

        proxy_authentication_handler = ProxyBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(proxy_authentication_handler)

        urllib2.install_opener(opener)
        result = urllib2.urlopen(request, post_dict)

        return result


    def URLOpen(self, url, post_dict=None, additional_user_agent_params=[]):
        '''
        Request to open the given url.

        :param str url:
            The url to be opened.

        :type post_dict: list( tuple(str, str) ) or dict or None or str
        :param post_dict:
            Information that will be taken as POST parameters.

            If post_dict is not a string, it'll be passed to urllib.urlencode (otherwise, if a
            string, clients are expected to use urllib.urlencode before passing the parameter to
            this function).

        :type additional_user_agent_params: list( str )
        :param additional_user_agent_params:
            The "User-Agent" request header at HTTP protocol contains information about the user
            agent originating the request. By default the User-Agent is ESSS but additional tokens
            and comments can be added to identify the agent and/or any subproduct of it.

        :rtype: file
        :returns:
            File with the url contents.
        '''
        request = self._CreateRequest(url, additional_user_agent_params)
        try:
            if post_dict is not None and not isinstance(post_dict, str):
                post_dict = urllib.urlencode(post_dict)
            result = urllib2.urlopen(request, post_dict)

        except HTTPError, e:
            error_code = e.code

            # If the code error is 407 (Proxy Authentication Required) and there is a callback
            # to request user and password, this service will try to open the given url again.
            if error_code == 407 and self._on_proxy_authentication_request is not None:
                result = self._URLOpenBehindProxyAuthentication(request, post_dict)
            else:
                raise

        return result


    def GetFileContents(self, url):
        '''
        Returns the contents of the given url file.

        :param str url:
            A file url. This method was intended for a text file, not binary files.
        '''
        url_file = self.URLOpen(url)

        # Obtain encoding from headers (taken from http://stackoverflow.com/questions/1020892/urllib2-read-to-unicode)
        import cgi
        _, params = cgi.parse_header(url_file.headers.get('Content-Type', ''))
        encoding = params.get('charset', 'utf-8')

        return url_file.read().decode(encoding)


    def DownloadFile(self, url, target_filename, report_hook=None, block_size=None, additional_user_agent_params=[]):
        '''
        Download a file from the given url. Saves it in the given name (target_filename).

        :param str url:
            The remote file url to download

        :param str target_filename:
            The local filename to save the file.

        :type report_hook: callable(read_size, total_size)
        :param report_hook:
            Called during the file download with the current read-size and total-size. If HTTP
            server do not provide the content-length information total_size is always -1.

        :param int block_size:
            The size of the read block. This defaults to DEFALT_BLOCK_SIZE. This is intended for
            debug purposes.

        :type additional_user_agent_params: list( str )
        :param additional_user_agent_params:
            The "User-Agent" request header at HTTP protocol contains information about the user
            agent originating the request. By default the User-Agent is ESSS but additional tokens
            and comments can be added to identify the agent and/or any subproduct of it.

        @raises:
            Raises the same exception of urllib2.urlopen, that is, HTTPError and URLError.

        :rtype: bool
        :returns:
            The final state of the download. True if the download ends successful; otherwise False.
        '''
        if report_hook is None:
            report_hook = lambda read_size, total_size: True

        if block_size is None:
            block_size = self.DEFAULT_BLOCK_SIZE


        source_file = self.URLOpen(url, additional_user_agent_params=additional_user_agent_params)

        result = False
        try:
            target_file = file(target_filename, 'wb')
            try:
                read_size = 0
                total_size = int(source_file.info().get('content-length', '-1'))

                while report_hook(read_size, total_size):
                    block = source_file.read(block_size)
                    block_len = len(block)
                    if block_len == 0:
                        result = True
                        break
                    read_size += block_len
                    target_file.write(block)
            finally:
                target_file.close()
        finally:
            source_file.close()

        # If the download was interrupted, the target file must be deleted.
        if result == False:
            import os
            if os.path.isfile(target_filename):
                os.remove(target_filename)

        return result
