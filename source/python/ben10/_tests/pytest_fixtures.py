from ben10.filesystem import CreateFile, StandardizePath
from ben10.fixtures import MultipleFilesNotFound, _EmbedDataFixture
from ben10.foundation.is_frozen import IsFrozen, SetIsFrozen
from ben10.foundation.string import Dedent
import faulthandler
import os
import pytest


pytest_plugins = ["ben10.fixtures"]



#===================================================================================================
# Test
#===================================================================================================
class TestEmbedData(object):

    def testEmbedData(self, embed_data):
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


    def testEmbedDataExistingDataDir(self, embed_data):
        # Create the directory manually (we must not use any embed_data functions or else the
        # directory is created)
        extra_txt = 'data_fixtures__testEmbedDataExistingDataDir/extra.txt'
        CreateFile(extra_txt, 'This file will perish')
        assert os.path.isfile(extra_txt)

        # Calling CreateDataDir again will recreate the directory, deleting the old file
        embed_data.CreateDataDir()
        assert not os.path.isfile(extra_txt)


    def testEmbedDataAssertEqualFiles(self, embed_data):
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
        assert str(e.value) == Dedent(
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
            str(e.value)
            == 'Files not found: '
            'missing.txt,data_fixtures__testEmbedDataAssertEqualFiles/missing.txt'
        )


    def testNotOnFrozen(self, monkeypatch, embed_data):
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
                in str(exception)
        finally:
            SetIsFrozen(was_frozen)


    def testEmbedDataFixture(self, request):
        assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False

        try:
            embed_data = _EmbedDataFixture(request)
            assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False

            assert embed_data.GetDataDirectory() == 'data_fixtures__testEmbedDataFixture'
            assert os.path.isdir('data_fixtures__testEmbedDataFixture') == True
        finally:
            embed_data.Finalizer()

        assert os.path.isdir('data_fixtures__testEmbedDataFixture') == False


@pytest.mark.parametrize('i', [0, 1])
def testFaultHandler(i, request):
    """
    Make sure that faulthandler library is enabled during tests run.

    .. note:: we use a parametrized test here to ensure we are taking parametrization in account
        when we generate the file name for the fault handler log file.
    """
    assert faulthandler.is_enabled()
    assert os.path.isfile(request.node.fault_handler_stream.name)
