from __future__ import unicode_literals
from ben10.filesystem import CreateFile, StandardizePath
from ben10.fixtures import InstallFaultHandler, MultipleFilesNotFound, _EmbedDataFixture
from ben10.foundation import handle_exception
from ben10.foundation.handle_exception import IgnoringHandleException
from ben10.foundation.string import Dedent
import faulthandler
import os
import pytest


pytest_plugins = b'pytester'


def testEmbedData(embed_data):
    assert not os.path.isdir('data_fixtures__testEmbedData')

    embed_data.CreateDataDir()

    assert os.path.isdir('data_fixtures__testEmbedData')

    # Checking if all contents of pytest_fixtures is present
    assert os.path.isfile(embed_data.GetDataFilename('alpha.txt'))
    assert os.path.isfile(embed_data.GetDataFilename('alpha.dist-12.0-win32.txt'))
    assert os.path.isfile(embed_data.GetDataFilename('alpha.dist-12.0.txt'))

    # Checking auxiliary functions
    assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedData'
    assert embed_data.GetDataFilename('alpha.txt') == 'data_fixtures__testEmbedData/alpha.txt'

    assert embed_data.GetDataDirectory(absolute=True) \
        == StandardizePath(os.path.abspath('data_fixtures__testEmbedData'))
    assert embed_data.GetDataFilename('alpha.txt', absolute=True) \
        == StandardizePath(os.path.abspath('data_fixtures__testEmbedData/alpha.txt'))


@pytest.mark.parametrize(('foo',), [('a',), ('b',), ('c',)])
def testEmbedDataParametrize(embed_data, foo):
    '''
    asserts that we get unique data directories when mixing embed_data with pytest.mark.parametrize
    '''
    if foo == 'a':
        assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedDataParametrize_foo0_'
    if foo == 'b':
        assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedDataParametrize_foo1_'
    if foo == 'c':
        assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedDataParametrize_foo2_'


def testEmbedDataExistingDataDir(embed_data):
    # Create the directory manually (we must not use any embed_data functions or else the
    # directory is created)
    extra_txt = 'data_fixtures__testEmbedDataExistingDataDir/extra.txt'
    CreateFile(extra_txt, 'This file will perish')
    assert os.path.isfile(extra_txt)

    # Calling CreateDataDir again will recreate the directory, deleting the old file
    embed_data.CreateDataDir()
    assert not os.path.isfile(extra_txt)


def testEmbedDataAssertEqualFiles(embed_data):
    CreateFile(embed_data.GetDataFilename('equal.txt'), 'This is alpha.txt')
    embed_data.AssertEqualFiles(
        'alpha.txt',
        'equal.txt'
    )

    CreateFile(embed_data.GetDataFilename('different.txt'), 'This is different.txt')
    with pytest.raises(AssertionError) as e:
        embed_data.AssertEqualFiles(
            'alpha.txt',
            'different.txt'
        )
    assert unicode(e.value) == Dedent(
        '''
        FILES DIFFER:
        data_fixtures__testEmbedDataAssertEqualFiles/alpha.txt
        data_fixtures__testEmbedDataAssertEqualFiles/different.txt
        ***\w

        ---\w

        ***************

        *** 1 ****

        ! This is alpha.txt
        --- 1 ----

        ! This is different.txt
        '''.replace('\w', ' ')
    )


    with pytest.raises(MultipleFilesNotFound) as e:
        embed_data.AssertEqualFiles(
            'alpha.txt',
            'missing.txt'
        )

    assert (
        unicode(e.value)
        == 'Files not found: '
        'missing.txt,data_fixtures__testEmbedDataAssertEqualFiles/missing.txt'
    )


def testEmbedDataFixture(request):
    assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False

    try:
        embed_data = _EmbedDataFixture(request)
        assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False

        assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedDataFixture'
        assert os.path.isdir('data_fixtures__testEmbedDataFixture') == True
    finally:
        embed_data.Finalizer()

    assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False


_invalid_chars_for_paths = os.sep + os.pathsep


def testFaultHandler(pytestconfig):
    '''
    Make sure that faulthandler library is enabled during tests
    '''
    assert faulthandler.is_enabled()
    assert pytestconfig.fault_handler_file is None


def testFaultHandlerWithoutStderr(monkeypatch, embed_data):
    """
    Test we are enabling fault handler in a file based on sys.executable in case sys.stderr does not
    point to a valid file. This happens in frozen applications without a console.
    """
    import sys

    class Dummy(object):
        pass

    monkeypatch.setattr(sys, 'stderr', Dummy())
    monkeypatch.setattr(sys, 'executable', embed_data['myapp'])
    config = Dummy()
    InstallFaultHandler(config)
    assert config.fault_handler_file is not None
    assert config.fault_handler_file.name == embed_data['myapp'] + ('.faulthandler-%s.txt' % os.getpid())
    assert os.path.isfile(config.fault_handler_file.name)
    config.fault_handler_file.close()


def testHandledExceptions(handled_exceptions):
    assert not handled_exceptions.GetHandledExceptions()

    with IgnoringHandleException():
        try:
            raise RuntimeError('test')
        except:
            handle_exception.HandleException()

    assert len(handled_exceptions.GetHandledExceptions()) == 1

    with pytest.raises(AssertionError):
        handled_exceptions.RaiseFoundExceptions()

    handled_exceptions.ClearHandledExceptions()


def testDataRegressionFixture(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir

    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys
    import yaml

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    monkeypatch.setattr(sys, 'GetData', lambda: {'contents': 'Foo', 'value': 10}, raising=False)
    source = '''
        import sys
        def test_1(data_regression):
            contents = sys.GetData()
            data_regression.Check(contents)
    '''
    testdir.makepyfile(test_file=source)

    # First run fails because there's no yml file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    def GetYmlContents():
        yaml_filename = str(testdir.tmpdir / 'test_file' / 'test_1.yml')
        assert os.path.isfile(yaml_filename)
        with open(yaml_filename) as f:
            return yaml.load(f)

    # ensure now that the file was generated and the test passes
    assert GetYmlContents() == {'contents': 'Foo', 'value': 10}
    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    # changing the regression data makes the test fail (file remains unchanged)
    monkeypatch.setattr(sys, 'GetData', lambda: {'contents': 'Bar', 'value': 20}, raising=False)
    result = testdir.inline_run()
    result.assertoutcome(failed=1)
    assert GetYmlContents() == {'contents': 'Foo', 'value': 10}

    # force regeneration (test fails again)
    result = testdir.inline_run('--force-regen')
    result.assertoutcome(failed=1)
    assert GetYmlContents() == {'contents': 'Bar', 'value': 20}

    # test should pass again
    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def testDataRegressionFixtureFullPath(testdir, tmpdir):
    """
    Test data_regression with ``fullpath`` parameter.

    :type testdir: _pytest.pytester.TmpTestdir
    """
    fullpath = tmpdir.join('full/path/to').ensure(dir=1).join('contents.yaml')
    assert not fullpath.isfile()

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        def test(data_regression):
            contents = {'data': [1, 2]}
            data_regression.Check(contents, fullpath=%s)
    ''' % (repr(str(fullpath)))
    testdir.makepyfile(test_foo=source)
    # First run fails because there's no yml file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    assert fullpath.isfile()
    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def testSessionTmpDir(testdir):

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        import os
        def test_1(session_tmp_dir):
            assert os.path.exists(session_tmp_dir)
            for i in xrange(10):
                filename = os.path.join(session_tmp_dir, 'file%d.txt' % i)
                if not os.path.exists(filename):
                    file(filename, 'w')
                    break
    '''
    testdir.makepyfile(test_file=source)

    def CheckSessionDir(session_dir, contents):
        assert session_dir.exists()
        assert set(os.listdir(unicode(session_dir))) == contents

    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    # Check directories created
    tmp_dir = testdir.tmpdir.join('tmp')
    assert tmp_dir.exists()

    session_0_dir = tmp_dir.join('session-tmp-dir-0')
    CheckSessionDir(session_0_dir, {'.lock', 'file0.txt'})

    # New run, new session tmp dir
    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    session_1_dir = tmp_dir.join('session-tmp-dir-1')
    CheckSessionDir(session_1_dir, {'.lock', 'file0.txt'})

    # Check if we can re-use the last session tmp dir
    result = testdir.inline_run('--last-session-tmp-dir')
    result.assertoutcome(passed=1)
    # Make sure the test created a new file
    CheckSessionDir(session_1_dir, {'.lock', 'file0.txt', 'file1.txt'})

    # Check if we can re-use a previous existing tmp dir
    result = testdir.inline_run('--session-tmp-dir=%s' % unicode(session_0_dir))
    result.assertoutcome(passed=1)
    # Make sure the test created a new file
    CheckSessionDir(session_0_dir, {'.lock', 'file0.txt', 'file1.txt'})


def testSessionTmpDirXDist(testdir):
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        import os
        import pytest

        @pytest.mark.parametrize('i', range(4))
        def test_foo(i, session_tmp_dir):
            assert os.path.isdir(session_tmp_dir)
    '''
    testdir.makepyfile(test_file=source)

    result = testdir.inline_run('-n2')
    result.assertoutcome(passed=4)
    assert {'session-tmp-dir-0'}.issubset(os.listdir(str(testdir.tmpdir.join('tmp'))))

    result = testdir.inline_run('-n4')
    result.assertoutcome(passed=4)
    assert {'session-tmp-dir-0', 'session-tmp-dir-1'}.issubset(os.listdir(str(testdir.tmpdir.join('tmp'))))
           

