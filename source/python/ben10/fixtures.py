# coding: UTF-8
'''
Collection of fixtures for pytests.

.. note::
    Coverage for this file gives a lot of misses, just like calling coverage from module's main.
'''
from __future__ import unicode_literals
from ben10.foundation import handle_exception
import locale
import os
import pytest
import sys



#===================================================================================================
# pytest_collection_modifyitems
#===================================================================================================
def pytest_collection_modifyitems(session, config, items):
    '''
    Multiplies the timeout by a factor when the test is marked as `slow` or `extra_slow`.
    '''
    from _pytest.mark import MarkDecorator
    from ben10.debug import IsPythonDebug
    for item in items:
        if item.get_marker('slow'):
            factor = 5.0
        elif item.get_marker('extra_slow'):
            factor = 20.0
        else:
            continue

        if IsPythonDebug():
            factor *= 2

        timeout_value = config.getoption('timeout')
        timeout_value *= factor
        item.add_marker(MarkDecorator('timeout', (timeout_value,), {}))



#===================================================================================================
# global_settings_fixture
#===================================================================================================
@pytest.yield_fixture(autouse=True, scope='session')
def global_settings_fixture(request):
    '''
    Auto-use fixture that configures global settings that should be set for all tests in our
    runs.
    '''
    from contextlib import contextmanager

    @contextmanager
    def NoDialogs():
        '''
        Makes the system hide the Windows Error Reporting dialog.
        '''
        if request.config.getoption('no_dialogs') and sys.platform.startswith('win'):
            # http://msdn.microsoft.com/en-us/library/windows/desktop/ms680621%28v=vs.85%29.aspx
            import ctypes
            SEM_NOGPFAULTERRORBOX = 0x0002
            old_error_mode = ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)  # @UndefinedVariable
            new_error_mode = old_error_mode | SEM_NOGPFAULTERRORBOX
            ctypes.windll.kernel32.SetErrorMode(new_error_mode)  # @UndefinedVariable

            try:
                yield
            finally:
                # If `reenable_error_dialogs` is False, this means that crashes happening after the
                # pytest suite is run (e.g., on garbage collection) may go completely unnoticed.
                #
                # This is temporarily False until we guarantee that there are no crashes like this
                # in # our test suite.
                reenable_error_dialogs = False
                if reenable_error_dialogs:
                    ctypes.windll.kernel32.SetErrorMode(old_error_mode)  # @UndefinedVariable
        else:
            yield

    @contextmanager
    def Development():
        '''
        Enable development-only checks
        '''
        from ben10.foundation.is_frozen import SetIsDevelopment
        SetIsDevelopment(True)
        yield

    with Development(), NoDialogs():
        yield



#===================================================================================================
# _ShowHandledExceptionsError
#===================================================================================================
class _ShowHandledExceptionsError(object):
    '''
    Helper class to deal with handled exceptions.
    '''

    def __init__(self):
        self._handled_exceptions = []
        self._handled_exceptions_types = []

    def _OnHandledException(self):
        '''
        Called when a handled exceptions was found.
        '''
        from StringIO import StringIO
        import traceback

        s = StringIO()
        traceback.print_exc(file=s)
        self._handled_exceptions_types.append(sys.exc_info()[0])
        self._handled_exceptions.append(s.getvalue())

    def __enter__(self, *args, **kwargs):
        handle_exception.on_exception_handled.Register(self._OnHandledException)
        return self

    def __exit__(self, *args, **kwargs):
        handle_exception.on_exception_handled.Unregister(self._OnHandledException)

    def ClearHandledExceptions(self):
        '''
        Clears the handled exceptions
        '''
        del self._handled_exceptions_types[:]
        del self._handled_exceptions[:]

    def GetHandledExceptionTypes(self):
        '''
        :return list(type):
            Returns a list with the exception types we found.
        '''
        return self._handled_exceptions_types

    def GetHandledExceptions(self):
        '''
        :return list(str):
            Returns a list with the representation of the handled exceptions.
        '''
        return self._handled_exceptions

    def RaiseFoundExceptions(self):
        '''
        Raises error for the handled exceptions found.
        '''
        if self._handled_exceptions:
            raise AssertionError('\n'.join(self._handled_exceptions))


#===================================================================================================
# handled_exceptions
#===================================================================================================
@pytest.yield_fixture(scope="function", autouse=True)
def handled_exceptions():
    '''
    This method will be called for all the functions automatically.

    For users which expect handled exceptions, it's possible to declare the fixture and
    say that the errors are expected and clear them later.

    I.e.:

    from ben10.foundation.handle_exception import IgnoringHandleException
    from ben10.foundation import handle_exception

    def testSomething(handled_exceptions):
        with IgnoringHandleException():
            try:
                raise RuntimeError('test')
            except:
                handle_exception.HandleException()

        # Check that they're there...
        handled_exceptions = handled_exceptions.GetHandledExceptions()

        # Clear them
        handled_exceptions.ClearHandledExceptions()

    Note that test-cases can still deal with this API without using a fixture by importing handled_exceptions
    and using it as an object.

    I.e.:

    from ben10.fixtures import handled_exceptions
    handled_exceptions.GetHandledExceptions()
    handled_exceptions.ClearHandledExceptions()
    '''
    try:
        with _ShowHandledExceptionsError() as show_handled_exceptions_error:
            handled_exceptions.ClearHandledExceptions = \
                show_handled_exceptions_error.ClearHandledExceptions

            handled_exceptions.GetHandledExceptions = \
                show_handled_exceptions_error.GetHandledExceptions

            handled_exceptions.GetHandledExceptionTypes = \
                show_handled_exceptions_error.GetHandledExceptionTypes

            yield show_handled_exceptions_error
    finally:
        handled_exceptions.ClearHandledExceptions = None
        handled_exceptions.GetHandledExceptions = None
        handled_exceptions.GetHandledExceptionTypes = None

    show_handled_exceptions_error.RaiseFoundExceptions()



#===================================================================================================
# pytest_configure
#===================================================================================================
def pytest_configure(config):
    '''
    Enable fault handler directly into sys.stderr.
    '''
    InstallFaultHandler(config)


def InstallFaultHandler(config):
    """
    Install fault handler. If we have a real sys.stderr, we install directly in there. Otherwise
    (frozen executable without console for example) we write into a file next to the executable,
    which is usually a frozen executable.

    .. note:: this is a separate function because we want to test it explicitly.

    :param config: pytest config object
    """
    try:
        import faulthandler
    except ImportError:
        pass
    else:
        if hasattr(sys.stderr, 'fileno'):
            stderr_fd_copy = os.dup(sys.stderr.fileno())
            stderr_copy = os.fdopen(stderr_fd_copy, 'w')
            faulthandler.enable(stderr_copy)
            config.fault_handler_file = None
        else:
            # in frozen executables it might be that sys.stderr is actually a wrapper and not a
            # real object, then write the fault handler to a file
            filename = os.path.splitext(sys.executable)[0] + ('.faulthandler-%d.txt' % os.getpid())
            config.fault_handler_file = file(filename, 'w')
            faulthandler.enable(config.fault_handler_file)


#===================================================================================================
# pytest_addoption
#===================================================================================================
def pytest_addoption(parser):
    '''
    Add extra options to pytest.

    :param optparse.OptionParser parser:
    '''
    group = parser.getgroup("debugconfig")  # default pytest group for debugging/reporting
    group.addoption(
        '--no-dialogs',
        action='store_true',
        default=False,
        help='Disable Windows Error dialog boxes during tests'
    )


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


# By setting UPDATE_ORIGINAL_FILES to True, the data dir will not be copied (and some additional
# places should also use this flag to overwrite files instead of creating them in a different place
# for comparison -- such as the method which compares a snapshot with an existing file in sci20).
UPDATE_ORIGINAL_FILES = False


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
        import re
        module_name = request.module.__name__.split('.')[-1]

        # Use node_name to support pytest.mark.parametrize, and replace all non-word chars with '_'
        # Inspired by builtin 'tmpdir' fixture
        node_name = re.sub("[\W]", "_", request.node.name)

        # @ivar _source_dir: unicode
        # The source directory name.
        # The contents of this directories populates the data-directory
        # This name is create based on the module_name
        self._source_dir = request.fspath.dirname + '/' + module_name

        # @ivar _data_dir: unicode
        # The data directory name
        # This name is created based on the module_name
        # Adding the function name to enable parallel run of tests in the same module (pytest_xdist)
        self._data_dir = module_name.replace('pytest_', 'data_')
        self._data_dir += '__' + node_name

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

        assert not self._finalized, "Oops. Finalizer has been called in the middle. Something is wrong."
        if self._created:
            return self._data_dir

        if os.path.isdir(self._data_dir):
            DeleteDirectory(self._data_dir)

        if IsDir(self._source_dir):
            if UPDATE_ORIGINAL_FILES:
                self._data_dir = self._source_dir
            else:
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

        if not UPDATE_ORIGINAL_FILES:
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


#===================================================================================================
# UnicodeSamples
#===================================================================================================
class UnicodeSamples(object):
    """
    Sample strings that are valid in different encodings, can be used in tests to ensure
    compliance with different encoding sets.

    :cvar PURE_ASCII:
        Only chars valid in ascii.

    :cvar LATIN_1:
        Only chars valid in latin-1.

    :cvar FULL_LATIN_1:
        All valid latin-1 characters.

    :cvar UNICODE:
        Sample of unicode chars.

    :cvar UNICODE_MULTIPLE_LANGUAGES:
        Sample of unicode chars from several languages.

    :cvar UNICODE_PREFERRED_LOCALE:
        Sample of unicode chars that are valid in the encoding of the current locale.

    Sources:
    - http://pages.ucsd.edu/~dkjordan/chin/unitestuni.html

    Note:
        We had to limit the unicode character examples to those who can be represented in ucs2. I.e, in our current
        compiled version of python, unichr(0x26B99) raises
        "ValueError: unichr() arg not in range(0x10000) (narrow Python build)"
    """
    PURE_ASCII = 'action'
    LATIN_1 = 'ação'
    FULL_LATIN_1 = b''.join(chr(i + 1) for i in xrange(255)).decode('latin-1')
    UNICODE = '動'
    UNICODE_MULTIPLE_LANGUAGES = UNICODE + '_ĂǜĵΜῆἄθΠηωχς пкת我。館來了。ώęăлտլმტკ सक 傷ทำ 森 ☃'
    UNICODE_PREFERRED_LOCALE = (LATIN_1 + UNICODE_MULTIPLE_LANGUAGES).encode(
        locale.getpreferredencoding(), 'replace').decode(locale.getpreferredencoding()).replace('?', '-')


    def IsUCS2Build(self):
        """
        If Python has been compiled with UCS-2 unicode support ("narrow unicode build").

        http://stackoverflow.com/questions/1446347/how-to-find-out-if-python-is-compiled-with-ucs-2-or-ucs-4

        :return: bool
        """
        return sys.maxunicode == 65535


    def IsUCS4Build(self):
        """
        If Python has been compiled with UCS-4 unicode support ("wide unicode build").

        http://stackoverflow.com/questions/1446347/how-to-find-out-if-python-is-compiled-with-ucs-2-or-ucs-4

        :return: bool
        """
        return sys.maxunicode == 1114111


@pytest.fixture
def unicode_samples():
    '''
    Component that contains samples from various character sets decoded as unicode.
    '''
    return UnicodeSamples()



#===================================================================================================
# _ScriptRunner
#===================================================================================================
class _ScriptRunner(object):
    '''
    Saves script and runs it, capturing output. Does not remove the script file.
    '''

    def ExecuteScript(self, filename, contents, *args):
        '''
        Saves script and runs it, capturing output. Does not remove the script file.

        :returns unicode:
            Script output.
        '''
        from ben10.execute import ExecutePython
        from ben10.filesystem import CreateFile

        CreateFile(filename, contents)

        output, _retcode = ExecutePython(filename, list(args))
        # Questionable whether we should perform strip here. But this is what the current uses
        # expect.
        return output.strip()


@pytest.fixture
def script_runner():
    '''
    Component to create and execute python scripts.
    '''
    return _ScriptRunner()
