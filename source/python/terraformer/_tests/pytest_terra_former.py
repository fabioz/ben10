from lib2to3.pgen2.parse import ParseError
from ben10.foundation.pushpop import PushPop
from ben10.foundation.string import Dedent
from terraformer import ImportBlock, TerraFormer
import pytest



def testAstVisitor():
    from terraformer._astvisitor import ASTVisitor

    class LogVisitor(ASTVisitor):

        def __init__(self):
            ASTVisitor.__init__(self)
            self.log = []

        def visit_start(self, tree):
            self.log.append('visit_start')

        def visit_end(self, tree):
            self.log.append('visit_end')

        def visit_class(self, name, bases, body):
            self.log.append('visit_class: %s' % name)
            ASTVisitor.visit_class(self, name, bases, body)

        def visit_function(self, name, args, body):
            self.log.append('visit_function: %s' % name)
            ASTVisitor.visit_function(self, name, args, body)

        def visit_import(self, names, import_from, body):
            self.log.append('visit_import: %s' % ','.join(map(str, names)))

    code = TerraFormer._Parse(Dedent(
        '''
        from alpha import Alpha

        class Zulu(Alpha):

            def __init__(self, name):
                self.name = name
        '''
    ))

    visitor = LogVisitor()
    visitor.visit(code)

    assert visitor.log == [
        'visit_start',
        'visit_import: Alpha',
        'visit_class: Zulu',
        'visit_function: __init__',
        'visit_end',
    ]


def testImportBlockZero(monkeypatch, embed_data):

    def TestIt(input, expected, import_blocks):
        input = Dedent(input)
        expected = Dedent(expected) + '\n'
        terra_former = TerraFormer(input)
        assert map(str, terra_former.import_blocks) == import_blocks

        terra_former.AddImportSymbol('__future__.unicode_literals')
        terra_former.ReorganizeImports()

        # Make sure that creating a TerraFormer won't make any changes to the AST
        obtained = str(terra_former.code)
        assert obtained == expected

    TestIt(
        '''
        from __future__ import unicode_literals
        ''',
        '''
        from __future__ import unicode_literals
        ''',
        [
            '<ImportBlock #0 (1, 0): __future__.unicode_literals>',
        ]
    )

    TestIt(
        '''

        ''',
        '''
        from __future__ import unicode_literals
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
        ]
    )

    TestIt(
        '''
        def Function():
            pass
        ''',
        '''
        from __future__ import unicode_literals
        def Function():
            pass
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
        ]
    )

    TestIt(
        '''
        """
        Docs
        """

        def Function():
            pass
        ''',
        '''
        from __future__ import unicode_literals
        """
        Docs
        """

        def Function():
            pass
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
        ]
    )

    TestIt(
        '''
        # Comments

        def Function():
            pass
        ''',
        '''
        from __future__ import unicode_literals
        # Comments

        def Function():
            pass
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
        ]
    )

    TestIt(
        '''
        #===================================================================================================
        # PrintLine
        #===================================================================================================
        def PrintLine(s):
            """
            Docs
            """
            print s
        ''',
        '''
        from __future__ import unicode_literals
        #===================================================================================================
        # PrintLine
        #===================================================================================================
        def PrintLine(s):
            """
            Docs
            """
            print s
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
        ]
    )

    TestIt(
        '''
        def Function(s):
            import alpha
        ''',
        '''
        from __future__ import unicode_literals
        def Function(s):
            import alpha
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
            '<ImportBlock #1 (2, 4): alpha>',
        ]
    )

    TestIt(
        '''
        # [[[cog
        # from coilib50.cpp.import_bindings import RepublishCppSymbols
        # cog.out(RepublishCppSymbols(
        #     'coilib50._coilib50_cpp_module',
        #     ['RedirectOutput'],
        # ))
        # ]]]
        from coilib50 import _coilib50_cpp_module
        RedirectOutput = _coilib50_cpp_module.RedirectOutput
        # [[[end]]] (checksum: e19f682169067c207e055a3a169feba7)
        ''',
        '''
        from __future__ import unicode_literals
        # [[[cog
        # from coilib50.cpp.import_bindings import RepublishCppSymbols
        # cog.out(RepublishCppSymbols(
        #     'coilib50._coilib50_cpp_module',
        #     ['RedirectOutput'],
        # ))
        # ]]]
        from coilib50 import _coilib50_cpp_module
        RedirectOutput = _coilib50_cpp_module.RedirectOutput
        # [[[end]]] (checksum: e19f682169067c207e055a3a169feba7)
        ''',
        [
            '<ImportBlock #0 (1, 0): >',
            '<ImportBlock #1 (8, 0): coilib50._coilib50_cpp_module>',
        ]
    )


def testTerraFormer(monkeypatch, embed_data):

    terra_former = TerraFormer(
        source=Dedent(
            '''
            import bravo
            import charlie
            from alpha import A1
            from bravo import (B1, B2, B3)
            # Delta Comment
            from delta.charlie.delta import DeltaClass

            from zulu import (Z1,
                Z2,  # Comment on Z2
                Z3
            )

            from yankee import Y1, \
                Y2, \
                Y3

            def Func():
                """
                Func is king.
                """
                import india_one
                var_alpha = alpha.AlphaClass()

                if True:
                    import india_in

                import india_out

            var_bravo = bravo.BravoClass()
            '''
        )
    )

    assert set([i.symbol for i in terra_former.symbols]) == {
        'alpha.A1',
        'bravo',
        'bravo.B1',
        'bravo.B2',
        'bravo.B3',
        'charlie',
        'delta.charlie.delta.DeltaClass',
        'india_one',
        'india_in',
        'india_out',
        'yankee.Y1',
        'yankee.Y2',
        'yankee.Y3',
        'zulu.Z1',
        'zulu.Z2',
        'zulu.Z3',
    }

    assert map(str, terra_former.import_blocks) == [
        '<ImportBlock #0 (1, 0): alpha.A1 bravo bravo.B1 bravo.B2 bravo.B3 charlie>',
        '<ImportBlock #1 (6, 0): delta.charlie.delta.DeltaClass yankee.Y1 yankee.Y2 yankee.Y3 zulu.Z1 zulu.Z2 zulu.Z3>',
        '<ImportBlock #2 (19, 4): india_one>',
        '<ImportBlock #3 (23, 8): india_in>',
        '<ImportBlock #4 (25, 4): india_out>',
    ]

    changed, output = terra_former.ReorganizeImports()
    print output

    assert output == Dedent(
        '''
            from alpha import A1
            from bravo import B1, B2, B3
            import bravo
            import charlie
            # Delta Comment
            from delta.charlie.delta import DeltaClass
            from yankee import Y1, Y2, Y3
            from zulu import Z1, Z2, Z3

            def Func():
                """
                Func is king.
                """
                import india_one
                var_alpha = alpha.AlphaClass()

                if True:
                    import india_in

                import india_out

            var_bravo = bravo.BravoClass()

        '''
    )


def testReorganizeImports(embed_data, line_tester):
    from ben10.filesystem import GetFileContents

    def Doit(lines):
        source = ''.join([i + '\n' for i in lines])
        terra = TerraFormer(source=source)
        changed_, output = terra.ReorganizeImports(
            refactor={
                'coilib50.basic.implements': 'etk11.foundation.interface',
                'coilib50.basic.inter': 'etk11.foundation.interface',
                'before_refactor_alpha.Alpha': 'after_refactor.Alpha',
                'before_refactor_bravo.Bravo': 'after_refactor.Bravo',
            }
        )
        return output.splitlines()

    line_tester.TestLines(
        GetFileContents(embed_data['reorganize_imports.txt']),
        Doit,
    )


def testQuotedBlock():
    assert TerraFormer._QuotedBlock(
        'alpha\nbravo\ncharlie\n'
    ) == '> alpha\n> bravo\n> charlie\n'


def testParse():
    with pytest.raises(ParseError):
        TerraFormer._Parse('class Class:\n')


def testLocalImports(monkeypatch, embed_data):
    monkeypatch.setattr(ImportBlock, 'PYTHON_EXT', '.py_')

    def TestIt(filename):
        full_filename=embed_data['testLocalImports/alpha/%s.py_' % filename]
        terra = TerraFormer(filename=full_filename)
        terra.Save()
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
        TestIt('romeo')
        TestIt('quilo')

        # Test MAX_FILE_SIZE
        with pytest.raises(RuntimeError):
            monkeypatch.setattr(TerraFormer, 'MAX_FILE_SIZE', 5)
            TestIt('quilo')



#===================================================================================================
# Fixture line_tester
#===================================================================================================
class LineTester(object):

    def _Fail(self, obtained, expected):
        import difflib

        diff = [i for i in difflib.context_diff(obtained, expected)]
        diff = '\n'.join(diff)
        raise AssertionError(diff)


    def TestLines(self, doc, processor):
        from ben10.foundation.reraise import Reraise

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


@pytest.fixture
def line_tester():
    return LineTester()


def testLineTester(line_tester):

    def Doit(lines):
        return ['(%s)' % i for i in lines]

    def RaiseException(lines):
        raise TypeError()

    line_tester.TestLines('===\nalpha\n---\n(alpha)', Doit)

    line_tester.TestLines('===\nalpha\n\n\n---\n(alpha)\n()\n()', Doit)

    with pytest.raises(AssertionError):
        line_tester.TestLines('===\nalpha\n---\nERROR\n===\nalpha\n---\n(alpha)', Doit)

    with pytest.raises(AssertionError):
        line_tester.TestLines('===\nalpha\n---\nERROR', Doit)

    with pytest.raises(Exception) as excinfo:
        line_tester.TestLines('===\nalpha\n\n\n---\n(alpha)\n()\n()', RaiseException)
    assert "While processing lines::" in str(excinfo.value)
