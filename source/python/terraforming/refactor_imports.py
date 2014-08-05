from ben10.filesystem import GetFileContents
from ben10.foundation.reraise import Reraise
from ben10.module_finder import ModuleFinder
import os


PYTHON_EXT = '.py'



#===================================================================================================
# ImportSymbol
#===================================================================================================
class ImportSymbol(object):
    '''
    Represents an import symbol.

    Examples:
        import alpha
        from alpha import Alpha
        from alpha import Alpha as MyAlpha

    :cvar str symbol:
        The symbol being imported.

    :cvar KIND_IMPORT_XXX kind:
        Either import-name (import XXX) or import-from (from XXX import YYY)

    :cvar str import_as:
        Optional rename of the import (import XXX as YYY)
    '''

    KIND_IMPORT_NAME = 298
    KIND_IMPORT_FROM = 297

    def __init__(self, symbol, import_as=None, comment='', kind=KIND_IMPORT_NAME):
        '''
        :param str symbol:
            The import-symbol.

        :param str|None import_as:
            Optional alias for the symbol.

        :param str comment:
            A comment associated with the import
            Ex. # @UnusedImport

        :param KIND_IMPORT_XXX kind:
            The kind of import.
        '''
        assert isinstance(symbol, (str, unicode))
        assert isinstance(comment, (str, unicode))
        assert kind in (self.KIND_IMPORT_NAME, self.KIND_IMPORT_FROM)

        self.symbol = symbol
        self.import_as = import_as
        self.comment = comment
        self.kind = kind


    def __repr__(self):
        return '<ImportSymbol "%s">' % self.symbol


    def GetPackageName(self):
        '''
        Returns the import-symbol prefix.

        This is only valid for import-symbols of type import-from, in which case it returns
        the "from" part of the import. Returns None if kind is import-name.

        Example:
            >s = ImportSymbol("Alpha", 'alpha')  # from alpha import Alpha
            >s.GetPackageName()
            'alpha'

        :return str:
        '''
        if self.kind == self.KIND_IMPORT_FROM:
            return self.symbol.rsplit('.', 1)[0]
        else:
            return None


    def GetToken(self):
        '''
        Returns the import token of a import-symbol of kind import-from.
        Returns the symbol if kind is import-name.

        :return str:
        '''
        if self.kind == self.KIND_IMPORT_FROM:
            return self.symbol.rsplit('.', 1)[1]
        else:
            return self.symbol


    def __cmp__(self, other):
        '''
        Implements object comparison.

        Uses only the symbol attribute for the comparison.
        '''
        return cmp(self.symbol, other.symbol)



#===================================================================================================
# ImportStatements
#===================================================================================================
class ImportStatements(object):
    '''
    Represents a collection of import-statements, containing many import symbols.
    '''
    WIDTH = 100

    def __init__(self, symbols, indent=0):
        '''
        :param list(ImportSymbol) symbols: List of symbols to initialize this import-statements.
        :param int indent: The original indentation of these import-statements.
        '''
        self.symbols = symbols
        self.indent = indent


    @classmethod
    def CreateFromNode(cls, node):
        '''
        Create an ImportStatements instance from the given lib2to3 node.

        :param lib2to3.Node node:
            This algorithm is expecting the leaf node that is poiting to the "import" name.
            From this node, it can extract the information about the import-symbols.

        :return tuple(ImportStatements, Node):
        '''
        from lib2to3 import pygram
        from lib2to3.pytree import Leaf

        def _Walk(nodes):
            for i_node in nodes:
                if isinstance(i_node, Leaf):
                    if i_node.value in (',', '(', ')'):
                        continue
                    yield i_node.value, None
                elif i_node.type in (
                    pygram.python_symbols.import_as_name,
                    pygram.python_symbols.dotted_as_name
                ):
                    yield (
                        str(i_node.children[0]).strip(),
                        str(i_node.children[2]).strip()
                    )
                elif i_node.type == pygram.python_symbols.dotted_name:
                    yield str(i_node).strip(), None
                else:
                    for j_child, j_import_as in _Walk(i_node.children):
                        yield j_child, j_import_as

        if node.parent.type == ImportSymbol.KIND_IMPORT_NAME:
            assert node.parent.children[0].type == 1
            assert node.parent.children[0].value == 'import'

            if node.parent.next_sibling.value == ';':
                # Ignores imports with code in the same line:
                #   Ex: import pdb;pdb.set_trace()
                return None, node

            assert node.parent.next_sibling.value.endswith('\n')
            comment = node.parent.next_sibling.prefix
            r_indent = node.column
            r_symbols = [
                ImportSymbol(i_value, import_as=i_import_as, comment=comment)
                for (i_value, i_import_as) in _Walk(node.parent.children[1:])
            ]
            return cls(r_symbols, r_indent), node

        elif node.parent.type == ImportSymbol.KIND_IMPORT_FROM:
            try:
                assert node.parent.children[0].type == 1
                assert node.parent.children[0].value == 'from'
                r_indent = node.parent.children[0].column

                handling_prefix = True
                prefix = ''
                r_symbols = []
                for i_child in node.parent.children[1:]:
                    if handling_prefix:
                        if i_child == node:
                            handling_prefix = False
                            continue
                        prefix += str(i_child).strip()
                    else:
                        assert node.parent.next_sibling.value in ('\n', '\r\n')
                        comment = node.parent.next_sibling.prefix
                        r_symbols += [
                            ImportSymbol(
                                prefix + '.' + i_value,
                                import_as=i_import_as,
                                comment=comment,
                                kind=ImportSymbol.KIND_IMPORT_FROM
                            )
                            for (i_value, i_import_as) in _Walk([i_child])
                        ]
                return cls(r_symbols, r_indent), node.parent.children[0]
            except Exception, e:
                Reraise(e, "While processing import-from on node: '%s'" % node.parent)


    def CreateNodes(self, page_width, refactor, filename=None):
        '''
        Create lib2to3 nodes from the internal information.

        :param int page_width:
            The algorithm tries to respect this page-width for all statements.

        :param dict refactor:
            A refactoring map, mapping the old symbol path to the new place.

        :param str filename:
            The name of the module we're working on.
            This is necessary for the local-imports algorithm.
        '''

        def GetLocalImportSymbol(import_symbol, filename):
            '''
            Converts the given import-symbol into a local import.

            This is necessary to avoid import loops in the following conditions:

            * Module importing module in the same package
            * The package (__init__.py) imports both symbols

                Ex.:
                /alpha/
                    __init__.py
                    [
                        from bravo import *
                        from charlie import *
                    ]
                    bravo.py
                    [
                        import alpha.charlie
                    ]
                    charlie.py

            We solve this by:

            * Imports in the above conditions must be local, not global.
                Ex.:
                    bravo.py
                    [
                        import charlie
                    ]

            Terms:
                * working: meaning the module we are working one. The import-symbol and filename given as parameters.
                * init: refers to package (__init__.py)
                * local: refers to the module, found in the same location the "working" module, that contains a symbol
                  used by the working symbol.

            '''

            def GetImportPackageAndToken(import_symbol):
                '''
                Obtain the import-symbol package and symbol
                '''
                r_package = import_symbol.GetPackageName()
                if r_package is None:
                    return None, None
                r_token = import_symbol.GetToken()
                return r_package, r_token


            if import_symbol.import_as:
                return import_symbol

            working_package, working_token = GetImportPackageAndToken(import_symbol)

            # CASE: ?
            if working_package is None:
                return import_symbol

            # CASE: Importing all symbols from a module/package. This case is ignored.
            if working_token == '*':
                return import_symbol

            # Obtain the package __init__.py filename
            package_init_filename = os.path.abspath(os.path.dirname(filename)) + '/__init__' + PYTHON_EXT
            if not os.path.isfile(package_init_filename):
                return import_symbol

            # CASE: The symbol is not available in the package
            init_import_symbol = GetImportSymbols(package_init_filename).get(working_token)
            if init_import_symbol is None:
                return import_symbol

            # Obtain the init_package_name: The module name for the package.
            # IMPORTANT: For this to work the package must be importable in the current PYTHONPATH.
            # Ex.
            #   alpha10.parent.working.py -> alpha10.parent
            module_finder = ModuleFinder()
            try:
                init_package_name = module_finder.ModuleName(package_init_filename).rsplit('.', 1)[0]
            except RuntimeError:
                return import_symbol

            # CASE: The symbol matches one found in the package, but it is from another package, not this one.
            if import_symbol.GetPackageName() != init_package_name:
                return import_symbol

            # CASE: Finally, we found that we are importing a symbol available in a local module using a global import.
            #       In this case we fix it using the same local import as the package __init__.py is using.
            return init_import_symbol


        def GetRefactoredImportSymbol(import_symbol, refactor):
            '''
            Returns the refactored import-symbol.

            :param ImportSymbol import_symbol:
                The import symbol to check for an refa

            :param dict refactor:
                A refactoring dictionary mapping old symbol python-path to the new python-path.

            :return ImportSymbol:
                Returns the refactored symbol or the import-symbol itself if no refactor
                alternative were found.
            '''
            if refactor is None:
                return import_symbol

            new_symbol = refactor.get(import_symbol.symbol)
            if new_symbol is not None:
                return ImportSymbol(
                    new_symbol,
                    import_symbol.import_as,
                    comment=import_symbol.comment,
                    kind=import_symbol.kind
                )

            new_prefix = refactor.get(import_symbol.GetPackageName())
            if new_prefix is not None:
                return ImportSymbol(
                    new_prefix + '.' + import_symbol.GetToken(),
                    import_symbol.import_as,
                    comment=import_symbol.comment,
                    kind=import_symbol.kind
                )
            return import_symbol


        def GenerateImportNode(symbol, indent, comment):
            '''
            Generate code (an lib2to3 parser-node) from the given import-symbol.

            :param ImportSymbol symbol:
                The symbol to generate the parse-node.

            :param int indent:
                The indentation for the generated code.

            :param str comment:
                The comment to associate with the parse-node.

            :return lib2to3.pytree.Node:
                Return a simple_stmt parser-node with the import statement code.
            '''
            from lib2to3 import pygram
            from lib2to3.fixer_util import Name, Newline
            from lib2to3.pytree import Node

            if i_symbol.import_as is not None:
                node = Node(
                    pygram.python_symbols.import_as_name,
                    [
                        Name(i_symbol.GetToken(), prefix=' '),
                        Name('as', prefix=' '),
                        Name(i_symbol.import_as, prefix=' ')
                    ]
                )
            else:
                node = Name(symbol.symbol, prefix=' ')

            new_line = Newline()
            new_line.prefix = comment
            return Node(
                pygram.python_symbols.simple_stmt,
                prefix=' ' * indent,
                children=[
                    Name('import'),
                    node,
                    new_line,
                ]
            )


        def TextWrapForNode(node, max_width, indent, start_at='(', end_at=')'):
            '''
            Wrap the given node so it fits in max-width.

            Changes the nodes in-place.

            :param lib2to3.pytree.Node:
                Return a simple_stmt parser-node with the import statement code..Node node:

            :param int max_width:
                The number of columns to wrap the text.

            :param int indent:
                The text indentation in number of characters, not in number of "tabs".

            :param str start_at:
                The value of the node to enable the wrapping.
                Some lines should no be broken until a given symbol such as open parenthesis.

            :param str end_at:
                The value of the node to disable the wrapping.
            '''
            from _lib2to3 import WalkLeafs

            started = False
            cumulative_len = 0
            symbols_count = 0
            for i_leaf in WalkLeafs(node):
                # TODO: BEN-28: [terraforming] Consider the EOL prefix in the cumulative_len, since it can contain comments
                if i_leaf.value == '\n':
                    break

                if not started:
                    leaf_len = len(str(i_leaf))
                    cumulative_len += leaf_len
                    started = i_leaf.value == start_at
                elif i_leaf.value == end_at:
                    break
                else:
                    symbols_count += 1

                    if i_leaf.prefix not in ( ', ', ',\n', '\n', ' ', ''):
                        raise NotImplementedError('Unexpected token prefix "%s"' % i_leaf.prefix)

                    leaf_len = len(str(i_leaf))
                    cumulative_len += leaf_len

                    if cumulative_len >= max_width:
                        if ',' in i_leaf.prefix:
                            i_leaf.prefix = ','
                        else:
                            i_leaf.prefix = ''
                        indentation = ' ' * (4 + indent)
                        i_leaf.prefix += '\n' + indentation
                        leaf_len = len(indentation) + len(str(i_leaf.value))
                        cumulative_len = leaf_len


        def GenerateImportFromNode(package_name, symbols, indent, comment):
            '''
            Generate an AST node for the given symbols in the import-from format

            :param str package_name:
                The name of the package to "import-from".
                Ex.:
                    from <package> import <symbols>

            :param list(ImportSymbol) symbols:
                The symbols to import from the package.
                Ex.:
                    from <package> import <symbols>

            :param int indent:
                The text indentation.

            :param str comment:
                The comment for the import statement.
                The comment is placed in the end of the line.
            '''
            from lib2to3 import pygram
            from lib2to3.fixer_util import Name, Newline
            from lib2to3.pytree import Node

            # children: the children nodes for the final from-import statement
            children = [
                Name('from', prefix=' ' * indent),
                Name(package_name, prefix=' '),
                Name('import', prefix=' '),
            ]

            # name_leaf: list of leaf nodes with the symbols to import
            name_leafs = []
            for i, i_symbol in enumerate(symbols):
                prefix = ' ' if i == 0 else ', '
                if i_symbol.import_as is not None:
                    node = Node(
                        pygram.python_symbols.import_as_name,
                        [
                            Name(i_symbol.GetToken(), prefix=prefix),
                            Name('as', prefix=' '),
                            Name(i_symbol.import_as, prefix=' ')
                        ]
                    )
                    name_leafs.append(node)
                else:
                    leaf = Name(i_symbol.GetToken(), prefix=prefix)
                    name_leafs.append(leaf)

            # nodes_wrap: if true, we need to wrap the import statement
            nodes_wrap = False
            line_len = 0
            line_len += reduce(lambda x, y:x + y, map(len, map(str, children)), 0)
            line_len += reduce(lambda x, y:x + y, map(len, map(str, name_leafs)), 0)
            if line_len > page_width:
                # Add parenthesis around the "from" names
                name_leafs[0].prefix = ''
                name_leafs.insert(0, Name('(', prefix=' '))
                name_leafs.append(Name(')'))
                nodes_wrap = True

            # Adds the name_leafs to the children list
            children += [
                Node(pygram.python_symbols.import_as_names, name_leafs)
            ]

            # from_import: the final node for the import statement
            from_import = Node(pygram.python_symbols.import_from, children)

            # result: a simple-statement node with the import statement and EOL.
            new_line = Newline()
            new_line.prefix = comment or ''
            result = Node(
                pygram.python_symbols.simple_stmt,
                children=[
                    from_import,
                    new_line,
                ],
            )

            # Wrap nodes if necessary (see nodes_wrap above)
            if nodes_wrap:
                TextWrapForNode(result, page_width, indent)

            return result

        def GetSortIndex(symbol):
            '''
            Index used to properly sort import statements in a group.
            '''
            if '@terraforming:last-import' in symbol.comment:
                return 1
            elif symbol.symbol.startswith('_'):
                return -1
            else:
                return 0

        # Collects the import-symbols in different lists to properly sort them.
        # We must do this in two steps because of the refactoring process that can change
        # the symbols completely.
        result = []
        import_from = {}
        import_names = []
        for i_symbol in self.symbols:
            symbol = GetRefactoredImportSymbol(i_symbol, refactor)

            if filename and os.path.basename(filename) != '__init__' + PYTHON_EXT:
                symbol = GetLocalImportSymbol(symbol, filename)

            if symbol.kind == symbol.KIND_IMPORT_FROM:
                import_from.setdefault(
                    (
                        GetSortIndex(symbol),
                        symbol.GetPackageName(),
                        symbol.comment
                    ),
                    []
                ).append(symbol)
            else:
                import_names.append(
                    (
                    GetSortIndex(symbol),
                    symbol
                    )
                )

        # Generates "from X import Y" statements
        for (_sort_index, i_prefix, i_comment), i_symbols in sorted(import_from.iteritems()):
            result.append(GenerateImportFromNode(i_prefix, sorted(i_symbols), self.indent, i_comment))

        # Generates "import X" statements
        for _sort_index, i_symbol in sorted(import_names):
            result.append(GenerateImportNode(i_symbol, self.indent, i_symbol.comment))

        return result



#===================================================================================================
# GetParseTree
#===================================================================================================
def GetParseTree(filename, source_code=None):
    '''
    Returns a lib2to3.pytree.Node:
    Return a simple_stmt parser-node with the import statement code. parse tree for the given filename or source_code.

    :param str filename:
        The name of the python module.

    :param str source_code:
        Optional parameter used for debug.
        Use filename=None to enable source_code.

    :return lib2to3.pytree.Node:
                Return a simple_stmt parser-node with the import statement code..pytree.Node:
    '''
    from ._lib2to3 import ParseString

    try:
        if filename is None:
            assert source_code is not None, "Parameter source_code is mandatory if filename is not given."

        if source_code is None:
            assert filename is not None, "Parameter filename is mandatory if source_code is not given."
            source_code = GetFileContents(filename)

        if len(source_code) > 500000:
            raise RuntimeError('File too big: %s' % len(source_code))

        # Fix the mandatory (for lib2to3) EOL in the end of the source-code.
        source_code = source_code.decode('latin1')
        if source_code and source_code[-1] != u'\n':
            source_code += u'\n'

        return ParseString(source_code)
    except Exception as exception:
        Reraise(exception, 'While processing filename:: %s' % filename)



IMPORT_PLACEHOLDER = '(IMPORT-PLACEHOLDER)'



#===================================================================================================
# _CreateImportMyRefactoringTool
#===================================================================================================
def _CreateImportMyRefactoringTool(options):
    from ._lib2to3 import MyRefactoringTool, BaseFix
    from lib2to3.pgen2 import token
    from lib2to3.fixer_util import Name

    class ImportSymbolsExtractor(BaseFix):
        '''
        A lib2to3.pytree.Node:
                    Return a simple_stmt parser-node with the import statement code. fix that extracts the import-symbols from a AST tree replacing them with
        place-holders for future replacement (see ImportSymbolsInjector).

        Stores the symbols in the options dictionary, under the key "isymbols".
        '''

        _accept_type = token.NAME

        def start_tree(self, tree, filename):
            self.import_placeholder_id = 0
            return BaseFix.start_tree(self, tree, filename)


        def match(self, node):
            if node.value == 'import':
                import_statements, node = ImportStatements.CreateFromNode(node)
                if import_statements is None:
                    return
                self.import_placeholder_id += 1
                groups = self.options['isymbols']
                cur_import_statements = groups.get(self.import_placeholder_id)
                if cur_import_statements is None:
                    groups[self.import_placeholder_id] = import_statements
                else:
                    cur_import_statements.symbols += import_statements.symbols
                return node


        def transform(self, node, results):
            # Place only on "IMPORT_PLACEHOLDER" at a time.
            cur = node.parent.parent
            prev = cur.prev_sibling
            if prev is not None:
                # Merge IMPORT_PLACEHOLDER only if we have no comments in the prefix.
                has_comments = '#' in node.parent.children[0].prefix
                prev_is_placeholder = prev.type == 1 and prev.value == IMPORT_PLACEHOLDER
                if prev_is_placeholder and not has_comments:
                    cur_index = self.import_placeholder_id
                    prev_index = self.import_placeholder_id - 1

                    isymbols = self.options['isymbols']
                    cur_import_statements = isymbols[cur_index]
                    prev_import_statements = isymbols[prev_index]
                    prev_import_statements.symbols += cur_import_statements.symbols
                    del isymbols[cur_index]
                    self.import_placeholder_id -= 1
                    cur.remove()
                    return
            cur.replace(Name(IMPORT_PLACEHOLDER, prefix=results.prefix))


    return MyRefactoringTool([ImportSymbolsExtractor], options=options)


#===================================================================================================
# _CreateInjectorMyRefactoringTool
#===================================================================================================
def _CreateInjectorMyRefactoringTool(options):
    from ._lib2to3 import MyRefactoringTool, BaseFix
    from lib2to3.pgen2 import token

    class ImportSymbolsInjector(BaseFix):
        '''
        Replaces place-holders in the AST tree by new nodes with all import statements
        reorganized.

        Gets the symbols from the options dictionary, under the key "isymbols".
        '''

        _accept_type = token.NAME

        def start_tree(self, tree, filename):
            self.import_placeholder_id = 0
            return BaseFix.start_tree(self, tree, filename)


        def match(self, node):
            if node.value == IMPORT_PLACEHOLDER:
                self.import_placeholder_id += 1
                return self.import_placeholder_id


        def transform(self, node, results):
            def InsertAfter(node, new_nodes):
                if node.parent:
                    for i, i_node in enumerate(node.parent.children):
                        if i_node is not node:
                            continue

                        node.parent.changed()
                        for j_new_node in reversed(new_nodes):
                            node.parent.children.insert(i, j_new_node)
                            j_new_node.parent = node.parent
                        return i

            import_statements = self.options['isymbols'][results]
            nodes = import_statements.CreateNodes(
                self.options.get('page_width'),
                self.options.get('refactor'),
                filename=self.options['filename'],
            )
            nodes[0].prefix = node.prefix
            InsertAfter(node, nodes)
            node.remove()

    return MyRefactoringTool([ImportSymbolsInjector], options=options)



#===================================================================================================
# GetImportSymbols
#===================================================================================================
def GetImportSymbols(filename):
    '''
    Returns the import-symbols for the given python module.

    :param str filename:
        A python module.

    :return dict(str:ImportSymbol):
        Maps the symbol token to a Symbol instance
    '''
    tree = GetParseTree(filename, None)
    options = {'isymbols' : {}}
    rt = _CreateImportMyRefactoringTool(options)
    rt.refactor_tree(tree, 'ImportSymbolsExtractor')
    result = {}
    for i_import_statements in options['isymbols'].itervalues():
        for j_import_symbol in i_import_statements.symbols:
            result[j_import_symbol.GetToken()] = j_import_symbol
    return result



#===================================================================================================
# ReorganizeImports
#===================================================================================================
def ReorganizeImports(filename, source_code=None, refactor={}, python_path='', page_width=100):
    '''
    Reorganizes all imports in the given source_code.

    :param str filename:
        The python module filename.
        Can be None IF using source_code parameter.

    :param str source_code:
        The python module content.
        Optional parameter used for tests.

    :param dict refactor:
        A dictionary mapping old symbols to new symbols.

    :param str python_path:
        An alternative python_path for testing.

    :param int page_width:
        The page-width (try) to format the import statements.

    :return boolean, str:
        Returns True if any changes were made.
        Returns the reorganized source code.
    '''

    if source_code is None:
        source_code = GetFileContents(filename)

    tree = GetParseTree(filename, source_code)

    options = {
        'isymbols' : {},

        'filename' : filename,
        'page_width' : page_width,
        'python_path' : python_path,
        'refactor' : refactor,
    }

    rt = _CreateImportMyRefactoringTool(options)
    rt.refactor_tree(tree, 'ImportSymbolsExtractor')

    rt = _CreateInjectorMyRefactoringTool(options)
    rt.refactor_tree(tree, 'ImportSymbolsInjector')

    result = unicode(tree).encode('latin1')
    changed = result != source_code

    return changed, result
