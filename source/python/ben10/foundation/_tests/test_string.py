# coding: UTF-8
from __future__ import unicode_literals
from ben10.foundation.string import Dedent, Indent, SafeSplit, ToUnicode, MatchAny
from mock import patch
import locale
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testDedent0(self):
        string = Dedent('oneline')
        assert string == 'oneline'


    def testDedent1(self):
        string = Dedent(
            '''
            oneline
            '''
        )
        assert string == 'oneline'


    def testDedent2(self):
        string = Dedent(
            '''
            oneline
            twoline
            '''
        )
        assert string == 'oneline\ntwoline'


    def testDedent3(self):
        string = Dedent(
            '''
            oneline
                tabbed
            '''
        )
        assert string == 'oneline\n    tabbed'


    def testDedent4(self):
        string = Dedent(
            '''
            oneline
                tabbed
            detabbed
            '''
        )
        assert string == 'oneline\n    tabbed\ndetabbed'


    def testDedent5(self):
        string = Dedent(
            '''
            oneline
            ''',
            ignore_first_linebreak=False
        )
        assert string == '\noneline'


    def testDedent6(self):
        string = Dedent(
            '''
            oneline
            ''',
            ignore_last_linebreak=False
        )
        assert string == 'oneline\n'


    def testDedent7(self):
        '''
        Test a string that has an 'empty line' with 4 spaces above indent level
        '''
        # Using a trick to avoid auto-format to remove the empty spaces.
        string = Dedent(
            '''
            line
            %s
            other_line
            ''' % '    '
        )
        assert string == 'line\n    \nother_line'


    def testDedent8(self):
        '''
        Test not the first line in the right indent.
        '''
        string = Dedent(
            '''
                alpha
              bravo
            charlie
            '''
        )
        assert string == '    alpha\n  bravo\ncharlie'


    def testDedent9(self):
        '''
        Test behavior when using \t at the start of a string. .. seealso:: BEN-21 @ JIRA
        '''
        string = Dedent(
            '''
                alpha
            \tbravo
            '''
        )
        assert string == '    alpha\n\tbravo'


    def testDedent10(self):
        '''
        Checking how Dedent handles empty lines at the end of string without parameters.
        '''
        string = Dedent(
            '''
            alpha
            '''
        )
        assert string == 'alpha'
        string = Dedent(
            '''
            alpha

            '''
        )
        assert string == 'alpha\n'
        string = Dedent(
            '''
            alpha


            '''
        )
        assert string == 'alpha\n\n'


    def testDedent11(self):
        '''
        Check calling Dedent more than once.
        '''
        string = Dedent(
            '''
            alpha
            bravo
            charlie
            '''
        )
        assert string == 'alpha\nbravo\ncharlie'
        string = Dedent(string)
        assert string == 'alpha\nbravo\ncharlie'
        string = Dedent(string)
        assert string == 'alpha\nbravo\ncharlie'


    def testIndent(self):
        assert Indent('alpha') == '    alpha'

        assert Indent('alpha', indent=2) == '        alpha'
        assert Indent('alpha', indentation='...') == '...alpha'

        # If the original text ended with '\n' the resulting text must also end with '\n'
        assert Indent('alpha\n') == '    alpha\n'

        # If the original text ended with '\n\n' the resulting text must also end with '\n\n'
        # Empty lines are not indented.
        assert Indent('alpha\n\n') == '    alpha\n\n'

        # Empty lines are not indented nor cleared.
        assert Indent('alpha\n  \ncharlie') == '    alpha\n  \n    charlie'

        # Empty lines are not indented nor cleared.
        assert Indent(['alpha', 'bravo']) == '    alpha\n    bravo\n'

        # Multi-line test.
        assert Indent('alpha\nbravo\ncharlie') == '    alpha\n    bravo\n    charlie'


    def testSafeSplit(self):
        assert SafeSplit('alpha', ' ') == ['alpha']
        assert SafeSplit('alpha bravo', ' ') == ['alpha', 'bravo']
        assert SafeSplit('alpha bravo charlie', ' ') == ['alpha', 'bravo', 'charlie']

        assert SafeSplit('alpha', ' ', 1) == ['alpha', '']
        assert SafeSplit('alpha bravo', ' ', 1) == ['alpha', 'bravo']
        assert SafeSplit('alpha bravo charlie', ' ', 1) == ['alpha', 'bravo charlie']

        assert SafeSplit('alpha', ' ', 1, default=9) == ['alpha', 9]
        assert SafeSplit('alpha bravo', ' ', 1, default=9) == ['alpha', 'bravo']
        assert SafeSplit('alpha bravo charlie', ' ', 1, default=9) == ['alpha', 'bravo charlie']

        assert SafeSplit('alpha', ' ', 2) == ['alpha', '', '']
        assert SafeSplit('alpha bravo', ' ', 2) == ['alpha', 'bravo', '']
        assert SafeSplit('alpha bravo charlie', ' ', 2) == ['alpha', 'bravo', 'charlie']

        assert SafeSplit('alpha:bravo:charlie', ':', 1) == ['alpha', 'bravo:charlie']
        assert SafeSplit('alpha:bravo:charlie', ':', 1, reversed=True) == ['alpha:bravo', 'charlie']

        assert SafeSplit('alpha', ':', 1, []) == ['alpha', []]
        assert SafeSplit('alpha', ':', 1, [], reversed=True) == [[], 'alpha']


    def testFormatIterable(self):
        from ben10.foundation.string import FormatIterable

        item1 = 'a'
        item2 = 'b'
        my_list = [item1, item2]

        assert FormatIterable(my_list) == "['a', 'b']"


    @patch.object(locale, 'getpreferredencoding', autospec=True, return_value='UTF-8')
    def testToUnicode(self, *args):
        value = RuntimeError('Não'.encode('cp1252'))

        result = ToUnicode(value)
        assert result == 'N�o'

        result = ToUnicode(value, error_strategy='ignore')
        assert result == 'No'

        with pytest.raises(UnicodeDecodeError):
            ToUnicode(value, error_strategy='strict')

        result = ToUnicode(value, 'cp1252')
        assert result == 'Não'


    def testMatchAny(self):
        assert MatchAny('alpha', ['alpha', 'bravo']) == True
        assert MatchAny('bravo', ['alpha', 'bravo']) == True
        assert MatchAny('charlie', ['alpha', 'bravo']) == False
        assert MatchAny('one:alpha', ['one:.*',]) == True
        assert MatchAny('two:alpha', ['one:.*',]) == False
