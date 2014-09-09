'''
This module contains a selection of file related functions that can be used anywhere.

Some sort of wrapper for common builtin 'os' operations with a nicer interface.

These functions abstract file location, most of them work for either local, ftp or http protocols


#===================================================================================================
# FTP LIMITATIONS:
#===================================================================================================
    Right now, all functions that require a FTP connection are ALWAYS creating and closing a FTP
    Host.

    Keep in mind that this process can be slow if you perform many of such operations in sequence.
'''
import contextlib
import os
import re
import sys



#===================================================================================================
# Constants
#===================================================================================================
SEPARATOR_UNIX = '/'
SEPARATOR_WINDOWS = '\\'
EOL_STYLE_NONE = None  # Binary files
EOL_STYLE_UNIX = '\n'
EOL_STYLE_WINDOWS = '\r\n'
EOL_STYLE_MAC = '\r'

def _GetNativeEolStyle(platform=sys.platform):
    '''
    Internal function that determines EOL_STYLE_NATIVE constant with the proper value for the
    current platform.
    '''
    _NATIVE_EOL_STYLE_MAP = {
        'win32' : EOL_STYLE_WINDOWS,
        'linux2' : EOL_STYLE_UNIX,
        'darwin' : EOL_STYLE_MAC,
    }
    result = _NATIVE_EOL_STYLE_MAP.get(platform)

    if result is None:
        from ._filesystem_exceptions import UnknownPlatformError
        raise UnknownPlatformError(platform)

    return result

EOL_STYLE_NATIVE = _GetNativeEolStyle()

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364939%28v=vs.85%29.aspx
# The drive type cannot be determined.
DRIVE_UNKNOWN = 0
# The root path is invalid; for example, there is no volume mounted at the specified path.
DRIVE_NO_ROOT_DIR = 1
# The drive has removable media; for example, a floppy drive, thumb drive, or flash card reader.
DRIVE_REMOVABLE = 2
# The drive has fixed media; for example, a hard disk drive or flash drive.
DRIVE_FIXED = 3
# The drive is a remote (network) drive.
DRIVE_REMOTE = 4
# The drive is a CD-ROM drive.
DRIVE_CDROM = 5
# The drive is a RAM disk
DRIVE_RAMDISK = 6

#===================================================================================================
# Cwd
#===================================================================================================
@contextlib.contextmanager
def Cwd(directory):
    '''
    Context manager for current directory (uses with_statement)

    e.g.:
        # working on some directory
        with Cwd('/home/new_dir'):
            # working on new_dir

        # working on some directory again

    :param str directory:
        Target directory to enter
    '''
    old_directory = os.getcwd()
    if directory is not None:
        os.chdir(directory)
    try:
        yield directory
    finally:
        os.chdir(old_directory)



#===================================================================================================
# NormalizePath
#===================================================================================================
def NormalizePath(path):
    '''
    Normalizes a path maintaining the final slashes.

    Some environment variables need the final slash in order to work.

    Ex. The SOURCES_DIR set by subversion must end with a slash because of the way it is used
    in the Visual Studio projects.

    :param str path:
        The path to normalize.

    :rtype: str
    :returns:
        Normalized path
    '''
    if path.endswith('/') or path.endswith('\\'):
        slash = os.path.sep
    else:
        slash = ''
    return os.path.normpath(path) + slash


#===================================================================================================
# CanonicalPath
#===================================================================================================
def CanonicalPath(path):
    '''
    Returns a version of a path that is unique.

    Given two paths path1 and path2:
        CanonicalPath(path1) == CanonicalPath(path2) if and only if they represent the same file on
        the host OS. Takes account of case, slashes and relative paths.

    :param str path:
        The original path.

    :rtype: str
    :returns:
        The unique path.
    '''
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    path = os.path.normcase(path)

    return path


#===================================================================================================
# StandardizePath
#===================================================================================================
def StandardizePath(path, strip=False):
    '''
    Replaces all slashes and backslashes with the target separator

    StandardPath:
        We are defining that the standard-path is the one with only back-slashes in it, either
        on Windows or any other platform.

    :param bool strip:
        If True, removes additional slashes from the end of the path.
    '''
    path = path.replace(SEPARATOR_WINDOWS, SEPARATOR_UNIX)
    if strip:
        path = path.rstrip(SEPARATOR_UNIX)
    return path



#===================================================================================================
# NormStandardPath
#===================================================================================================
def NormStandardPath(path):
    '''
    Normalizes a standard path (posixpath.normpath) maintaining any slashes at the end of the path.

    Normalize:
        Removes any local references in the path "/../"

    StandardPath:
        We are defining that the standard-path is the one with only back-slashes in it, either
        on Windows or any other platform.
    '''
    import posixpath
    if path.endswith('/'):
        slash = '/'
    else:
        slash = ''
    return posixpath.normpath(path) + slash



#===================================================================================================
# CreateMD5
#===================================================================================================
def CreateMD5(source_filename, target_filename=None):
    '''
    Creates a md5 file from a source file (contents are the md5 hash of source file)

    :param str source_filename:
        Path to source file

    :type target_filename: str or None
    :param target_filename:
        Name of the target file with the md5 contents

        If None, defaults to source_filename + '.md5'
    '''
    from ben10.foundation.hash import Md5Hex

    if target_filename is None:
        target_filename = source_filename + '.md5'

    from urlparse import urlparse
    source_url = urlparse(source_filename)

    # Obtain MD5 hex
    if _UrlIsLocal(source_url):
        # If using a local file, we can give Md5Hex the filename
        md5_contents = Md5Hex(filename=source_filename)
    else:
        # Md5Hex can't handle remote files, we open it and pray we won't run out of memory.
        md5_contents = Md5Hex(contents=GetFileContents(source_filename))

    # Write MD5 hash to a file
    CreateFile(target_filename, md5_contents)



MD5_SKIP = 'md5_skip'  # Returned to show that a file copy was skipped because it hasn't changed.
#===================================================================================================
# CopyFile
#===================================================================================================
def CopyFile(source_filename, target_filename, override=True, md5_check=False, copy_symlink=True):
    '''
    Copy a file from source to target.

    :param  source_filename:
        @see _DoCopyFile

    :param  target_filename:
        @see _DoCopyFile

    :param bool md5_check:
        If True, checks md5 files (of both source and target files), if they match, skip this copy
        and return MD5_SKIP

        Md5 files are assumed to be {source, target} + '.md5'

        If any file is missing (source, target or md5), the copy will always be made.

    :param  copy_symlink:
        @see _DoCopyFile

    :raises FileAlreadyExistsError:
        If target_filename already exists, and override is False

    :raises NotImplementedProtocol:
        If file protocol is not accepted

        Protocols allowed are:
            source_filename: local, ftp, http
            target_filename: local, ftp

    :rtype: None | MD5_SKIP
    :returns:
        MD5_SKIP if the file was not copied because there was a matching .md5 file

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from ben10.filesystem import FileNotFoundError

    # Check override
    if not override and Exists(target_filename):
        from ._filesystem_exceptions import FileAlreadyExistsError
        raise FileAlreadyExistsError(target_filename)

    # Don't do md5 check for md5 files themselves.
    md5_check = md5_check and not target_filename.endswith('.md5')

    # If we enabled md5 checks, ignore copy of files that haven't changed their md5 contents.
    if md5_check:
        source_md5_filename = source_filename + '.md5'
        target_md5_filename = target_filename + '.md5'
        try:
            source_md5_contents = GetFileContents(source_md5_filename)
        except FileNotFoundError:
            source_md5_contents = None

        try:
            target_md5_contents = GetFileContents(target_md5_filename)
        except FileNotFoundError:
            target_md5_contents = None

        if source_md5_contents is not None and \
           source_md5_contents == target_md5_contents and \
           Exists(target_filename):
            return MD5_SKIP

    # Copy source file
    _DoCopyFile(source_filename, target_filename, copy_symlink=copy_symlink)

    # If we have a source_md5, but no target_md5, create the target_md5 file
    if md5_check and source_md5_contents is not None and source_md5_contents != target_md5_contents:
        CreateFile(target_md5_filename, source_md5_contents)


def _DoCopyFile(source_filename, target_filename, copy_symlink=True):
    '''
    :param str source_filename:
        The source filename.
        Schemas: local, ftp, http

    :param str target_filename:
        Target filename.
        Schemas: local, ftp

    :param  copy_symlink:
        @see _CopyFileLocal

    :raises FileNotFoundError:
        If source_filename does not exist
    '''
    from urlparse import urlparse

    source_url = urlparse(source_filename)
    target_url = urlparse(target_filename)

    if _UrlIsLocal(source_url):
        if not Exists(source_filename):
            from ben10.filesystem import FileNotFoundError
            raise FileNotFoundError(source_filename)

        if _UrlIsLocal(target_url):
            # local to local
            _CopyFileLocal(source_filename, target_filename, copy_symlink=copy_symlink)
        elif target_url.scheme in ['ftp']:
            # local to remote
            from _filesystem_remote import FTPUploadFileToUrl
            FTPUploadFileToUrl(source_filename, target_url)
        else:
            from ._filesystem_exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)

    elif source_url.scheme in ['http', 'ftp']:
        if _UrlIsLocal(target_url):
            # HTTP/FTP to local
            from _filesystem_remote import DownloadUrlToFile
            DownloadUrlToFile(source_url, target_filename)
        else:
            # HTTP/FTP to other ==> NotImplemented
            from ._filesystem_exceptions import NotImplementedProtocol
            raise NotImplementedProtocol(target_url.scheme)
    else:
        from ._filesystem_exceptions import NotImplementedProtocol  # @Reimport
        raise NotImplementedProtocol(source_url.scheme)


def _CopyFileLocal(source_filename, target_filename, copy_symlink=True):
    '''
    Copy a file locally to a directory.

    :param str source_filename:
        The filename to copy from.

    :param str target_filename:
        The filename to copy to.

    :param bool copy_symlink:
        If True and source_filename is a symlink, target_filename will also be created as
        a symlink.

        If False, the file being linked will be copied instead.
    '''
    import shutil
    try:
        # >>> Create the target_filename directory if necessary
        dir_name = os.path.dirname(target_filename)
        if dir_name and not os.path.isdir(dir_name):
            os.makedirs(dir_name)

        if copy_symlink and IsLink(source_filename):
            # >>> Delete the target_filename if it already exists
            if os.path.isfile(target_filename) or IsLink(target_filename):
                DeleteFile(target_filename)

            # >>> Obtain the relative path from link to source_filename (linkto)
            source_filename = ReadLink(source_filename)
            CreateLink(source_filename, target_filename)
        else:
            # shutil can't copy links in Windows, so we must find the real file manually
            if sys.platform == 'win32':
                while IsLink(source_filename):
                    link = ReadLink(source_filename)
                    if os.path.isabs(link):
                        source_filename = link
                    else:
                        source_filename = os.path.join(os.path.dirname(source_filename), link)

            shutil.copyfile(source_filename, target_filename)
            shutil.copymode(source_filename, target_filename)
    except Exception, e:
        from ben10.foundation.reraise import Reraise
        Reraise(e, 'While executiong _filesystem._CopyFileLocal(%s, %s)' % (source_filename, target_filename))



#===================================================================================================
# CopyFiles
#===================================================================================================
def CopyFiles(source_dir, target_dir, create_target_dir=False, md5_check=False):
    '''
    Copy files from the given source to the target.

    :param str source_dir:
        A filename, URL or a file mask.
        Ex.
            x:\coilib50
            x:\coilib50\*
            http://server/directory/file
            ftp://server/directory/file


    :param str target_dir:
        A directory or an URL
        Ex.
            d:\Temp
            ftp://server/directory

    :param bool create_target_dir:
        If True, creates the target path if it doesn't exists.

    :param bool md5_check:
        .. seealso:: CopyFile

    :raises DirectoryNotFoundError:
        If target_dir does not exist, and create_target_dir is False

    .. seealso:: CopyFile for documentation on accepted protocols

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    import fnmatch

    # Check if we were given a directory or a directory with mask
    if IsDir(source_dir):
        # Yes, it's a directory, copy everything from it
        source_mask = '*'
    else:
        # Split directory and mask
        source_dir, source_mask = os.path.split(source_dir)

    # Create directory if necessary
    if not IsDir(target_dir):
        if create_target_dir:
            CreateDirectory(target_dir)
        else:
            from ._filesystem_exceptions import DirectoryNotFoundError
            raise DirectoryNotFoundError(target_dir)

    # List and match files
    filenames = ListFiles(source_dir)

    # Check if we have a source directory
    if filenames is None:
        return

    # Copy files
    for i_filename in filenames:
        if md5_check and i_filename.endswith('.md5'):
            continue  # md5 files will be copied by CopyFile when copying their associated files

        if fnmatch.fnmatch(i_filename, source_mask):
            source_path = source_dir + '/' + i_filename
            target_path = target_dir + '/' + i_filename

            if IsDir(source_path):
                # If we found a directory, copy it recursively
                CopyFiles(source_path, target_path, create_target_dir=True, md5_check=md5_check)
            else:
                CopyFile(source_path, target_path, md5_check=md5_check)



#===================================================================================================
# CopyFilesX
#===================================================================================================
def CopyFilesX(file_mapping):
    '''
    Copies files into directories, according to a file mapping

    :param list(tuple(str,str)) file_mapping:
        A list of mappings between the directory in the target and the source.
        For syntax, @see: ExtendedPathMask

    :rtype: list(tuple(str,str))
    :returns:
        List of files copied. (source_filename, target_filename)

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from ._duplicates import ExtendedPathMask, FindFiles

    # List files that match the mapping
    files = []
    for i_target_path, i_source_path_mask in file_mapping:
        tree_recurse, flat_recurse, dirname, in_filters, out_filters = ExtendedPathMask.Split(i_source_path_mask)

        _AssertIsLocal(dirname)

        filenames = FindFiles(dirname, in_filters, out_filters, tree_recurse)
        for i_source_filename in filenames:
            if os.path.isdir(i_source_filename):
                continue  # Do not copy dirs

            i_target_filename = i_source_filename[len(dirname) + 1:]
            if flat_recurse:
                i_target_filename = os.path.basename(i_target_filename)
            i_target_filename = os.path.join(i_target_path, i_target_filename)

            files.append((
                StandardizePath(i_source_filename),
                StandardizePath(i_target_filename)
            ))

    # Copy files
    for i_source_filename, i_target_filename in files:
        # Create target dir if necessary
        target_dir = os.path.dirname(i_target_filename)
        CreateDirectory(target_dir)

        CopyFile(i_source_filename, i_target_filename)

    return files



#===================================================================================================
# IsFile
#===================================================================================================
def IsFile(path):
    '''
    :param str path:
        Path to a file (local or ftp)

    :raises NotImplementedProtocol:
        If checking for a non-local, non-ftp file

    :rtype: bool
    :returns:
        True if the file exists

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse
    url = urlparse(path)

    if _UrlIsLocal(url):
        if IsLink(path):
            return IsFile(ReadLink(path))
        return os.path.isfile(path)

    elif url.scheme == 'ftp':
        from ben10.filesystem._filesystem_remote import FTPIsFile
        return FTPIsFile(url)
    else:
        from ben10.filesystem import NotImplementedProtocol
        raise NotImplementedProtocol(url.scheme)


def GetDriveType(path):
    '''
    Determine the type of drive, which can be one of the following values:
        DRIVE_UNKNOWN = 0
            The drive type cannot be determined.

        DRIVE_NO_ROOT_DIR = 1
            The root path is invalid; for example, there is no volume mounted at the specified path.

        DRIVE_REMOVABLE = 2
            The drive has removable media; for example, a floppy drive, thumb drive, or flash card reader.

        DRIVE_FIXED = 3
            The drive has fixed media; for example, a hard disk drive or flash drive.

        DRIVE_REMOTE = 4
            The drive is a remote (network) drive.

        DRIVE_CDROM = 5
            The drive is a CD-ROM drive.

        DRIVE_RAMDISK = 6
            The drive is a RAM disk

    :note:
        The implementation is valid only for Windows OS
        Linux will always return DRIVE_UNKNOWN

    :param path:
        Path to a file or directory
    '''
    if sys.platform == 'win32':
        import win32file
        if IsFile(path):
            path = os.path.dirname(path)

        # A trailing backslash is required.
        return win32file.GetDriveType(path + '\\')

    else:
        return DRIVE_UNKNOWN




#===================================================================================================
# IsDir
#===================================================================================================
def IsDir(directory):
    '''
    :param str directory:
        A path

    :rtype: bool
    :returns:
        Returns whether the given path points to an existent directory.

    :raises NotImplementedProtocol:
        If the path protocol is not local or ftp

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse
    directory_url = urlparse(directory)

    if _UrlIsLocal(directory_url):
        return os.path.isdir(directory)
    elif directory_url.scheme == 'ftp':
        from ben10.filesystem._filesystem_remote import FTPIsDir
        return FTPIsDir(directory_url)
    else:
        from ._filesystem_exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# Exists
#===================================================================================================
def Exists(path):
    '''
    :rtype: bool
    :returns:
        True if the path already exists (either a file or a directory)

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse
    path_url = urlparse(path)

    # Handle local
    if _UrlIsLocal(path_url):
        return IsFile(path) or IsDir(path) or IsLink(path)
    return IsFile(path) or IsDir(path)



#===================================================================================================
# CopyDirectory
#===================================================================================================
def CopyDirectory(source_dir, target_dir, override=False):
    '''
    Recursively copy a directory tree.

    :param str source_dir:
        Where files will come from

    :param str target_dir:
        Where files will go to

    :param bool override:
        If True and target_dir already exists, it will be deleted before copying.

    :raises NotImplementedForRemotePathError:
        If trying to copy to/from remote directories
    '''
    _AssertIsLocal(source_dir)
    _AssertIsLocal(target_dir)

    if override and IsDir(target_dir):
        DeleteDirectory(target_dir, skip_on_error=False)

    import shutil
    shutil.copytree(source_dir, target_dir)



#===================================================================================================
# DeleteFile
#===================================================================================================
def DeleteFile(target_filename):
    '''
    Deletes the given local filename.

    .. note:: If file doesn't exist this method has no effect.

    :param str target_filename:
        A local filename

    :raises NotImplementedForRemotePathError:
        If trying to delete a non-local path

    :raises FileOnlyActionError:
        Raised when filename refers to a directory.
    '''
    _AssertIsLocal(target_filename)

    try:
        if IsLink(target_filename):
            DeleteLink(target_filename)
        elif IsFile(target_filename):
            os.remove(target_filename)
        elif IsDir(target_filename):
            from ._filesystem_exceptions import FileOnlyActionError
            raise FileOnlyActionError(target_filename)
    except Exception, e:
        from ben10.foundation.reraise import Reraise
        Reraise(e, 'While executing filesystem.DeleteFile(%s)' % (target_filename))



#===================================================================================================
# AppendToFile
#===================================================================================================
def AppendToFile(filename, contents, eol_style=EOL_STYLE_NATIVE, encoding=None):
    '''
    Appends content to a local file.

    :param str filename:

    :param str contents:

    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
        Replaces the EOL by the appropriate EOL depending on the eol_style value.
        Considers that all content is using only "\n" as EOL.

    :param str encoding:
        Target file's content encoding.

    :raises NotImplementedForRemotePathError:
        If trying to modify a non-local path

    :raises ValueError:
        If trying to mix unicode `contents` without `encoding`, or `encoding` without
        unicode `contents`
    '''
    _AssertIsLocal(filename)

    # Unicode
    unicode_contents = isinstance(contents, unicode)
    use_encoding = encoding is not None
    if unicode_contents ^ use_encoding:  # XOR
        raise ValueError('Either use unicode contents with an encoding, or string contents without encoding.')

    if unicode_contents:
        contents = contents.encode(encoding)
    contents = _HandleContentsEol(contents, eol_style)

    oss = open(filename, 'ab')
    try:
        oss.write(contents)
    finally:
        oss.close()



#===================================================================================================
# MoveFile
#===================================================================================================
def MoveFile(source_filename, target_filename):
    '''
    Moves a file.

    :param str source_filename:

    :param str target_filename:

    :raises NotImplementedForRemotePathError:
        If trying to operate with non-local files.
    '''
    _AssertIsLocal(source_filename)
    _AssertIsLocal(target_filename)

    import shutil
    shutil.move(source_filename, target_filename)



#===================================================================================================
# MoveDirectory
#===================================================================================================
def MoveDirectory(source_dir, target_dir):
    '''
    Moves a directory.

    :param str source_dir:

    :param str target_dir:

    :raises NotImplementedError:
        If trying to move anything other than:
            Local dir -> local dir
            FTP dir -> FTP dir (same host)


    '''
    if not IsDir(source_dir):
        from ._filesystem_exceptions import DirectoryNotFoundError
        raise DirectoryNotFoundError(source_dir)

    if Exists(target_dir):
        from ._filesystem_exceptions import DirectoryAlreadyExistsError
        raise DirectoryAlreadyExistsError(target_dir)

    from urlparse import urlparse
    source_url = urlparse(source_dir)
    target_url = urlparse(target_dir)

    # Local to local
    if _UrlIsLocal(source_url) and _UrlIsLocal(target_url):
        import shutil
        shutil.move(source_dir, target_dir)

    # FTP to FTP
    elif source_url.scheme == 'ftp' and target_url.scheme == 'ftp':
        if source_url.hostname != target_url.hostname:
            raise NotImplementedError('Can only move FTP directories in the same host')

        from ._filesystem_remote import FTPMoveDirectory
        return FTPMoveDirectory(source_url, target_url)
    else:
        raise NotImplementedError('Can only move directories local->local or ftp->ftp')


#===================================================================================================
# GetFileContents
#===================================================================================================
def GetFileContents(filename, binary=False, encoding=None):
    '''
    Reads a file and returns its contents. Works for both local and remote files.

    :param str filename:

    :param bool binary:
        If True returns the file as is, ignore any EOL conversion.

    :param str encoding:
        File's encoding. If not None, contents obtained from file will be decoded using this
        `encoding`.

    :rtype: str | unicode
    :returns:
        The file's contents.
        Returns unicode string when `encoding` is not None.

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    source_file = OpenFile(filename, binary=binary)
    try:
        contents = source_file.read()
    finally:
        source_file.close()

    if encoding is not None:
        contents = contents.decode(encoding)
    return contents


#===================================================================================================
# GetFileLines
#===================================================================================================
def GetFileLines(filename):
    '''
    Reads a file and returns its contents as a list of lines. Works for both local and remote files.

    :param str filename:

    :rtype: list(str)
    :returns:
        The file's lines

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    return GetFileContents(filename, binary=False).split('\n')


def OpenFile(filename, binary=False):
    '''
    Open a file and returns it.
    Consider the possibility of a remote file (HTTP, HTTPS, FTP)

    :param str filename:
        Local or remote filename.

    :param bool binary:
        If True returns the file as is, ignore any EOL conversion.

    :rtype: file
    :returns:
        The open file, it must be closed by the caller

    @raise: FileNotFoundError
        When the given filename cannot be found

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse
    filename_url = urlparse(filename)

    # Check if file is local
    if _UrlIsLocal(filename_url):
        if not os.path.isfile(filename):
            from ._filesystem_exceptions import FileNotFoundError
            raise FileNotFoundError(filename)
        mode = 'r'
        if binary:
            mode += 'b'
        else:
            mode += 'U'
        return file(filename, mode)

    # Not local
    import _filesystem_remote
    return _filesystem_remote.OpenFile(filename_url)



#===================================================================================================
# ListFiles
#===================================================================================================
def ListFiles(directory):
    '''
    Lists the files in the given directory

    :type directory: str | unicode
    :param directory:
        A directory or URL

    :rtype: list(str) | list(unicode)
    :returns:
        List of filenames/directories found in the given directory.
        Returns None if the given directory does not exists.

        If `directory` is a unicode string, all files returned will also be unicode

    :raises NotImplementedProtocol:
        If file protocol is not local or FTP

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse
    directory_url = urlparse(directory)

    # Handle local
    if _UrlIsLocal(directory_url):
        if not os.path.isdir(directory):
            return None
        return os.listdir(directory)

    # Handle FTP
    elif directory_url.scheme == 'ftp':
        from _filesystem_remote import FTPListFiles
        return FTPListFiles(directory_url)

    else:
        from ._filesystem_exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# CheckIsFile
#===================================================================================================
def CheckIsFile(filename):
    '''
    Check if the given file exists.

    @filename: str
        The filename to check for existence.

    @raise: FileNotFoundError
        Raises if the file does not exist.
    '''
    if not IsFile(filename):
        from ._filesystem_exceptions import FileNotFoundError
        raise FileNotFoundError(filename)



#===================================================================================================
# CheckIsDir
#===================================================================================================
def CheckIsDir(directory):
    '''
    Check if the given directory exists.

    @filename: str
        Path to a directory being checked for existence.

    @raise: DirectoryNotFoundError
        Raises if the directory does not exist.
    '''
    if not IsDir(directory):
        from ._filesystem_exceptions import DirectoryNotFoundError
        raise DirectoryNotFoundError(directory)



#===================================================================================================
# CreateFile
#===================================================================================================
def CreateFile(filename, contents, eol_style=EOL_STYLE_NATIVE, create_dir=True, encoding=None):
    '''
    Create a file with the given contents.

    :param str filename:
        Filename and path to be created.

    :param str contents:
        The file contents as a string.

    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
        Replaces the EOL by the appropriate EOL depending on the eol_style value.
        Considers that all content is using only "\n" as EOL.

    :param bool create_dir:
        If True, also creates directories needed in filename's path

    :param str encoding:
        Target file's content encoding.

    :return str:
        Returns the name of the file created.

    :raises NotImplementedProtocol:
        If file protocol is not local or FTP

    :raises ValueError:
        If trying to mix unicode `contents` without `encoding`, or `encoding` without
        unicode `contents`

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    # Unicode
    unicode_contents = isinstance(contents, unicode)
    use_encoding = encoding is not None
    if unicode_contents ^ use_encoding:  # XOR
        raise ValueError('Either use unicode contents with an encoding, or string contents without encoding.')

    if unicode_contents:
        contents = contents.encode(encoding)

    # Replaces eol on each line by the given eol_style.
    contents = _HandleContentsEol(contents, eol_style)

    # If asked, creates directory containing file
    if create_dir:
        dirname = os.path.dirname(filename)
        if dirname:
            CreateDirectory(dirname)

    from urlparse import urlparse
    filename_url = urlparse(filename)

    # Handle local
    if _UrlIsLocal(filename_url):
        with open(filename, 'wb') as oss:
            oss.write(contents)

    # Handle FTP
    elif filename_url.scheme == 'ftp':
        from _filesystem_remote import FTPCreateFile
        FTPCreateFile(filename_url, contents)

    else:
        from ._filesystem_exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(filename_url.scheme)

    return filename



def ReplaceInFile(filename, old, new):
    '''
    Replaces all occurrences of "old" by "new" in the given file.

    :param str filename:
        The name of the file.
    :param str old:
        The string to search for.
    :param str new:
        Replacement string.
    :return str:
        The new contents of the file.
    '''
    content = GetFileContents(filename)
    content = content.replace(old, new)
    CreateFile(filename, content)
    return content



#===================================================================================================
# CreateDirectory
#===================================================================================================
def CreateDirectory(directory):
    '''
    Create directory including any missing intermediate directory.

    :param str directory:

    :return str|urlparse.ParseResult:
        Returns the created directory or url (see urlparse).

    :raises NotImplementedProtocol:
        If protocol is not local or FTP.

    .. seealso:: FTP LIMITATIONS at this module's doc for performance issues information
    '''
    from urlparse import urlparse

    directory_url = urlparse(directory)

    # Handle local
    if _UrlIsLocal(directory_url):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    # Handle FTP
    elif directory_url.scheme == 'ftp':
        from _filesystem_remote import FTPCreateDirectory
        FTPCreateDirectory(directory_url)
        return directory_url

    else:
        from ._filesystem_exceptions import NotImplementedProtocol
        raise NotImplementedProtocol(directory_url.scheme)



#===================================================================================================
# CreateTemporaryDirectory
#===================================================================================================
class CreateTemporaryDirectory(object):
    '''
    Context manager to create a temporary file and remove if at the context end.

    :ivar str dirname:
        Name of the created directory
    '''
    def __init__(self, suffix='', prefix='tmp', base_dir=None, maximum_attempts=100):
        '''
        :param str suffix:
            A suffix to add in the name of the created directory

        :param str prefix:
            A prefix to add in the name of the created directory

        :param str base_dir:
            A path to use as base in the created directory (if any). The temp directory will be a
            child of the given base dir

        :param int maximum_attemps:
            The maximum number of attempts to obtain the temp dir name.

        '''
        self.suffix = suffix
        self.prefix = prefix
        self.base_dir = base_dir
        self.maximum_attempts = maximum_attempts

        self.dirname = None


    def __enter__(self):
        '''
        :return str:
            The path to the created temp file.
        '''
        if self.base_dir is None:
            # If no base directoy was given, let us create a dir in system temp area
            import tempfile
            self.dirname = tempfile.mkdtemp(self.suffix, self.prefix)
            return self.dirname


        # Listing the files found in the base dir
        existing_files = set(ListFiles(self.base_dir))

        # If a base dir was given, let us generate a unique directory name there and use it
        from ben10.foundation.hash import IterHashes
        for random_component in IterHashes(iterator_size=self.maximum_attempts):
            candidate_name = '%stemp_dir_%s%s' % (self.prefix, random_component, self.suffix)
            candidate_path = os.path.join(self.base_dir, candidate_name)
            if candidate_path not in existing_files:
                CreateDirectory(candidate_path)
                self.dirname = candidate_path
                return self.dirname

        raise RuntimeError(
            'It was not possible to obtain a temporary dirname from %s' % self.base_dir)


    def __exit__(self, *args):
        if self.dirname is not None:
            DeleteDirectory(self.dirname, skip_on_error=False)



#===================================================================================================
# CreateTemporaryFile
#===================================================================================================
class CreateTemporaryFile(object):
    '''
    Context manager to create a temporary file and remove if at the context end.

    :ivar str filename:
        Name of the created file
    '''
    def __init__(
        self,
        contents,
        eol_style=EOL_STYLE_NATIVE,
        encoding=None,
        suffix='',
        prefix='tmp',
        base_dir=None,
        maximum_attempts=100):
        '''
        :param contents: .. seealso:: CreateFile
        :param eol_style: .. seealso:: CreateFile
        :param encoding: .. seealso:: CreateFile

        :param str suffix:
            A suffix to add in the name of the created file

        :param str prefix:
            A prefix to add in the name of the created file

        :param str base_dir:
            A path to use as base in the created file. Uses temp dir if not given.

        :param int maximum_attemps:
            The maximum number of attempts to obtain the temp file name.
        '''

        import tempfile

        self.contents = contents
        self.eol_style = eol_style
        self.encoding = encoding
        self.suffix = suffix
        self.prefix = prefix
        self.base_dir = base_dir or tempfile.gettempdir()
        self.maximum_attempts = maximum_attempts

        self.filename = None


    def __enter__(self):
        '''
        :return str:
            The path to the created temp file.
        '''
        from ._filesystem_exceptions import FileAlreadyExistsError
        from ben10.foundation.hash import IterHashes

        for random_component in IterHashes(iterator_size=self.maximum_attempts):
            filename = os.path.join(self.base_dir, self.prefix + random_component + self.suffix)

            try:
                CreateFile(
                    filename=filename,
                    contents=self.contents,
                    eol_style=self.eol_style,
                    encoding=self.encoding,
                )
                self.filename = filename
                return filename

            except FileAlreadyExistsError:
                pass

        raise RuntimeError('It was not possible to obtain a temporary filename in "%s"' % self.base_dir)


    def __exit__(self, *args):
        if self.filename is not None:
            DeleteFile(self.filename)



#===================================================================================================
# DeleteDirectory
#===================================================================================================
def DeleteDirectory(directory, skip_on_error=False):
    '''
    Deletes a directory.

    :param str directory:

    :param bool skip_on_error:
        If True, ignore any errors when trying to delete directory (for example, directory not
        found)

    :raises NotImplementedForRemotePathError:
        If trying to delete a remote directory.
    '''
    _AssertIsLocal(directory)

    import shutil
    def OnError(fn, path, excinfo):
        '''
        Remove the read-only flag and try to remove again.
        On Windows, rmtree fails when trying to remove a read-only file. This fix it!
        Another case: Read-only directories return True in os.access test. It seems that read-only
        directories has it own flag (looking at the property windows on Explorer).
        '''
        if IsLink(path):
            return

        if fn is os.remove and os.access(path, os.W_OK):
            raise

        # Make the file WRITEABLE and executes the original delete function (osfunc)
        import stat
        os.chmod(path, stat.S_IWRITE)
        fn(path)

    try:
        shutil.rmtree(directory, onerror=OnError)
    except:
        if not skip_on_error:
            raise  # Raise only if we are not skipping on error



#===================================================================================================
# GetMTime
#===================================================================================================
def GetMTime(path):
    '''
    :param str path:
        Path to file or directory

    :rtype: float
    :returns:
        Modification time for path.

        If this is a directory, the highest mtime from files inside it will be returned.

    @note:
        In some Linux distros (such as CentOs, or anything with ext3), mtime will not return a value
        with resolutions higher than a second.

        http://stackoverflow.com/questions/2428556/os-path-getmtime-doesnt-return-fraction-of-a-second
    '''
    _AssertIsLocal(path)

    if os.path.isdir(path):
        from ._duplicates import FindFiles
        files = FindFiles(path)

        if len(files) > 0:
            return max(map(os.path.getmtime, files))

    return os.path.getmtime(path)



#===================================================================================================
# ListMappedNetworkDrives
#===================================================================================================
def ListMappedNetworkDrives():
    '''
    On Windows, returns a list of mapped network drives

    :return: tuple(string, string, bool)
        For each mapped netword drive, return 3 values tuple:
            - the local drive
            - the remote path-
            - True if the mapping is enabled (warning: not reliable)
    '''
    if sys.platform != 'win32':
        raise NotImplementedError
    drives_list = []
    netuse = _CallWindowsNetCommand(['use'])
    for line in netuse.split(EOL_STYLE_WINDOWS):
        match = re.match("(\w*)\s+(\w:)\s+(.+)", line.rstrip())
        if match:
            drives_list.append((match.group(2), match.group(3), match.group(1) == 'OK'))
    return drives_list



#===================================================================================================
# DeleteLink
#===================================================================================================
def DeleteLink(path):
    if sys.platform != 'win32':
            os.unlink(path)
    else:
        import win32file
        if IsDir(path):
            win32file.RemoveDirectory(path)
        else:
            win32file.DeleteFile(path)



#===================================================================================================
# CreateLink
#===================================================================================================
def CreateLink(target_path, link_path, override=True):
    '''
    Create a symbolic link at `link_path` pointing to `target_path`.

    :param str target_path:
        Link target

    :param str link_path:
        Fullpath to link name

    :param bool override:
        If True and `link_path` already exists as a link, that link is overridden.
    '''
    _AssertIsLocal(target_path)
    _AssertIsLocal(link_path)

    if override and IsLink(link_path):
        DeleteLink(link_path)

    # Create directories leading up to link
    dirname = os.path.dirname(link_path)
    if dirname:
        CreateDirectory(dirname)

    if sys.platform != 'win32':
        return os.symlink(target_path, link_path)  # @UndefinedVariable

    else:
        import win32file
        try:
            win32file.CreateSymbolicLink(link_path, target_path, 1)
        except Exception, e:
            from ben10.foundation.reraise import Reraise
            Reraise(e, 'Creating link "%(link_path)s" pointing to "%(target_path)s"' % locals())



#===================================================================================================
# IsLink
#===================================================================================================
def IsLink(path):
    '''
    :param str path:
        Path being tested

    :returns bool:
        True if `path` is a link
    '''
    _AssertIsLocal(path)

    if sys.platform != 'win32':
        return os.path.islink(path)

    # Code taken from http://stackoverflow.com/a/7924557/1209622
    import win32file
    REPARSE_FOLDER = (win32file.FILE_ATTRIBUTE_DIRECTORY | 1024)
    file_attrs = win32file.GetFileAttributes(path)
    if file_attrs < 0:
        return False
    return file_attrs & REPARSE_FOLDER == REPARSE_FOLDER



#===================================================================================================
# ReadLink
#===================================================================================================
def ReadLink(path):
    '''
    Read the target of the symbolic link at `path`.

    :param str path:
        Path to a symbolic link

    :returns str:
        Target of a symbolic link
    '''
    _AssertIsLocal(path)

    if sys.platform != 'win32':
        return os.readlink(path)  # @UndefinedVariable

    import win32file
    import winioctlcon
    handle = win32file.CreateFile(
        path,  # fileName
        win32file.GENERIC_READ,  # desiredAccess
        0,  # shareMode
        None,  # attributes
        win32file.OPEN_EXISTING,  # creationDisposition
        win32file.FILE_FLAG_OPEN_REPARSE_POINT | win32file.FILE_FLAG_BACKUP_SEMANTICS,  # flagsAndAttributes
        None  # hTemplateFile
    )

    try:
        buf = win32file.DeviceIoControl(
            handle,  # hFile
            winioctlcon.FSCTL_GET_REPARSE_POINT,  # dwIoControlCode
            None,  # data
            1024,  # readSize
        )
        buf = buf[20::2].encode('latin1', errors='replace')
        if '\\??\\' in buf:
            return StandardizePath(buf.split('\\??\\')[0])
        else:
            return StandardizePath(buf[:len(buf) / 2])
    finally:
        handle.Close()


#===================================================================================================
# Internal functions
#===================================================================================================
def _UrlIsLocal(directory_url):
    '''
    :param ParseResult directory_url:
        A parsed url as returned by urlparse.urlparse.

    :rtype: bool
    :returns:
        Returns whether the given url refers to a local path.

    .. note:: The "directory_url.scheme" is the drive letter for a local path on Windows and an empty string
    for a local path on Linux. The other possible values are "http", "ftp", etc. So, checking if
    the length is less than 2 characters long checks that the url is local.
    '''
    return len(directory_url.scheme) < 2


def _AssertIsLocal(path):
    '''
    Checks if a given path is local, raise an exception if not.

    This is used in filesystem functions that do not support remote operations yet.

    :param str path:

    :raises NotImplementedForRemotePathError:
        If the given path is not local
    '''
    from urlparse import urlparse
    if not _UrlIsLocal(urlparse(path)):
        from ._filesystem_exceptions import NotImplementedForRemotePathError
        raise NotImplementedForRemotePathError


def _HandleContentsEol(contents, eol_style):
    '''
    Replaces eol on each line by the given eol_style.

    :param str contents:
    :type eol_style: EOL_STYLE_XXX constant
    :param eol_style:
    '''
    if eol_style == EOL_STYLE_NONE:
        return contents

    if eol_style == EOL_STYLE_UNIX:
        return contents.replace('\r\n', eol_style).replace('\r', eol_style)

    if eol_style == EOL_STYLE_MAC:
        return contents.replace('\r\n', eol_style).replace('\n', eol_style)

    if eol_style == EOL_STYLE_WINDOWS:
        return contents.replace('\r\n', '\n').replace('\r', '\n').replace('\n', EOL_STYLE_WINDOWS)

    raise ValueError('Unexpected eol style: %r' % (eol_style,))


def _CallWindowsNetCommand(parameters):
    '''
    Call Windows NET command, used to acquire/configure network services settings.

    :param parameters: list of command line parameters

    :return: command output
    '''
    import subprocess
    popen = subprocess.Popen(["net"] + parameters, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdoutdata, stderrdata = popen.communicate()
    if stderrdata:
        raise OSError("Failed on call net.exe: %s" % stderrdata)
    return stdoutdata
