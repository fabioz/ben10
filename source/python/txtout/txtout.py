from __future__ import unicode_literals
from ben10.foundation.types_ import CheckType
import os
import sys



#===================================================================================================
# IndentContextManager
#===================================================================================================
class IndentContextManager(object):
    '''
    Represents a section in the output stream.

    Used with the 'with' statement.

    Starts a new indentation level upon entry, and dedent on exit.
    '''
    def __init__(self, oss):
        self._oss = oss


    def __enter__(self):
        self._oss.Indent()


    def __exit__(self, *args):
        self._oss.Dedent()



#===================================================================================================
# AbstractTextOutput
#===================================================================================================
class AbstractTextOutput(object):

    def __init__(self, stream=None, verbose_level=1):
        if stream is None:
            stream = sys.stdout
        self.SetOutputStream(stream)
        self.verbose_level = verbose_level
        self.default_verbose = 1
        self._registered_keywords = {}
        self._current_keywords = set([])


    # Output Stream --------------------------------------------------------------------------------

    def OutputStream(self):
        if hasattr(self._oss, '_stream'):
            return self._oss._stream
        else:
            return self._oss


    def SetOutputStream(self, stream, force_console=False, verbose=False):
        self._oss = stream


    # Verbose --------------------------------------------------------------------------------------

    class InvalidKeywordError(RuntimeError):
        pass


    def TestVerbose(self, verbose):
        return verbose <= self.verbose_level


    def _HandleVerbose(self, kargs):
        '''
        Returns wheter to continue or not a print proceses based on the verbose level ('verbose'
        keyword in the p_kargs)
        '''
        verbose = kargs.get('verbose', self.default_verbose)
        result = self.TestVerbose(verbose)
        return result


    def _HandleKeywords(self, kargs):
        keywords = kargs.get('keywords')
        if keywords is None:
            return True

        CheckType(keywords, (list, tuple))

        # Check if keywords are valid
        # ==> Raises InvalidKeywordError
        for i_keyword in keywords:
            if i_keyword not in self._registered_keywords:
                raise self.InvalidKeywordError(
                    'The keyword %r is not registered in this TextOutput.\n'
                    'Use the method RegisterKeyword to register a keyword BEFORE using it.' % i_keyword)

        # Check if keywords is current.
        for i_keyword in keywords:
            if i_keyword in self._current_keywords:
                return True
        return False


    # Basic write methods --------------------------------------------------------------------------

    def writeln(self, p_text=''):
        '''
            Writes a line in the output stream.

            * 'writeln' is expected by the UnitTest framework.
        '''
        self._oss.write(p_text)
        self._oss.write('\n')


    def write(self, p_text):
        '''
            Writes in the output stream.

            * 'write' implements the file interface.
        '''
        self._oss.write(p_text)


    def flush(self):
        '''
        Emulating file interface (flush method) as expected on coilib50's unittest framekwork.
        '''
        self._oss.flush()


    # Indent ---------------------------------------------------------------------------------------

    def ResetIndentation(self, **kargs):
        return

    def Indent(self, **kargs):
        return

    def Dedent(self, **kargs):
        return


    # Hi-level writing methods ---------------------------------------------------------------------

    def LINE(self, p_char, **kargs):
        raise NotImplementedError()


    def P(self, *args, **kargs):
        raise NotImplementedError()


    def I(self, *args, **kargs):
        raise NotImplementedError()


    def DT(self, *args, **kargs):
        raise NotImplementedError()


    def DD(self, p_caption, p_text, **kargs):
        raise NotImplementedError()


    def PROCESSING(self, state, text=None, **kargs):
        raise NotImplementedError()


    def ERROR(self, p_text, **kargs):
        raise NotImplementedError()


    def HEADER(self, *args, **kargs):
        raise NotImplementedError()


    def DETAILED_EXCEPTION(self, **kargs):
        raise NotImplementedError()


    def EXCEPTION(self, **kargs):
        raise NotImplementedError()


    def TABLE(self, **kargs):
        raise NotImplementedError()



#===================================================================================================
# HtmlTextOutput
#===================================================================================================
class HtmlTextOutput(AbstractTextOutput):


    # Hi-level writing methods ---------------------------------------------------------------------

    def LINE(self, p_char, **kargs):
        self.write('---')


    def P(self, *args, **kargs):
        self.write('<P>' + ' '.join(args) + '</P>\n')


    def I(self, *args, **kargs):
        self.write('<I>' + ' '.join(args) + '</I>\n')


    def DT(self, *args, **kargs):
        self.write('<DT>' + ' '.join(args) + '</DT>\n')


    def DD(self, p_caption, p_text, **kargs):
        self.DT(p_caption)
        self.write('<DD>' + p_text + '</DD>\n')


    def PROCESSING(self, state, text=None, **kargs):
        self.write(state)
        if text is not None:
            self.write(text)


    def ERROR(self, p_text, **kargs):
        return


    def HEADER(self, *args, **kargs):
        return


    def EXCEPTION(self, **kargs):
        return


    def TABLE(self, **kwargs):
        return


#===================================================================================================
# TextOutput
#===================================================================================================
class TextOutput(AbstractTextOutput):
    '''
    Text output formatter.

    :cvar bool WRAP_LINES:
        If enabled, this class will use `c_page_width` to determine the size of lines printed.
        This determines how many chars are printed in `self.LINE`, and at what length text will be
        wrapped
            .. seealso:: textwrap.wrap

        If disabled, text lines will have no limit (meaning that even very long lines of text will
        be printed in a single line in a console), and will also cap `self.LINE` characters to 80
        (useful for testing, when we don't want output length to vary)
    '''
    DEFAULT_PAGE_WIDTH = 80
    WRAP_LINES = True

    c_indent_len = 4
    c_indent_str = ' ' * c_indent_len
    c_page_width = int(os.environ.get('ESSS_WIDTH', DEFAULT_PAGE_WIDTH))


    def __init__(self, stream=None, verbose_level=1):
        if stream is None:
            stream = sys.stdout
        super(TextOutput, self).__init__(
            stream,
            verbose_level=verbose_level
        )
        self._indentation = 0
        self._processing_count = 0
        self._processing_indent = 0



    # Output Stream --------------------------------------------------------------------------------
    def SetOutputStream(self, stream, force_console=False, verbose=False):
        '''
        Set the output stream for the given one.
        '''
        import color_stream

        if stream is None:
            stream = sys.stdout

        self._oss = color_stream.ColorStream(stream, force_console=force_console, verbose=verbose)

        if force_console or self._oss.IsConsole():
            self.flat_output = False
        else:
            self.flat_output = True


    # Keywords -------------------------------------------------------------------------------------
    def SetKeyword(self, keyword, on=True):
        if on:
            self._current_keywords.add(keyword)
        else:
            self._current_keywords.remove(keyword)


    def ListKeywords(self):
        return self._registered_keywords.keys()


    def RegisterKeyword(self, keyword, help_line):
        '''
        Register a new keyword in the text-output.
        Keywords are used to filter output for methods that have the "keywords" argument.
        Methods that do not have the keywords argument are not influencied by the current
        keywords.
        '''
        self._registered_keywords[keyword] = help_line


    # Indentation ----------------------------------------------------------------------------------
    def ResetIndentation(self, **kargs):
        '''
        Resets the indentation level.
        '''
        if not self._HandleVerbose(kargs):
            return

        self._indentation = 0


    def Indent(self, **kargs):
        '''
        Adds one to the global indentation level.

        * The global indentation is used for all method calls without "indent" keyword.
        '''
        if not self._HandleVerbose(kargs):
            return

        self._indentation += 1


    def Dedent(self, **kargs):
        '''
        Subs one to the global indentation level.

        * The global indentation is used for all method calls without "indent" keyword.
        '''
        if not self._HandleVerbose(kargs):
            return

        self._indentation -= 1


    def __i(self, p_indent):
        if p_indent is None:
            p_indent = 0
        return self.c_indent_str * (self._indentation + p_indent)


    def _IndentStrings(self, p_indent, p_mark=''):
        '''
        Returns a pair of strings, one for the first line indentation and the other for the
        other lines.

        The first line indentation adds the given 'mark' to it. The other lines indentation,
        replace the mark for white spaces, making the text aligned.
        '''
        r_next = self.__i(p_indent)
        r_first = r_next + p_mark
        r_next = r_next + ' ' * len(p_mark)
        return r_first, r_next


    # Write ----------------------------------------------------------------------------------------
    def WriteCarriageReturn(self):
        '''
        Writes a carriage return, considering the "IsConsole" property. For non-console streams,
        writes '\\r' instead of the carriage return code.
        '''
        if self._oss.IsConsole():
            self._oss.write('\r')
        else:
            self._oss.write('\\r')


    def ColorWrite(self, p_color, p_text):
        '''
        Writes in the output stream using the given color.
        '''
        if p_color is not None and not self.flat_output:
            try:
                self._oss.SetColor(p_color)
                self.write(p_text)
            finally:
                self._oss.Reset()
        else:
            self.write(p_text)


    def _WrapLines(self, p_text, p_first_indent, p_next_indent, page_width=None):
        '''
        Wrap the given text, observing the page_width and the given indentations.
        '''
        import textwrap

        if not self.WRAP_LINES:
            # When fixed width is disabled, pass a large size to textwrap, to ignore wrapping
            # (we still use it to handle indents)
            page_width = sys.maxint
        elif page_width is None:
            page_width = self.c_page_width

        result = []

        for i_line in p_text.split('\n'):
            # textwrap.wrap eats up empty strings, so we do a specific handling for those cases
            if i_line == '':
                result.append(p_first_indent)  # String is empty, we just print the indent
                continue

            result += textwrap.wrap(
                i_line,
                page_width,
                initial_indent=p_first_indent,
                subsequent_indent=p_next_indent
            )

        return result


    def _DoPrint(self, p_args, p_first_indent, p_next_indent, color=None, page_width=None):
        '''
        Prints a text (p_args) observing the page_width, indentations and color.
        '''
        text = ' '.join(map(unicode, p_args))

        for i_line in self._WrapLines(text, p_first_indent, p_next_indent, page_width=page_width):
            self.ColorWrite(color, '%s\n' % i_line)


    # Handlers -------------------------------------------------------------------------------------
    def _HandleIndent(self, p_kargs):
        '''
        Handles the 'indent' and 'mark' keywords of the given 'kargs'. Returns the same result
        as "_IndentStrings".

        * The default indent is defined by the internal indentation level (see Indent, Dedent)
        * The mark is used by "Items" methods, by default is an empty string.
        '''
        indent = p_kargs.get('indent')
        mark = p_kargs.get('mark', '')
        return self._IndentStrings(indent, mark)


    def _HandleMargin(self, p_kargs, p_key):
        margin = p_kargs.get(p_key, 0)
        while margin > 0:
            self.write('\n')
            margin -= 1


    def _HandleTopMargin(self, p_kargs):
        self._HandleMargin(p_kargs, 'top_margin')


    def _HandleBottomMargin(self, p_kargs):
        self._HandleMargin(p_kargs, 'bottom_margin')


    def _HandleColor(self, p_kargs, p_key):
        return p_kargs.get(p_key, None)


    # High-level writing methods -------------------------------------------------------------------
    def LINE(self, p_char, **kargs):
        '''
        Draw a line, using the given character, obeserving indentation and page width.
        '''
        if not self._HandleVerbose(kargs):
            return

        if not self._HandleKeywords(kargs):
            return

        if p_char is None:
            return

        indent = self._HandleIndent(kargs)[0]

        if self.WRAP_LINES:
            size = self.c_page_width - len(indent)
        else:
            size = self.DEFAULT_PAGE_WIDTH

        self._HandleTopMargin(kargs)
        self.ColorWrite(kargs.get('color'), '%s%s\n' % (indent, p_char * size))
        self._HandleBottomMargin(kargs)


    def P(self, *args, **kargs):
        '''
        Print a paragram, observing the indentation, verbose level and text width.

        Format:
        <MESSAGE>

        Keyword Arguments:
            indent=None
            verbose=1
        '''
        if not self._HandleVerbose(kargs):
            return IndentContextManager(self)

        if not self._HandleKeywords(kargs):
            return IndentContextManager(self)

        if args:
            first_indent, next_indent = self._HandleIndent(kargs)
            self._HandleTopMargin(kargs)
            self._DoPrint(args, first_indent, next_indent, kargs.get('color'), kargs.get('page_width'))
            self._HandleBottomMargin(kargs)
        else:
            self.write('\n')

        return IndentContextManager(self)



    def I(self, *args, **kargs):
        '''
        Print an item, observing the indentation, verbose level and text width.

        - Can spread to multiple lines, all aligned with the first line text.

        Format:
        - <MESSAGE>

        Keyword Arguments:
            indent=None
            verbose=1
            mark='- '
        '''
        if not self._HandleVerbose(kargs):
            return IndentContextManager(self)

        if not self._HandleKeywords(kargs):
            return IndentContextManager(self)

        kargs.setdefault('mark', '- ')
        first_indent, next_indent = self._HandleIndent(kargs)

        self._HandleTopMargin(kargs)
        self._DoPrint(args, first_indent, next_indent, kargs.get('color'), kargs.get('page_width'))
        self._HandleBottomMargin(kargs)

        return IndentContextManager(self)


    def DT(self, *args, **kargs):
        '''
        Prints a definition title, observing the indentation, verbose level and text width.

        Format:
        \n
        <MESSAGE>:

        Keyword Arguments:
            indent=None
            verbose=1
            mark=''
        '''
        if not args:
            raise RuntimeError('No arguments to DT')

        if not self._HandleVerbose(kargs):
            return

        if not self._HandleKeywords(kargs):
            return

        first_indent, next_indent = self._HandleIndent(kargs)
        message = [' '.join(args) + ':']

        self._HandleTopMargin(kargs)
        self._DoPrint(message, first_indent, next_indent, kargs.get('color'), kargs.get('page_width'))
        self._HandleBottomMargin(kargs)

        return IndentContextManager(self)


    def DD(self, p_caption, p_text, **kargs):

        if not self._HandleVerbose(kargs):
            return

        if not self._HandleKeywords(kargs):
            return

        caption_kargs = {}
        caption_kargs.update(kargs)
        caption_kargs['color'] = kargs.get('caption_color')

        self.DT(p_caption, **caption_kargs)

        kargs['top_margin'] = 0
        kargs['indent'] = kargs.get('indent', 0) + 1
        self.P(p_text, **kargs)

        self._HandleBottomMargin(kargs)


    def PROCESSING(self, state, text=None, **kargs):

        def IsEnd():
            'Returns whether the call is a processing ending call.'
            return text is None


        def DoPrintState(indent, state, carriage_return):
            if carriage_return:
                self.WriteCarriageReturn()
            color = self._HandleColor(kargs, 'state_color')
            self.ColorWrite(color, indent + state)


        def DoPrintText(first_indent, indent, text):
            color = self._HandleColor(kargs, 'text_color')
            lines = self._WrapLines(text, '', '', page_width=self.c_page_width - len(indent))
            if len(lines) == 1:
                self.ColorWrite(color, first_indent + lines[0])
            else:
                for i, i_line in enumerate(lines):
                    if i == 0:
                        i_line = first_indent + i_line
                    else:
                        i_line = indent + i_line
                    self.ColorWrite(color, i_line + '\n')


        def PrintState(indent, state):
            if self.flat_output:
                DoPrintState('', state, False)
            else:
                DoPrintState(indent, state, True)


        def PrintText(indent, text):
            if self.flat_output:
                DoPrintText(first_indent, indent, text)
                DoPrintState('', state, False)
            else:
                DoPrintState(first_indent, state, False)
                DoPrintText('', indent, text)

        if not self._HandleVerbose(kargs):
            return

        if not self._HandleKeywords(kargs):
            return

        if self._processing_count > 0:
            processing_indent = self._processing_count
            if IsEnd():
                processing_indent -= 1
            kargs['indent'] = processing_indent
        else:
            processing_indent = 0

        first_indent, next_indent = self._HandleIndent(kargs)

        if IsEnd():
            self._processing_count -= 1
            PrintState(first_indent, state)
            self.write('\n')
        else:
            self._processing_count += 1
            if self._processing_indent < processing_indent:
                self.write('\n')
            PrintText(next_indent + ' ' * len(state), text)
            self._processing_indent = processing_indent


    def ERROR(self, *args, **kargs):
        kargs.setdefault('line_char', '*')
        kargs.setdefault('line_color', 'RED')
        self.HEADER('ERROR\n  ' + '\n  '.join(args), **kargs)


    def HEADER(self, *args, **kargs):
        if not self._HandleVerbose(kargs):
            return

        if not self._HandleKeywords(kargs):
            return

        self._HandleTopMargin(kargs)

        indent = kargs.get('indent', 0)
        line_char = kargs.get('line_char', '-')
        line_color = kargs.get('line_color')
        text_color = kargs.get('color')

        self.LINE(line_char, color=line_color, indent=indent)
        self.P(' '.join(args), color=text_color, indent=indent)
        self.LINE(line_char, color=line_color, indent=indent)
        self._HandleBottomMargin(kargs)


    def DETAILED_EXCEPTION(self, **kargs):
        from ben10.foundation.print_detailed_traceback import PrintDetailedTraceback
        PrintDetailedTraceback(stream=self, max_line_width=self.c_page_width)


    def EXCEPTION(self, **kargs):
        '''
        Prints-out the exception being handling.

        Keywords params:
            top_margin:
            bottom_margin:
            indent:
            verbose:
                IGNORED
            line_color:
                Determines the color of the lines. (default None)
            line_char:
                Determins the character used to draw the 'main' lines (default '*')
                - If None, does not print the lines.
            track_back:
                A boolean indicating if we should print the traceback info (default True)
        '''
        def TrackBackFrames(p_track_back):
            '''
                Returns a list of dict, containing the trackback information.
            '''
            import traceback
            table = traceback.extract_tb(p_track_back)
            result = []
            for i_entry in table:
                result.append(
                    dict(
                        zip(
                            ('filename', 'line_no', 'function', 'text'),
                             i_entry
                        )
                    )
                )
            return result

        if not self._HandleVerbose(kargs):
            return

        try:
            klass, message, trace_back = sys.exc_info()

            if klass is None:
                return

            self._HandleTopMargin(kargs)

            indent = kargs.get('indent', 0)
            line_color = kargs.get('line_color')
            line_char = kargs.get('line_char', '*')

            # 001) Exception class name and message
            self.LINE(line_char, indent=indent, color=line_color)
            self.P(klass.__name__ + ':', indent=indent)
            self.P(message, indent=indent + 1)

            # 002) Traceback
            extended_message = kargs.get('extended_message')
            if extended_message:
                self.LINE('-', indent=indent, color=line_color)
                self.P(
                    extended_message,
                    indent=indent)

            # 002) Traceback
            if kargs.get('track_back', True):
                self.LINE('-', indent=indent, color=line_color)
                for i_frame in TrackBackFrames(trace_back):
                    self.DD(
                        '%(filename)s:%(line_no)s' % i_frame,
                        '%(text)s' % i_frame,
                        indent=indent)
            self.LINE(line_char, indent=indent, color=line_color)

            self._HandleBottomMargin(kargs)

        except Exception, e:
            print '*' * 80
            print 'Major failure: Error while handling an exception'
            print '-' * 80
            print e
            print '*' * 80
            raise


    def TABLE(self, widths, labels, values):
        '''
        Print a table of values, correctly indented.

        :param  widths:
            A list of width, one for each column
        @type labels:
            [int]

        :param  labels:
            A list of labels, one for each column
            If None, does not print labels
        @type labels:
            [unicode]

        :param  values:
            A list of values, each entry must have a value for each column.
        @type values:
            [[unicode]]
        '''

        def Print(message, color=None):
            self.P(message, color=color, indent=1)

        # Create format
        format = ''
        for i_width in widths:
            format += '%%%ss' % i_width

        if labels is not None:
            CheckType(labels, (list, tuple))
            Print(format % tuple(labels), 'WHITE')

        for i_value in values:
            CheckType(i_value, (list, tuple))
            Print(format % tuple(i_value))



#===================================================================================================
# TextOutputWrapper
#===================================================================================================
class TextOutputWrapper(object):

    def __init__(self, text_output, keywords):
        self.text_output = text_output
        self.keywords = keywords


    def Indent(self, *args, **kargs):
        kargs.setdefault('keywords', self.keywords)
        return self.text_output.Indent(*args, **kargs)


    def Dedent(self, *args, **kargs):
        kargs.setdefault('keywords', self.keywords)
        return self.text_output.Dedent(*args, **kargs)


    def I(self, *args, **kargs):
        kargs.setdefault('keywords', self.keywords)
        id_tag = '[%s]' % ','.join(self.keywords)
        args = list(args)
        args.append(id_tag)
        return self.text_output.I(*args, **kargs)


    def P(self, *args, **kargs):
        kargs.setdefault('keywords', self.keywords)
        args = list(args)
        args.append('  [%s]' % ','.join(self.keywords))
        return self.text_output.P(*args, **kargs)

