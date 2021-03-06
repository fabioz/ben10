from __future__ import unicode_literals
from ben10.foundation.callback import After, Before, Callback, Callbacks, Remove, _CallbackWrapper
from ben10.foundation.types_ import Null
from ben10.foundation.weak_ref import WeakMethodRef
import mock
import pytest
import weakref


#===================================================================================================
# _MyClass
#===================================================================================================
class _MyClass(object):

    def SetAlpha(self, value):
        self.alpha = value

    def SetBravo(self, value):
        self.bravo = value



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def setup_method(self, method):
        class C(object):
            def foo(s, arg):  # @NoSelf
                self.foo_called = (s, arg)
                return arg
        self.foo_called = None

        self.C = C
        self.a = C()
        self.b = C()

        def after(*args):
            self.after_called = args
            self.after_count += 1

        self.after = after
        self.after_called = None
        self.after_count = 0

        def before(*args):
            self.before_called = args
            self.before_count += 1

        self.before = before
        self.before_called = None
        self.before_count = 0


    def testClassOverride(self):
        Before(self.C.foo, self.before)
        After(self.C.foo, self.after)

        self.a.foo(1)
        assert self.foo_called == (self.a, 1)
        assert self.after_called == (self.a, 1)
        assert self.after_count == 1
        assert self.before_called == (self.a, 1)
        assert self.before_count == 1

        self.b.foo(2)
        assert self.foo_called == (self.b, 2)
        assert self.after_called == (self.b, 2)
        assert self.after_count == 2
        assert self.before_called == (self.b, 2)
        assert self.before_count == 2

        Remove(self.C.foo, self.before)

        self.a.foo(3)
        assert self.foo_called == (self.a, 3)
        assert self.after_called == (self.a, 3)
        assert self.after_count == 3
        assert self.before_called == (self.b, 2)
        assert self.before_count == 2


    def testInstanceOverride(self):
        Before(self.a.foo, self.before)
        After(self.a.foo, self.after)

        self.a.foo(1)
        assert self.foo_called == (self.a, 1)
        assert self.after_called == (1,)
        assert self.before_called == (1,)
        assert self.after_count == 1
        assert self.before_count == 1

        self.b.foo(2)
        assert self.foo_called == (self.b, 2)
        assert self.after_called == (1,)
        assert self.before_called == (1,)
        assert self.after_count == 1
        assert self.before_count == 1

        assert Remove(self.a.foo, self.before) == True

        self.a.foo(2)
        assert self.foo_called == (self.a, 2)
        assert self.after_called == (2,)
        assert self.before_called == (1,)
        assert self.after_count == 2
        assert self.before_count == 1

        Before(self.a.foo, self.before)
        Before(self.a.foo, self.before)  # Registering twice has no effect the 2nd time

        self.a.foo(5)
        assert self.before_called == (5,)
        assert self.before_count == 2


    def testBoundMethodsWrong(self):
        foo = self.a.foo
        Before(foo, self.before)
        After(foo, self.after)

        foo(10)
        assert 0 == self.before_count
        assert 0 == self.after_count


    def testBoundMethodsRight(self):
        foo = self.a.foo
        foo = Before(foo, self.before)
        foo = After(foo, self.after)

        foo(10)
        assert self.before_count == 1
        assert self.after_count == 1


    def testReferenceDies(self):
        class Receiver(object):

            def before(dummy, *args):  # @NoSelf
                self.before_count += 1
                self.before_args = args

        rec = Receiver()
        self.before_count = 0
        self.before_args = None

        foo = self.a.foo
        foo = Before(foo, rec.before)

        foo(10)
        assert self.before_args == (10,)
        assert self.before_count == 1

        del rec  # kill the receiver

        foo(20)
        assert self.before_args == (10,)
        assert self.before_count == 1


    def testSenderDies(self):

        class Sender(object):
            def foo(s, *args):  # @NoSelf
                s.args = args
            def __del__(dummy):  # @NoSelf
                self.sender_died = True

        self.sender_died = False
        s = Sender()
        w = weakref.ref(s)
        Before(s.foo, self.before)
        s.foo(10)
        f = s.foo  # hold a strong reference to s
        assert self.before_count == 1
        assert self.before_called == (10,)

        assert not self.sender_died
        del s
        assert self.sender_died

        with pytest.raises(ReferenceError):
            f(10)  # must have already died: we don't have a strong reference
        assert w() is None


    def testLessArgs(self):

        class C(object):
            def foo(self, _x, _y, **_kwargs):
                pass

        def after_2(x, y, *args, **kwargs):
            self.after_2_res = x, y

        def after_1(x, *args, **kwargs):
            self.after_1_res = x

        def after_0(*args, **kwargs):
            self.after_0_res = 0

        self.after_2_res = None
        self.after_1_res = None
        self.after_0_res = None

        c = C()

        After(c.foo, after_2)
        After(c.foo, after_1)
        After(c.foo, after_0)

        c.foo(10, 20, foo=1)
        assert self.after_2_res == (10, 20)
        assert self.after_1_res == 10
        assert self.after_0_res == 0


    def testWithCallable(self):
        class Stub(object):
            def call(self, _b):
                pass

        class Aux(object):
            def __call__(self, _b):
                self.called = True


        s = Stub()
        a = Aux()
        After(s.call, a)
        s.call(True)

        assert a.called


    def testCallback(self):

        self.args = [None, None]
        def f1(*args):
            self.args[0] = args

        def f2(*args):
            self.args[1] = args


        c = Callback()
        c.Register(f1)

        c(1, 2)

        assert self.args[0] == (1, 2)

        c.Unregister(f1)
        self.args[0] = None
        c(10, 20)
        assert self.args[0] == None

        def foo(): pass
        #self.assertNotRaises(FunctionNotRegisteredError, c.Unregister, foo)
        c.Unregister(foo)


    def test_extra_args(self):
        '''
            Tests the extra-args parameter in Register method.
        '''
        self.zulu_calls = []

        def zulu_one(*args):
            self.zulu_calls.append(args)

        def zulu_too(*args):
            self.zulu_calls.append(args)

        alpha = Callback()
        alpha.Register(zulu_one, [1, 2])

        assert self.zulu_calls == []

        alpha('a')
        assert self.zulu_calls == [
            (1, 2, 'a')
            ]

        alpha('a', 'b', 'c')
        assert self.zulu_calls == [
            (1, 2, 'a'),
            (1, 2, 'a', 'b', 'c')
            ]

        # Test a second method with extra-args
        alpha.Register(zulu_too, [9])

        alpha('a')
        assert self.zulu_calls == [
            (1, 2, 'a'),
            (1, 2, 'a', 'b', 'c'),
            (1, 2, 'a'),
            (9, 'a'),
            ]

    def test_sender_as_parameter(self):
        self.zulu_calls = []

        def zulu_one(*args):
            self.zulu_calls.append(args)

        def zulu_two(*args):
            self.zulu_calls.append(args)

        Before(self.a.foo, zulu_one, sender_as_parameter=True)

        assert self.zulu_calls == []
        self.a.foo(0)
        assert self.zulu_calls == [(self.a, 0)]

        # The second method registered with the sender_as_parameter on did not receive it.
        Before(self.a.foo, zulu_two, sender_as_parameter=True)

        self.zulu_calls = []
        self.a.foo(1)
        assert self.zulu_calls == [(self.a, 1), (self.a, 1)]


    def test_sender_as_parameter_after_and_before(self):
        self.zulu_calls = []

        def zulu_one(*args):
            self.zulu_calls.append((1, args))

        def zulu_too(*args):
            self.zulu_calls.append((2, args))

        Before(self.a.foo, zulu_one, sender_as_parameter=True)
        After(self.a.foo, zulu_too)

        assert self.zulu_calls == []
        self.a.foo(0)
        assert self.zulu_calls == [(1, (self.a, 0)), (2, (0,))]



    def testContains(self):
        def foo(x):
            pass

        c = Callback()
        assert not c.Contains(foo)
        c.Register(foo)

        assert c.Contains(foo)
        c.Unregister(foo)
        assert not c.Contains(foo)


    def testCallbackReceiverDies(self):
        class A(object):
            def on_foo(dummy, *args):  # @NoSelf
                self.args = args


        self.args = None
        a = A()
        weak_a = weakref.ref(a)

        foo = Callback()
        foo.Register(a.on_foo)

        foo(1, 2)
        assert self.args == (1, 2)
        assert weak_a() is a

        foo(3, 4)
        assert self.args == (3, 4)
        assert weak_a() is a

        del a
        assert weak_a() is None
        foo(5, 6)
        assert self.args == (3, 4)


    def testActionMethodDies(self):
        class A(object):
            def foo(self):
                pass

        def FooAfter():
            self.after_exec += 1

        self.after_exec = 0

        a = A()
        weak_a = weakref.ref(a)
        After(a.foo, FooAfter)
        a.foo()

        assert self.after_exec == 1

        del a

        # IMPORTANT: behaviour change. The description below is for the previous
        # behaviour. That is not true anymore (the circular reference is not kept anymore)

        # callback creates a circular reference; that's ok, because we want
        # to still be able to do "x = a.foo" and keep a strong reference to it

        assert weak_a() is None


    def testAfterRegisterMultipleAndUnregisterOnce(self):
        class A(object):
            def foo(self):
                pass

        a = A()

        def FooAfter1():
            Remove(a.foo, FooAfter1)
            self.after_exec += 1

        def FooAfter2():
            self.after_exec += 1

        self.after_exec = 0
        After(a.foo, FooAfter1)
        After(a.foo, FooAfter2)
        a.foo()

        # it was iterating in the original after, so, this case
        # was only giving 1 result and not 2 as it should
        assert 2 == self.after_exec

        a.foo()
        assert 3 == self.after_exec
        a.foo()
        assert 4 == self.after_exec

        After(a.foo, FooAfter2)
        After(a.foo, FooAfter2)
        After(a.foo, FooAfter2)

        a.foo()
        assert 5 == self.after_exec

        Remove(a.foo, FooAfter2)
        a.foo()
        assert 5 == self.after_exec


    def testOnClassMethod(self):
        class A(object):
            @classmethod
            def foo(cls):
                pass

        self.after_exec_class_method = 0
        def FooAfterClassMethod():
            self.after_exec_class_method += 1

        self.after_exec_self_method = 0
        def FooAfterSelfMethod():
            self.after_exec_self_method += 1

        After(A.foo, FooAfterClassMethod)

        a = A()
        After(a.foo, FooAfterSelfMethod)

        a.foo()
        assert 1 == self.after_exec_class_method
        assert 1 == self.after_exec_self_method

        Remove(A.foo, FooAfterClassMethod)
        a.foo()
        assert 1 == self.after_exec_class_method
        assert 2 == self.after_exec_self_method


    def testSenderDies2(self):
        After(self.a.foo, self.after, True)
        self.a.foo(1)
        assert (self.a, 1) == self.after_called

        a = weakref.ref(self.a)
        self.after_called = None
        self.foo_called = None
        del self.a
        assert a() is None


    def testCallbacks(self):
        self.called = 0
        def bar(*args):
            self.called += 1

        callbacks = Callbacks()
        callbacks.Before(self.a.foo, bar)
        callbacks.After(self.a.foo, bar)

        self.a.foo(1)
        assert 2 == self.called
        callbacks.RemoveAll()
        self.a.foo(1)
        assert 2 == self.called


    def testAfterRemove(self):

        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        After(my_object.SetAlpha, my_object.SetBravo)

        my_object.SetAlpha(1)
        assert my_object.bravo == 1

        Remove(my_object.SetAlpha, my_object.SetBravo)

        my_object.SetAlpha(2)
        assert my_object.bravo == 1


    def testAfterRemoveCallback(self):
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        # Test After/Remove with a callback
        event = Callback()
        After(my_object.SetAlpha, event)
        event.Register(my_object.SetBravo)

        my_object.SetAlpha(3)
        assert my_object.bravo == 3

        Remove(my_object.SetAlpha, event)

        my_object.SetAlpha(4)
        assert my_object.bravo == 3


    def testAfterRemoveCallbackAndSenderAsParameter(self):
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)

        def event(obj_or_value, value):
            self._value = value

        # Test After/Remove with a callback and sender_as_parameter
        After(my_object.SetAlpha, event, sender_as_parameter=True)

        my_object.SetAlpha(3)

        assert 3 == self._value

        Remove(my_object.SetAlpha, event)

        my_object.SetAlpha(4)
        assert 3 == self._value

    def testDeadCallbackCleared(self):
        my_object = _MyClass()
        my_object.SetAlpha(0)
        my_object.SetBravo(0)
        self._value = []

        class B(object):
            def event(s, value):  # @NoSelf
                self._b_value = value

        class A(object):
            def event(s, obj, value):  # @NoSelf
                self._a_value = value

        a = A()
        b = B()

        # Test After/Remove with a callback and sender_as_parameter
        After(my_object.SetAlpha, a.event, sender_as_parameter=True)
        After(my_object.SetAlpha, b.event, sender_as_parameter=False)

        w = weakref.ref(a)
        my_object.SetAlpha(3)
        assert 3 == self._a_value
        assert 3 == self._b_value
        del a
        my_object.SetAlpha(4)
        assert 3 == self._a_value
        assert 4 == self._b_value
        assert w() is None


    def testRemoveCallback(self):

        class C(object):
            def __init__(self, name):
                self.name = name

            def OnCallback(self):
                pass

            def __eq__(self, other):
                return self.name == other.name

            def __ne__(self, other):
                return not self == other

        instance1 = C('instance')
        instance2 = C('instance')
        assert instance1 == instance2

        c = Callback()
        c.Register(instance1.OnCallback)
        c.Register(instance2.OnCallback)

        # removing first callback, and checking that it was actually removed as expected
        c.Unregister(instance1.OnCallback)
        assert not c.Contains(instance1.OnCallback) == True

        #self.assertNotRaises(RuntimeError, c.Unregister, instance1.OnCallback)
        c.Unregister(instance1.OnCallback)


        # removing second callback, and checking that it was actually removed as expected
        c.Unregister(instance2.OnCallback)
        assert not c.Contains(instance2.OnCallback) == True

        #self.assertNotRaises(RuntimeError, c.Unregister, instance2.OnCallback)
        c.Unregister(instance2.OnCallback)


    def testRegisterTwice(self):
        self.called = 0
        def After(*args):
            self.called += 1

        c = Callback()
        c.Register(After)
        c.Register(After)
        c.Register(After)
        c()
        assert self.called == 1


    def testHandleErrorOnCallback(self):
        old_default_handle_errors = Callback.DEFAULT_HANDLE_ERRORS
        Callback.DEFAULT_HANDLE_ERRORS = False
        try:

            self.called = 0
            def After(*args, **kwargs):
                self.called += 1
                raise RuntimeError('test')

            def After2(*args, **kwargs):
                self.called += 1
                raise RuntimeError('test2')

            c = Callback(handle_errors=True)
            c.Register(After)
            c.Register(After2)

            from ben10.foundation import callback
            with mock.patch('ben10.foundation.handle_exception.HandleException', autospec=True) as mocked:
                c()
                assert self.called == 2
            assert mocked.call_count == 2

            with mock.patch('ben10.foundation.handle_exception.HandleException', autospec=True) as mocked:
                c(1, a=2)
                assert self.called == 4
            assert mocked.call_count == 2
            mocked.assert_called_with(
                '''Error while trying to call \n  File "%s", line 661, in After2 (Called from Callback)\nArgs: (1,)\nKwargs: {\'a\': 2}\n''' % __file__
            )

            # test the default behaviour: errors are not handled and stop execution as usual
            self.called = 0
            c = Callback()
            c.Register(After)
            c.Register(After2)
            with pytest.raises(RuntimeError):
                c()
            assert self.called == 1
        finally:
            Callback.DEFAULT_HANDLE_ERRORS = old_default_handle_errors


    def testAfterBeforeHandleError(self):

        class C(object):
            def Method(self, x):
                return x * 2

        def AfterMethod(*args):
            self.before_called += 1
            raise RuntimeError

        def BeforeMethod(*args):
            self.after_called += 1
            raise RuntimeError

        self.before_called = 0
        self.after_called = 0

        c = C()
        Before(c.Method, BeforeMethod)
        After(c.Method, AfterMethod)

        with mock.patch('ben10.foundation.callback._callback.HandleErrorOnCallback', autospec=True) as mocked:
            assert c.Method(10) == 20
            assert self.before_called == 1
            assert self.after_called == 1
        assert mocked.call_count == 2

        with mock.patch('ben10.foundation.callback._callback.HandleErrorOnCallback', autospec=True) as mocked:
            assert c.Method(20) == 40
            assert self.before_called == 2
            assert self.after_called == 2
        assert mocked.call_count == 2


    def testKeyReusedAfterDead(self, monkeypatch):
        self._gotten_key = False
        def GetKey(*args, **kwargs):
            self._gotten_key = True
            return 1

        monkeypatch.setattr(Callback, '_GetKey', GetKey)

        def AfterMethod(*args):
            pass

        def AfterMethodB(*args):
            pass

        c = Callback()

        c.Register(AfterMethod)
        self._gotten_key = False
        assert not c.Contains(AfterMethodB)
        assert c.Contains(AfterMethod)
        assert self._gotten_key

        # As we made _GetKey return always the same, this will make it remove one and add the
        # other one, so, the contains will have to check if they're actually the same or not.
        c.Register(AfterMethodB)
        self._gotten_key = False
        assert c.Contains(AfterMethodB)
        assert not c.Contains(AfterMethod)
        assert self._gotten_key

        class A(object):

            def __init__(self):
                self._a = 0

            def GetA(self):
                return self._a

            def SetA(self, value):
                self._a = value

            a = property(GetA, SetA)

        a = A()
        # If registering a bound, it doesn't contain the unbound
        c.Register(a.SetA)
        assert not c.Contains(AfterMethodB)
        assert not c.Contains(A.SetA)
        assert c.Contains(a.SetA)

        # But if registering an unbound, it contains the bound
        c.Register(A.SetA)
        assert not c.Contains(AfterMethodB)
        assert c.Contains(A.SetA)
        assert c.Contains(a.SetA)

        c.Register(a.SetA)
        assert len(c) == 1
        del a
        assert not c.Contains(AfterMethodB)
        assert len(c) == 0

        a = A()
        c.Register(_CallbackWrapper(WeakMethodRef(a.SetA)))
        assert len(c) == 1
        del a
        assert not c.Contains(AfterMethodB)
        assert len(c) == 0


    def testNeedsUnregister(self):
        c = Callback()
        # Even when the function isn't registered, we not raise an error.
        def Func():
            pass
        #self.assertNotRaises(RuntimeError, c.Unregister, Func)
        c.Unregister(Func)


    def testUnregisterAll(self):
        c = Callback()

        #self.assertNotRaises(AttributeError, c.UnregisterAll)
        c.UnregisterAll()

        self.called = False
        def Func():
            self.called = True

        c.Register(Func)
        c.UnregisterAll()

        c()
        assert self.called == False


    def testOnClassAndOnInstance(self):
        vals = []
        class Stub(object):
            def call(self, *args, **kwargs):
                pass

        def OnCall1(instance, val):
            vals.append(('call_instance', val))

        def OnCall2(val):
            vals.append(('call_class', val))

        After(Stub.call, OnCall1)
        s = Stub()
        After(s.call, OnCall2)

        s.call(True)
        assert [('call_instance', True), ('call_class', True)] == vals


    def testOnClassAndOnInstance2(self):
        vals = []
        class Stub(object):
            def call(self, *args, **kwargs):
                pass

        def OnCall1(instance, val):
            vals.append(('call_class', val))

        def OnCall2(val):
            vals.append(('call_instance', val))

        s = Stub()
        After(s.call, OnCall2)
        After(Stub.call, OnCall1)

        # Tricky thing here: because we added the callback in the class after we added it to the
        # instance, the callback on the instance cannot be rebound, thus, calling it on the instance
        # won't really trigger the callback on the class (not really what would be expected of the
        # after method, but I couldn't find a reasonable way to overcome that).
        # A solution could be keeping track of all callbacks and rebinding all existent ones in the
        # instances to the one in the class, but it seems overkill for such an odd situation.
        s.call(True)
        assert [('call_instance', True), ] == vals


    def testOnNullClass(self):

        class _MyNullSubClass(Null):

            def GetIstodraw(self):
                return True

        s = _MyNullSubClass()
        def AfterSetIstodraw():
            pass
        w = After(s.SetIstodraw, AfterSetIstodraw)


    def testCallbackWithMagicMock(self):
        """
        Check that we can register mock.MagicMock objects in callbacks.

        This makes it easier to test that public callbacks are being called with correct arguments.

        Usage (in testing, of course):

            save_listener = mock.MagicMock(spec=lambda: None)
            project_manager.on_save.Register(save_listener)
            project_manager.SlotSave()
            assert save_listener.call_args == mock.call('foo.file', '.txt')

        Instead of the more traditional:

            def OnSave(filename, ext):
                self.filename = filename
                self.ext = ext

            self.filename = None
            self.ext = ext

            project_manager.on_save.Register(OnSave)
            project_manager.SlotSave()
            assert (self.filename, self.ext) == ('foo.file', '.txt')
        """
        c = Callback()

        with pytest.raises(RuntimeError):
            c.Register(mock.MagicMock())

        magic_mock = mock.MagicMock(spec=lambda: None)
        c = Callback()
        c.Register(magic_mock)

        c(10, name='X')
        assert magic_mock.call_args_list == [mock.call(10, name='X')]

        c(20, name='Y')
        assert magic_mock.call_args_list == [mock.call(10, name='X'), mock.call(20, name='Y')]

        c.Unregister(magic_mock)
        c(30, name='Z')
        assert len(magic_mock.call_args_list) == 2
