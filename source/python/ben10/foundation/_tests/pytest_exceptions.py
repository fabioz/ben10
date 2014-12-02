# coding: UTF-8
from __future__ import unicode_literals
from ben10.foundation.exceptions import ExceptionToUnicode
import locale
import sys



def testExceptionToUnicode():
    fse = sys.getfilesystemencoding()
    lpe = locale.getpreferredencoding()

    exception_message = 'кодирование'
    # Use another message if this machine's locale does not support cyrilic
    try:
        exception_message.encode(lpe)
    except UnicodeEncodeError:
        exception_message = 'látïn-1'

    fse_exception_message = exception_message.encode(fse)
    lpe_exception_message = exception_message.encode(lpe)

    # unicode exception
    assert ExceptionToUnicode(Exception(exception_message)) == exception_message
    assert ExceptionToUnicode(Exception(fse_exception_message)) == exception_message
    assert ExceptionToUnicode(Exception(lpe_exception_message)) == exception_message

    # OSError
    assert ExceptionToUnicode(OSError(2, exception_message)) == '[Errno 2] ' + exception_message
    assert ExceptionToUnicode(OSError(2, fse_exception_message)) == '[Errno 2] ' + exception_message
    assert ExceptionToUnicode(OSError(2, lpe_exception_message)) == '[Errno 2] ' + exception_message

    # IOError is really stupid, unicode(IOError('á')) actually raises UnicodeEncodeError
    # (not UnicodeDecodeError!)
    assert ExceptionToUnicode(IOError(exception_message)) == exception_message
    assert ExceptionToUnicode(IOError(fse_exception_message)) == exception_message
    assert ExceptionToUnicode(IOError(lpe_exception_message)) == exception_message

    # Custom exception
    class MyException(Exception):
        def __unicode__(self):
            return 'hardcoded unicode repr'
    assert ExceptionToUnicode(MyException(exception_message)) == 'hardcoded unicode repr'

    # Unknown encoding
    assert ExceptionToUnicode(Exception(b'random \x90\xa1\xa2')) == 'random \ufffd\ufffd\ufffd'


