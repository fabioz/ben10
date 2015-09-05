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
    Multiplies the timeout by a factor when the test is marked as `slow`.
    '''
    timeout_value = config.getoption('timeout', default=None)

    if timeout_value is None:
        return

    from _pytest.mark import MarkDecorator
    from ben10 import debug

    for item in items:
        item_timeout = timeout_value

        timeout_marker = item.get_marker('timeout')
        if timeout_marker is not None:
            item_timeout = timeout_marker.args[0]

        factor = 1.0
        if item.get_marker('slow'):
            factor = 5.0

        if debug.IsPythonDebug():
            factor *= 3

        item_timeout *= factor

        item.add_marker(MarkDecorator('timeout', (item_timeout,), {}))



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
        if request.config.getoption('no_dialogs', None) and sys.platform.startswith('win'):
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
        assert len(handled_exceptions.GetHandledExceptions()) == 1

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
    if IsMasterNode(config):
        CreateSessionTmpDir(config)
    # 'xdist' is the name of plugin in usual environments. 'xdist.plugin' is the name in frozen
    # executables: we require xdist otherwise some of the features on this module will not work
    # properly
    xdist = config.pluginmanager.hasplugin('xdist') or config.pluginmanager.hasplugin('xdist.plugin')
    assert xdist, 'xdist plugin not available'
    config.pluginmanager.register(_XDistTmpDirPlugin(), 'xdist-tmp-dir')


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

    parser.addoption(
        '--force-regen',
        action='store_true',
        default=False,
        help='Re-generate all data_regression fixture data files.',
    )

    # Session Temporary Directory
    parser.addoption(
        '--session-tmp-dir',
        default=None,
        help='Specify the session temporary directory to be used (use in DEV only).',
    )
    parser.addoption(
        '--last-session-tmp-dir',
        action='store_true',
        default=False,
        help='When enabled the last session temporary directory will be used (use in DEV only).',
    )


#===================================================================================================
# pytest_report_header
#===================================================================================================
def pytest_report_header(config):
    return ['session-tmp-dir: %s' % config.session_tmp_dir]


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

    This directory is created in the ``session_tmp_dir`` using the name of the module + name
    of the test (for example "x:/ben10/tmp/session-tmp-dir-0/test_fixtures__testEmbedData").
    Differently from our implementation in xUnit, the directory *IS NOT* deleted at the end of the
    test, we rely on ``session_tmp_dir`` automatic cleanup for that. This is intentional as makes
    it easy to consult the directories to get at generated images, diffs, etc.
    '''

    def __init__(self, request, session_tmp_dir):
        from ben10.filesystem import CopyDirectory, StandardizePath
        import errno
        import re

        module_name = request.module.__name__.split('.')[-1]

        # source directory: same name as the name of the test's module
        self._source_dir = request.fspath.dirname + '/' + module_name
        if UPDATE_ORIGINAL_FILES:
            self._data_dir = self._source_dir
            return

        # replace all non-word chars with '_' in the node name to support parametrize
        # Inspired by builtin 'tmpdir' fixture
        node_name = re.sub("[\W]", "_", request.node.name)
        node_name = node_name[:50]

        # traditionally, we change the "test_" prefix to "data_"
        data_dir_basename = module_name.replace('test_', 'data_')
        data_dir_basename += '__' + node_name

        # ensure a unique directory, copying over the contents of the source directory if it exists
        i = 1
        basename = data_dir_basename
        while True:
            data_dir = os.path.join(session_tmp_dir, basename)
            try:
                if os.path.isdir(self._source_dir):
                    CopyDirectory(self._source_dir, data_dir, override=False)
                else:
                    os.makedirs(data_dir)
                self._data_dir = data_dir
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            basename = '{}-{}'.format(data_dir_basename, i)
            i += 1
            assert i < 999, 'give up trying to find unique dirs for: %s' % data_dir

        # "standardize" the path: for some reason a lot of code on ben10' execute needs this to
        # work.
        self._data_dir = StandardizePath(self._data_dir)


    def GetDataDirectory(self):
        '''
        :rtype: unicode
        :returns:
            Returns the absolute path to data-directory name to use, standardized by StandardizePath.

        @remarks:
            This method triggers the data-directory creation.
        '''
        return self._data_dir


    def GetDataFilename(self, *parts):
        '''
        Returns an absolute filename in the data-directory (standardized by StandardizePath).

        @params parts: list(unicode)
            Path parts. Each part is joined to form a path.

        :rtype: unicode
        :returns:
            The full path prefixed with the data-directory.

        @remarks:
            This method triggers the data-directory creation.
        '''
        from ben10.filesystem import StandardizePath
        result = [self._data_dir] + list(parts)
        result = '/'.join(result)
        return StandardizePath(result)


    def __getitem__(self, index):
        return self.GetDataFilename(index)


    def AssertEqualFiles(self, obtained_fn, expected_fn, fix_callback=lambda x:x, binary=False, encoding=None):
        '''
        Compare two files contents. If the files differ, show the diff and write a nice HTML
        diff file into the data directory.

        Searches for the filenames both inside and outside the data directory (in that order).

        :param unicode obtained_fn: basename to obtained file into the data directory, or full path.

        :param unicode expected_fn: basename to expected file into the data directory, or full path.

        :param bool binary:
            Thread both files as binary files.

        :param unicode encoding:
            File's encoding. If not None, contents obtained from file will be decoded using this
            `encoding`.

        :param callable fix_callback:
            A callback to "fix" the contents of the obtained (first) file.
            This callback receives a list of strings (lines) and must also return a list of lines,
            changed as needed.
            The resulting lines will be used to compare with the contents of expected_fn.

        :param bool binary:
            .. seealso:: ben10.filesystem.GetFileContents
        '''
        __tracebackhide__ = True
        from ben10.filesystem import GetFileContents, GetFileLines
        import io

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

        obtained_fn = FindFile(obtained_fn)
        expected_fn = FindFile(expected_fn)

        if binary:
            obtained_lines = GetFileContents(obtained_fn, binary=True)
            expected_lines = GetFileContents(expected_fn, binary=True)
            assert obtained_lines == expected_lines
        else:
            obtained_lines = fix_callback(GetFileLines(obtained_fn, encoding=encoding))
            expected_lines = GetFileLines(expected_fn, encoding=encoding)

            if obtained_lines != expected_lines:
                html_fn = os.path.splitext(obtained_fn)[0] + '.diff.html'
                html_diff = self._GenerateHTMLDiff(
                    expected_fn, expected_lines, obtained_fn, obtained_lines)
                with io.open(html_fn, 'w') as f:
                    f.write(html_diff)

                import difflib
                diff = ['FILES DIFFER:', obtained_fn, expected_fn]
                diff += ['HTML DIFF: %s' % html_fn]
                diff += difflib.context_diff(obtained_lines, expected_lines)
                raise AssertionError('\n'.join(diff))


    def _GenerateHTMLDiff(self, expected_fn, expected_lines, obtained_fn, obtained_lines):
        """
        Returns a nice side-by-side diff of the given files, as a string.

        """
        import difflib
        differ = difflib.HtmlDiff()
        return differ.make_file(
            fromlines=expected_lines,
            fromdesc=expected_fn,
            tolines=obtained_lines,
            todesc=obtained_fn,
        )


@pytest.fixture  # pylint: disable=E1101
def embed_data(request, session_tmp_dir):  # pylint: disable=C0103
    '''
    Create a temporary directory with input data for the test.
    The directory contents is copied from a directory with the same name as the module located in
    the same directory of the test module.
    '''
    result = _EmbedDataFixture(request, session_tmp_dir)
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


@pytest.fixture
def data_regression(embed_data, request):
    """
    :param embed_data:
    :param request:
    :return:
    """
    return DataRegressionFixture(embed_data, request)


class DataRegressionFixture(object):
    """
    Fixture used to test arbitrary data against known versions previously
    recorded by this same fixture. Useful to test 3rd party APIs or where testing directly
    generated data from other sources.

    Create a dict in your test containing a arbitrary data you want to test, and
    call the `Check` function. The first time it will fail but will generate a file in your
    data directory.

    Subsequent runs against the same data will now compare against the generated file and pass
    if the dicts are equal, or fail showing a diff otherwise. To regenerate the data,
    either set `force_regen` attribute to True or pass the `--force-regen` flag to pytest
    which will regenerate the data files for all tests. Make sure to diff the files to ensure
    the new changes are expected and not regressions.

    The dict may be anything serializable by the `yaml` library.

    :type embed_data: ben10.fixtures._EmbedDataFixture
    """

    def __init__(self, embed_data, request):
        """
        :param embed_data: embed_data fixture
        :type request: SubRequest
        """
        self.request = request
        self.embed_data = embed_data
        self.force_regen = False


    def Check(self, data_dict, basename=None, fullpath=None):
        """
        Checks the given dict against a previously recorded version, or generate a new file.

        :param dict data_dict: any yaml serializable dict.

        :param unicode basename: basename of the file to test/record. If not given the name
            of the test is used.
        :param unicode fullpath: complete path to use as a reference file. This option
            will ignore embed_data completely, being useful if a reference file is located
            in the session data dir for example.

        basename and fullpath are exclusive.
        """
        __tracebackhide__ = True

        import io

        def CheckFn(obtained_filename, expected_filename):
            """
            Check if dict contents dumped to a file match the contents in expected file.
            """
            self.embed_data.AssertEqualFiles(
                os.path.abspath(obtained_filename), os.path.abspath(expected_filename))

        def DumpFn(filename):
            """Dump dict contents to the given filename"""
            import yaml
            with io.open(filename, 'wb') as f:
                yaml.safe_dump(
                    data_dict,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    encoding='utf-8',
                )

        FileRegressionCheck(
            embed_data=self.embed_data,
            request=self.request,
            check_fn=CheckFn,
            dump_fn=DumpFn,
            extension='.yml',
            basename=basename,
            fullpath=fullpath,
            force_regen=self.force_regen,
        )


def FileRegressionCheck(
    embed_data,
    request,
    check_fn,
    dump_fn,
    extension,
    basename=None,
    fullpath=None,
    force_regen=False,
):
    """
    First run of this check will generate a expected file. Following attempts will always try to
    match obtained files with that expected file.

    If expected file needs to be updated, just enable `force_regen` argument.

    :param _EmbedDataFixture embed_data: Fixture embed_data.
    :param SubRequest request: Pytest request object.
    :param function check_fn: A function that receives as arguments, respectively, absolute path to
        obtained file and absolute path to expected file. It must assert if contents of file match.
        Function can safely assume that obtained file is already dumped and only care about
        comparison.
    :param function dump_fn: A function that receive an absolute file path as argument. Implementor
        must dump file in this path.
    :param unicode extension: Extension of files compared by this check.
    :param unicode basename: basename of the file to test/record. If not given the name
        of the test is used.
    :param unicode fullpath: complete path to use as a reference file. This option
        will ignore `embed_data` fixture completely, being useful if a reference file is located
        in the session data dir for example.
    :param bool force_regen: if true it will regenerate expected file.
    """
    import re

    assert not (basename and fullpath), "pass either basename or fullpath, but not both"

    if fullpath:
        filename = source_filename = os.path.abspath(fullpath)
        source_dir = os.path.dirname(filename)
    else:
        dump_ext = extension
        if basename is None:
            basename = re.sub("[\W]", "_", request.node.name)
        filename = embed_data.GetDataFilename(basename) + dump_ext
        source_dir = embed_data._source_dir
        source_filename = os.path.join(source_dir, basename + dump_ext)

    force_regen = force_regen or request.config.getoption('force_regen')
    if force_regen or not os.path.isfile(filename):
        if not os.path.isdir(source_dir):
            os.makedirs(source_dir)

        dump_fn(source_filename)

        if not os.path.isfile(filename):
            msg = 'File not found in data directory, created one at: {}'
            pytest.fail(msg.format(source_filename))
        else:
            msg = '--force-regen set, regenerating file at: {} '
            pytest.fail(msg.format(source_filename))
    else:
        path, ext = os.path.splitext(filename)
        obtained_filename = path + '.obtained' + ext

        dump_fn(obtained_filename)

        check_fn(os.path.abspath(obtained_filename), filename)


#===================================================================================================
# Session Temporary Directory
#===================================================================================================
@pytest.fixture(scope=b'session')
def session_tmp_dir(request):
    '''
    Creates a root directory to be used as a root directory for a pytest session.
    The last 3 session temporary direrctory will be kept, older ones will be deleted.

    It's default configuration can be change by:
        '--session-tmp-dir': Specify the session temporary directory to be used.
        '--last-session-tmp-dir': the last session temporary dir created will be used.',
    '''
    if IsMasterNode(request.config):
        return request.config.session_tmp_dir
    else:
        return request.config.slaveinput['session-tmp-dir']


def CreateSessionTmpDir(config):
    '''
    :see: session_tmp_dir
    '''
    from py.path import local

    root_dir = config.rootdir.join('tmp')
    root_dir.ensure(dir=1)

    def SetTmpDir(tmp_dir):
        # Just in case there is no cache plugin
        if hasattr(config, 'cache'):
            config.cache.set("session_tmp_dir/last_session_tmp_dir", str(tmp_dir))
        config.session_tmp_dir = str(tmp_dir)

    # Use specified directory
    tmp_dir = config.getoption('session_tmp_dir', None)
    if tmp_dir is not None:
        if not os.path.isabs(tmp_dir):
            tmp_dir = root_dir.join(tmp_dir)
        return SetTmpDir(tmp_dir)

    # Use last session directory
    if config.getoption('last_session_tmp_dir', False):
        last_session_tmp_dir = config.cache.get("session_tmp_dir/last_session_tmp_dir", None)
        if last_session_tmp_dir and os.path.exists(last_session_tmp_dir):
            return SetTmpDir(last_session_tmp_dir)

    # Create new tmp directory
    tmp_dir = local.make_numbered_dir(prefix='session-tmp-dir-', rootdir=root_dir)
    return SetTmpDir(tmp_dir)


class _XDistTmpDirPlugin(object):
    """
    Dummy plugin that is registered inside the pytest_configure in this module.

    This will install a hook called by pytest_xdist when it is about to setup a slave, and
    is used to send the created session-tmp-dir from the master to the slave.

    We can't just declare this plugin directly at the module level because pytest validates hooks
    (any function which starts with "pytest_" is checked), and depending on the command line
    options when ben10.fixtures is seen by pytest xdist might not be loaded yet, hence the
    new hook is not registered then the validation fails.
    """

    def pytest_configure_node(self, node):
        """xdist plugin hook"""
        node.slaveinput['session-tmp-dir'] = node.config.session_tmp_dir


def IsSlaveNode(config):
    """Return True if the code running the given pytest.config object is running in a xdist slave
    node.
    """
    return hasattr(config, 'slaveinput')


def IsMasterNode(config):
    """Return True if the code running the given pytest.config object is running in a xdist master
    node or not running xdist at all.
    """
    return not IsSlaveNode(config)


# ==================================================================================================
# FakeTrFixture
# ==================================================================================================
@pytest.fixture
def fake_tr(mocker):
    """
    Fixture that replaces `tr` method used to translate messages by an implementation that only
    is able to translate messages contained in explicitly added Qt translation files.

    This method aids tests that want to translate messages but are localized at points where Qt
    is not included in environment. This weird scenario happens because currently our translation
    files are all in Qt format, even for libraries without Qt as dependency.

    :type mocker: MockTest
    """
    fake_tr_ = FakeTrFixture()
    # Translations files are located at the root of python path of each project.
    fake_tr_.SetRelativeLocation('/python/')

    import __builtin__
    mocker.patch.object(__builtin__, 'tr', fake_tr_)

    return fake_tr_


class FakeTrFixture(object):
    """
    Implementation of `fake_tr` fixture.
    """

    def __init__(self):
        # {context: {location: {source: translation}}}
        self._translations = {}
        self._relative_location = None

    def SetRelativeLocation(self, path):
        """
        Changes location of translation calls to be relative to first match
        of given path, using a reverse search.

        :param unicode path: A full or partial path.
        """
        self._relative_location = path

    def AddTranslations(self, locale_filename):
        """
        Add _translations in file to list of known translated messages.

        :param unicode locale_filename: A translation file (.ts extension).
        """
        import xml.etree.ElementTree as ET
        locale_file = ET.parse(locale_filename)
        root = locale_file.getroot()

        translations = self._translations
        for context_node in root.getchildren():
            name_node = context_node.find('name')
            context_name = name_node.text

            messages = translations.setdefault(context_name, {})
            for message_node in context_node.findall('message'):
                source_node = message_node.find('source')
                source = source_node.text

                location_node = message_node.find('location')
                location = location_node.get('filename')

                translation_node = message_node.find('translation')
                translation = translation_node.text

                locations = messages.setdefault(location, {})
                # If missing translation it is going to simply return source value
                locations[source] = translation or source

    def GetTranslation(self, context, location, source):
        """
        :param unicode context: Context of message.
        :param unicode location: File where message is located.
        :param unicode source: Message to be translated.
        """
        context_ = self._translations[context]
        location_ = context_[location]
        return unicode(location_[source])

    def __call__(self, text, context=None):
        from os.path import basename, splitext
        import sys

        if not text:
            return text

        # get the calling filename
        f = sys._getframe(1)
        try:
            filename = f.f_code.co_filename
        finally:
            del f

        if context is None:
            # extract directory and extension
            context = basename(splitext(filename)[0])

        from ben10 import filesystem
        location = filesystem.StandardizePath(filename)

        if self._relative_location is not None:
            relative_index = location.rfind(self._relative_location)
            assert relative_index != -1
            location = location[relative_index + len(self._relative_location):]

        return self.GetTranslation(context, location, text)
