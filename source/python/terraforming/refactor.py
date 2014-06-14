'''
This module provides instruments to perform code refactoring.
'''
from ._lib2to3 import MyRefactoringTool, ParseString, WalkLeafs
from .refactor_imports import ReorganizeImports
from ben10.filesystem import CreateFile, EOL_STYLE_UNIX, GetFileContents, GetFileLines
from ben10.foundation.reraise import Reraise
from copy import copy, deepcopy
from lib2to3.fixer_base import BaseFix
import re



#===================================================================================================
# TerraForming
#===================================================================================================
class TerraForming(object):
    '''
    Python refactoring tool class. Including the following:
        * Imports organizer with optional imports renaming.
        * Fix division-lines
        * Convert to py.test

    import-symbols:
        The symbol being imported and how it is being imported. This is a 2-tuple with the values:
            [0]: Import mode. Either "from" or "import"
            [1]: The imported symbol.
        Ex:
            "from etk11.foundation.bunch import Bunch"
            import-symbol:
                ("from", "etk11.foundation.bunch.Bunch")

            "import etk11.foundation.bunch"
            import-symbol:
                ("import", "etk11.foundation.bunch")

    import-lines:
        The import statement in a single line
    '''
    PAGE_WIDTH = 100
    TAB_WIDTH = 4


    # Public API ===================================================================================

    def ConvertToPytest(self, filename):
        '''
        Converts the given filename to a py.test.

        :param str filename:
        '''
        try:
            input_ = GetFileContents(filename)
            output = self._ConvertToPytestImpl(input_)
            CreateFile(filename, output, eol_style=EOL_STYLE_UNIX)
        except Exception, e:
            Reraise(e, "While processing file: %s" % filename)


    def FixDivisionLines(self, filename):
        '''
        Fix the width of all "division-lines" found.
        A division-line is a commented line containing only equal signs (=) or dashes (-)

        :param str filename:
        '''
        try:
            lines = GetFileLines(filename)
            lines = self._FixDivisionLinesImpl(lines)
            content = '\n'.join(lines)
            CreateFile(filename, content, eol_style=EOL_STYLE_UNIX)
        except Exception, e:
            Reraise(e, "While processing file: %s" % filename)


    def RightTrimSpaces(self, filename):
        '''
        Remove any spaces on the end of each line of the given file.

        :param str filename:
        '''
        try:
            lines = GetFileLines(filename)
            lines = self._RightTrimSpacesImpl(lines)
            content = '\n'.join(lines)
            CreateFile(filename, content, eol_style=EOL_STYLE_UNIX)
        except Exception, e:
            Reraise(e, "While processing file: %s" % filename)


    def ReorganizeImports(self, filename, refactor={}, python_path=''):
        '''
        Reorganizes all import statements in the given filename, optionally performing a "move"
        refactoring.

        This is the main API for TerraForming.

        :param str filename:
            The file to perform the reorganization/refactoring. Note that the file is always
            rewritten by this algorithm, no backups. It's assumed that you're using a version
            control system.

        :param dict refactor:
            A dictionary mapping the moved symbols path. The keys are the current path, the values
            are the new path.
            Ex:
                {
                    'coilbi50.basic.Bunch' : 'etk11.foundation.bunch.Bunch',
                    'coilbi50.basic.interfaces' : 'etk11.interfaces',
                }

            Note that we do not support symbol renaming, only move. This means that the last part of
            the string must be the same. In the example, "Bunch" and "interface".

        :param str python_path:
            An alternative python_path for testing.

        :return boolean:
            Returns True if the file was changed.
        '''
        try:
            changed, output = ReorganizeImports(filename, refactor=refactor, python_path=python_path)
            CreateFile(filename, output, eol_style=EOL_STYLE_UNIX)
            return changed
        except Exception, e:
            Reraise(e, 'On TerraForming.ReorganizeImports with filename: %s' % filename)


    def CheckImports(self, filename, source_code=None, refactor={}, python_path=''):
        '''
        Checks if the file would be changed by ReorganizeImports.

        :return boolean:
            Returns True if the file would be changed.
            The file is never changed by this algorithm, just checked.

        .. seealso:: ReorganizeImports
        '''
        try:
            changed, _output = ReorganizeImports(
                filename,
                source_code=source_code,
                refactor=refactor,
                python_path=python_path)
            return changed
        except Exception, e:
            Reraise(e, 'On TerraForming.CheckImports with filename: %s' % filename)


    def FixAll(self, filename):
        '''
        Perform all format fixes, including:
            - RTrim
            - TABs
            - EOLs

        :param str filename:
            The file to perform the reorganization/refactoring. Note that the file is always
            rewritten by this algorithm, no backups. It's assumed that you're using a version
            control system.

        :return boolean:
            Returns True if the file was changed.
        '''
        try:
            input_lines = GetFileLines(filename)
            lines = self._RightTrimSpacesImpl(input_lines)
            lines = self._FixTabsImpl(lines)
            content = '\n'.join(lines)
            CreateFile(filename, content, eol_style=EOL_STYLE_UNIX)
            return input_lines != lines
        except Exception, e:
            Reraise(e, "On TerraForming.FixAll with filename: %s" % filename)


    # Implementation ===============================================================================

    # Fix division lines in files, making them obey the page-width.

    def _FixDivisionLinesImpl(self, lines, page_width=PAGE_WIDTH):
        '''
        Fix the width of the division lines in a python module.

        :param list(str) lines:
            Lines of a python module to refactor.

        :return list(str):
            Refactored lines for the given python module (lines)
        '''
        r_lines = []
        for i_line in lines:
            striped_line = i_line.lstrip()
            if striped_line.startswith('#'):
                indent_width = len(i_line) - len(striped_line)
                line_width = page_width - (indent_width + 1)
                i_line, _count = re.subn('#([ =]+)$', '#' + '=' * line_width, i_line)
                i_line, _count = re.subn('#([ -]+)$', '#' + '-' * line_width, i_line)
            r_lines.append(i_line)
        return r_lines


    def _RightTrimSpacesImpl(self, lines):
        '''
        Remove spaces from the right side of each line.

        :param list(str) lines:
            Input lines.

        :return list(str):
            Modified lines.
        '''
        return [i.rstrip(' \t') for i in lines]


    def _FixTabsImpl(self, lines, tab_width=4):
        '''
        Replaces TABS with SPACES.

        :param list(str) lines:
            Input lines.

        :return list(str):
            Modified lines.
        '''
        return [i.replace('\t', ' ' * tab_width) for i in lines]


    @staticmethod
    def GetCodeTree(code):
        '''
        Obtain the lib2to3 node from the given code (str).

        * Handles the necessary of EOL at the end of the code.

        :param str code:
            Python code (multiline)

        :return:
            Parsed lib2to3 syntax tree.
        '''
        code += '\n' # Append EOL so ParseString works
        try:
            result = ParseString(code)
        except Exception, e:
            Reraise(e, 'While parsing code::\n%s' % code)

        # Find the added EOL in the resulting tree
        last_eol_leaf = None
        for i in WalkLeafs(result.children[0]):
            if i.value == '\n':
                last_eol_leaf = i
        last_eol_leaf.remove()

        return result


    @staticmethod
    def FixIndentation(tree, first_line_prefix, next_lines_prefix):
        '''
        Fix indentation of the given lib2to3 syntax tree.

        Sometimes, after we replace exiting code with our code we need to fix the indentation of the
        new code.

        TODO: EDEN-334: Fix indentation after "to_pytest" refactoring
        This is a work in progress. Currently we are not correctly generating indented code when the
        original code has multi-lines.

        :param lib2to3.Node tree:
            Syntax tree to fix the indentation.

        :param first_line_prefix:
            The prefix (indentation/comments) for the first line.

        :param next_lines_prefix:
            The prefix for the next lines.
        '''
        # Fist line
        tree.prefix = first_line_prefix

        # Next lines
        if next_lines_prefix and '\n' in str(tree):
            prefix_next = ''
            skip = True
            for i_leaf in WalkLeafs(tree.children[0]):
                # Skips the first node to avoid re-applying the prefix
                if skip:
                    skip = False
                    continue

                # Other times the indentation is in the node following an EOL (first statement of a
                # function)
                if i_leaf.value == '\n':
                    prefix_next = True
                    continue
                if prefix_next:
                    i_leaf.prefix = next_lines_prefix
                    prefix_next = False
                    continue


    def _ConvertToPytestImpl(self, source_code, refactor={}):

        class ConvertPyTestFix(BaseFix):

            refactorings = [
                dict(
                    find='self.assertEqual(*)',
                    replace='assert $1 == $2',
                ),
                dict(
                    find='self.assertTrue(*)',
                    replace='assert $1 == True',
                ),
                dict(
                    find='self.assertRaises(*)',
                    replace='with pytest.raises($1):\n    $2($3+)',
                ),
                dict(
                    find='self.GetDataFilename(*)',
                    replace='embed_data[$1]',
                    func_params=['embed_data'],
                    pytest_plugin=['coilib50._pytest.fixtures'],
                ),
                dict(
                    find='self.GetDataDirectory(*)',
                    replace='embed_data.GetDataDirectory($0)',
                    func_params=['embed_data'],
                    pytest_plugin=['coilib50._pytest.fixtures'],
                ),
            ]

            CHANGES = {
                'self.assertEqual' : dict(assert_='=='),
                'self.assertEquals' : dict(assert_='=='),
                'self.assertNotEqual' : dict(assert_='!='),
                'self.assertSetEqual' : dict(assert_='==', wrapper='set(%s)'),
                'self.assertIsSame' : dict(assert_='is'),
                'self.assertIn' : dict(assert_='in'),
                'self.assertTrue' : dict(assert_=None, wrapper='%s == True'),
                'self.assertFalse' : dict(assert_=None, wrapper='%s == False'),
                'self.assert_' : dict(assert_=None, wrapper='%s'),

                'self.assertRaises' : dict(replace='with pytest.raises(arg1):\n    arg2(args3)'),
                'self.ExecuteCommandLineTestsFromFile' : dict(replace='command_line_executer.ExecuteCommandLineTestsFromFile(args1)'),

                'self.GetDataDirectory' : dict(replace='embed_data.GetDataDirectory()', fixtures=['embed_data']),
                'self.GetDataFilename' : dict(replace='embed_data[arg1]', fixtures=['embed_data']),
            }


            def GetArgNodes(self, nodes):
                for i_node in nodes:
                    if i_node.type == 12 and i_node.value in (',',):
                        continue
                    yield i_node


            def start_tree(self, tree, filename):
                self.fixtures = set()
                return BaseFix.start_tree(self, tree, filename)


            def match(self, node):

                # Identify the Test class
                if node.type == self.syms.classdef and node.children[1].value == 'Test':
                    return self.syms.classdef

                # Identify the test function
                if node.type == self.syms.funcdef and node.children[1].value.startswith("test"):
                    return self.syms.funcdef

                # Identify "self.XXX" calls...
                # For now, "self.XXX" is is the only kind of replacements we do
                if node.type == self.syms.power and node.children[0].value == 'self':
                    funccall = '%s.%s' % (node.children[0].value, node.children[1].children[1])
                    changes = self.CHANGES.get(funccall)
                    if changes is None:
                        return False

                    args_node = node.children[2].children[1]
                    args_node2 = deepcopy(node.children[2].children[1])
                    args_node2.remove()
                    if len(node.children[2].children) < 3:
                        args = []
                    elif args_node.type == self.syms.arglist:
                        args = [i for i in self.GetArgNodes(args_node.children)]
                    else:
                        args = [args_node]
                    for i in args:
                        i.remove()

                    for i in changes.get('fixtures', []):
                        self.fixtures.add(i)

                    return dict(
                        args_node=args_node2,
                        args=args,
                        changes=changes,
                    )


            def transform(self, node, results):

                def FindPrefix(node):

                    def FindIndentation(text):
                        text = text.lstrip('\n')
                        count = len(text) - len(text.lstrip(' '))
                        return ' ' * count

                    result = node.prefix
                    if result == '':
                        # Handles the indentation for the first statement of a function, that is not
                        # in the first statement node prefix, but in a leaf node of type "5"

                        # parent: Finds the 'suite' parent, a function definition.
                        parent = node.parent
                        while parent is not None:
                            if parent.type == self.syms.suite:
                                break
                            parent = parent.parent
                        else:
                            parent = None

                        if parent:
                            # indent_leaf: finds the leaf containing the indentation.
                            for indent_leaf in parent.children:
                                if indent_leaf.type == 5:
                                    break
                            else:
                                indent_leaf = None

                            # result: Finally, obtain the indentation from type-5 leaf value.
                            if indent_leaf:
                                result = indent_leaf.value

                    return FindIndentation(result)

                # Handle Test class declaration:
                # * Removes any derived class
                if results == self.syms.classdef:
                    process = False
                    for i_child in node.children[:]:
                        if process:
                            if i_child.type < 256 and i_child.value == ')':
                                i_child.remove()
                                break

                            i_child.remove()
                            continue

                        if i_child.type < 256 and i_child.value == '(':
                            i_child.remove()
                            process = True
                            continue
                    return

                # Handle test functions
                # * Adds any fixtures requested by pytest conversion.
                # * Note that funcdef is matched AFTER all internal code is matched, so this is
                #   called AFTER all method calls were processed.
                if results == self.syms.funcdef:
                    # TODO: EDEN-335: [refactor.to_pytest] Handle the addition of needed fixtures
                    # args = [i.value for i in WalkLeafs(node.children[2])]
                    return

                next_line_prefix = FindPrefix(node)

                # dd: Create a replacement dict from the original information from the original
                # code.
                dd = {}
                dd['args_node'] = results['args_node']
                dd.update(results['changes'])
                wrapper = results['changes'].get('wrapper', '%s')
                multiline = False
                for i, i_arg in enumerate(results['args']):
                    multiline = multiline or '\n' in i_arg.prefix
                    i_arg.prefix = ''
                    dd['arg%d' % (i + 1)] = i_arg
                    dd['p%d' % (i + 1)] = wrapper % i_arg

                    nodes = deepcopy(results['args_node'])
                    nodes.children = nodes.children[i * 2:]
                    if nodes.children:
                        nodes.children[0].prefix = ''
                    dd['args%d' % (i + 1)] = nodes

                # new_code: A string containing the new replacement code.
                if 'assert_' in dd:
                    if dd['assert_'] is None:
                        new_code = 'assert %(p1)s' % dd
                    else:
                        new_code = 'assert %(p1)s %(assert_)s %(p2)s' % dd
                        if multiline:
                            new_code = 'assert (\n    %(p1)s\n    %(assert_)s %(p2)s\n)' % dd
                elif 'wrapper' in dd:
                    if 'p1' in dd:
                        new_code = dd['p1']
                    else:
                        new_code = dd['wrapper'] % ''
                elif 'replace' in dd:
                    new_code = dd['replace']

                # new_node: A new lib2to3 node representing the new-code
                new_node = TerraForming.GetCodeTree(new_code)

                if 'replace' in dd:
                    for i_leaf in WalkLeafs(new_node):
                        if i_leaf.value in ('arg1', 'arg2', 'arg3'):
                            node_ = copy(dd[i_leaf.value])
                            node_.prefix = i_leaf.prefix
                            i_leaf.replace(node_)

                        if i_leaf.value in ('args1', 'args2', 'args3'):
                            new_value = dd.get(i_leaf.value)
                            if new_value is None:
                                # If we don't have ARGS we delete the parent, which olds "()" for
                                # the function call.
                                # CASE: self.assertRaises(E, F) # note that there is no third+ parameter
                                i_leaf.parent.remove()
                            else:
                                node_ = copy(new_value)
                                i_leaf.replace(node_)

                TerraForming.FixIndentation(new_node, node.prefix, next_lines_prefix=next_line_prefix)

                if True:
                    print '=' * 80
                    print str(node)
                    print '-' * 80
                    print "1-PREFIX: '%s'" % node.prefix
                    print "N-PREFIX: '%s'" % next_line_prefix
                    print '-' * 80
                    print str(new_code)
                    print '-' * 80
                    print str(new_node)

                node.replace(new_node)

        try:
            tree = ParseString(source_code)
        except Exception as exception:
            Reraise(exception, 'While processing source::\n%s\n---\n' % source_code)

        options = {'isymbols' : {}}

        rt = MyRefactoringTool([ConvertPyTestFix], options=options)
        rt.refactor_tree(tree, 'ConvertPyTestFix')

        return str(tree)
