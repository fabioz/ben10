from __future__ import unicode_literals
from ben10.execute import GetUnicodeArgv
import io
import sys


def _ExitAndPrintMessage(message):
    print(message)
    sys.exit()

if __name__ == '__main__':
    try:
        unicode_args = GetUnicodeArgv()
    except Exception as e:
        _ExitAndPrintMessage('Could not get unicode args: "%s"' % e.message)

    for arg in unicode_args:
        if not isinstance(arg, unicode):
            _ExitAndPrintMessage('There are arguments in unicode_args that are not unicode. unicode_args=%s' % unicode_args)

    try:
        input_filename = unicode_args[1]
        content = io.open(input_filename).read()
    except IOError:
        _ExitAndPrintMessage('Could not open file "%s"' % input_filename)

    _ExitAndPrintMessage(content)
