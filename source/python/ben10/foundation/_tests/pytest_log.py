from StringIO import StringIO
from ben10.foundation import log
from ben10.foundation.string import Dedent
import sys



#===================================================================================================
# Test
#===================================================================================================
def testHandlers():
    stream = StringIO()
    original = sys.stderr
    null_handler = log.NullHandler()
    try:
        sys.stderr = stream

        logger = log.GetLogger('test_handler')
        logger.Error('Test')

        logger.AddHandler(null_handler)
        logger.Error('Test2')
    finally:
        logger.RemoveHandler(null_handler)
        sys.stderr = original

    # Change: No handlers could be found for logger "test_handler" is not logged
    # as we now add a NullHandler by default (in which case that warning won't appear
    # and a StreamHandler won't be automatically created!)
    assert stream.getvalue().strip() == ''


def testWithLogger():
    contents = Dedent(
        '''
        from __future__ import with_statement
        from ben10.log import StartLogging, GetLogger
        with StartLogging() as logger:
            GetLogger('').Warn('something')
            assert 'something' in logger.GetRecordedLog()
            assert 'something' in logger.GetRecordedLog()
        '''
    )
    code = compile(contents, '<string>', 'exec')


def testAddDebugStreamHandler(capsys):
    logger = log.AddDebugStreamHandler('test_handler')
    logger.Error('alpha')
    assert capsys.readouterr() == ('', 'alpha\n')


def testStartLogging(capsys):
    logger = log.GetLogger('test_handler')
    logger.Error('alpha')
    with log.StartLogging('test_handler') as logger_stack:
        logger.Error('bravo')
    logger.Error('bravo')
    assert logger_stack.GetRecordedLog() == 'bravo\n'


def testExceptionWithDetailedTraceback():
    with log.StartLogging() as logger:
        try:
            raise RuntimeError('testDetailedTraceback: error occurred')
        except RuntimeError:
            log.GetLogger().ExceptionWithDetailedTraceback('HEADER')

        assert 'HEADER' in logger.GetRecordedLog()
        assert 'testDetailedTraceback: error occurred' in logger.GetRecordedLog()
