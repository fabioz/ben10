'''
Patches and fixes for lib2to3
'''

#===================================================================================================
# Replace lib2to3.pgen2.pgen.generate_grammar to avoid depending on external file (Grammar.txt)
#===================================================================================================
import lib2to3.pgen2.pgen

# This is the same as Grammar.txt, reproduced here to avoid dependency to external file.
GRAMMAR = '''
# Grammar for 2to3. This grammar supports Python 2.x and 3.x.

# Note:  Changing the grammar specified in this file will most likely
#        require corresponding changes in the parser module
#        (../Modules/parsermodule.c).  If you can't make the changes to
#        that module yourself, please co-ordinate the required changes
#        with someone who can; ask around on python-dev for help.  Fred
#        Drake <fdrake@acm.org> will probably be listening there.

# NOTE WELL: You should also follow all the steps listed in PEP 306,
# "How to Change Python's Grammar"

# Commands for Kees Blom's railroad program
#diagram:token NAME
#diagram:token NUMBER
#diagram:token STRING
#diagram:token NEWLINE
#diagram:token ENDMARKER
#diagram:token INDENT
#diagram:output\input python.bla
#diagram:token DEDENT
#diagram:output\textwidth 20.04cm\oddsidemargin  0.0cm\evensidemargin 0.0cm
#diagram:rules

# Start symbols for the grammar:
#    file_input is a module or sequence of commands read from an input file;
#    single_input is a single interactive statement;
#    eval_input is the input for the eval() and input() functions.
# NB: compound_stmt in single_input is followed by extra NEWLINE!
file_input: (NEWLINE | stmt)* ENDMARKER
single_input: NEWLINE | simple_stmt | compound_stmt NEWLINE
eval_input: testlist NEWLINE* ENDMARKER

decorator: '@' dotted_name [ '(' [arglist] ')' ] NEWLINE
decorators: decorator+
decorated: decorators (classdef | funcdef)
funcdef: 'def' NAME parameters ['->' test] ':' suite
parameters: '(' [typedargslist] ')'
typedargslist: ((tfpdef ['=' test] ',')*
                ('*' [tname] (',' tname ['=' test])* [',' '**' tname] | '**' tname)
                | tfpdef ['=' test] (',' tfpdef ['=' test])* [','])
tname: NAME [':' test]
tfpdef: tname | '(' tfplist ')'
tfplist: tfpdef (',' tfpdef)* [',']
varargslist: ((vfpdef ['=' test] ',')*
              ('*' [vname] (',' vname ['=' test])*  [',' '**' vname] | '**' vname)
              | vfpdef ['=' test] (',' vfpdef ['=' test])* [','])
vname: NAME
vfpdef: vname | '(' vfplist ')'
vfplist: vfpdef (',' vfpdef)* [',']

stmt: simple_stmt | compound_stmt
simple_stmt: small_stmt (';' small_stmt)* [';'] NEWLINE
small_stmt: (expr_stmt | print_stmt  | del_stmt | pass_stmt | flow_stmt |
             import_stmt | global_stmt | exec_stmt | assert_stmt)
expr_stmt: testlist_star_expr (augassign (yield_expr|testlist) |
                     ('=' (yield_expr|testlist_star_expr))*)
testlist_star_expr: (test|star_expr) (',' (test|star_expr))* [',']
augassign: ('+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' |
            '<<=' | '>>=' | '**=' | '//=')
# For normal assignments, additional restrictions enforced by the interpreter
print_stmt: 'print' ( [ test (',' test)* [','] ] |
                      '>>' test [ (',' test)+ [','] ] )
del_stmt: 'del' exprlist
pass_stmt: 'pass'
flow_stmt: break_stmt | continue_stmt | return_stmt | raise_stmt | yield_stmt
break_stmt: 'break'
continue_stmt: 'continue'
return_stmt: 'return' [testlist]
yield_stmt: yield_expr
raise_stmt: 'raise' [test ['from' test | ',' test [',' test]]]
import_stmt: import_name | import_from
import_name: 'import' dotted_as_names
import_from: ('from' ('.'* dotted_name | '.'+)
              'import' ('*' | '(' import_as_names ')' | import_as_names))
import_as_name: NAME ['as' NAME]
dotted_as_name: dotted_name ['as' NAME]
import_as_names: import_as_name (',' import_as_name)* [',']
dotted_as_names: dotted_as_name (',' dotted_as_name)*
dotted_name: NAME ('.' NAME)*
global_stmt: ('global' | 'nonlocal') NAME (',' NAME)*
exec_stmt: 'exec' expr ['in' test [',' test]]
assert_stmt: 'assert' test [',' test]

compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef | classdef | decorated
if_stmt: 'if' test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
while_stmt: 'while' test ':' suite ['else' ':' suite]
for_stmt: 'for' exprlist 'in' testlist ':' suite ['else' ':' suite]
try_stmt: ('try' ':' suite
           ((except_clause ':' suite)+
        ['else' ':' suite]
        ['finally' ':' suite] |
       'finally' ':' suite))
with_stmt: 'with' with_item (',' with_item)*  ':' suite
with_item: test ['as' expr]
with_var: 'as' expr
# NB compile.c makes sure that the default except clause is last
except_clause: 'except' [test [(',' | 'as') test]]
suite: simple_stmt | NEWLINE INDENT stmt+ DEDENT

# Backward compatibility cruft to support:
# [ x for x in lambda: True, lambda: False if x() ]
# even while also allowing:
# lambda x: 5 if x else 2
# (But not a mix of the two)
testlist_safe: old_test [(',' old_test)+ [',']]
old_test: or_test | old_lambdef
old_lambdef: 'lambda' [varargslist] ':' old_test

test: or_test ['if' or_test 'else' test] | lambdef
or_test: and_test ('or' and_test)*
and_test: not_test ('and' not_test)*
not_test: 'not' not_test | comparison
comparison: expr (comp_op expr)*
comp_op: '<'|'>'|'=='|'>='|'<='|'<>'|'!='|'in'|'not' 'in'|'is'|'is' 'not'
star_expr: '*' expr
expr: xor_expr ('|' xor_expr)*
xor_expr: and_expr ('^' and_expr)*
and_expr: shift_expr ('&' shift_expr)*
shift_expr: arith_expr (('<<'|'>>') arith_expr)*
arith_expr: term (('+'|'-') term)*
term: factor (('*'|'/'|'%'|'//') factor)*
factor: ('+'|'-'|'~') factor | power
power: atom trailer* ['**' factor]
atom: ('(' [yield_expr|testlist_gexp] ')' |
       '[' [listmaker] ']' |
       '{' [dictsetmaker] '}' |
       '`' testlist1 '`' |
       NAME | NUMBER | STRING+ | '.' '.' '.')
listmaker: (test|star_expr) ( comp_for | (',' (test|star_expr))* [','] )
testlist_gexp: (test|star_expr) ( comp_for | (',' (test|star_expr))* [','] )
lambdef: 'lambda' [varargslist] ':' test
trailer: '(' [arglist] ')' | '[' subscriptlist ']' | '.' NAME
subscriptlist: subscript (',' subscript)* [',']
subscript: test | [test] ':' [test] [sliceop]
sliceop: ':' [test]
exprlist: (expr|star_expr) (',' (expr|star_expr))* [',']
testlist: test (',' test)* [',']
dictsetmaker: ( (test ':' test (comp_for | (',' test ':' test)* [','])) |
                (test (comp_for | (',' test)* [','])) )

classdef: 'class' NAME ['(' [arglist] ')'] ':' suite

arglist: (argument ',')* (argument [',']
                         |'*' test (',' argument)* [',' '**' test]
                         |'**' test)
argument: test [comp_for] | test '=' test  # Really [keyword '='] test

comp_iter: comp_for | comp_if
comp_for: 'for' exprlist 'in' testlist_safe [comp_iter]
comp_if: 'if' old_test [comp_iter]

testlist1: test (',' test)*

# not used in grammar, but may appear in "node" passed from Parser to Compiler
encoding_decl: NAME

yield_expr: 'yield' [testlist]
'''

def generate_grammar(filename="Grammar.txt"):
    from StringIO import StringIO
    p = lib2to3.pgen2.pgen.ParserGenerator(filename, stream=StringIO(GRAMMAR))
    return p.make_grammar()
lib2to3.pgen2.pgen.generate_grammar = generate_grammar


#===================================================================================================
# Normal Imports
#===================================================================================================
from lib2to3.fixer_base import BaseFix
from lib2to3.pytree import Leaf
from lib2to3.refactor import FixerError, RefactoringTool
import operator


#===================================================================================================
# MyRefactoringTool
#===================================================================================================
class MyRefactoringTool(RefactoringTool):
    '''
    Some small changes in code in order to work with our kind of transformations.
    '''

    def traverse_by(self, fixers, traversal):
        '''
        Override to make a copy of nodes before traversing them.
        '''
        if not fixers:
            return
        nodes = [i for i in traversal]  # <-- our change
        for node in nodes:
            for fixer in fixers[node.type]:
                results = fixer.match(node)
                if results:
                    new = fixer.transform(node, results)
                    if new is not None:
                        node.replace(new)
                        node = new

    def get_fixers(self):
        '''
        Override to handle fixers as classes.
        '''
        pre_order_fixers = []
        post_order_fixers = []
        for fix_mod_path in self.fixers:
            assert issubclass(fix_mod_path, BaseFix)
            fix_name = fix_mod_path.__name__
            fixer = fix_mod_path(self.options, self.fixer_log)
            if (
                fixer.explicit
                and self.explicit is not True
                and fix_mod_path not in self.explicit
            ):
                self.log_message("Skipping implicit fixer: %s", fix_name)
                continue

            self.log_debug("Adding transformation: %s", fix_name)
            if fixer.order == "pre":
                pre_order_fixers.append(fixer)
            elif fixer.order == "post":
                post_order_fixers.append(fixer)
            else:
                raise FixerError("Illegal fixer order: %r" % fixer.order)

        key_func = operator.attrgetter("run_order")
        pre_order_fixers.sort(key=key_func)
        post_order_fixers.sort(key=key_func)
        return (pre_order_fixers, post_order_fixers)



#===================================================================================================
# WalkLeafs
#===================================================================================================
def WalkLeafs(node):
    if isinstance(node, Leaf):
        yield node
    else:
        for i_child in node.children:
            for j_leaf in WalkLeafs(i_child):
                yield j_leaf


#===================================================================================================
# ParseString
#===================================================================================================
def ParseString(s):
    from lib2to3 import pygram, pytree
    from lib2to3.pgen2 import driver
    from lib2to3.refactor import _detect_future_features

    # Selects the appropriate grammar depending on the usage of "print_function" future feature.
    future_features = _detect_future_features(s)
    if 'print_function' in future_features:
        grammar = pygram.python_grammar_no_print_statement
    else:
        grammar = pygram.python_grammar

    driver_ = driver.Driver(grammar, pytree.convert)
    return driver_.parse_string(s, True)



def GetNodeLineNumber(node):
    parent = node
    while parent:
        if hasattr(parent, 'lineno'):
            return parent.lineno
        parent = parent.parent
    return 0
