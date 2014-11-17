from __future__ import unicode_literals
from ben10.filesystem import CreateFile, StandardizePath
from ben10.fixtures import MultipleFilesNotFound, _EmbedDataFixture
from ben10.foundation import handle_exception
from ben10.foundation.handle_exception import IgnoringHandleException
from ben10.foundation.is_frozen import IsFrozen, SetIsFrozen
from ben10.foundation.string import Dedent
import faulthandler
import os
import pytest



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
        *** FILENAME: data_fixtures__testEmbedDataAssertEqualFiles/alpha.txt
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


def testNotOnFrozen(monkeypatch, embed_data):
    '''
    We fail to create data directory IF we are inside a generated executable (IsFrozen).
    '''
    was_frozen = IsFrozen()
    try:
        SetIsFrozen(True)

        with pytest.raises(RuntimeError) as exception:
            embed_data.CreateDataDir()

        assert \
            '_EmbedDataFixture is not ready for execution inside an executable.' \
            in unicode(exception)
    finally:
        SetIsFrozen(was_frozen)


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

@pytest.mark.parametrize('i', [0, 1, 'foo-' + _invalid_chars_for_paths])
def testFaultHandler(i, request):
    """
    Make sure that faulthandler library is enabled during tests run.

    .. note:: we use a parametrized test here to ensure we are taking parametrization in account
        when we generate the file name for the fault handler log file, including using
        a parameter that contains invalid characters for paths.
    """
    assert faulthandler.is_enabled()
    assert os.path.isfile(request.node.fault_handler_stream.name)


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


