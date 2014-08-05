'''
IMPORTANT:
    Avoid importing lib2to3 on module level becase this makes multi-processing test execution fail.
    This is because lib2to3 have a mechanism of generating a syntax file (pickle) in module level
    that crashes when executing in parallel.
'''
from ben10.filesystem import CreateFile, EOL_STYLE_NONE, EOL_STYLE_UNIX, GetFileContents
from ben10.foundation.pushpop import PushPop
from ben10.foundation.reraise import Reraise
from ben10.foundation.string import Dedent
from terraforming.refactor import TerraForming
from terraforming.refactor_imports import ReorganizeImports
import difflib
import inspect
import pytest
import sys


#===================================================================================================
# Test
#===================================================================================================
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


    def testReorganizeImports(self, embed_data):
        terra = TerraForming()
        terra.ReorganizeImports(embed_data['testReorganizeImports.py_'])

        embed_data.AssertEqualFiles(
            'testReorganizeImports.py_',
            'testReorganizeImports.expected.py_'
        )


    def testReorganizeImportsImpl(self, embed_data):
        '''
        Unsuported cases:
            * Import with dots:
                import .alpha
                ---
                import .alpha
            * Different imports that are re-factored to the same package don't get merged
                # With refactoring
                #  alpha.Alpha -> zulu.Alpha
                #  bravo.Bravo -> zulu.Bravo
                from alpha import Alpha
                from bravo import Bravo
                ---
                # With refactoring
                #  alpha.Alpha -> zulu.Alpha
                #  bravo.Bravo -> zulu.Bravo
                from zulu import Alpha, Bravo
            * Import, then comment, then import
                import alpha

                # Comment
                import bravo
                bravo.Bravo()
                ---
                import alpha

                # Comment
                import bravo
                bravo.Bravo()
        '''
        terra = TerraForming()

        def Doit(lines):
            source_code = ''.join([i + '\n' for i in lines])
            changed, output = ReorganizeImports(
                filename=None,
                source_code=source_code,
                refactor={
                    'coilib50.basic.implements': 'etk11.foundation.interface',
                    'coilib50.basic.inter': 'etk11.foundation.interface',
                }
            )
            return output.splitlines()

        self._TestLines(
            GetFileContents(embed_data['reorganize_imports.txt']),
            Doit,
        )


    def testLocalImports(self, monkeypatch, embed_data):
        from terraforming import refactor_imports

        monkeypatch.setattr(refactor_imports, 'PYTHON_EXT', '.py_')
        terra = TerraForming()

        def TestIt(filename):
            terra.ReorganizeImports(
                embed_data['testLocalImports/alpha/%s.py_' % filename],
                python_path=embed_data['testLocalImports']
            )
            embed_data.AssertEqualFiles(
                embed_data['testLocalImports/alpha/%s.py_' % filename],
                embed_data['testLocalImports/alpha.expected/%s.py_' % filename]
            )

        import sys
        sys_path = [embed_data.GetDataFilename('testLocalImports', absolute=True)] + sys.path[:]
        with PushPop(sys, 'path', sys_path):
            TestIt('__init__')
            TestIt('_yankee')
            TestIt('_alpha_core')
            TestIt('simentar_test_base')



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
    retcode = pytest.main(['--cov-report=term-missing', '--cov=aasimar10.refactor', __file__])
    sys.exit(retcode)
