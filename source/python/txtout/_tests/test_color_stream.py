from __future__ import unicode_literals
from io import StringIO
from txtout.color_stream import ColorStream, UnixConsole



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testColorStream(self):
        stream = StringIO()
        color_stream = ColorStream(stream, verbose=True)
        color_stream.write('alpha')
        color_stream.SetColor('RED')
        color_stream.write('bravo')
        color_stream.Reset()
        color_stream.writeln('charlie')
        color_stream.writeln('delta')

        assert stream.getvalue() == 'alpha<RED>bravo<RESET>charlie\ndelta\n'

        color_stream.write(u'echo')
        assert stream.getvalue() == 'alpha<RED>bravo<RESET>charlie\ndelta\necho'


    def testUnixConsole(self):

        stream = StringIO()
        con = UnixConsole(stream)
        stream.write('alpha')
        con.SetColor('RED')
        stream.write('bravo')
        con.Reset()
        stream.write('charlie')

        assert stream.getvalue() == 'alpha\x1B[31mbravo\x1B[0mcharlie'


    def testClearAnsiColorEscapeSequences(self):

        assert (
            ColorStream.ClearAnsiColorEscapeSequences('alpha\x1B[31mbravo\x1B[0mcharlie')
            == 'alphabravocharlie'
        )
