from __future__ import unicode_literals
from io import StringIO
from namespace import (CantFindBestMatchException, InvalidNamespaceKeyName, Namespace,
    NamespaceKeyError, NamespaceValue)
from namespace.namespace_types import LIST, MergedTypesDontMatchException, PATH, PATHLIST, STRING
import os
import pytest
import sys



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testCopy(self):
        # Create a namespace with some stuff in it
        ns = Namespace()
        ns['key'] = 'value'
        ns['flag:key2'] = 'value2'
        ns.SetFlag('flag')
        ns['@key'] = callback = lambda *args, **kwargs: None

        from copy import copy
        ns2 = copy(ns)

        # Make sure they have the same values
        assert ns2['key'] == 'value'
        assert ns['key'] == 'value'

        assert ns2['key2'] == 'value2'
        assert ns['key2'] == 'value2'

        assert ns2.GetFlags() == ['flag']
        assert ns.GetFlags() == ['flag']

        assert ns2._callbacks == {'key' : callback}
        assert ns._callbacks == {'key' : callback}

        # Make some changes to copy
        ns2['key'] = 'new_value'
        ns2.SetFlag('other_flag')
        ns2['@key'] = new_callback = lambda *args, **kwargs: None

        # Test values
        assert ns2['key'] == 'new_value'
        assert ns['key'] == 'value'

        assert ns2['key2'] == 'value2'
        assert ns['key2'] == 'value2'

        assert ns2.GetFlags() == ['flag', 'other_flag']
        assert ns.GetFlags() == ['flag']

        assert ns2._callbacks == {'key' : new_callback}
        assert ns._callbacks == {'key' : callback}


    def testOverridingVariables(self):
        ns = Namespace()

        ns['flag:key'] = 'value_with_flag'

        ns.SetFlag('flag')
        assert ns['key'] == 'value_with_flag'

        # Since we still have a flag active, that value is chosen
        ns['key'] = 'value_without_flag'
        assert ns['key'] == 'value_with_flag'

        # Using a special syntax, we can override flag values
        ns['*:key'] = 'overriding_flag'
        assert ns['key'] == 'overriding_flag'


    def testValidVariableNames(self):
        ns = Namespace()

        ns['value'] = 'this is fine'
        ns['flag:value'] = 'this is fine'
        ns[':declaring_flag'] = 'this is fine'

        with pytest.raises(InvalidNamespaceKeyName):
            ns.__setitem__('', 'this will not work')
        with pytest.raises(InvalidNamespaceKeyName):
            ns.__setitem__(':', 'this will not work')
        with pytest.raises(InvalidNamespaceKeyName):
            ns.__setitem__('flag:', 'this will not work')


    def testMergeWithDifferentTypes(self):
        ns = Namespace()

        ns['key'] = LIST('key_no_flag')
        ns['flag:key'] = PATH('key_with_flag')

        # Using explicit flags would mean both keys have 1 positive match each
        # This must raise an error
        with pytest.raises(MergedTypesDontMatchException):
            ns.GetValue('key', explicit_flags=('flag', 'other_flag'))


    def testFlagTie(self):
        ns = Namespace()

        ns['other_flag:key'] = 'key_no_flag'
        ns['flag:key'] = 'key_with_flag'

        # Using explicit flags would mean both keys have 1 positive match each
        # This must raise an error
        with pytest.raises(CantFindBestMatchException):
            ns.GetValue('key', explicit_flags=('flag', 'other_flag'))



    def testMergeCoincidingFlags(self):
        ns = Namespace()

        # Test with string, the best match must prevail
        ns['key'] = 'key_no_flag'
        ns['flag:key'] = 'key_with_flag'

        # No flags, only one value
        assert (
            ns.GetValue('key', as_string=True)
            == 'key_no_flag'
        )


        assert (
            ns.GetValue('key', explicit_flags=('flag',), as_string=True)
            == 'key_with_flag'
        )

        # Now using mergeable types
        ns['key'] = LIST('key_no_flag')
        ns['flag:key'] = LIST('key_with_flag')

        assert (
            ns.GetValue('key')
            == LIST('key_no_flag')
        )

        assert (
            ns.GetValue('key', explicit_flags=('flag',))
            == LIST('key_no_flag', 'key_with_flag')
        )

        # Also, paths
        ns['key'] = PATHLIST('path/no_flag')
        ns['flag:key'] = PATHLIST('path/flag')

        assert (
            ns.GetValue('key')
            == PATHLIST('path/no_flag')
        )

        assert (
            ns.GetValue('key', explicit_flags=('flag',))
            == PATHLIST('path/no_flag', 'path/flag')
        )

        # Testing with negative flag
        ns['key'] = 'key_no_flag'
        ns['!fake_flag:key'] = 'key_with_negative_flag'

        assert ns.GetValue('key', as_string=True) == 'key_with_negative_flag'

        # Double negative flag
        ns['!other_fake_flag:!fake_flag:key'] = 'key_with_double_negative_flag'
        assert ns.GetValue('key', as_string=True) == 'key_with_double_negative_flag'



    def testOnMissingKeyCallback(self):
        ns = Namespace()

        self.missing_key = None
        self.abort_calls = 0
        def MyAbortCallback(missing_key):
            self.missing_key = missing_key
            self.abort_calls += 1
            return Namespace.ABORT

        self.continue_calls = 0
        def MyContinueCallback(missing_key):
            self.missing_key = missing_key
            self.continue_calls += 1
            ns.SetValue(self.missing_key, 'value')
            return Namespace.RETRY


        # Test with GetValue -----------------------------------------------------------------------
        # Try to access a non existing variable
        # The callback will tell it to abort, we should get an exception
        with pytest.raises(NamespaceKeyError):
            ns.GetValue('key', on_missing_callback=MyAbortCallback)
        assert self.abort_calls == 1
        assert self.missing_key == 'key'

        # Try to access a non existing variable
        # The callback will load the variable and tell the namespace to continue
        obtained = ns.GetValue(
            'key',
            as_string=True,
            on_missing_callback=MyContinueCallback
        )
        assert obtained == 'value'
        assert self.continue_calls == 1
        assert self.missing_key == 'key'


        # Test with Evaluate -----------------------------------------------------------------------
        # Try to access a non existing variable
        # The callback will tell it to abort, we should get an exception
        with pytest.raises(NamespaceKeyError):
            ns.Evaluate('`key_2`', on_missing_callback=MyAbortCallback)
        assert self.abort_calls == 2
        assert self.missing_key == 'key_2'

        # Try to access a non existing variable
        # The callback will load the variable and tell the namespace to continue
        obtained = ns.Evaluate('`key_2`', on_missing_callback=MyContinueCallback)

        assert obtained == 'value'
        assert self.continue_calls == 2
        assert self.missing_key == 'key_2'



    def testDirectValues(self):
        '''
        Test direct values SET and GET.
        '''
        ns = Namespace()
        ns['name'] = 'python'
        ns['version'] = '2.4.3'
        ns['fullname'] = '`name`-`version`'
        ns['root_dir'] = '`fullname`'
        ns['lib_dir'] = '`root_dir`/lib'
        ns['DEPENDENCIES'] = []

        assert ns.GetValue('name', as_string=True) == 'python'
        assert ns.GetValue('fullname', as_string=True) == 'python-2.4.3'
        assert ns.GetValue('lib_dir', as_string=True) == 'python-2.4.3/lib'


    def testFlagsDeclaration(self):
        '''
        Test the declaration of flags and the error raised when trying to declare a variable
        using an undeclared flag.
        '''
        ns = Namespace()
        ns['name'] = 'alpha-flagless'

        # Declare the flag and then declare the name using it.
        ns._DeclareFlag('win32', 'Platform flag for all Windows systems.')
        ns['win32:name'] = 'alpha-w32'


    def testVariableNotFound(self):
        ns = Namespace()
        with pytest.raises(NamespaceKeyError):
            ns.GetValue('alpha')

        ns._DeclareFlag('win32', 'Platform flag for all Windows systems.')
        ns['win32:alpha'] = 'Alpha'

        with pytest.raises(NamespaceKeyError):
            ns.GetValue('alpha')


    def testPrint(self):
        ns = Namespace(flags=['win32'])
        ns._DeclareFlag('win32', 'Windows-OS')
        ns._DeclareFlag('mac', 'Mac-OS')
        ns['alpha'] = 'Alpha'
        ns['win32:alpha'] = 'Alpha-W32'
        ns['mac:alpha'] = 'Alpha-MAC'

        oss = StringIO()
        ns.Print(oss)

        assert (
            oss.getvalue()
            == '\n'
            '  alpha = STRING:Alpha\n'
            '        = (mac) STRING:Alpha-MAC\n'
            '        = (win32) STRING:Alpha-W32\n'
        )

        oss = StringIO()
        ns.Print(oss, evaluate=True)
        assert (
            oss.getvalue()
            == '\n'
            '  alpha = Alpha-W32\n'
        )

        oss = StringIO()
        ns.PrintDeclaredFlags(oss)
        assert (
            oss.getvalue()
            == '\n'
            '  mac = Mac-OS\n'
            '  win32 = Windows-OS\n',
        )

        oss = StringIO()
        ns.PrintImplicitFlags(oss)
        assert (
            oss.getvalue()
            == '\n'
            '  win32\n',
        )


    def testPathListValues(self):
        '''
        Test values that are paths
        '''
        ns = Namespace()
        ns['name'] = 'python'
        ns['version'] = '2.4.3'
        ns['fullname'] = '`name`-`version`'
        ns['libs'] = PATHLIST('`fullname`.lib', '/alpha/bravo/`name`.lib', 'c:\\alpha\\bravo\\`name`.lib')

        assert ns.GetValue('libs', as_string=True) == 'python-2.4.3.lib,/alpha/bravo/python.lib,c:/alpha/bravo/python.lib'

        if sys.platform == 'win32':
            assert ns.GetValue('libs$', as_string=True) == 'python-2.4.3.lib;\\alpha\\bravo\\python.lib;c:\\alpha\\bravo\\python.lib'
        else:
            assert ns.GetValue('libs$', as_string=True) == 'python-2.4.3.lib:/alpha/bravo/python.lib:c:/alpha/bravo/python.lib'


    def testSinglePathValues(self):
        '''
        Test values that are single paths
        '''
        ns = Namespace()
        ns['name'] = 'python'
        ns['version'] = '2.4.3'
        ns['fullname'] = '`name`-`version`'
        ns['libs'] = PATH('`fullname`.lib')
        ns['yes_flag:libs'] = PATH('yes_dir')

        assert ns.GetValue('libs', as_string=True) == 'python-2.4.3.lib'

        ns.SetFlag('yes_flag')
        assert ns.GetValue('libs', as_string=True) == 'yes_dir'


    def testNegativeFlags(self):
        '''
        Using negative flags
        '''
        ns = Namespace(flags=['win32'])
        ns._DeclareFlag('win32', 'Windows-OS')
        ns['win32:variable'] = 'Windows'
        ns['!win32:variable'] = 'NotWindows'
        assert ns.GetValue('variable', as_string=True) == 'Windows'

        ns = Namespace()
        ns._DeclareFlag('win32', 'Windows-OS')
        ns['win32:variable'] = 'Windows'
        ns['!win32:variable'] = 'NotWindows'
        assert ns.GetValue('variable', as_string=True) == 'NotWindows'


    def testGetWithFlags(self):
        '''
        Test get with flags
        '''
        ns = Namespace()
        ns._DeclareFlag('win32', 'Windows-OS')

        ns['lib_dir'] = 'lib'
        ns['win32:lib_dir'] = 'lib/win32'
        assert ns.GetValue('lib_dir', as_string=True) == 'lib'
        assert ns.GetValue('win32:lib_dir', as_string=True) == 'lib/win32'

        ns['win32:lib_dir'] = 'library/windows'
        assert ns.GetValue('lib_dir', as_string=True) == 'lib'
        assert ns.GetValue('win32:lib_dir', as_string=True) == 'library/windows'

        ns['win32:lib_dir'] = 'lib-w32'
        assert ns.GetValue('lib_dir', as_string=True) == 'lib'
        assert ns.GetValue('win32:lib_dir', as_string=True) == 'lib-w32'

        # Indirect flagged value
        ns['win32:lib_dir'] = 'lib-w32'
        ns['lib_dir2'] = 'LIB `lib_dir`'

        assert ns.GetValue('lib_dir2', as_string=True) == 'LIB lib'
        assert ns.GetValue('win32:lib_dir2', as_string=True) == 'LIB lib-w32'


    def testEvaluate(self):
        ns = Namespace()
        ns['name'] = 'Alpha'
        assert (
            ns.Evaluate('Hello `name`. How are you?')
            == 'Hello Alpha. How are you?')

        assert ns.Evaluate("Alpha ``Zulu`` Bravo") == 'Alpha `Zulu` Bravo'


    def testEvaluateFlags(self):
        ns = Namespace(flags=['win32', 'other_flag'])
        ns._DeclareFlag('other_flag', 'Flag for testing')
        ns._DeclareFlag('win32', 'Windows-OS')
        ns._DeclareFlag('linux', 'Linux-OS')

        assert ns.EvaluateFlags('')
        assert ns.EvaluateFlags('win32')
        assert ns.EvaluateFlags('win32:other_flag')
        assert not ns.EvaluateFlags('!win32')


    def testCreateFromNamespaceKey(self):
        from namespace import NamespaceKey

        def Test(namespace_key, expected_flags, expected_key):
            key = NamespaceKey(namespace_key)
            obtained_flags, obtained_key = key.flags, key.key
            assert repr(obtained_flags) == expected_flags
            assert obtained_key == expected_key

        Test('alpha', '<Flags >', 'alpha')

        # This is a signal telling that we want NO flags to be passed to this evaluation
        Test(':alpha', 'None', 'alpha')

        Test('X:alpha', '<Flags X>', 'alpha')
        Test('X:!Y:alpha', '<Flags X:!Y>', 'alpha')
        Test('!Z:X:!Y:alpha', '<Flags X:!Y:!Z>', 'alpha')


    def testNamespaceKey(self):
        from namespace import Flags, NamespaceKey

        key = NamespaceKey('yes:zulu')
        assert key.key == 'zulu'
        assert key.flags == Flags(['yes'], [])


    def testCallback(self):

        class MyCallback(object):

            call_count = 0

            def __init__(self):
                self.old_value = None
                self.new_value = None

            def __call__(self, namespace, old_value, new_value):
                self.__class__.call_count += 1
                self.old_value = old_value
                self.new_value = new_value

        ns = Namespace()

        # Use a normal key
        ns.SetValue('key1', 'value1')
        assert MyCallback.call_count == 0

        # Override it without a callback
        ns.SetValue('key1', 'value2')
        assert MyCallback.call_count == 0

        # Add a callback
        my_callback = MyCallback()
        ns.SetValue('@key1', my_callback)
        assert MyCallback.call_count == 0

        # Now this shold trigger the callback
        ns.SetValue('key1', 'value3')
        assert MyCallback.call_count == 1
        assert my_callback.old_value == STRING('value2')
        assert my_callback.new_value == STRING('value3')

        # Another change triggers it again
        ns.SetValue('key1', 'value4')
        assert MyCallback.call_count == 2
        assert my_callback.old_value == STRING('value3')
        assert my_callback.new_value == STRING('value4')

        # Even setting the same value will trigger the callback
        ns.SetValue('key1', 'value5')
        assert MyCallback.call_count == 3
        assert my_callback.old_value == STRING('value4')
        assert my_callback.new_value == STRING('value5')

        # Check callback old/new values when setting a value with flags
        ns['win32:key1'] = 'flagged1'
        assert MyCallback.call_count == 4
        assert my_callback.old_value == None
        assert my_callback.new_value == STRING('flagged1')

        # Check callback old/new values when setting a value with flags
        ns['win32:key1'] = 'flagged2'
        assert MyCallback.call_count == 5
        assert my_callback.old_value == STRING('flagged1')
        assert my_callback.new_value == STRING('flagged2')

        # Check callback old/new values when setting a value with flags
        ns['key1'] = 'value6'
        assert MyCallback.call_count == 6
        assert my_callback.old_value == STRING('value5')
        assert my_callback.new_value == STRING('value6')

        # Delete a key associated with a callback
        del ns['key1']
        assert MyCallback.call_count == 7
        assert my_callback.old_value == STRING('value6')
        assert my_callback.new_value == None

        # Check deletion with flags
        del ns['win32:key1']
        assert MyCallback.call_count == 8
        assert my_callback.old_value == STRING('flagged2')
        assert my_callback.new_value == None

        # Check deletion with all flags
        ns['some_flag:key1'] = 'some_flag_value'
        assert MyCallback.call_count == 9
        assert my_callback.old_value == None
        assert my_callback.new_value == STRING('some_flag_value')

        del ns['*:key1']
        assert MyCallback.call_count == 10
        assert my_callback.old_value == None  # We had no value associated with 'pure' key1
        assert my_callback.new_value == None


    def testPATH(self):
        ns = Namespace()
        ns['alpha'] = PATH('c:/Windows/System32')
        assert ns['alpha'].__class__ == unicode
        assert ns.GetValue('alpha').value == 'c:/Windows/System32'
        assert ns['alpha'] == 'c:/Windows/System32'
        assert ns['alpha#'] == 'PATH:c:/Windows/System32'
        assert ns['alpha$'] == os.path.normpath('c:/Windows/System32')

        assert ns.GetValue('alpha').__class__ == PATH
        assert ns.GetValue('alpha').AsString('$v') == 'c:/Windows/System32'

        ns['bravo'] = PATH('c:/Windows\\System32')
        assert ns['bravo'].__class__ == unicode

        # Note that even if the PATH was initialized with a mix of slashes, the stored value is kept
        # standardized.
        assert ns.GetValue('bravo').value == 'c:/Windows/System32'
        assert ns['bravo'] == 'c:/Windows/System32'
        assert ns['bravo#'] == 'PATH:c:/Windows/System32'
        assert ns['bravo$'] == os.path.normpath('c:/Windows/System32')

        assert ns.GetValue('bravo').__class__ == PATH
        assert ns.GetValue('bravo').AsString('$v') == 'c:/Windows/System32'


    def testSplitNameAndSuffix(self):
        assert Namespace.SplitNameAndVariation('alpha') == ('alpha', 'STR')
        assert Namespace.SplitNameAndVariation('alpha$') == ('alpha', '$')
        assert Namespace.SplitNameAndVariation('alpha#') == ('alpha', '#')
        assert Namespace.SplitNameAndVariation('alpha%') == ('alpha%', 'STR')
        assert Namespace.SplitNameAndVariation('charlie_delta') == ('charlie_delta', 'STR')
        assert Namespace.SplitNameAndVariation('charlie_delta$') == ('charlie_delta', '$')
        assert Namespace.SplitNameAndVariation('charlie_delta#') == ('charlie_delta', '#')
        assert Namespace.SplitNameAndVariation('echo99') == ('echo99', 'STR')
        assert Namespace.SplitNameAndVariation('echo99$') == ('echo99', '$')


    def testDelValue(self):
        # Level 1: Deleting a value from NamespaceVAlue
        nv = NamespaceValue()
        nv.SetValueWithFlags(('alpha',), 'ALPHA')
        nv.SetValueWithFlags(('bravo',), 'BRAVO')

        assert nv.GetValueWithFlags(('alpha',)) == 'ALPHA'
        assert nv.GetValueWithFlags(('bravo',)) == 'BRAVO'

        nv.DelValueWithFlags(('alpha',))

        assert nv.GetValueWithFlags(('alpha',)) is None
        assert nv.GetValueWithFlags(('bravo',)) == 'BRAVO'

        # Level 2: Deleting a value from the namespace.

        n = Namespace()
        n[':alpha'] = 'ALPHA'
        n[':bravo'] = 'BRAVO'
        n[':charlie'] = 'CHARLIE'

        n['var'] = 'value'
        n['alpha:var'] = 'value-alpha'
        n['bravo:var'] = 'value-bravo'

        assert n['var'] == 'value'
        assert n['alpha:var'] == 'value-alpha'
        assert n['bravo:var'] == 'value-bravo'
        assert n['charlie:var'] == 'value'

        del n['alpha:var']

        assert n['var'] == 'value'
        assert n['alpha:var'] == 'value'
        assert n['bravo:var'] == 'value-bravo'
        assert n['charlie:var'] == 'value'

        n.ClearValue('var')

        with pytest.raises(NamespaceKeyError):
            n.__getitem__('var')
        with pytest.raises(NamespaceKeyError):
            n.__getitem__('alpha:var')
        with pytest.raises(NamespaceKeyError):
            n.__getitem__('bravo:var')
        with pytest.raises(NamespaceKeyError):
            n.__getitem__('bravo:var')
        with pytest.raises(NamespaceKeyError):
            n.__getitem__('charlie:var')


    def testExplicitFlags(self):
        n = Namespace()

        def AssertExist(name, value):
            assert n[name] == value

        # If there is no explicit variable with "alpha:" flag, we fallback to the nearest match
        n['var'] = '0'
        AssertExist('alpha:var', '0')

        # The nearest match still is '0'
        n['alpha:bravo:var'] = 'AB'
        AssertExist('alpha:var', '0')

        # Now, with the flag set, the nearest match is "alpha:bravo:"
        n.SetFlag('bravo')
        AssertExist('alpha:var', 'AB')

        # Setting bravo variation now makes "var" defaults to bravo (since we have the flag set in
        # the Namespace)
        n['bravo:var'] = 'B'
        AssertExist('var', 'B')

        # By requesting to explictly remove "bravo:" flag, the nearest match is again '0'
        AssertExist('!bravo:var', '0')


    def testExplicitFlagsAndExpansion(self):
        n = Namespace()

        n['name'] = 'NAME'

        n['title'] = 'The `name`'
        assert n['title'] == 'The NAME'

        # Here we have an error, because "alt:name" is not defined
        n['alt:title'] = 'The alternative `name`'
        assert n['alt:title'] == 'The alternative NAME'

        n['sur:name'] = 'SURNAME'
        assert n['sur:title'] == 'The SURNAME'
