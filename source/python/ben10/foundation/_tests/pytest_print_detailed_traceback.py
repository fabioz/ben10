# coding: UTF-8
from __future__ import unicode_literals
from ben10.filesystem import CreateFile
from ben10.foundation.print_detailed_traceback import PrintDetailedTraceback
from io import BytesIO, StringIO
import pytest
import re


def testPrintDetailedTraceback(embed_data):

    def Pad(seq):
        """Pads a sequence of strings with up to 4 leading '0' chars"""
        result = []
        for value in seq:
            try:
                result.append('0' * (4 - len(value)) + value)
            except TypeError:
                # we raise our own exception because the message changes between python versions
                raise TypeError("object of type 'int' has no len()")
        return result

    data = map(unicode, xrange(100))
    data[3] = 3

    stream = StringIO()
    try:
        Pad(data)
    except:
        PrintDetailedTraceback(max_levels=2, stream=stream, max_line_width=100)
    else:
        assert False, 'Pad() should fail with an exception!'

    ss = stream.getvalue()

    # >>> Remove parts of the string that are platform/file system dependent

    # remove filename
    filename_re = re.compile(re.escape(__file__) + '?', re.IGNORECASE)
    ss = re.sub(filename_re, '/path_to_file/file.py', ss)

    # remove address of objects
    address_re = re.compile('at 0x([a-f0-9]+)', re.IGNORECASE)
    ss = re.sub(address_re, 'at 0x0', ss)

    # "self" description because the name of the module changes if we run this test
    # from the command line vs running it with runtests
    self_re = re.compile('self = <.*>', re.IGNORECASE)
    ss = re.sub(self_re, 'self = <Test.testPrintDetailedTraceback>', ss)

    obtained_filename = embed_data['traceback.obtained.txt']
    CreateFile(obtained_filename, ss)

    # Changes
    # File "/path_to_file/file.py", line 51, in testPrintDetailedTraceback
    # to:
    # File "/path_to_file/file.py", line XX, in testPrintDetailedTraceback
    def FixIt(lines):
        import re
        return [re.sub('line (\\d)+', 'line XX', i) for i in lines]

    embed_data.AssertEqualFiles(
        obtained_filename,
        'traceback.expected.txt',
        fix_callback = FixIt
    )


def testNoException():
    '''
    Should not print anything in case there's no exception info (complies with the behavoir from
    traceback.print_exception)
    '''
    from StringIO import StringIO as OldStringIO

    # "Old", non-io StringIO: doesn't perform typechecks when writing. Since when there's no
    # exception the code falls back to traceback.print_exception, the stream must be able to
    # accept bytes.
    stream = OldStringIO()
    PrintDetailedTraceback(exc_info=(None, None, None), stream=stream)
    assert stream.getvalue() == 'None\n'


@pytest.mark.parametrize(('exception_message',), [(u'fake unicode message',), (u'Сообщение об ошибке.',)])
def testPrintDetailedTracebackWithUnicode(exception_message):
    '''
    Test PrintDetailedTraceback with 'plain' unicode arguments and an unicode argument with cyrillic
    characters
    '''

    stream = StringIO()
    try:
        raise Exception(exception_message)
    except:
        PrintDetailedTraceback(stream=stream)

    assert 'Exception: %s' % (exception_message) in stream.getvalue()


@pytest.mark.parametrize(('exception_message',), [(u'fake unicode message',), (u'Сообщение об ошибке.',)])
def testPrintDetailedTracebackToFakeStderr(exception_message):
    '''
    Test PrintDetailedTraceback with 'plain' unicode arguments and an unicode argument with cyrillic
    characters, written to a buffer similar to PrintDetailedTraceback()'s default stream, sys.std_err
    '''
    import sys

    # Since we want to check the values written, create a 'fake_stderr' that is simple a BytesIO
    # with the same expected encoding as sys.std_err's encoding.
    sys.stderr = fake_stderr = BytesIO()
    sys.stderr.encoding = 'ascii'
    try:
        raise Exception(exception_message)
    except:
        PrintDetailedTraceback(stream=fake_stderr)

    written_traceback = fake_stderr.getvalue()
    encoded_message = exception_message.encode(sys.stderr.encoding, errors='replace')
    assert b'Exception: %s' % encoded_message in written_traceback


@pytest.mark.parametrize(('exception_message',), [(u'fake unicode message',), (u'Сообщение об ошибке.',)])
def testPrintDetailedTracebackToRealStderr(exception_message):
    '''
    The same as above, but writing to the real stderr. Just a smoke test to verify that no errors
    occur.
    '''
    try:
        raise Exception(exception_message)
    except:
        PrintDetailedTraceback()


def testOmitLocals():
    '''
    Makes sure arguments and local variables are not present in traceback contents whenever
    omit locals option is enabled.
    '''
    stream = StringIO()
    def Flawed(foo):
        arthur = 'dent'  # @UnusedVariable
        raise Exception('something')

    try:
        Flawed(foo='bar')
    except:
        PrintDetailedTraceback(stream=stream, omit_locals=True)

    stream_value = stream.getvalue()
    assert 'foo' not in stream_value
    assert 'bar' not in stream_value
    assert 'arthur' not in stream_value
    assert 'dent' not in stream_value
