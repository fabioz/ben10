from ._import_symbol import ImportSymbol
import os


def index(node):
    return node.parent.children.index(node)

def insert_before(node, code):
    if not node.parent:
        raise TypeError("Can't insert before node that doesn't have a parent.")
    if not isinstance(code, list):
        code = [code]

    pos = index(node)
    new_children = []
    for i, i_child in enumerate(node.parent.children):
        if i == pos:
            new_children += code
        new_children.append(i_child)

    for j_node in code:
        j_node.parent = node.parent
    node.parent.children = new_children
    node.parent.changed()


#===================================================================================================
# ImportBlock
#===================================================================================================
class ImportBlock(object):

    PYTHON_EXT = '.py'

    def __init__(self, code_position, code_replace, id, lineno, indent, symbols):
        # The new import-block will be inserted BEFORE this code. The code will not be altered.
        self._code_position = code_position
        # The new import-block will REPLACE this node(s).
        self._code_replace = code_replace
        self.id = id
        self.lineno = lineno
        self.indent = indent
        self.symbols = set(symbols)


    def __str__(self):
        '''
        The string representation for import-block contains:
            - The import-block id (sequential number in the module)
            - The coordinates: line number and indent
            - A list of import-symbols.
        '''
        return "<ImportBlock #%d (%d, %d): %s>" % (
            self.id,
            self.lineno,
            self.indent,
            ' '.join(sorted([i.symbol for i in self.symbols]))
        )


    def Reorganize(self, page_width=100, refactor=None, filename=None):
        '''
        Reorganize the import-statements replacing the previous code by brand new import-statements

        :param page_width:
        :param refactor:
        :param filename:
        :return:
        '''
        if self.symbols:
            # Create new nodes with all the import-statements.
            nodes = self.CreateNodes(
                self.symbols,
                self.indent,
                page_width=page_width,
                refactor=refactor,
                filename=filename,
            )

            # Some extra fixes on new created nodes.
            if self._code_replace:
                # Copies the prefix from the replaced code.
                nodes[0].prefix = self._code_replace[0].prefix

                # Remove EOL from new nodes under certain conditions:
                next_node = self._code_replace[-1].next_sibling
                if next_node and next_node.value == ';':
                    del nodes[-1].children[-1]

            # Insert new nodes before the marked position.
            insert_before(self._code_position, nodes)

            # Delete the code this code block replaces.
            for i_node in self._code_replace:
                i_node.remove()

            self._code_position = nodes[0]
            self._code_replace = nodes
        else:
            for i_node in self._code_replace:
                i_node.remove()


    def AddImportSymbol(self, import_symbol):
        result = ImportSymbol(import_symbol, kind=ImportSymbol.KIND_IMPORT_FROM)
        self.symbols.add(result)
        return result


    @classmethod
    def CreateNodes(cls, symbols, indent, page_width, refactor, filename=None):
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
            from ben10.module_finder import ModuleFinder

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
            package_init_filename = os.path.abspath(
                os.path.dirname(filename)
            ) + '/__init__' + cls.PYTHON_EXT
            if not os.path.isfile(package_init_filename):
                return import_symbol

            # CASE: The symbol is not available in the package
            from ._terra_former import TerraFormer
            package_terra_former = TerraFormer(filename=package_init_filename)
            package_import_symbols = {i.GetToken() : i for i in package_terra_former.symbols}
            init_import_symbol = package_import_symbols.get(working_token)
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
            started = False
            cumulative_len = 0
            symbols_count = 0
            for i_leaf in cls._WalkLeafs(node):
                # TODO: BEN-28: [terraformer] Consider the EOL prefix in the cumulative_len, since it can contain comments
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
            children += [Node(pygram.python_symbols.import_as_names, name_leafs)]

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
            if '@terraforming:last-import' in symbol.comment or '@terraformer:last-import' in symbol.comment:
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
        for i_symbol in symbols:
            symbol = GetRefactoredImportSymbol(i_symbol, refactor)

            if filename and os.path.basename(filename) != '__init__' + cls.PYTHON_EXT:
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
            result.append(GenerateImportFromNode(i_prefix, sorted(i_symbols), indent, i_comment))

        # Generates "import X" statements
        for _sort_index, i_symbol in sorted(import_names):
            result.append(GenerateImportNode(i_symbol, indent, i_symbol.comment))

        return result

    @classmethod
    def _WalkLeafs(cls, node):
        from lib2to3.pytree import Leaf

        if isinstance(node, Leaf):
            yield node
        else:
            for i_child in node.children:
                for j_leaf in cls._WalkLeafs(i_child):
                    yield j_leaf
