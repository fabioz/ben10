from __future__ import unicode_literals
from ben10.foundation.string import Dedent
from io import StringIO
from txtout.txtout import TextOutput
import textwrap



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testIndentContextManager(self):
        stream = StringIO()
        output = TextOutput(stream)

        output.P()  # Empty line
        output.P('Simple line')
        output.P('Indented line', indent=1)

        # We simulate the with_statement, since coilib50 cannot depend on it
        with_stmt = output.P('Now using with!', top_margin=1)
        with_stmt.__enter__()
        output.I('Item inside context')
        with_stmt.__exit__()

        output.I('Item outside context', top_margin=1)

        expected_output = Dedent(
            '''

                Simple line
                    Indented line

                Now using with!
                    - Item inside context

                - Item outside context

            '''
        )
        assert stream.getvalue() == expected_output



    def testPageWidthParameter(self):
        oss = TextOutput()
        oss.c_page_width = 80
        oss.RegisterKeyword('yes', 'This will be shown')
        oss.RegisterKeyword('no', 'This will not be shown')
        oss.SetKeyword('yes', True)

        stream = StringIO()
        oss.SetOutputStream(stream)
        try:
            raise RuntimeError('This is an exception')
        except Exception:
            oss.EXCEPTION()
        assert stream.getvalue() == Dedent(
            '''
            ********************************************************************************
            RuntimeError:
                This is an exception
            --------------------------------------------------------------------------------
            %s
                raise RuntimeError('This is an exception')
            ********************************************************************************

            '''
        # Hard-coded 57 points to the "raise RuntimeError('This is an exception')" line in this file
        ) % '\n'.join(textwrap.wrap(__file__ + ':57:', 80))

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.P('alpha bravo charlie delta echo foxtrot')
        oss.P('No show', verbose=4)
        oss.P('No show', keywords=('no',))
        assert stream.getvalue() == Dedent(
            '''
            alpha bravo charlie delta echo foxtrot

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.P('alpha bravo charlie delta echo foxtrot', page_width=12)
        assert stream.getvalue() == Dedent(
            '''
            alpha bravo
            charlie
            delta echo
            foxtrot

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.I('alpha')
        oss.I('bravo')
        oss.I('charlie')
        oss.I('No show', verbose=4)
        oss.I('No show', keywords=('no',))
        assert stream.getvalue() == Dedent(
            '''
            - alpha
            - bravo
            - charlie

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.TABLE([7, 8, 9], ['alpha', 'bravo', 'charlie'], [[1, 2, 3], [4, 5, 6]])
        assert 'x\n' + stream.getvalue() == Dedent(
            '''
            x
                  alpha   bravo  charlie
                      1       2        3
                      4       5        6

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.HEADER("This is header")
        oss.HEADER('No show', verbose=4)
        oss.HEADER('No show', keywords=('no',))
        assert stream.getvalue() == Dedent(
            '''
            --------------------------------------------------------------------------------
            This is header
            --------------------------------------------------------------------------------

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.ERROR('Oops!')
        oss.ERROR('Oops!', verbose=4)
        oss.ERROR('Oops!', keywords=('no',))
        assert stream.getvalue() == Dedent(
            '''
            ********************************************************************************
            ERROR
              Oops!
            ********************************************************************************

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.flat_output = False
        oss.PROCESSING('...', 'Doing')
        oss.PROCESSING('Done')
        oss.PROCESSING('...', 'Multi\nline\ndoing')
        oss.PROCESSING('Done')
        oss.flat_output = True
        oss.PROCESSING('...', 'Doing')
        oss.PROCESSING('Done')
        oss.PROCESSING('No show', verbose=4)
        oss.PROCESSING('No show', keywords=('no',))
        assert stream.getvalue() == Dedent(
            '''
            ...Doing\\rDone
            ...Multi
               line
               doing
            \\rDone
            Doing...Done

            '''
        )

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.DT('caption', 'value')
        oss.DT('No show', verbose=4)
        oss.DT('No show', keywords=('no',))
        assert (stream.getvalue() == 'caption value:\n')

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.DD('caption', 'value')
        oss.DD('No show', 'No show', verbose=4)
        oss.DD('No show', 'No show', keywords=('no',))
        assert (stream.getvalue() == 'caption:\n    value\n')

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.LINE('-')
        oss.LINE('X', verbose=4)
        oss.LINE('X', keywords=('no',))
        assert (stream.getvalue() == '-' * 80 + '\n')

        stream = StringIO()
        oss.SetOutputStream(stream)
        oss.Indent()
        oss.Indent()
        oss.P('alpha')
        oss.Dedent()
        oss.P('bravo')
        oss.ResetIndentation()
        oss.P('charlie')
        assert (stream.getvalue() == '        alpha\n    bravo\ncharlie\n')


    def testPrintEmptyString(self):
        stream = StringIO()

        oss = TextOutput(stream)
        oss.P('')
        expected_output = '\n'
        assert stream.getvalue() == expected_output


    def testPrintEmptyStringIndent(self):
        stream = StringIO()

        oss = TextOutput(stream)
        oss.P('', indent=1)
        expected_output = '    \n'
        assert stream.getvalue() == expected_output


    def testDefaultVerbose(self):
        stream = StringIO()
        oss = TextOutput(stream, verbose_level=1)
        oss.P('Alpha')
        oss.P('Bravo')
        assert stream.getvalue() == 'Alpha\nBravo\n'

        stream = StringIO()
        oss = TextOutput(stream, verbose_level=1)
        oss.default_verbose = 2
        oss.P('Alpha')
        oss.P('Bravo')
        assert stream.getvalue() == ''
