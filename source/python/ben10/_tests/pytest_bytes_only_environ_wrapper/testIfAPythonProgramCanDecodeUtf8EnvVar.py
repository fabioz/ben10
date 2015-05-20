from __future__ import unicode_literals
from ben10.fixtures import UnicodeSamples
import os
import sys


def _ExitAndPrintMessage(message):
    print(message)
    sys.exit()

if __name__ == '__main__':
    var_name = 'MY_UNICODE_VAR'
    expected_value = UnicodeSamples.UNICODE_MULTIPLE_LANGUAGES

    if var_name not in os.environ:
        _ExitAndPrintMessage('There is not env var named "%s"' % var_name)

    obtained_value = os.environ[var_name]
    obtained_value_unicode = obtained_value.decode('utf-8')

    if obtained_value_unicode != expected_value:
        msg = 'Env var "%s" has a value different from expected.\nObtained:"%s"\nExpected:"%s"' % \
            (obtained_value_unicode, expected_value)
        _ExitAndPrintMessage()

    _ExitAndPrintMessage('OK')
