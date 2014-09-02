

class ASTError(Exception):
    pass


def is_leaf_of_type(leaf, *types):
    from lib2to3.pytree import Leaf

    return isinstance(leaf, Leaf) and leaf.type in types


def is_node_of_type(node, *types):
    from lib2to3 import pytree
    from lib2to3.pytree import Node

    return isinstance(node, Node) and pytree.type_repr(node.type) in types


def leaf_value(leaf):
    return leaf.value


def remove_commas(nodes):
    from lib2to3.pgen2 import token

    def isnt_comma(node):
        return not is_leaf_of_type(node, token.COMMA)
    return filter(isnt_comma, nodes)


def remove_defaults(nodes):
    from lib2to3.pgen2 import token

    ignore_next = False
    for node in nodes:
        if ignore_next is True:
            ignore_next = False
            continue
        if is_leaf_of_type(node, token.EQUAL):
            ignore_next = True
            continue
        yield node


def derive_class_name(node):
    return str(node).strip()


def derive_class_names(node):
    if node is None:
        return []
    elif is_node_of_type(node, 'arglist'):
        return map(derive_class_name, remove_commas(node.children))
    else:
        return [derive_class_name(node)]


def derive_argument(node):
    from lib2to3.pgen2 import token

    if is_leaf_of_type(node, token.NAME):
        return node.value
    elif is_node_of_type(node, 'tfpdef'):
        return tuple(
            map(
                derive_argument,
                remove_commas(node.children[1].children)
            )
        )


def derive_arguments_from_typedargslist(typedargslist):
    from lib2to3.pgen2 import token

    prefix = ''
    for node in remove_defaults(remove_commas(typedargslist.children)):
        if is_leaf_of_type(node, token.STAR):
            prefix = '*'
        elif is_leaf_of_type(node, token.DOUBLESTAR):
            prefix = '**'
        elif prefix:
            yield prefix + derive_argument(node)
            prefix = ''
        else:
            yield derive_argument(node)


def derive_arguments(node):
    if node == []:
        return []
    elif is_node_of_type(node, 'typedargslist'):
        return list(derive_arguments_from_typedargslist(node))
    else:
        return [derive_argument(node)]


def derive_import_name(node):
    from lib2to3.pgen2 import token

    if is_leaf_of_type(node, token.NAME, token.STAR):
        return node.value
    elif is_node_of_type(node, 'dotted_as_name', 'import_as_name'):
        return (derive_import_name(node.children[0]),
                derive_import_name(node.children[2]))
    elif is_node_of_type(node, 'dotted_name'):
        return "".join(map(leaf_value, node.children))
    elif node is None:
        return
    else:
        raise ASTError("derive_import_name: unknown node type: %r." % node)


def derive_import_names(node):
    if node is None:
        return None
    elif is_node_of_type(node, 'dotted_as_names', 'import_as_names'):
        return map(
            derive_import_name,
            remove_commas(node.children)
        )
    else:
        return [derive_import_name(node)]


class ASTVisitor(object):
    DEFAULT_PATTERNS = [
        ('_visit_all', "file_input< nodes=any* >"),
        ('_visit_all', "suite< nodes=any* >"),
        ('_visit_class', "body=classdef< 'class' name=NAME ['(' bases=any ')'] ':' any >"),
        ('_visit_function', "body=funcdef< 'def' name=NAME parameters< '(' [args=any] ')' > ':' any >"),
        ('_visit_import',
            "body=import_name< 'import' names=any > | "
            "body=import_from< 'from' import_from=any 'import' names=any > | "
            "body=import_from< 'from' import_from=any 'import' '(' names=any ')' >"
        ),
    ]

    def __init__(self):
        self.patterns = []
        for method, pattern in self.DEFAULT_PATTERNS:
            self.register_pattern(method, pattern)

    def register_pattern(self, method, pattern):
        """Register method to handle given pattern.
        """
        from lib2to3.patcomp import compile_pattern

        self.patterns.append((method, compile_pattern(pattern)))

    def visit(self, tree):
        self.visit_start(tree)
        result = self._visit(tree)
        self.visit_end(tree)
        return result

    def visit_start(self, tree):
        pass

    def visit_end(self, tree):
        pass

    def visit_leaf(self, leaf):
        pass

    def visit_node(self, node):
        for method, pattern in self.patterns:
            results = {}
            if pattern.match(node, results):
                getattr(self, method)(results)
                break
        else:
            # For unknown nodes simply descend to their list of children.
            self._visit(node.children)

    def visit_class(self, name, bases, body):
        self._visit(body.children)

    def visit_function(self, name, args, body):
        self._visit(body.children)

    def visit_import(self, names, import_from, body):
        ''

    def _visit(self, tree):
        """Main entry point of the ASTVisitor class.
        """
        from lib2to3.pytree import Leaf, Node

        if isinstance(tree, Leaf):
            self.visit_leaf(tree)
        elif isinstance(tree, Node):
            self.visit_node(tree)
        elif isinstance(tree, list):
            for subtree in tree:
                self._visit(subtree)
        else:
            raise ASTError("Unknown tree type: %r." % tree)

    def _visit_all(self, results):
        self._visit(results['nodes'])

    def _visit_class(self, results):
        self.visit_class(
            name=results['name'].value,
            bases=derive_class_names(results.get('bases')),
            body=results['body']
        )

    def _visit_function(self, results):
        self.visit_function(
            name=results['name'].value,
            args=derive_arguments(results.get('args', [])),
            body=results['body']
        )

    def _visit_import(self, results):
        self.visit_import(
            names=derive_import_names(results['names']),
            import_from=derive_import_name(results.get('import_from')),
            body=results['body']
        )
