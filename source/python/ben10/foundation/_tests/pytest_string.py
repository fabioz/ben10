from ben10.foundation.string import Dedent, Indent, SafeSplit



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
        Coverage 100%

        TODO: BEN-21: Strange behavior on Dedent when mixing tabs and spaces.
        '''
        string = Dedent(
            '''
                alpha
            \tbravo
            '''
        )
        assert string == '                alpha\n            \tbravo'


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

