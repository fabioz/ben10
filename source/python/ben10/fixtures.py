'''
Collection of fixtures for pytests.

.. note::
    Coverage for this file gives a lot of misses, just like calling coverage from module's main.
'''
from __future__ import unicode_literals
import faulthandler
import os
import pytest



#===================================================================================================
# pytest_sessionstart
#===================================================================================================
def pytest_sessionstart(session):
    '''
    pytest hook called before each session begins (including on each slave when running in xdist).

    We use this hook in order to configure global settings that should be set for all tests in our
    runs.
    '''
    from ben10.foundation.is_frozen import SetIsDevelopment
    import sys

    if sys.platform.startswith('win'):
        # Makes the system hide the Windows Error Reporting dialog.
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms680621%28v=vs.85%29.aspx
        import ctypes
        SEM_NOGPFAULTERRORBOX = 0x0002
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)

    # Enable development-only checks
    SetIsDevelopment(True)


#===================================================================================================
# pytest_runtest_protocol
#===================================================================================================
def pytest_runtest_protocol(item, __multicall__):
    '''
    pytest hook that implements the full test run protocol, setup/call/teardown.

    - faulthandler: we enable a fault handler in the current process, which will stream crash errors
        to a file in the directory configured by the "--fault-handler-dir" command-line option.
        The file is named based on the module and test name, for example:
            "~/ben10._tests.pytest_fixtures.testFaultHandler.txt"

        Since this file is only useful if a a test crashes, it is removed during tear down if
        no crash occurred.
    '''
    # skip items that are not python test items (for example: pytest)
    if not hasattr(item, 'module'):
        return
    name = '%s.%s.txt'  % (item.module.__name__, item.name)
    invalid_chars = [os.sep, os.pathsep, ':', '<', '>', '@']
    if os.altsep:
        invalid_chars.append(os.altsep)
    for c in invalid_chars:
        name = name.replace(c, '-')
    filename = os.path.join(item.config.getoption('fault_handler_dir'), name)
    item.fault_handler_stream = open(filename, 'w')
    faulthandler.enable(item.fault_handler_stream)
    try:
        return __multicall__.execute()
    finally:
        item.fault_handler_stream.close()
        item.fault_handler_stream = None
        try:
            os.remove(filename)
        except (OSError, IOError):
            pass


#===================================================================================================
# pytest_addoption
#===================================================================================================
def pytest_addoption(parser):
    '''
    Add an option to pytest to change the default directory where to write fault handler report
    files. Specially useful in the CI server.

    :param optparse.OptionParser parser:
    '''
    group = parser.getgroup("debugconfig") # default pytest group for debugging/reporting
    group.addoption(
        '--fault-handler-dir',
        dest="fault_handler_dir",
        default=os.getcwdu(),
        metavar="dir",
        help="directory where to save crash reports (must exist)")


#===================================================================================================
# pytest_report_header
#===================================================================================================
def pytest_report_header(config):
    '''
    pytest hook to add a line to the report header showing the directory where fault handler report
    files will be generated.
    '''
    return ['fault handler directory: %s' % config.getoption('fault_handler_dir')]


#===================================================================================================
# MultipleFilesNotFound
#===================================================================================================
class MultipleFilesNotFound(RuntimeError):
    '''
    Raised when a file is not found, including variations of filename.
    '''

    def __init__(self, filenames):
        RuntimeError.__init__(self)
        self._filenames = filenames

    def __str__(self):
        return 'Files not found: %s' % ','.join(self._filenames)



#===================================================================================================
# embed_data
#===================================================================================================

class _EmbedDataFixture(object):
    '''
    This fixture create a temporary data directory for the test.
    The contents of the directory is a copy of a 'data-directory' with the same name of the module
    (without the .py extension).

    :ivar boolean delete_dir:
        Determines if the data-directory is deleted at finalization. Default to True.
        This may be used for debugging purposes to examine the data-directory as left by the test.
        Remember that each test recreates the entire data directory.
    '''

    def __init__(self, request):

        # @ivar _module_dir: unicode
        # The module name.
        self._module_name = request.module.__name__.split('.')[-1]
        self._function_name = request.function.__name__

        # @ivar _source_dir: unicode
        # The source directory name.
        # The contents of this directories populates the data-directory
        # This name is create based on the module_name
        self._source_dir = request.fspath.dirname + '/' + self._module_name

        # @ivar _data_dir: unicode
        # The data directory name
        # This name is created based on the module_name
        # Adding the function name to enable parallel run of tests in the same module (pytest_xdist)
        self._data_dir = self._module_name.replace('pytest_', 'data_')
        self._data_dir += '__' + self._function_name

        # @ivar _created: boolean
        # Internal flag that controls whether we created the data-directory or not.
        # - False: Initial state. The data-directory was not created yet
        # - True: The directory was created. The directory is created lazily, that is, when needed.
        self._created = False

        # @ivar _finalize: boolean
        # Whether we have finalized.
        self._finalized = False

        self.delete_dir = True


    def CreateDataDir(self):
        '''
        Creates the data-directory as a copy of the source directory.

        :rtype: unicode
        :returns:
            Path to created data dir
        '''
        from ben10.filesystem import CopyDirectory, CreateDirectory, DeleteDirectory, IsDir
        from ben10.foundation.is_frozen import IsFrozen

        assert not self._finalized, "Oops. Finalizer has been called in the middle. Something is wrong."
        if self._created:
            return self._data_dir

        if os.path.isdir(self._data_dir):
            DeleteDirectory(self._data_dir)

        if IsFrozen():
            raise RuntimeError("_EmbedDataFixture is not ready for execution inside an executable.")

        if IsDir(self._source_dir):
            CopyDirectory(self._source_dir, self._data_dir)
        else:
            CreateDirectory(self._data_dir)

        self._created = True
        return self._data_dir


    def GetDataDirectory(self, absolute=False, create_dir=True):
        '''
        :param bool absolute:
            If True, returns the path as an abspath

        :param bool create_dir:
            If True (default) creates the data directory.

        :rtype: unicode
        :returns:
            Returns the data-directory name.

        @remarks:
            This method triggers the data-directory creation.
        '''
        if create_dir:
            self.CreateDataDir()

        if absolute:
            from ben10.filesystem import StandardizePath
            return StandardizePath(os.path.abspath(self._data_dir))

        return self._data_dir


    def GetDataFilename(self, *parts, **kwargs):
        '''
        Returns a full filename in the data-directory.

        @params parts: list(unicode)
            Path parts. Each part is joined to form a path.

        :keyword bool absolute:
            If True, returns the filename as an abspath

        :rtype: unicode
        :returns:
            The full path prefixed with the data-directory.

        @remarks:
            This method triggers the data-directory creation.
        '''
        # Make sure the data-dir exists.
        self.CreateDataDir()

        result = [self._data_dir] + list(parts)
        result = '/'.join(result)

        if 'absolute' in kwargs and kwargs['absolute']:
            from ben10.filesystem import StandardizePath
            result = StandardizePath(os.path.abspath(result))

        return result

    def __getitem__(self, index):
        return self.GetDataFilename(index)


    def Finalizer(self):
        '''
        Deletes the data-directory upon finalizing (see FixtureRequest.addfinalizer)
        '''
        from ben10.filesystem._filesystem import DeleteDirectory

        if self.delete_dir:
            DeleteDirectory(self._data_dir, skip_on_error=True)
        self._finalized = True


    def AssertEqualFiles(self, filename1, filename2, fix_callback=lambda x:x, binary=False, encoding=None):
        '''
        Compare two files contents, showing a nice diff view if the files differs.

        Searches for the filenames both inside and outside the data directory (in that order).

        :param unicode filename1:

        :param unicode filename2:

        :param bool binary:
            Thread both files as binary files.

        :param unicode encoding:
            File's encoding. If not None, contents obtained from file will be decoded using this
            `encoding`.

        :param callable fix_callback:
            A callback to "fix" the contents of the obtained (first) file.
            This callback receives a list of strings (lines) and must also return a list of lines,
            changed as needed.
            The resulting lines will be used to compare with the contents of filename2.

        :param bool binary:
            .. seealso:: ben10.filesystem.GetFileContents
        '''
        __tracebackhide__ = True
        from ben10.filesystem import GetFileContents, GetFileLines

        def FindFile(filename):
            # See if this path exists in the data dir
            data_filename = self.GetDataFilename(filename)
            if os.path.isfile(data_filename):
                return data_filename

            # If not, we might have already received a full path
            if os.path.isfile(filename):
                return filename

            # If we didn't find anything, raise an error
            raise MultipleFilesNotFound([filename, data_filename])

        filename1 = FindFile(filename1)
        filename2 = FindFile(filename2)

        if binary:
            obtained = GetFileContents(filename1, binary=True)
            expected = GetFileContents(filename2, binary=True)
            assert obtained == expected
        else:
            obtained = fix_callback(GetFileLines(filename1, encoding=encoding))
            expected = GetFileLines(filename2, encoding=encoding)

            if obtained != expected:
                import difflib
                diff = ['*** FILENAME: ' + filename1]
                diff += difflib.context_diff(obtained, expected)
                diff = '\n'.join(diff)
                raise AssertionError(diff)


@pytest.fixture  # pylint: disable=E1101
def embed_data(request):  # pylint: disable=C0103
    '''
    Create a temporary directory with input data for the test.
    The directory contents is copied from a directory with the same name as the module located in
    the same directory of the test module.
    '''
    result = _EmbedDataFixture(request)
    request.addfinalizer(result.Finalizer)
    return result


@pytest.fixture
def platform():
    '''
    The current platform information in a nicely packaged Platform object.
    '''
    from ben10.foundation.platform_ import Platform
    return Platform.GetCurrentPlatform()
