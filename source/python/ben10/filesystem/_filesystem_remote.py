from __future__ import unicode_literals
from contextlib import closing
from ftputil.error import FTPIOError, FTPOSError, PermanentError
import ftplib
import ftputil



#===================================================================================================
# FTPHost
#===================================================================================================
# Always use UTF-8 in ftputil, otherwise it sometimes uses UTF-8, and other times latin-1
ftputil.tool.LOSSLESS_ENCODING = 'UTF-8'
class _MyFTP(ftplib.FTP):
    def __init__(self, host='', user='', passwd='', acct='', port=ftplib.FTP.port):
        # Must call parent constructor without any parameter so it don't try to perform
        # the connect without the port parameter (it have the same "if host" code in there)
        ftplib.FTP.__init__(self)

        if host:
            self.connect(host, port)

            if user:
                self.login(user, passwd, acct)
            else:
                self.login()

        # Use active FTP by default
        self.set_pasv(False)


    # ftplib does not support unicode in Python < 3
    # This was taken from http://stackoverflow.com/a/10691041
    def putline(self, line):
        line = line + '\r\n'
        if isinstance(line, unicode):
            line = line.encode('UTF-8')
        self.sock.sendall(line)


class _MyPassiveFTP(_MyFTP):
    def __init__(self, *args, **kwargs):
        _MyFTP.__init__(self, *args, **kwargs)
        self.makepasv()
        self.set_pasv(True)


def FTPHost(url):
    '''
    Create an ftputil.FTPHost instance at the target url. Configure the host to correctly use the
    url's port.

    :param ParseResult url:
        As returned by urlparse.urlparse

    :rtype: ftputil.FTPHost
    '''
    from functools import partial
    create_host = partial(
        ftputil.FTPHost,
        url.hostname,
        url.username,
        url.password,
        port=url.port
    )

    try:
        import sys

        # In Windows, use Active FTP by default
        if sys.platform == 'win32':
            host = create_host(session_factory=_MyFTP)

            # Check if a simple operation fails in active ftp, if it does, switch to passive ftp
            try:
                host.stat('~')
            except Exception, e:
                if e.errno in [425, 500]:
                    # 425 = Errno raised when trying to a server without active ftp
                    # 500 = Illegal PORT command. In this case we also want to try passive mode.
                    host = create_host(session_factory=_MyPassiveFTP)

            return host

        # In Linux, use Passive FTP by default
        else:
            try:
                return create_host(session_factory=_MyPassiveFTP)
            except:
                # If we cant use Passive FTP, fallback to Active (this can happen if the server does
                # not accept PASV command).
                return create_host(session_factory=_MyFTP)


    except FTPOSError, e:
        if e.args[0] in [11004, -3]:
            from ben10.foundation.reraise import Reraise
            Reraise(
                e,
                'Could not connect to host "%s"\n'
                'Make sure that:\n'
                '- You have a working network connection\n'
                '- This hostname is valid\n'
                '- This hostname is not being blocked by a firewall\n' % url.hostname,
            )
        raise



#===================================================================================================
# FTPUploadFileToUrl
#===================================================================================================
def FTPUploadFileToUrl(source_filename, target_url):
    '''
    Uploads the given LOCAL file to the given ftp url.

    :param unicode source_filename:
        The local filename to copy from.

    :param ParseResult target_url:
        The target directory.

        A parsed url as returned by urlparse.urlparse
    '''
    with closing(FTPHost(target_url)) as ftp_host:
        ftp_host.upload(source_filename, target_url.path)



#===================================================================================================
# DownloadUrlToFile
#===================================================================================================
def DownloadUrlToFile(source_url, target_filename):
    '''
    Downloads file in source_url to target_filename

    :param ParseResult source_url:
        A parsed url as returned by urlparse.urlparse

    :param unicode target_filename:
        A target filename
    '''
    try:
        if source_url.scheme == 'ftp':
            return _FTPDownload(source_url, target_filename)

        # Use shutil for other schemes
        iss = OpenFile(source_url)
        try:
            with file(target_filename, 'wb') as oss:
                import shutil
                shutil.copyfileobj(iss, oss)
        finally:
            iss.close()
    except FTPIOError, e:
        if e.errno == 550:
            from _filesystem_exceptions import FileNotFoundError
            raise FileNotFoundError(source_url.path)
        raise



#===================================================================================================
# OpenFile
#===================================================================================================
def OpenFile(filename_url, binary=False, encoding=None):
    '''
    :param ParseResult filename_url:
        Target file to be opened

        A parsed url as returned by urlparse.urlparse

    :param binary:
        .. seealso:: ben10.filesystem.OpenFile

    :param encoding:
        .. seealso:: ben10.filesystem.OpenFile

    :returns file:
        The open file

    @raise: FileNotFoundError
        When the given filename cannot be found

    @raise: CantOpenFileThroughProxyError
        When trying to access a file through a proxy, using a protocol not supported by urllib

    @raise: DirectoryNotFoundError
        When trying to access a remote directory that does not exist

    @raise: ServerTimeoutError
        When failing to connect to a remote server
    '''

    if filename_url.scheme == 'ftp':
        try:
            return _FTPOpenFile(filename_url, binary=binary, encoding=encoding)
        except FTPIOError, e:
            if e.errno == 550:
                from _filesystem_exceptions import FileNotFoundError
                raise FileNotFoundError(filename_url.path)
            raise

    try:
        import urllib
        return urllib.urlopen(filename_url.geturl(), None)
    except IOError, e:
        # Raise better errors than the ones given by urllib
        import errno
        filename = filename_url.path
        if e.errno == errno.ENOENT:  # File does not exist
            from _filesystem_exceptions import FileNotFoundError  # @Reimport
            raise FileNotFoundError(filename)

        if 'proxy' in unicode(e.strerror):
            from _filesystem_exceptions import CantOpenFileThroughProxyError
            raise CantOpenFileThroughProxyError(filename)

        if '550' in unicode(e.strerror):
            from _filesystem_exceptions import DirectoryNotFoundError
            raise DirectoryNotFoundError(filename)

        if '11001' in unicode(e.strerror):
            from _filesystem_exceptions import ServerTimeoutError
            raise ServerTimeoutError(filename)

        # If it's another error, just raise it again.
        raise e



def _FTPDownload(source_url, target_filename):
    '''
    Downloads a file through FTP

    .. see:: DownloadUrlToFile
        for param docs
    '''
    with closing(FTPHost(source_url)) as ftp_host:
        ftp_host.download(source=source_url.path, target=target_filename)


def _FTPOpenFile(filename_url, binary=False, encoding=None):
    '''
    Opens a file (FTP only) and sets things up to close ftp connection when the file is closed.

    .. see:: OpenFile
        for param docs
    '''
    ftp_host = FTPHost(filename_url)
    try:
        mode = 'r'
        if binary:
            mode += 'b'
            encoding = None

        open_file = ftp_host.open(filename_url.path, mode, encoding=encoding)

        # Set it up so when open_file is closed, ftp_host closes too
        def FTPClose():
            # Before closing, remove callback to avoid recursion, since ftputil closes all files
            # it has
            from ben10.foundation.callback import Remove
            Remove(open_file.close, FTPClose)

            ftp_host.close()

        from ben10.foundation.callback import After
        After(open_file.close, FTPClose)

        return open_file
    except:
        ftp_host.close()
        raise



#===================================================================================================
# FTPCreateFile
#===================================================================================================
def FTPCreateFile(url, contents, binary=False, encoding=None):
    '''
    Creates a file in a ftp server.

    :param ParseResult url:
        File to be created.
        A parsed url as returned by urlparse.urlparse

    :param contents:
        .. seealso:: ben10.filesystem.CreateFile

    :param binary:
        .. seealso:: ben10.filesystem.CreateFile

    :param encoding:
        .. seealso:: ben10.filesystem.CreateFile
    '''
    mode = 'wb' if binary else 'w'
    with closing(FTPHost(url)) as ftp_host:
        with ftp_host.open(url.path, mode, encoding=encoding) as oss:
            oss.write(contents)


#===================================================================================================
# FTPIsFile
#===================================================================================================
def FTPIsFile(url):
    '''
    :param ParseResult url:
        URL for file we want to check

    :returns bool:
        True if file exists.
    '''
    with closing(FTPHost(url)) as ftp_host:
        try:
            return ftp_host.path.isfile(url.path)
        except PermanentError, e:
            if e.errno == 550:
                # "No such file or directory"
                return False
            else:
                raise



#===================================================================================================
# FTPCreateDirectory
#===================================================================================================
def FTPCreateDirectory(url):
    '''
    :param ParseResult url:
        Target url to be created

        A parsed url as returned by urlparse.urlparse
    '''
    with closing(FTPHost(url)) as ftp_host:
        ftp_host.makedirs(url.path)



#===================================================================================================
# FTPMoveDirectory
#===================================================================================================
def FTPMoveDirectory(source_url, target_url):
    '''
    :param ParseResult url:
        Target url to be created

        A parsed url as returned by urlparse.urlparse
    '''
    with closing(FTPHost(source_url)) as ftp_host:
        ftp_host.rename(source_url.path, target_url.path)



#===================================================================================================
# FTPIsDir
#===================================================================================================
def FTPIsDir(url):
    '''
    List files in a url

    :param ParseResult url:
        Directory url we are checking

        A parsed url as returned by urlparse.urlparse

    :rtype: bool
    :returns:
        True if url is an existing dir
    '''
    with closing(FTPHost(url)) as ftp_host:
        try:
            # NOTE: Raising an error because ftputil enters a infinite loop if the path starts with
            # two slashes.
            assert not url.path.startswith('//'), "Invalid URL: Path starts with two slashes."
            return ftp_host.path.isdir(url.path)
        except PermanentError, e:
            if e.errno == 550:
                # "No such file or directory"
                return False
            else:
                raise



#===================================================================================================
# FTPListFiles
#===================================================================================================
def FTPListFiles(url):
    '''
    List files in a url

    :param ParseResult url:
        Target url being searched for files

        A parsed url as returned by urlparse.urlparse

    :rtype: list(unicode) or None
    :returns:
        List of files, or None if directory does not exist (error 550 CWD)
    '''
    with closing(FTPHost(url)) as ftp_host:
        try:
            # NOTE: Raising an error because ftputil enters a infinite loop if the path starts with
            # two slashes.
            assert not url.path.startswith('//'), "Invalid URL: Path starts with two slashes."
            return ftp_host.listdir(url.path)
        except PermanentError, e:
            if e.errno == 550:
                # "No such file or directory"
                return None
            else:
                raise
