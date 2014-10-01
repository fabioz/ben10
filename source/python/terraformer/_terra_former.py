from ben10.filesystem import GetFileContents
from ben10.foundation.memoize import Memoize



class FileTooBigError(RuntimeError):
    '''
    Exception raised when a big file is detected.
    We raise this exception before asking lib2to3 to handle it because if we let this to lib2to3 we
    end getting a infinite loop.
    '''



#===================================================================================================
# TerraFormer
#===================================================================================================
class TerraFormer(object):
    '''
    Python code refactoring class.

    # Reorganize Imports:

    ### Unsupported cases:
    * Import with dots:
        import .alpha
        ---
        import .alpha

    '''

    MAX_FILE_SIZE = 500000

    def __init__(self, source=None, filename=None):
        if source is None:
            source = GetFileContents(filename)

        file_size = len(source)
        if file_size > self.MAX_FILE_SIZE:
            # Some big files make the Parse algorithm get stuck.
            raise FileTooBigError('File %s too big: %d' % (filename, file_size))

        self.filename = filename
        self.source = source
        self.symbols = set()
        self.names = set()
        self.import_blocks = []

        self.code = self._Parse(self.source)

        from ._visitor import ASTVisitor
        visitor = ASTVisitor()
        visitor.Visit(self.code)
        self.symbols, self.import_blocks = visitor.symbols, visitor.import_blocks


    @classmethod
    @Memoize(maxsize=1000)
    def Factory(self, filename, source=None):
        return TerraFormer(source=source, filename=filename)


    @classmethod
    def _QuotedBlock(cls, text):
        return ''.join(["> %s" % line for line in text.splitlines(True)])


    @classmethod
    def _Parse(cls, code):
        '''
        Parses the given code string returning its lib2to3 AST tree.
        '''
        # Prioritary import.
        from . import _lib2to3  # @NotUsedImport

        # Other imports
        from ben10.foundation.reraise import Reraise
        from lib2to3 import pygram, pytree
        from lib2to3.pgen2 import driver
        from lib2to3.pgen2.parse import ParseError
        from lib2to3.pygram import python_symbols
        from lib2to3.pytree import Leaf, Node
        from lib2to3.refactor import _detect_future_features

        if isinstance(code, str):
            code = code.decode('latin1')

        added_newline = False
        if code and not code.endswith("\n"):
            code += "\n"
            added_newline = True

        # Selects the appropriate grammar depending on the usage of "print_function" future feature.
        future_features = _detect_future_features(code)
        if 'print_function' in future_features:
            grammar = pygram.python_grammar_no_print_statement
        else:
            grammar = pygram.python_grammar

        try:
            drv = driver.Driver(grammar, pytree.convert)
            result = drv.parse_string(code, True)
        except ParseError as e:
            Reraise(e, "Had problems parsing:\n%s\n" % cls._QuotedBlock(code))

        # Always return a Node, not a Leaf.
        if isinstance(result, Leaf):
            result = Node(python_symbols.file_input, [result])

        result.added_newline = added_newline

        return result


    @classmethod
    def WalkLeafs(cls, node):
        from lib2to3.pytree import Leaf

        if isinstance(node, Leaf):
            yield node
        else:
            for i_child in node.children:
                for j_leaf in cls.WalkLeafs(i_child):
                    yield j_leaf


    def GetSymbolFromToken(self, token):
        tokens = {i.GetToken() : i for i in self.symbols}
        return tokens.get(token)


    def GetModuleName(self):
        '''
        Returns the python module name.
        Ex.
            alpha10.parent.working.py -> alpha10.parent

        IMPORTANT: For this to work the package must be importable in the current PYTHONPATH.

        :return str:
            The module name in the format:
                xxx.yyy.zzz
        '''
        from ben10.module_finder import ModuleFinder

        module_finder = ModuleFinder()
        try:
            return module_finder.ModuleName(self.filename).rsplit('.', 1)[0]
        except RuntimeError:
            return None


    def ReorganizeImports(
            self,
            refactor={},
            page_width=100
        ):
        '''
        Reorganizes all imports-blocks.

        :param dict refactor:
            A dictionary mapping old symbols to new symbols.

        :param int page_width:
            The page-width to format the import statements.

        :return boolean, str:
            Returns True if any changes were made.
            Returns the reorganized source code.
        '''
        for i_import_block in self.import_blocks:
            i_import_block.Reorganize(page_width, refactor, self.filename)

        output = unicode(self.code)
        output = output.encode('latin1')
        changed = output != self.source

        return changed, output


    def Save(self):
        from ben10.filesystem import CreateFile, EOL_STYLE_UNIX

        changed, output = self.ReorganizeImports()

        if changed:
            assert self.filename is not None, "No filename set on TerraFormer."
            CreateFile(self.filename, output, eol_style=EOL_STYLE_UNIX)

        return changed


    def AddImportSymbol(self, import_symbol):
        from ._symbol import ImportSymbol

        import_block = self.import_blocks[0]
        symbol = import_block.ObtainImportSymbol(import_symbol, kind=ImportSymbol.KIND_IMPORT_FROM)
        if symbol:
            self.symbols.add(symbol)
