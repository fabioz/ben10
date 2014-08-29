from ._astvisitor import ASTVisitor



#===================================================================================================
# ImportVisitor
#===================================================================================================
class ImportVisitor(ASTVisitor):

    IMPORT_BLOCK = '(IMPORT-BLOCK #%d)'

    def __init__(self):
        ASTVisitor.__init__(self)
        self.symbols = []
        self.import_blocks = []
        self._first_leaf = None
        self._last_leaf = None


    def visit_end(self, tree):
        from lib2to3.pgen2 import token
        from lib2to3.pytree import Leaf
        from ._import_block import ImportBlock

        if not self.import_blocks:
            assert self._first_leaf is not None
            value = self.IMPORT_BLOCK % 0
            leaf = Leaf(token.NAME, value)

            lineno = self._GetImportBlockLineNumber(self._first_leaf)

            self._first_leaf.parent.insert_child(0, leaf)

            import_block = ImportBlock(leaf, len(self.import_blocks), lineno, 0, [])
            self.import_blocks.append(import_block)


    def visit_leaf(self, leaf):
        from lib2to3.pgen2 import token

        # Keep the last-leaf to enable the creation of import-blocks from multiple
        # import-symbols.
        if self._first_leaf is None:
            if leaf.type not in (token.STRING, token.NEWLINE):
                self._first_leaf = leaf

        if leaf.value not in ('\r\n', '\n'):
            self._last_leaf = leaf

    def visit_import(self, names, import_from, body):
        from ._import_symbol import ImportSymbol

        # Get prefix, indent and comment
        first_leaf = body
        while first_leaf.children:
            first_leaf = first_leaf.children[0]
        next_node = body.next_sibling
        # ...
        prefix = first_leaf.prefix
        indent = first_leaf.column
        inline_comment = next_node.prefix
        has_line_comment = '#' in prefix
        has_eol = next_node.value == u'\n'

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
            symbols.append(
                ImportSymbol(
                    symbol,
                    import_as=import_as,
                    comment=inline_comment,
                    kind=kind
                )
            )

        # Import Block:
        if inline_comment:
            next_node.prefix = ''
            next_node.changed()

        is_import_block = self._last_leaf and self._last_leaf.value.startswith('(IMPORT-BLOCK #')
        if is_import_block and not has_line_comment:
            import_block = self.import_blocks[-1]
            if import_block.indent != indent:
                self._CreateNewImportBlock(body, symbols, prefix, indent)
            else:
                self._MergeImportBlock(body, symbols, import_block)
        else:
            self._CreateNewImportBlock(body, symbols, prefix, indent)

        self.symbols += symbols


    def _GetImportBlockLineNumber(self, node):
        '''
        Obtain the line number for the import-block.

        TODO: WIP: return a valid number but not the correct line number.
        '''
        from terraforming._lib2to3 import GetNodeLineNumber

        if node.next_sibling:
            node = node.next_sibling
        return GetNodeLineNumber(node) - node.prefix.count('\n')


    def _MergeImportBlock(self, body, symbols, import_block):
        '''
        Merges the symbols into another import-block.
        '''
        next = body.next_sibling
        if next and next.value in ('\n','\r\n'):
            next.remove()
        body.remove()
        import_block.symbols += symbols


    def _CreateNewImportBlock(self, body, symbols, prefix, indent):
        '''
        Create a new import-block.
        '''
        from ._import_block import ImportBlock
        from lib2to3.pgen2 import token
        from lib2to3.pytree import Leaf

        value = self.IMPORT_BLOCK % (len(self.import_blocks) + 1)
        self._last_leaf = Leaf(token.NAME, value, prefix=prefix)

        body.replace(self._last_leaf)
        import_block = ImportBlock(
            self._last_leaf,
            len(self.import_blocks),
            self._GetImportBlockLineNumber(self._last_leaf),
            indent,
            symbols
        )
        self.import_blocks.append(import_block)
        return import_block
