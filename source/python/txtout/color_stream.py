from __future__ import unicode_literals
import sys



#===================================================================================================
# NoColorConsole
#===================================================================================================
class NoColorConsole(object):

    def SetColor(self, _foreground, _background=''):
        ''

    def Reset(self):
        ''



#===================================================================================================
# WindowsConsole
#===================================================================================================
class WindowsConsole(object):

    def __init__(self):

        def GetConst(prefix, name):
            import win32console
            return getattr(win32console, prefix + '_' + name)


        def FillColorMap(prefix, colors):
            result = { '' : 0 }
            for i_color_name, i_color_components in colors.items():
                if i_color_components:
                    value = GetConst(prefix, 'INTENSITY')
                else:
                    value = 0
                for i_component in i_color_components:
                    value |= GetConst(prefix, i_component)
                result[i_color_name] = value
            return result


        def FillColorMaps():
            colors = dict(
                BLACK=[],
                BLUE=['BLUE'],
                CYAN=['GREEN', 'BLUE'],
                GREEN=['GREEN'],
                MAGENTA=['RED', 'BLUE'],
                RED=['RED'],
                WHITE=['RED', 'GREEN', 'BLUE'],
                YELLOW=['RED', 'GREEN'],
            )
            self.foreground_map = FillColorMap('FOREGROUND', colors)
            self.background_map = FillColorMap('BACKGROUND', colors)


        def InitConsoleScreenBuffer():
            self._output_handle = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
            if self._output_handle is None:
                self._console_screen_buffer = None
            else:
                try:
                    self._reset = self._output_handle.GetConsoleScreenBufferInfo()['Attributes']
                except Exception:
                    # There is no valid console, such as when running from inside Eclipse.
                    self._console_screen_buffer = None
                else:
                    self._console_screen_buffer = win32console.PyConsoleScreenBufferType(self._output_handle)

        try:
            import win32console
        except ImportError:
            self._console_screen_buffer = None
        else:
            FillColorMaps()
            InitConsoleScreenBuffer()


    def SetColor(self, foreground, background=''):
        if self._console_screen_buffer is None:
            return
        fg_color = self.foreground_map[foreground]
        bg_color = self.background_map[background]
        self._console_screen_buffer.SetConsoleTextAttribute(fg_color | bg_color)


    def Reset(self):
        if self._console_screen_buffer is None:
            return
        self._console_screen_buffer.SetConsoleTextAttribute(self._reset)



#===================================================================================================
# TextConsole
#===================================================================================================
class TextConsole(object):

    def __init__(self, p_stream, verbose):
        self.stream = p_stream
        self.verbose = verbose


    def SetColor(self, p_foreground, _background=''):
        if self.verbose:
            self.stream.write('<%s>' % p_foreground)


    def Reset(self):
        if self.verbose:
            self.stream.write('<RESET>')



#===================================================================================================
# UnixConsole
#===================================================================================================
class UnixConsole(object):

    color_map = {
        'BLACK'   : 30,
        'BLUE'    : 34,
        'CYAN'    : 36,
        'GREEN'   : 32,
        'MAGENTA' : 35,
        'RED'     : 31,
        'WHITE'   : 37,
        'YELLOW'  : 33,
    }

    def __init__(self, p_stream):
        self.stream = p_stream


    def _ESC(self, p_code):
        self.stream.write(chr(27) + '[' + p_code)


    def SetColor(self, p_foreground, _background=''):
        self._ESC('%dm' % self.color_map[p_foreground])


    def Reset(self):
        self._ESC('0m')



#===================================================================================================
# SafeStreamFilter
#===================================================================================================
class SafeStreamFilter(object):
    '''
    Filters unicode characters by replacing their occurrences by their backslash representations.

    This is used for target streams that are not capable of printing unicode characters, namely the
    console.
    '''

    def __init__(self, stream):
        self.stream = stream
        if hasattr(stream, 'encoding'):
            self.encoding = stream.encoding
        else:
            self.encoding = None


    def write(self, text):
        try:
            self.stream.write(text)
        except UnicodeEncodeError:
            encoding = 'ascii'
            text = text.encode(encoding, 'backslashreplace').decode(encoding)
            self.stream.write(text)


    def writeln(self, text):
        return self.write(text + '\n')


    def flush(self):
        self.stream.flush()



#===================================================================================================
# ColorStream
#===================================================================================================
class ColorStream(object):

    COLORS = ['BLACK', 'BLUE', 'CYAN', 'GREEN', 'MAGENTA', 'RED', 'WHITE', 'YELLOW']

    def __init__(self, stream, force_console=False, verbose=False):
        '''
        :param bool force_console:
            Forces the ColorStream to create a console handle, even if the "IsConsole" function
            returns False.

        :param bool verbose:
            TextConsole option receives the verbose parameter in order to print color codes.

        * This is needed once the color_extension of UnitTest uses an wrapper for the StdOut as
          the stream
        '''
        # Use a filter for strange character if the target encoding matches the console.
        stream = SafeStreamFilter(stream)

        self._stream = stream
        self._CreateConsole(force_console, verbose)

        # controls if we should ignore encoding errors while writing to the stream
        self.ignore_encoding_errors = False


    def _CreateConsole(self, force_console, verbose):

        if force_console or self.IsConsole():
            if sys.platform == 'win32':
                try:
                    self.__console = WindowsConsole()
                except Exception:
                    # This error happens on executables. It is trying to obtain a handle that is
                    # invalid.
                    # (6, "DuplicateHandle", "The handle is invalid.")
                    self.__console = TextConsole(self._stream, verbose)
            else:
                self.__console = UnixConsole(self._stream)
        else:
            self.__console = TextConsole(self._stream, verbose)


    def IsConsole(self):
        '''
        Returns whether the associated stream is a console stream.

        * Check if the stream IS "stdout".
        '''
        if isinstance(self._stream, SafeStreamFilter):
            stream = self._stream.stream
        else:
            stream = self._stream
        return stream in [sys.__stdout__, sys.__stderr__]


    def write(self, p_contents):
        try:
            self._stream.write(p_contents)
        except UnicodeEncodeError, e:
            if self.ignore_encoding_errors:
                sys.stderr.write('EncodingErrorIgnored: %s' % e)
            else:
                raise

    def writeln(self, p_contents=''):
        self._stream.writeln(p_contents)


    def flush(self):
        self._stream.flush()


    def SetColor(self, p_foreground, p_background=''):
        self.__console.SetColor(p_foreground, p_background)


    def Reset(self):
        '''
        Resets any color attributes with the values stored at the console (__console) creation.
        '''
        self.__console.Reset()


    @classmethod
    def ClearAnsiColorEscapeSequences(cls, text):
        '''
        :param unicode text:
            A text with zero or more ansi color scape sequences.

        :rtype: unicode
        :returns:
            Returns the given text with all ansi color scape sequences removed.
        '''
        import re
        return re.subn('\\x1b\[.*?m', '', text)[0]
