from __future__ import unicode_literals
from ben10.foundation.types_ import Method, Null
from ben10.interface import (AssertImplements, Attribute, BadImplementationError,
    DeclareClassImplements, GetImplementedInterfaces, IAdaptable, ImplementsInterface, Interface,
    InterfaceError, InterfaceImplementorStub, IsImplementation, ReadOnlyAttribute)
import pytest
import sys



#===================================================================================================
# _InterfM1
#===================================================================================================
class _InterfM1(Interface):
    def m1(self):
        ''


#===================================================================================================
# _InterfM2
#===================================================================================================
class _InterfM2(Interface):
    def m2(self):
        ''


#===================================================================================================
# _InterfM3
#===================================================================================================
class _InterfM3(Interface):
    def m3(self, arg1, arg2):
        ''


#===================================================================================================
# _InterfM4
#===================================================================================================
class _InterfM4(_InterfM3):

    def m4(self):
        ''



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testBasics(self):
        class I(Interface):

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''

        class C(object):
            ImplementsInterface(I)

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''


        class C2(object):

            def foo(self, a, b=None):
                ''

            def bar(self):
                ''


        class D(object):
            ''

        assert IsImplementation(I(C()), I) == True  # OK

        assert IsImplementation(C, I) == True  # OK
        assert IsImplementation(C2, I) == False  # Does not declare
        assert not IsImplementation(D, I) == True  # nope

        assert I(C) is C
        assert I(C2) is C2
        with pytest.raises(InterfaceError):
            I()

        with pytest.raises(BadImplementationError):
            I(D)


        # Now declare that C2 implements I
        DeclareClassImplements(C2, I)

        assert IsImplementation(C2, I) == True  # Does not declare


    def testMissingMethod(self):
        class I(Interface):

            def foo(self, a, b=None):
                ''


        def TestMissingMethod():
            class C(object):
                ImplementsInterface(I)

        with pytest.raises(AssertionError):
            TestMissingMethod()


        def TestMissingSignature():
            class C(object):
                ImplementsInterface(I)

                def foo(self, a):
                    ''

        with pytest.raises(AssertionError):
            TestMissingSignature()


        def TestMissingSignatureOptional():
            class C(object):
                ImplementsInterface(I)

                def foo(self, a, b):
                    ''

        with pytest.raises(AssertionError):
            TestMissingSignatureOptional()


        def TestWrongParameterName():
            class C(object):
                ImplementsInterface(I)

                def foo(self, a, c):
                    ''

        with pytest.raises(AssertionError):
            TestWrongParameterName()



    def testSubclasses(self):
        class I(Interface):

            def foo(self, a, b=None):
                ''

        class C(object):
            ImplementsInterface(I)
            def foo(self, a, b=None):
                ''

        class D(C):
            ''


    def testSubclasses2(self):
        class I(Interface):
            def foo(self):
                ''

        class I2(Interface):
            def bar(self):
                ''

        class C(object):
            ImplementsInterface(I)
            def foo(self):
                ''

        class D(C):
            ImplementsInterface(I2)
            def bar(self):
                ''

        class E(D):
            ''

        assert GetImplementedInterfaces(C) == set([I])
        assert GetImplementedInterfaces(D) == set([I2, I])
        assert GetImplementedInterfaces(E) == set([I2, I])



    def testNoName(self):
        class I(Interface):
            def MyMethod(self, foo):
                ''

        class C(object):
            def MyMethod(self, bar):
                ''

        with pytest.raises(AssertionError):
            AssertImplements(C(), I)



    def testAttributes(self):
        class IZoo(Interface):
            zoo = Attribute(int)

        class I(Interface):
            foo = Attribute(int)
            bar = Attribute(unicode)
            foobar = Attribute(int, None)
            a_zoo = Attribute(IZoo)


        class Zoo(object):
            ImplementsInterface(IZoo)

        # NOTE: This class 'C' doesn't REALLY implements 'I', although it says so. The problem is
        #       that there's a flaw with attributes *not being checked*.

        # In fact: Attributes should not be in the  (Abstract) properties COULD be in
        #          the interface, but they SHOULD NOT be type-checked (because it involves a
        #          getter call, and this affects runtime behaviour).
        #          This should be reviewed later.
        class C(object):
            ImplementsInterface(I)

        c1 = C()
        c1.foo = 10
        c1.bar = 'hello'
        c1.foobar = 20

        a_zoo = Zoo()
        a_zoo.zoo = 99
        c1.a_zoo = a_zoo

        c2 = C()

        assert IsImplementation(C, I) == True
        assert IsImplementation(c1, I) == True
        assert IsImplementation(c2, I) == True

        # NOTE: Testing private methods here
        # If we do a deprecated "full check", then its behaviour is a little bit more correct.
        from ben10.interface._interface import _IsImplementationFullChecking
        assert not _IsImplementationFullChecking(C, I) == True  # only works with instances
        assert _IsImplementationFullChecking(c1, I) == True  # OK, has attributes
        assert not _IsImplementationFullChecking(c2, I) == True  # not all the attributes necessary

        # must not be true if including an object that doesn't implement IZoo interface expected for
        # a_zoo attribute
        c1.a_zoo = 'wrong'
        assert not _IsImplementationFullChecking(c1, I) == True  # failed, invalid attr type
        c1.a_zoo = a_zoo

        # test if we can set foobar to None
        c1.foobar = None
        assert IsImplementation(c1, I) == True  # OK

        c1.foobar = 'hello'
        assert not _IsImplementationFullChecking(c1, I) == True  # failed, invalid attr type


    def testPassNoneInAssertImplementsFullChecking(self):
        with pytest.raises(AssertionError):
            AssertImplements(None, _InterfM1)

        with pytest.raises(AssertionError):
            AssertImplements(10, _InterfM1)


    def testOldStyle(self):
        '''
        Interfaces are *deprecated* for old-style classes. They are checked only in the first
        usage of AssertImplements.
        '''

        class Old:
            ImplementsInterface(_InterfM1, old_style=True)

            def m1(self):
                ''

        class Old2:
            ImplementsInterface(_InterfM1, old_style=True)  # but do not really implements


        AssertImplements(Old, _InterfM1)  # Not raises AssertionError
        with pytest.raises(AssertionError):
            AssertImplements(Old2, _InterfM1)


        AssertImplements(Old(), _InterfM1)  # Not raises AssertionError
        with pytest.raises(AssertionError):
            AssertImplements(Old2(), _InterfM1)



    def testNoInitCheck(self):
        class NoCheck(object):
            ImplementsInterface(_InterfM1, no_init_check=True)

        no_check = NoCheck()
        with pytest.raises(AssertionError):
            AssertImplements(no_check, _InterfM1)



    def testCallbackAndInterfaces(self):
        '''
            Tests if the interface "AssertImplements" works with "callbacked" methods.
        '''
        class My(object):
            ImplementsInterface(_InterfM1)

            def m1(self):
                ''

        def MyCallback():
            ''

        from ben10.foundation.callback import After

        o = My()
        AssertImplements(o, _InterfM1)

        After(o.m1, MyCallback)

        AssertImplements(o, _InterfM1)
        AssertImplements(o, _InterfM1)  # Not raises BadImplementationError


    def testInterfaceStub(self):
        class My(object):
            ImplementsInterface(_InterfM1)

            def m1(self):
                return 'm1'
            def m2(self):
                ''

        m0 = My()
        m1 = _InterfM1(m0)  # will make sure that we only access the attributes/methods declared in the interface
        assert 'm1' == m1.m1()
        getattr(m0, 'm2')  # Not raises AttributeError
        with pytest.raises(AttributeError):
            getattr(m1, 'm2')

        _InterfM1(m1)  # Not raise BadImplementationError


    def testIsImplementationWithSubclasses(self):
        '''
        Checks if the IsImplementation method works with subclasses interfaces.

        Given that an interface I2 inherits from I1 of a given object declared that it implements I2
        then it is implicitly declaring that implements I1.
        '''

        class My2(object):
            ImplementsInterface(_InterfM2)

            def m2(self):
                ''

        class My3(object):
            ImplementsInterface(_InterfM3)

            def m3(self, arg1, arg2):
                ''

        class My4(object):
            ImplementsInterface(_InterfM4)

            def m3(self, arg1, arg2):
                ''

            def m4(self):
                ''

        m2 = My2()
        m3 = My3()
        m4 = My4()

        # My2
        assert IsImplementation(m2, _InterfM3) == False

        # My3
        assert IsImplementation(m3, _InterfM3) == True
        assert IsImplementation(m3, _InterfM4) == False

        # My4
        assert IsImplementation(m4, _InterfM4) == True
        assert IsImplementation(m4, _InterfM3) == True

        # When wrapped in an m4 interface it should still accept m3 as a declared interface
        wrapped_intef_m4 = _InterfM4(m4)
        assert IsImplementation(wrapped_intef_m4, _InterfM4) == True
        assert IsImplementation(wrapped_intef_m4, _InterfM3) == True


    def testIsImplementationWithBuiltInObjects(self):

        my_number = 10
        assert IsImplementation(my_number, _InterfM1) == False


    def testClassImplementMethod(self):
        '''
        Tests replacing a method that implements an interface with a class.

        The class must be derived from "Method" in order to be accepted as a valid
        implementation.
        '''

        class My(object):
            ImplementsInterface(_InterfM1)

            def m1(self):
                ''

        class MyRightMethod(Method):

            def __call__(self):
                ''

        class MyWrongMethod(object):

            def __call__(self):
                ''


        # NOTE: It doesn't matter runtime modifications in the instance, what is really being tested
        #       is the *class* of the object (My) is what is really being tested.
        m = My()
        m.m1 = MyWrongMethod()
        assert IsImplementation(m, _InterfM1) == True

        m.m1 = MyRightMethod()
        assert IsImplementation(m, _InterfM1) == True


        # NOTE: Testing behaviour of private methods here.
        from ben10.interface._interface import _IsImplementationFullChecking

        m = My()
        m.m1 = MyWrongMethod()
        r = _IsImplementationFullChecking(m, _InterfM1)
        assert r == False

        m.m1 = MyRightMethod()
        r = _IsImplementationFullChecking(m, _InterfM1)
        assert r == True

        del m.m1
        assert IsImplementation(m, _InterfM1) == True


    def testGetImplementedInterfaces(self):
        class A(object):
            ImplementsInterface(_InterfM1)
            def m1(self):
                ''
        class B(A):
            ''


        class C(object):
            ImplementsInterface(_InterfM4)
            def m4(self):
                ''

            def m3(self, arg1, arg2):
                ''

        assert 1 == len(GetImplementedInterfaces(B()))
        assert set(GetImplementedInterfaces(C())) == set([_InterfM4, _InterfM3])


    def testGetImplementedInterfaces2(self):
        class A(object):
            ImplementsInterface(_InterfM1)
            def m1(self):
                ''
        class B(A):
            ImplementsInterface(_InterfM2)
            def m2(self):
                ''

        assert 2 == len(GetImplementedInterfaces(B()))
        with pytest.raises(AssertionError):
            AssertImplements(A(), _InterfM2)

        AssertImplements(B(), _InterfM2)


    def testAdaptableInterface(self):

        class A(object):
            ImplementsInterface(IAdaptable)

            def GetAdapter(self, interface_class):
                if interface_class == _InterfM1:
                    return B()

        class B(object):
            ImplementsInterface(_InterfM1)

            def m1(self):
                ''

        a = A()
        b = _InterfM1(a)  # will try to adapt, as it does not directly implements m1
        assert b is not None
        b.m1()  # has m1
        with pytest.raises(AttributeError):
            getattr(b, 'non_existent')

        assert isinstance(b, InterfaceImplementorStub)


    def testNull(self):
        AssertImplements(Null(), _InterfM2)  # Not raises BadImplementationError

        class ExtendedNull(Null):
            ''

        AssertImplements(ExtendedNull(), _InterfM2)  # Not raises BadImplementationError


    def testSetItem(self):
        class InterfSetItem(Interface):
            def __setitem__(self, id, subject):
                ''
            def __getitem__(self, id):
                ''

        class A(object):
            ImplementsInterface(InterfSetItem)
            def __setitem__(self, id, subject):
                self.set = (id, subject)
            def __getitem__(self, id):
                return self.set

        a = InterfSetItem(A())
        a['10'] = 1
        assert ('10', 1) == a['10']


    def testAssertImplementsDoesNotDirObject(self):
        '''
        AssertImplements does not attempt to __getattr__ methods from an object, it only considers
        methods that are actually bound to the class.
        '''
        class M1(object):
            def __getattr__(self, attr):
                assert attr == 'm1'  # This test only accepts this attribute
                class MyMethod(Method):
                    def __call__(self):
                        ''
                return MyMethod()

        m1 = M1()
        m1.m1()
        with pytest.raises(AssertionError):
            AssertImplements(m1, _InterfM1)



    def testImplementorWithAny(self):
        '''
        You must explicitly declare that you implement an Interface.
        '''

        class M3(object):
            def m3(self, *args, **kwargs):
                ''

        with pytest.raises(AssertionError):
            AssertImplements(M3(), _InterfM3)



    def testInterfaceCheckRequiresInterface(self):
        class M3(object):

            def m3(self, *args, **kwargs):
                ''

        with pytest.raises(InterfaceError):
            AssertImplements(M3(), M3)

        with pytest.raises(InterfaceError):
            IsImplementation(M3(), M3)



    def testReadOnlyAttribute(self):
        class IZoo(Interface):
            zoo = ReadOnlyAttribute(int)


        class Zoo(object):
            ImplementsInterface(IZoo)

            def __init__(self, value):
                self.zoo = value


        a_zoo = Zoo(value=99)
        AssertImplements(a_zoo, IZoo)


    def testReadOnlyAttributeMissingImplementation(self):
        '''
        First implementation of changes in interfaces to support read-only attributes was not
        including read-only attributes when AssertImplements was called.

        This caused missing read-only attributes to go unnoticed and sometimes false positives,
        recognizing objects as valid implementations when in fact they weren't.
        '''
        class IZoo(Interface):
            zoo = ReadOnlyAttribute(int)

        # Doesn't have necessary 'zoo' attribute, should raise a bad implementation error
        class FlawedZoo(object):
            ImplementsInterface(IZoo)

            def __init__(self, value):
                ''

        # NOTE: Testing private methods here
        from ben10.interface._interface import _AssertImplementsFullChecking

        a_flawed_zoo = FlawedZoo(value=101)
        with pytest.raises(BadImplementationError):
            _AssertImplementsFullChecking(a_flawed_zoo, IZoo)


    def testImplementsTwice(self):
        class I1(Interface):
            def Method1(self):
                ''

        class I2(Interface):
            def Method2(self):
                ''

        def Create():

            class Foo(object):
                ImplementsInterface(I1)
                ImplementsInterface(I2)

                def Method2(self):
                    ''

        # Error because I1 is not implemented.
        with pytest.raises(AssertionError):
            Create()


    def testDeclareClassImplements(self):
        class I1(Interface):
            def M1(self):
                ''

        class I2(Interface):
            def M2(self):
                ''

        class C0(object):
            ''

        class C1(object):
            def M1(self):
                ''

        class C2(object):
            def M2(self):
                ''

        class C2B(object):
            ImplementsInterface(I2)
            def M2(self):
                ''

        class C12B(C1, C2B):
            ''

        with pytest.raises(AssertionError):
            DeclareClassImplements(C0, I1)


        assert IsImplementation(C1, I1) == False
        with pytest.raises(AssertionError):
            AssertImplements(C1, I1)


        assert IsImplementation(C12B, I1) == False  # C1 still does not implements I1

        DeclareClassImplements(C1, I1)

        assert IsImplementation(C1, I1) == True
        AssertImplements(C1, I1)

        # C1 is parent of C12B, and, above, it was declared that C1 implements I1, so C12B should
        # automatically implement I1. But this is not automatic, so you must also declare for it!

        assert IsImplementation(C12B, I1) == False  # not automatic
        assert IsImplementation(C12B, I2) == True  # inheritance for Implements still works automatically

        DeclareClassImplements(C12B, I1)

        assert IsImplementation(C12B, I1) == True  # now it implements
        assert IsImplementation(C12B, I2) == True

        DeclareClassImplements(C2, I2)

        assert IsImplementation(C2, I2) == True
        AssertImplements(C2, I2)

        # Exception: if I define a class *after* using DeclareClassImplements in the base, it works:
        class C12(C1, C2):
            ''

        AssertImplements(C12, I1)
        AssertImplements(C12, I2)


    def testCallableInterfaceStub(self):
        '''
        Validates that is possible to create stubs for interfaces of callables (i.e. declaring
        __call__ method in interface).

        If a stub for a interface not declared as callable is tried to be executed as callable it
        raises an error.
        '''
        # ok, calling a stub for a callable
        class IFoo(Interface):
            def __call__(self, bar):
                ''

        class Foo(object):
            ImplementsInterface(IFoo)

            def __call__(self, bar):
                ''

        foo = Foo()
        stub = IFoo(foo)
        stub(bar=None)  # NotRaises TypeError

        # wrong, calling a stub for a non-callable
        class IBar(Interface):
            def something(self, stuff):
                ''

        class Bar(object):
            ImplementsInterface(IBar)

            def something(self, stuff):
                ''

        bar = Bar()
        stub = IBar(bar)
        with pytest.raises(AttributeError):
            stub(stuff=None)


    def testImplementsInterfaceAsBoolError(self):
        '''
        Test if the common erroneous use of interface.ImplementsInterface() instead of
        interface.IsImplementation() to test if an object implements an interface correctly
        raises a RuntimeError.
        '''
        class I1(Interface):
            def M1(self):
                pass

        class C1(object):

            ImplementsInterface(I1)

            def M1(self):
                pass

        obj = C1()

        assert IsImplementation(obj, I1)

        with pytest.raises(RuntimeError):
            if ImplementsInterface(obj, I1):
                pytest.fail('Managed to test "if ImplementsInterface(obj, I1):"')
