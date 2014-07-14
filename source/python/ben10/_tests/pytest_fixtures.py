from ben10.filesystem import CreateFile, StandardizePath
from ben10.fixtures import MultipleFilesNotFound, SkipIfImportError, _EmbedDataFixture
from ben10.foundation import is_frozen
from ben10.foundation.string import Dedent
import os
import pytest



pytest_plugins = ["ben10.fixtures"]



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

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
        monkeypatch.setattr(is_frozen, 'IsFrozen', lambda:True)

        with pytest.raises(RuntimeError) as exception:
            embed_data.CreateDataDir()

        assert \
            '_EmbedDataFixture is not ready for execution inside an executable.' \
            in str(exception)


    def testSkipIfImportError(self):
        r = SkipIfImportError('sys')
        assert repr(r) == "<MarkDecorator 'skipif' {'args': ('False',), 'kwargs': {}}>"

        r = SkipIfImportError('invalid')
        assert repr(r) == "<MarkDecorator 'skipif' {'args': ('True',), 'kwargs': {}}>"


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


    @pytest.mark.performance
    def testPerformance(self, performance):
        setup = \
            '''
            def hello():
                for i in range(5000):
                    hello_world = 'hello' + 'world'
            '''
        stmt = 'hello()'

        PERF = 1.34  # Real expected performance

        # This should pass
        performance(setup, stmt, expected_performance=PERF, accepted_variance=1)

        # This should fail because we were too slow
        with pytest.raises(AssertionError):
            performance(setup, stmt, expected_performance=PERF / 10, accepted_variance=1)

        # This should pass because we were too slow, but we accept a huge variance
        performance(setup, stmt, expected_performance=PERF / 10, accepted_variance=100)

        # This should fail because we were too fast!
        with pytest.raises(AssertionError):
            performance(setup, stmt, expected_performance=PERF * 10, accepted_variance=1)

        # This should pass because we were too fast, but we accept a huge variance
        performance(setup, stmt, expected_performance=PERF * 10, accepted_variance=100)

        # Check show_graph option
        import mock
        with mock.patch('ben10.debug.profiling.ShowGraph', autospec=True) as mock_show_graph:
            performance(setup, stmt, expected_performance=PERF, accepted_variance=1, show_graph=True)
        assert mock_show_graph.call_count == 1
