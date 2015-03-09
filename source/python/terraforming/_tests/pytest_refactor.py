from __future__ import unicode_literals
'''
IMPORTANT:
    Avoid importing lib2to3 on module level becase this makes multi-processing test execution fail.
    This is because lib2to3 have a mechanism of generating a syntax file (pickle) in module level
    that crashes when executing in parallel.
'''
from ben10.filesystem import CreateFile, EOL_STYLE_NONE, EOL_STYLE_UNIX
from ben10.foundation.reraise import Reraise
from ben10.foundation.string import Dedent
from terraforming.refactor import TerraForming
import difflib
import inspect
import pytest
import sys


#===================================================================================================
# Test
#===================================================================================================
@pytest.mark.xfail(reason='EDEN-1067')
class Test(object):

    def testFixAll(self, embed_data):
        terra = TerraForming()

        source = Dedent(
            r'''
                alpha
                bravo\s\t\s
                charlie
                \tdelta
                echo\r
                foxtrot
                golf #Comment
                hotel
            '''.replace('\s', ' ').replace(r'\t', '\t').replace(r'\r', '\r').replace(r'\n', '\n')
        )
        CreateFile(embed_data['testFixAll.py_'], source, eol_style=EOL_STYLE_NONE)

        expected = Dedent(
            r'''
                alpha
                bravo
                charlie
                \s\s\s\sdelta
                echo
                foxtrot
                golf #Comment
                hotel
            '''.replace(r'\s', ' ')
        )
        CreateFile(embed_data['testFixAll.expected.py_'], expected, eol_style=EOL_STYLE_UNIX)

        terra.FixAll(embed_data['testFixAll.py_'])

        embed_data.AssertEqualFiles(
            'testFixAll.py_',
            'testFixAll.expected.py_'
        )


    def testFixDivisionLines(self, embed_data):
        terra = TerraForming()
        terra.FixDivisionLines(embed_data['testFixDivisionLines.py_'])

        embed_data.AssertEqualFiles(
            'testFixDivisionLines.py_',
            'testFixDivisionLines.expected.py_'
        )


    def testRightTrimSpaces(self, embed_data):
        terra = TerraForming()

        CreateFile(
            embed_data['testRightTrimSpaces.py_'],
            'alpha\nbravo  \ncharlie    \n'
        )
        CreateFile(
            embed_data['testRightTrimSpaces.expected.py_'],
            'alpha\nbravo\ncharlie\n'
        )

        terra.RightTrimSpaces(embed_data['testRightTrimSpaces.py_'])

        embed_data.AssertEqualFiles(
            'testRightTrimSpaces.py_',
            'testRightTrimSpaces.expected.py_'
        )


    def testFixDivisionLinesImpl(self):
        '''
        #=======================
        # Double
        # ==================
        #------
        # Single
        # -------------------------
        #====================== Header
        # -- Header
        a = "#======================"
        ---
        #=========
        # Double
        #=========
        #---------
        # Single
        #---------
        #====================== Header
        # -- Header
        a = "#======================"
        '''
        terra = TerraForming()

        def Doit(lines):
            return terra._FixDivisionLinesImpl(lines, 10)

        self._TestLines(inspect.getdoc(self.testFixDivisionLinesImpl), Doit)


    def testConvertToPytest(self, embed_data):
        terra = TerraForming()
        terra.ConvertToPytest(embed_data['testConvertToPytest.py_'])

        embed_data.AssertEqualFiles(
            'testConvertToPytest.py_',
            'testConvertToPytest.expected.py_'
        )


    def testConvertToPytestImpl(self):
        '''
        class Test(unittest.TestCase):

            def testAlpha(self):
                print "BEFORE"
                self.assertEqual(x, 10)
                print "AFTER"

            def testBravo(self):
                assert True
        ---
        class Test:

            def testAlpha(self):
                print "BEFORE"
                assert x == 10
                print "AFTER"

            def testBravo(self):
                assert True
        '''
        terra = TerraForming()

        def Doit(lines):
            source_code = '\n'.join(lines) + '\n'
            output = terra._ConvertToPytestImpl(source_code)
            return output.split('\n')[:-1]

        self._TestLines(inspect.getdoc(self.testConvertToPytestImpl), Doit)


    # TestLines ====================================================================================

    def _Fail(self, obtained, expected):
        diff = [i for i in difflib.context_diff(obtained, expected)]
        diff = '\n'.join(diff)
        raise AssertionError(diff)

    def _TestLines(self, doc, processor):
        lines = doc.split('\n')
        input_ = []
        expected = []
        stage = 'input'
        for i_line in lines:
            if i_line.strip() == '---':
                stage = 'output'
                continue
            if i_line.strip() == '===':
                try:
                    obtained = processor(input_)
                except Exception as exception:
                    Reraise(exception, 'While processing lines::\n  %s\n' % '\n  '.join(input_))
                if obtained != expected:
                    self._Fail(obtained, expected)
                input_ = []
                expected = []
                stage = 'input'
                continue

            if stage == 'input':
                input_.append(i_line)
            else:
                expected.append(i_line)

        if input_:
            obtained = processor(input_)
            if obtained != expected:
                self._Fail(obtained, expected)


    def _TestTestLines(self):

        def Doit(lines):
            return ['(%s)' % i for i in lines]

        self._TestLines('===\nalpha\n---\n(alpha)', Doit)

        self._TestLines('===\nalpha\n\n\n---\n(alpha)\n()\n()', Doit)

        with pytest.raises(AssertionError):
            self._TestLines('===\nalpha\n---\nERROR\n===\nalpha\n---\n(alpha)', Doit)

        with pytest.raises(AssertionError):
            self._TestLines('===\nalpha\n---\nERROR', Doit)



#===================================================================================================
# Entry Point
#===================================================================================================
if __name__ == '__main__':
    # Executes with specific coverage.
    retcode = pytest.main(['--cov-report=term-missing', '--cov=aasimar.refactor', __file__])
    sys.exit(retcode)
