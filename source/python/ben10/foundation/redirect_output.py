from __future__ import unicode_literals
import contextlib



#===================================================================================================
# CaptureStd
#===================================================================================================
@contextlib.contextmanager
def CaptureStd():
    '''
    Context manager used to capture stdout and stderr.

    e.g.
        with CaptureStd() as output:
            print 'hey'

        repr(output.stdout) == 'hey\n'
        repr(output.stderr) == ''

    @note:
        This replaces some older code that fiddled around with file descriptions, using os.dup2
    '''
    class CapturedOutput(object):
        def __init__(self):
            from cStringIO import StringIO
            self._stdout = StringIO()
            self._stderr = StringIO()

        @property
        def stdout(self):
            return self._stdout.getvalue()

        @property
        def stderr(self):
            return self._stderr.getvalue()


    import sys
    oldout, olderr = sys.stdout, sys.stderr
    try:
        output = CapturedOutput()

        sys.stdout = output._stdout
        sys.stderr = output._stderr

        yield output
    finally:
        sys.stdout, sys.stderr = oldout, olderr

