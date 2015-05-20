from __future__ import unicode_literals
from ben10.filesystem import NormalizePath
from ben10.foundation.exceptions import ExceptionToUnicode
from namespace.namespace_types import (ENVIRON, INamespaceType, LIST, MIXED_PRIORITY,
    NamespaceTypeFactory, NamespaceTypeMergeException, OVERRIDE, PATH, PATHLIST, RAW, STRING)
import os
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testReprList(self):

        assert (
            '%r' % LIST('a', 'b')
            == repr(LIST('a', 'b'))
        )
        assert (
            repr(LIST('a', 'b'))
            == "LIST('a', 'b')"
        )
        assert (
            '%r' % LIST('a', 'b')
            == "LIST('a', 'b')"
        )


    def testListIter(self):
        var = LIST(1, 2, 3)

        assert 1 in var
        assert 2 in var
        assert 3 in var


    def testMergeEmpty(self):
        '''
        Test exceptional cases when merging 2 empty lists
        '''
        var1 = PATHLIST()
        var2 = PATHLIST()

        assert (
            var1.Merge(var2)
            == PATHLIST()
        )

        # A PATHLIST with empty string is the same as an empty PATHLIST. This is used by the
        # Namespace when a PATHLIST references another via evaluation. An empty string is returned
        # when evaluating a PATHLIST namespace variable. The variable should interpret it as a
        # PATHLIST
        var1 = PATHLIST('')
        var2 = PATHLIST('')

        assert (
            var1.Merge(var2)
            == PATHLIST()
        )


    def testListPriorityList(self):
        '''
        Test behavior of LIST merging and evaluation
        '''
        var1 = LIST('a', 'b', priority=200)
        var2 = LIST('c', 'd', priority=100)

        assert var1.priority == 200
        assert var1.priority_list == [200, 200]

        assert var2.priority == 100
        assert var2.priority_list == [100, 100]

        var3 = var1.Merge(var2)
        assert var3.priority == MIXED_PRIORITY
        assert var3.priority_list == (100, 100, 200, 200)

        # Everything should remain the same with evaluated lists
        from namespace import Namespace
        var1 = var1.Evaluate(namespace=Namespace())
        var2 = var2.Evaluate(namespace=Namespace())

        assert var1.priority == 200
        assert var1.priority_list == [200, 200]

        assert var2.priority == 100
        assert var2.priority_list == [100, 100]

        var3 = var1.Merge(var2)
        assert var3.priority == MIXED_PRIORITY
        assert var3.priority_list == (100, 100, 200, 200)

        # This once caused an error when after evaluating a mixed_priority list would make all
        # internal priorities wrong (this test was created to make sure this won't happen again)
        var3 = var3.Evaluate(namespace=Namespace())
        assert var3.priority == MIXED_PRIORITY
        assert var3.priority_list == (100, 100, 200, 200)


    def testMergePriorities(self):

        var1 = PATHLIST('highest', priority=1)
        var2 = PATHLIST('medium', priority=2)
        var3 = PATHLIST('lowest', priority=3)

        # Testing priority results
        self.AssertEqualAsString(var1.Merge(var2), PATHLIST('highest', 'medium'))
        self.AssertEqualAsString(var2.Merge(var3), PATHLIST('medium', 'lowest'))
        self.AssertEqualAsString(var1.Merge(var3), PATHLIST('highest', 'lowest'))


        # Results must always be the same, regardless of order
        self.AssertEqualAsString(var1.Merge(var2), var2.Merge(var1))
        self.AssertEqualAsString(var2.Merge(var3), var3.Merge(var2))
        self.AssertEqualAsString(var1.Merge(var3), var3.Merge(var1))

        self.AssertEqualAsString(var1.Merge(var3).Merge(var2), PATHLIST('highest', 'medium', 'lowest'))
        self.AssertEqualAsString(
            var1.Merge(var3).Merge(var2),
            var2.Merge(var3).Merge(var1),
        )

        # When using same priority, left has precedence over right
        var4 = PATHLIST('same_1', priority=5)
        var5 = PATHLIST('same_2', priority=5)

        self.AssertEqualAsString(var4.Merge(var5), PATHLIST('same_1', 'same_2'))
        self.AssertEqualAsString(var5.Merge(var4), PATHLIST('same_2', 'same_1'))

        # Testing with override priority
        var6 = PATHLIST('6', priority=OVERRIDE)
        var7 = PATHLIST('7', priority=OVERRIDE)

        # Right operator overrides left, regardless of its priority
        self.AssertEqualAsString(var1.Merge(var6), PATHLIST('6'))
        self.AssertEqualAsString(var6.Merge(var1), PATHLIST('6'))

        with pytest.raises(NamespaceTypeMergeException):
            var6.Merge(var7)


    def testLIST(self):
        var1 = LIST('alpha', 'bravo')
        assert var1.GetValue() == ['alpha', 'bravo']
        assert var1.AsString() == 'alpha,bravo'
        assert var1.GetValue(variation=INamespaceType.VARIATION_STR) == 'alpha,bravo'
        assert var1.GetValue(variation=INamespaceType.VARIATION_ENV) == 'alpha,bravo'
        assert var1.GetValue(variation=INamespaceType.VARIATION_IO) == 'LIST:alpha,bravo'

        assert (
            LIST.CreateFromString('alpha,bravo')
            == LIST('alpha', 'bravo')
        )
        assert (
            LIST.CreateFromString('alpha')
            == LIST('alpha')
        )
        assert (
            LIST.CreateFromString('')
            == LIST()
        )

    def testRawTypes(self):

        def TestRawValue(value):
            var = RAW(value)

            assert var.GetValue() == value
            assert var.GetValue(variation=INamespaceType.VARIATION_STR) == value
            assert var.GetValue(variation=INamespaceType.VARIATION_ENV) == value
            assert var.GetValue(variation=INamespaceType.VARIATION_IO) == value

            assert var.ExpandScopeInExpression('doesnt matter') == var
            assert var.Evaluate('ignored' == 'params'), var

            with pytest.raises(NotImplementedError):
                var.CreateFromString('any string')

        TestRawValue(True)
        TestRawValue(False)
        TestRawValue(1)
        TestRawValue([5])

        class Mock():
            pass

        TestRawValue(Mock)


    def testPATHLIST(self):
        var0 = PATHLIST('alpha', 'bravo')
        assert var0.GetValue() == ['alpha', 'bravo']
        assert var0.AsString() == 'alpha,bravo'
        assert var0.GetValue(variation=INamespaceType.VARIATION_STR) == 'alpha,bravo'
        assert var0.GetValue(variation=INamespaceType.VARIATION_ENV) == os.pathsep.join(['alpha', 'bravo'])
        assert var0.GetValue(variation=INamespaceType.VARIATION_IO) == 'PATHLIST:alpha,bravo'

        var1 = PATHLIST('alpha')
        assert var1.value == ['alpha']

        var2 = PATHLIST('alpha', priority=OVERRIDE)
        assert var2.value == ['alpha']

        self.AssertEqualAsString(var1.value, var2.value)

        var3 = PATHLIST('alpha', '/bravo/charlie', 'delta/zulu/../foxtrot', 'c:\\golf\\hotel', '/india/')
        assert var3.value == ['alpha', '/bravo/charlie', 'delta/foxtrot', 'c:/golf/hotel', '/india/']

        assert (
            var3.AsString()
            == 'alpha,/bravo/charlie,delta/foxtrot,c:/golf/hotel,/india/'
        )

        with pytest.raises(DeprecationWarning):
            PATHLIST(['c:/alpha', 'c:/bravo'])


    def testPATH(self):
        var = PATH('c:/alpha/bravo')
        assert var.value == 'c:/alpha/bravo'
        assert var.GetValue() == 'c:/alpha/bravo'
        assert var.GetValue(INamespaceType.VARIATION_ENV) == os.path.normpath('c:/alpha/bravo')
        assert var.GetValue(INamespaceType.VARIATION_IO) == 'PATH:c:/alpha/bravo'
        assert var.AsString() == 'c:/alpha/bravo'

        var = PATH('c:\\alpha\\bravo')
        assert var.value == 'c:/alpha/bravo'
        assert var.GetValue() == 'c:/alpha/bravo'
        assert var.GetValue(INamespaceType.VARIATION_ENV) == os.path.normpath('c:/alpha/bravo')
        assert var.GetValue(INamespaceType.VARIATION_IO) == 'PATH:c:/alpha/bravo'
        assert var.AsString() == 'c:/alpha/bravo'

        var = PATH('c:/alpha/zulu/../bravo')
        assert var.value == 'c:/alpha/bravo'
        assert var.GetValue() == 'c:/alpha/bravo'
        assert var.GetValue(INamespaceType.VARIATION_ENV) == os.path.normpath('c:/alpha/bravo')
        assert var.GetValue(INamespaceType.VARIATION_IO) == 'PATH:c:/alpha/bravo'
        assert var.AsString() == 'c:/alpha/bravo'

        var = PATH('c:\\alpha\\zulu\\..\\bravo')
        assert var.value == 'c:/alpha/bravo'
        assert var.GetValue() == 'c:/alpha/bravo'
        assert var.GetValue(INamespaceType.VARIATION_ENV) == os.path.normpath('c:/alpha/bravo')
        assert var.GetValue(INamespaceType.VARIATION_IO) == 'PATH:c:/alpha/bravo'
        assert var.AsString() == 'c:/alpha/bravo'

        var = PATH('alpha/')
        assert var.value == 'alpha/'
        assert var.GetValue() == 'alpha/'
        assert var.GetValue(INamespaceType.VARIATION_ENV) == NormalizePath('alpha/')
        assert var.GetValue(INamespaceType.VARIATION_IO) == 'PATH:alpha/'
        assert var.AsString() == 'alpha/'


    def testENVIRON(self):
        from namespace import Namespace

        namespace = Namespace()
        namespace['system.platform'] = 'SomeOS'

        # A variable cannot be mandatory and have a default value
        with pytest.raises(AssertionError):
            ENVIRON('name', default='default', mandatory=True)

        # If no default value is set, None is returned for missing non-mandatory variables
        missing = ENVIRON('NOT_EXISTENT_ENVIRONMENT')
        value = missing.GetValue()
        assert None == value

        # The default value is returned for missing non-mandatory variables
        missing = ENVIRON('NOT_EXISTENT_ENVIRONMENT', default='default')
        value = missing.GetValue()
        assert 'default' == value

        # Checking if the value in "default" is expanded using the namespace Evaluate method.
        var1 = ENVIRON('NOT_EXISTENT_ENVIRONMENT', default='`system.platform`')
        r = var1.Evaluate(namespace)
        assert unicode(r) == 'SomeOS'

        # Key error is raised for missin madatory variables
        with pytest.raises(KeyError):
            ENVIRON('NOT_EXISTENT_ENVIRONMENT', mandatory=True).GetValue()


    def testMergeNonLists(self):
        var1 = STRING('alpha', priority=OVERRIDE)
        var2 = STRING('bravo')
        var3 = var1.Merge(var2)
        assert var3.GetValue() == 'alpha'

        var1 = STRING('alpha')
        var2 = STRING('bravo', priority=OVERRIDE)
        var3 = var1.Merge(var2)
        assert var3.GetValue() == 'bravo'

        var1 = STRING('alpha', priority=OVERRIDE)
        var2 = STRING('bravo', priority=OVERRIDE)
        with pytest.raises(NamespaceTypeMergeException):
            var1.Merge(var2)

        var1 = ENVIRON('bravo')
        var2 = STRING('alpha', priority=OVERRIDE)
        var3 = var1.Merge(var2)


    def testAsString(self):
        a = STRING('Alpha')
        assert a.AsString() == 'Alpha'
        assert a.AsString('($t): $v') == '(STRING): Alpha'

        # Template is the first parameter
        assert a.AsString('$v') == 'Alpha'

        assert a.AsString(template='$t') == 'STRING'
        assert a.AsString(template='$j$t') == 'STRING'
        assert a.AsString(template='$j$t', justify=10) == '    STRING'

        assert a.AsString(template='($f)', flags=['one', 'two']) == '(one:two)'
        assert a.AsString(template='($f)',) == '()'


    def testNamespaceFactory(self):
        assert NamespaceTypeFactory.CreateFromString('LIST:foo,bar') == LIST('foo', 'bar')
        assert NamespaceTypeFactory.CreateFromString('PATH:foo') == PATH('foo')
        assert NamespaceTypeFactory.CreateFromString('PATHLIST:foo,bar') == PATHLIST('foo', 'bar')
        assert NamespaceTypeFactory.CreateFromString('STRING:foo') == STRING('foo')
        assert NamespaceTypeFactory.CreateFromString('STRING:x:/foo') == STRING('x:/foo')
        assert NamespaceTypeFactory.CreateFromString('foo') == STRING('foo')
        assert NamespaceTypeFactory.CreateFromString('x:/foo') == STRING('x:/foo')
        assert repr(NamespaceTypeFactory.CreateFromString('ENVIRON:$foo')) == repr(ENVIRON('$foo'))

        with pytest.raises(RuntimeError) as e:
            NamespaceTypeFactory.CreateFromString('CALLABLE:foo')
        assert ExceptionToUnicode(e.value) == 'CALLABLE not available in NamespaceTypeFactory'


    def AssertEqualAsString(self, obj1, obj2):
        assert unicode(obj1) == unicode(obj2)
