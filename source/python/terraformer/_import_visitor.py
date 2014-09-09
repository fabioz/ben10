from lib2to3.pygram import python_symbols
from compiler.symbols import FunctionScope, ClassScope, ModuleScope
from ._astvisitor import ASTVisitor



#===================================================================================================
# ImportVisitor
#===================================================================================================
class ImportVisitor(ASTVisitor):

    def __init__(self):
        ASTVisitor.__init__(self)
        self._module = None
        self._current_import_block = None
        self.scopes = []
        self._scope_stack = []
        self._klass_stack = []
        self.import_blocks = []
        self.symbols = set()


    def visit_start(self, tree):
        from ._import_block import ImportBlock
        from lib2to3.pygram import python_symbols
        from lib2to3.pytree import Leaf

        # Find the code-position for the import-block. Either a leaf or an import statement.
        types=(python_symbols.import_from, python_symbols.import_name)
        code_position = tree
        while not isinstance(code_position, Leaf) and code_position.type not in types:
            code_position = code_position.children[0]

        # Line number is based on the first leaf.
        first_leaf = self._GetFirstLeaf(tree)
        lineno = self._GetImportBlockLineNumber(first_leaf)

        # Create import-block zero, a place-holder for import-symbols additions.
        self._current_import_block = ImportBlock(code_position, [], 0, lineno, 0, [])
        self.import_blocks.append(self._current_import_block)

        # Module scope.
        scope = ModuleScope()
        self._module = self.scopes.append(scope)
        self._scope_stack.append(scope)


    def visit_leaf(self, leaf):

        if self._current_import_block:
            # Append 'intermediate' tokens to the import-block or reset it.
            if leaf.value in (u'\n', u'\r\n'):
                self._current_import_block._code_replace.append(leaf)
            else:
                self._current_import_block = None

        # from lib2to3.pgen2 import token
        # from lib2to3.pygram import python_symbols
        # if leaf.type in (token.NAME,):
        #     if leaf.parent.type in (python_symbols.power,):
        #         self.names.setdefault(unicode(leaf.parent), []).append(leaf.parent)
        #     elif leaf.parent.type in (python_symbols.expr_stmt,):
        #         self.names.setdefault(leaf.value, []).append(leaf)


    def visit_import(self, names, import_from, body):
        from ._import_symbol import ImportSymbol
        from terraforming._lib2to3 import GetNodeLineNumber

        # Get prefix, indent and comment
        first_leaf = self._GetFirstLeaf(body)
        next_node = body.next_sibling
        # ...
        prefix = first_leaf.prefix
        lineno = GetNodeLineNumber(first_leaf)
        indent = first_leaf.column
        inline_comment = next_node.prefix
        has_line_comment = '#' in prefix

        # Get symbols
        symbols = []
        for i_name in names:
            if isinstance(i_name, tuple):
                i_name, import_as = i_name
            else:
                import_as = None
            if import_from:
                symbol = '%s.%s' % (import_from, i_name)
                kind = ImportSymbol.KIND_IMPORT_FROM
            else:
                symbol = i_name
                kind = ImportSymbol.KIND_IMPORT_NAME
            symbol = ImportSymbol(
                symbol,
                import_as,
                inline_comment,
                kind,
                lineno
            )
            symbols.append(symbol)

        if self._current_import_block and not has_line_comment:
            import_block = self._current_import_block
            if import_block.indent != indent:
                self._current_import_block = self._CreateNewImportBlock(body, symbols, prefix, indent)
            else:
                code_replace = [body]
                connection_node = body.next_sibling
                while connection_node and connection_node.value in (u'\n'):
                    code_replace.append(connection_node)
                    connection_node = connection_node.next_sibling

                import_block._code_replace += code_replace
                import_block.symbols.update(set(symbols))
        else:
            self._current_import_block = self._CreateNewImportBlock(body, symbols, prefix, indent)

        self.symbols.update(set(symbols))


    def visit_class(self, name, bases, body):
        parent = self._scope_stack and self._scope_stack[-1]
        # parent.add_def(node.name)
        # for n in node.bases:
        #     self.visit(n, parent)
        scope = ClassScope(name, self._module)
        if parent.nested or isinstance(parent, FunctionScope):
            scope.nested = 1
        # if node.doc is not None:
        #     scope.add_def('__doc__')
        # scope.add_def('__module__')
        self.scopes.append(scope)
        self._klass_stack.append(scope)
        self._scope_stack.append(scope)
        self._visit(body.children)
        self._scope_stack.pop()
        self._klass_stack.pop()
        #self.handle_free_vars(scope, parent)


    def visit_function(self, name, args, body):
        parent = self._scope_stack and self._scope_stack[-1]
        klass_name = self._klass_stack and self._klass_stack[-1].name
        # if node.decorators:
        #     self.visit(node.decorators, parent)
        parent.add_def(name)
        # for n in node.defaults:
        #     self.visit(n, parent)
        scope = FunctionScope(name, self._module, klass_name)
        if parent.nested or isinstance(parent, FunctionScope):
            scope.nested = 1
        self.scopes.append(scope)
        # self._do_args(scope, node.argnames)
        self._scope_stack.append(scope)
        self._visit(body.children)
        self._scope_stack.pop()
        # self.handle_free_vars(scope, parent)


    def _GetImportBlockLineNumber(self, node):
        '''
        Obtain the line number for the import-block.

        TODO: WIP: return a valid number but not the correct line number.
        '''
        from terraforming._lib2to3 import GetNodeLineNumber

        return GetNodeLineNumber(node) - node.prefix.count('\n')


    def _GetFirstLeaf(self, node):
        from lib2to3.pytree import Leaf

        r_leaf = node
        while not isinstance(r_leaf, Leaf):
            r_leaf = r_leaf.children[0]
        return r_leaf


    def _CreateNewImportBlock(self, body, symbols, prefix, indent):
        '''
        Create a new import-block.
        '''
        from ._import_block import ImportBlock

        code_replace = [body]
        connection_node = body.next_sibling
        while connection_node and connection_node.value in (u'\n', u'\r\n'):
            code_replace.append(connection_node)
            connection_node = connection_node.next_sibling

        import_block = ImportBlock(
            body,
            code_replace,
            len(self.import_blocks),
            symbols[0].lineno,
            indent,
            symbols
        )

        self.import_blocks.append(import_block)
        return import_block
