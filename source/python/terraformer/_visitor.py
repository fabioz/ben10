

class ASTError(Exception):
    pass


def IsLeafOfType(leaf, *types):
    from lib2to3.pytree import Leaf

    return isinstance(leaf, Leaf) and leaf.type in types


def IsNodeOfType(node, *types):
    from lib2to3.pytree import Node, type_repr
    return isinstance(node, Node) and type_repr(node.type) in types


def RemoveCommas(nodes):
    from lib2to3.pgen2 import token

    def isnt_comma(node):
        return not IsLeafOfType(node, token.COMMA)
    return filter(isnt_comma, nodes)


def RemoveDefaults(nodes):
    from lib2to3.pgen2 import token

    ignore_next = False
    for node in nodes:
        if ignore_next is True:
            ignore_next = False
            continue
        if IsLeafOfType(node, token.EQUAL):
            ignore_next = True
            continue
        yield node


def DeriveClassName(node):
    return str(node).strip()


def DeriveClassNames(node):
    if node is None:
        return []
    elif IsNodeOfType(node, 'arglist'):
        return map(DeriveClassName, RemoveCommas(node.children))
    else:
        return [DeriveClassName(node)]


def DeriveArgument(node):
    from lib2to3.pgen2 import token

    if IsLeafOfType(node, token.NAME):
        return node
    elif IsNodeOfType(node, 'tfpdef'):
        return tuple(
            map(
                DeriveArgument,
                RemoveCommas(node.children[1].children)
            )
        )


def DeriveArgumentsFromTypedArgList(typedargslist):
    from lib2to3.pgen2 import token

    prefix = ''
    for node in RemoveDefaults(RemoveCommas(typedargslist.children)):
        if IsLeafOfType(node, token.STAR):
            prefix = '*'
        elif IsLeafOfType(node, token.DOUBLESTAR):
            prefix = '**'
        elif prefix:
            #node.prefix = prefix
            yield DeriveArgument(node)
            prefix = ''
        else:
            yield DeriveArgument(node)


def DeriveArguments(node):
    if node == []:
        return []
    elif IsNodeOfType(node, 'typedargslist'):
        return list(DeriveArgumentsFromTypedArgList(node))
    else:
        return [DeriveArgument(node)]


def DeriveImportName(node):
    from lib2to3.pgen2 import token

    if IsLeafOfType(node, token.NAME, token.STAR, token.DOT):
        return node.value
    elif IsNodeOfType(node, 'dotted_as_name', 'import_as_name'):
        return (
            DeriveImportName(node.children[0]),
            DeriveImportName(node.children[2])
        )
    elif IsNodeOfType(node, 'dotted_name'):
        return "".join([i.value for i in node.children])
    elif node is None:
        return
    else:
        raise ASTError("DeriveImportName: unknown node type: %r." % node)


def DeriveImportNames(node):
    if node is None:
        return None
    elif IsNodeOfType(node, 'dotted_as_names', 'import_as_names'):
        return map(
            DeriveImportName,
            RemoveCommas(node.children)
        )
    else:
        return [DeriveImportName(node)]


class ASTVisitor(object):

    PATTERNS = [
        ('_VisitAll', "file_input< nodes=any* >"),
        ('_VisitAll', "suite< nodes=any* >"),
        ('_VisitClass', "body=classdef< 'class' name=NAME ['(' bases=any ')'] ':' any >"),
        ('_VisitFunction', "body=funcdef< 'def' name=NAME parameters< '(' [args=any] ')' > ':' any >"),
        ('_VisitImport',
            "body=import_name< 'import' names=any > | "
            "body=import_from< 'from' import_from=any 'import' names=any > | "
            "body=import_from< 'from' import_from=any 'import' '(' names=any ')' >"
        ),
        ('_VisitPowerSymbol', "body=power< left=NAME trailer< middle='.' right=NAME > any* >"),
        ('_VisitAssignment', "body=expr_stmt< name=any '=' value=any >"),
    ]

    def __init__(self):
        self.patterns = []
        self._assignment = 0
        for method, pattern in self.PATTERNS:
            self.RegisterPattern(method, pattern)

        self._module = None
        self._current_import_block = None
        self._scope_stack = []
        self._klass_stack = []
        self.import_blocks = []
        self.symbols = set()
        self.__assignment = False


    def RegisterPattern(self, method, pattern):
        from lib2to3.patcomp import compile_pattern
        self.patterns.append((method, compile_pattern(pattern)))


    def Visit(self, tree):
        self.EvVisitStart(tree)
        result = self._Visit(tree)
        self.EvVisitEnd(tree)
        return result


    # Events ---------------------------------------------------------------------------------------

    def EvVisitStart(self, tree):
        from ._symbol import ModuleScope
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

        # Module scope.
        self._module = ModuleScope(None, 'module', tree)
        self._scope_stack.append(self._module)

        # Create import-block zero, a place-holder for import-symbols additions.
        self._CreateImportBlock(self._module, code_position, code_replace=[], lineno=lineno)


    def _CreateImportBlock(self, parent, code_position, code_replace, lineno, indent=0):
        from ._symbol import ImportBlock

        id = len(self.import_blocks)
        self._current_import_block = ImportBlock(
            parent,
            code_position,
            code_replace,
            id,
            lineno,
            indent
        )
        self.import_blocks.append(self._current_import_block)
        return self._current_import_block


    def EvVisitEnd(self, tree):
        pass


    def EvVisitLeaf(self, leaf):
        # Handle import-block, connecting import-symbols.
        if self._current_import_block:
            # Append 'intermediate' tokens to the import-block or reset it.
            if leaf.value in (u'\n', u'\r\n'):
                self._current_import_block._code_replace.append(leaf)
            else:
                self._current_import_block = None

        # Handle NAME tokens.
        # NOTE: Can't use DEFAULT_PATTERNS because those are only for Nodes.
        from lib2to3.pgen2 import token
        if leaf.type in (token.NAME,):
            self.EvVisitName(leaf)

    def EvVisitName(self, body):
        current_scope = self._scope_stack[-1]
        symbol = body.value

        if self._assignment == 1:  # Assignee
            current_scope.AddSymbolDefinition(symbol, body)
        if self._assignment == 2:  # Value
            current_scope.AddSymbolUsage(symbol, body)


    def EvVisitImport(self, names, import_from, body):
        from ._lib2to3 import GetNodeLineNumber

        # Create Import-Block
        first_leaf = self._GetFirstLeaf(body)
        prefix = first_leaf.prefix
        has_line_comment = '#' in prefix
        indent = first_leaf.column

        if self._current_import_block and not has_line_comment and self._current_import_block.column == indent:
            code_replace = [body]
            connection_node = body.next_sibling
            while connection_node and connection_node.value in (u'\n'):
                code_replace.append(connection_node)
                connection_node = connection_node.next_sibling
            self._current_import_block._code_replace += code_replace
        else:
            self._CreateNewImportBlock(body, prefix, indent)

        # Create Import-Symbols
        lineno = GetNodeLineNumber(first_leaf)
        next_node = body.next_sibling
        inline_comment = next_node.prefix
        symbols = self._CreateImportSymbols(names, import_from, inline_comment, lineno)

        self.symbols.update(set(symbols))


    def _CreateImportSymbols(self, names, import_from, inline_comment, lineno):
        from ._symbol import ImportSymbol, ImportBlock, ImportFromScope

        assert self._current_import_block is not None
        assert isinstance(self._current_import_block, ImportBlock)

        result = set()
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

            r = self._current_import_block.ObtainImportSymbol(
                symbol,
                import_as,
                inline_comment,
                kind,
                lineno
            )
            result.add(r)
        return result


    def EvVisitSymbol(self, symbol, nodes, body):
        '''
        TODO: Create a Symbol that:
        * can "edit" the nodes.
        * reffers to the import-symbol.
        '''
        current_scope = self._scope_stack[-1]
        if self._assignment == 1:  # Assignee
            current_scope.AddSymbolDefinition(symbol, body)
        else:
            current_scope.AddSymbolUsage(symbol, body)


    def EvVisitAssignment(self, name, value, body):
        assert len(body.children) == 3
        assert body.children[0] is name
        assert body.children[2] is value
        self._current_import_block = None
        self._assignment = 1
        self._Visit(name)
        self._assignment = 2
        self._Visit(value)
        self.__assignment = 0


    def EvVisitClass(self, name, bases, body):
        from ._symbol import ClassScope, FunctionScope

        self._current_import_block = None

        parent = self._scope_stack[-1]

        # Add this class bases uses
        for i_base in bases:
            parent.AddSymbolUsage(i_base, body)

        # TODO: nodes should point to the class name node (for renaming), not the entire code.
        scope = ClassScope(parent, name, None)
        if parent.nested or isinstance(parent, FunctionScope):
            scope.nested = 1

        self._klass_stack.append(scope)
        self._scope_stack.append(scope)
        self._Visit(body.children)  # Visit only CODE child, not the class declaration.
        self._scope_stack.pop()
        self._klass_stack.pop()


    def EvVisitFuncion(self, name, args, body):
        from ._symbol import FunctionScope

        self._current_import_block = None

        parent = self._scope_stack[-1]
        scope = FunctionScope(parent, name, body)  # TODO: We should have the function name as body.
        if parent.nested or isinstance(parent, FunctionScope):
            scope.nested = 1

        scope.HandleArgs(args, body)

        self._scope_stack.append(scope)
        self._Visit(body.children)
        self._scope_stack.pop()


    def _VisitNode(self, node):
        for method, pattern in self.patterns:
            results = {}
            if pattern.match(node, results):
                getattr(self, method)(results)
                break
        else:
            # For unknown nodes simply descend to their list of children.
            self._Visit(node.children)


    # Utitilites -----------------------------------------------------------------------------------

    def _GetImportBlockLineNumber(self, node):
        '''
        Obtain the line number for the import-block.

        TODO: WIP: return a valid number but not the correct line number.
        '''
        from ._lib2to3 import GetNodeLineNumber

        return GetNodeLineNumber(node) - node.prefix.count('\n')


    def _GetFirstLeaf(self, node):
        from lib2to3.pytree import Leaf

        r_leaf = node
        while not isinstance(r_leaf, Leaf):
            r_leaf = r_leaf.children[0]
        return r_leaf


    def _CreateNewImportBlock(self, body, prefix, indent):
        '''
        Create a new import-block.
        '''
        from ._lib2to3 import GetNodeLineNumber

        code_replace = [body]
        connection_node = body.next_sibling
        while connection_node and connection_node.value in (u'\n', u'\r\n'):
            code_replace.append(connection_node)
            connection_node = connection_node.next_sibling

        parent = self._scope_stack[-1]
        return self._CreateImportBlock(
            parent,
            code_position=body,
            code_replace=code_replace,
            lineno=GetNodeLineNumber(body),
            indent=indent
        )


    # Pattern Handlers -----------------------------------------------------------------------------

    def _Visit(self, tree):
        """Main entry point of the ASTVisitor class.
        """
        from lib2to3.pytree import Leaf, Node

        if isinstance(tree, Leaf):
            self.EvVisitLeaf(tree)
        elif isinstance(tree, Node):
            self._VisitNode(tree)
        elif isinstance(tree, list):
            for subtree in tree:
                self._Visit(subtree)
        else:
            raise ASTError("Unknown tree type: %r." % tree)


    def _VisitAll(self, results):
        self._Visit(results['nodes'])


    def _VisitClass(self, results):
        self.EvVisitClass(
            name=results['name'].value,
            bases=DeriveClassNames(results.get('bases')),
            body=results['body']
        )


    def _VisitFunction(self, results):
        self.EvVisitFuncion(
            name=results['name'].value,
            args=DeriveArguments(results.get('args', [])),
            body=results['body']
        )


    def _VisitImport(self, results):
        self.EvVisitImport(
            names=DeriveImportNames(results['names']),
            import_from=DeriveImportName(results.get('import_from')),
            body=results['body']
        )


    def _VisitPowerSymbol(self, results):
        left=results.get('left')
        middle=results.get('middle')
        right=results.get('right')
        body=results['body']
        self.EvVisitSymbol(
            symbol=u'.'.join((left.value, right.value)),
            nodes=[left,middle,right],
            body=body
        )
        self._Visit(body.children[2:])


    def _VisitAssignment(self, results):
        name=results.get('name')
        value=results.get('value')
        self.EvVisitAssignment(
            name=name,
            value=value,
            body=results['body']
        )
