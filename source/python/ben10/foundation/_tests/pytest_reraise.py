# coding=utf-8
from __future__ import unicode_literals
from ben10.foundation.exceptions import ExceptionToUnicode
from ben10.foundation.reraise import Reraise
import pytest



#===================================================================================================
# ExecutePythonCode
#===================================================================================================
def ExecutePythonCode(code):
    exec compile(code, '<string>', 'exec')



parametrized_exceptions = pytest.mark.parametrize('exception_type, string_statement, expected_inner_exception_message', [
    (ValueError, "raise ValueError('message')", 'message'),
    (KeyError, "raise KeyError('message')", "u'message'"),
    (OSError, "raise OSError(2, 'message')", '[Errno 2] message'),
    (SyntaxError, "raise SyntaxError('message')", 'message'),
    (UnicodeDecodeError, "u'£'.encode('utf-8').decode('ascii')", "'ascii' codec can't decode byte 0xc2 in position 0: ordinal not in range(128)"),
    (UnicodeEncodeError, "u'£'.encode('ascii')", "'ascii' codec can't encode character u'\\xa3' in position 0: ordinal not in range(128)"),
    (AttributeError, "raise AttributeError('message')", 'message'),

    (OSError, "raise OSError()", ''),
    (OSError, "raise OSError(1)", '1'),
    (OSError, "raise OSError(2, '£ message')", '[Errno 2] £ message'),
    (IOError, "raise IOError('исключение')", "исключение"),

    # exceptions in which the message is a 'bytes' but is encoded in UTF-8
    (OSError, "raise OSError(2, b'£ message')", '[Errno 2] Â£ message'),
    (Exception, "raise Exception(b'£ message')", 'Â£ message'),
    (SyntaxError, "raise SyntaxError(b'£ message')", 'Â£ message'),

], ids=[
    'ValueError',
    'KeyError',
    'OSError',
    'SyntaxError',
    'UnicodeDecodeError',
    'UnicodeEncodeError',
    'AttributeError',

    'OSError - empty',
    'OSError - ErrorNo, empty message',
    'OSError - ErrorNo, unicode message',
    'IOError - unicode message',

    'OSError - bytes message',
    'Exception - bytes message',
    'SyntaxError - bytes message',
])


@parametrized_exceptions
def testReraiseKeepsTraceback(exception_type, string_statement, expected_inner_exception_message):
    def RaiseError():
        ExecutePythonCode(string_statement)
        pytest.fail('Should not reach here')

    def RaiseErrorByReraising():
        try:
            RaiseError()
        except exception_type, inner_exception:
            Reraise(inner_exception, 'Reraise message')
        except Exception, e:
            pytest.fail('got wrong type: %s. Exception: %s' % (type(e), e))

    with pytest.raises(exception_type) as e:
        RaiseErrorByReraising()

    # Reraise() should not appear in the traceback
    crash_entry = e.traceback.getcrashentry()
    for traceback_entry in e.traceback:
        if traceback_entry == crash_entry:
            assert traceback_entry.path == '<string>'
        else:
            assert traceback_entry.path.basename == 'pytest_reraise.py'

    assert crash_entry.locals['code'] == string_statement


@parametrized_exceptions
def testReraiseAddsMessagesCorrectly(exception_type, string_statement, expected_inner_exception_message):
    def foo():
        ExecutePythonCode(string_statement)
        pytest.fail('Should not reach here')

    def bar():
        try:
            foo()
        except Exception, exception:
            Reraise(exception, "While doing 'bar'")

    def foobar():
        try:
            try:
                bar()
            except Exception, exception:
                Reraise(exception, "While doing x:")
        except Exception, exception:
            Reraise(exception, "While doing y:")

    with pytest.raises(exception_type) as e:
        foobar()

    assert ExceptionToUnicode(e.value) == "\nWhile doing y:\nWhile doing x:\nWhile doing 'bar'\n" + expected_inner_exception_message


@parametrized_exceptions
def testPickle(exception_type, string_statement, expected_inner_exception_message):
    '''
    Make sure that we can Pickle reraised exceptions.
    '''
    try:
        try:
            ExecutePythonCode(string_statement)
            pytest.fail('Should not reach here')
        except exception_type as original_exception:
            Reraise(original_exception, 'new stuff')
    except Exception as reraised_exception:
        import cPickle
        dumped_exception = cPickle.dumps(reraised_exception)
        pickled_exception = cPickle.loads(dumped_exception)
        assert ExceptionToUnicode(pickled_exception) == ExceptionToUnicode(reraised_exception)
        assert ExceptionToUnicode(pickled_exception) != ''
        assert ExceptionToUnicode(reraised_exception) != ''
