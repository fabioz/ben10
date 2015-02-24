from __future__ import unicode_literals
from _callback_wrapper import _CallbackWrapper
from ben10.foundation.odict import odict
from ben10.foundation.reraise import Reraise
import mock
import new
import weakref



#===================================================================================================
# Callback
#===================================================================================================
class Callback(object):
    '''
    Object that provides a way for others to connect in it and later call it to call
    those connected.

    .. note:: This implementation is improved in that it works directly accessing functions based
    on a key in an ordered dict, so, Register, Unregister and Contains are much faster than the
    old callback.

    .. note:: it only stores weakrefs to objects connected

    .. note:: __slots__ added, so, it cannot have weakrefs to it (but as it stores weakrefs
        internally, that shouldn't be a problem). If weakrefs are really needed,
        __weakref__ should be added to the slots.
    '''

    __slots__ = [
        '_callbacks',
        '_handle_errors',
        '__weakref__'  # We need this to be able to add weak references to callback objects.
    ]

    #This constant defines whether the errors will be handled by default in all Callbacks or not.
    #Handled errors won't stop the execution if an exception happens when executing the callbacks.
    DEFAULT_HANDLE_ERRORS = True

    INFO_POS_FUNC_OBJ = 0
    INFO_POS_FUNC_FUNC = 1
    INFO_POS_FUNC_CLASS = 2

    def __init__(self, handle_errors=None):
        '''
        :param bool handle_errors:
            If True, any errors raised while calling the callbacks will not stop the execution
            flow of the application, but will call the system error handler so that error
            does not fail silently.
        '''
        if handle_errors is None:
            handle_errors = self.DEFAULT_HANDLE_ERRORS
        self._handle_errors = handle_errors
        # _callbacks is no longer lazily created: This makes the creation a bit slower, but
        # everything else is faster (as having to check for hasattr each time is slow).
        self._callbacks = odict()


    def _GetKey(self, func):
        '''
        :param object func:
            The function for which we want the key.

        :rtype: object
        :returns:
            Returns the key to be used to access the object.

        .. note:: The key is guaranteed to be unique among the living objects, but if the object
        is garbage collected, a new function may end up having the same key.
        '''
        if func.__class__ == _CallbackWrapper:
            func = func.OriginalMethod()

        try:
            if func.im_self is not None:
                # bound method
                return (id(func.im_self), id(func.im_func), id(func.im_class))
            else:
                return (id(func.im_func), id(func.im_class))

        except AttributeError:
            # not a method -- a callable: create a strong reference (the CallbackWrapper
            # is depending on this behaviour... is it correct?)
            return id(func)


    def _GetInfo(self, func):
        '''
        :rtype: tuple(func_obj, func_func, func_class)
        :returns:
            Returns a tuple with the information needed to call a method later on (close to the
            WeakMethodRef, but a bit more specialized -- and faster for this context).
        '''
        #Note: if it's a _CallbackWrapper, we want to register it and not the 'original method'
        #at this point
        try:
            if func.im_self is not None:
                # bound method
                return (weakref.ref(func.im_self), func.im_func, func.im_class)
            else:
                # unbound method
                return (None, func.im_func, func.im_class)
        except AttributeError:
            # not a method -- a callable: create a strong reference (the CallbackWrapper
            # is depending on this behaviour... is it correct?)
            return (None, func, None)


    def __call__(self, *args, **kwargs):  # @DontTrace
        '''
        Calls every registered function with the given args and kwargs.
        '''
        callbacks = self._callbacks
        if not callbacks:
            return

        #Note: There's a copy of this code in the _CalculateToCall method below. It's a copy
        #because we don't want to had a function call overhead here.
        to_call = []


        for id, info_and_extra_args in callbacks.items(): #iterate in a copy

            info = info_and_extra_args[0]
            func_obj = info[self.INFO_POS_FUNC_OBJ]
            if func_obj is not None:
                #Ok, we have a self.
                func_obj = func_obj()
                if func_obj is None:
                    #self is dead
                    del callbacks[id]
                else:
                    func_func = info[self.INFO_POS_FUNC_FUNC]
                    to_call.append(
                        (
                            new.instancemethod(func_func, func_obj, info[self.INFO_POS_FUNC_CLASS]),
                            info_and_extra_args[1]
                        )
                    )
            else:
                func_func = info[self.INFO_POS_FUNC_FUNC]
                if func_func.__class__ == _CallbackWrapper:
                    #The instance of the _CallbackWrapper already died! (func_obj is None)
                    original_method = func_func.OriginalMethod()
                    if original_method is None:
                        del callbacks[id]
                        continue

                #No self: either classmethod or just callable
                to_call.append((func_func, info_and_extra_args[1]))

        #let's keep the 'if' outside of the iteration...
        if self._handle_errors:
            for func, extra_args in to_call:
                try:
                    func(*extra_args + args, **kwargs)
                except Exception, e:
                    from _callback import ErrorNotHandledInCallback
                    #Note that if some error shouldn't really be handled here, clients can raise
                    #a subclass of ErrorNotHandledInCallback
                    if isinstance(e, ErrorNotHandledInCallback):
                        Reraise(e, 'Error while trying to call %r' % func)
                    else:
                        from _callback import HandleErrorOnCallback
                        HandleErrorOnCallback(func, *extra_args + args, **kwargs)
        else:
            for func, extra_args in to_call:
                try:
                    func(*extra_args + args, **kwargs)
                except Exception, e:
                    Reraise(e, 'Error while trying to call %r' % func)


    def _CalculateToCall(self):
        '''
        Copy of the code above so that subclasses can use it (we don't want the overhead in the
        call above).
        '''
        callbacks = self._callbacks
        if not callbacks:
            return

        to_call = []

        for id, info_and_extra_args in callbacks.items(): #iterate in a copy

            info = info_and_extra_args[0]
            func_obj = info[self.INFO_POS_FUNC_OBJ]
            if func_obj is not None:
                #Ok, we have a self.
                func_obj = func_obj()
                if func_obj is None:
                    #self is dead
                    del callbacks[id]
                else:
                    func_func = info[self.INFO_POS_FUNC_FUNC]
                    to_call.append(
                        (
                            new.instancemethod(func_func, func_obj, info[self.INFO_POS_FUNC_CLASS]),
                            info_and_extra_args[1]
                        )
                    )
            else:
                func_func = info[self.INFO_POS_FUNC_FUNC]
                if func_func.__class__ == _CallbackWrapper:
                    #The instance of the _CallbackWrapper already died! (func_obj is None)
                    original_method = func_func.OriginalMethod()
                    if original_method is None:
                        del callbacks[id]
                        continue

                #No self: either classmethod or just callable
                to_call.append((func_func, info_and_extra_args[1]))

        return to_call


    #Should be OK using a mutable object here as it'll only be accessed internally and
    #should never have anything appended.
    _EXTRA_ARGS_CONSTANT = tuple()


    def Register(self, func, extra_args=_EXTRA_ARGS_CONSTANT):
        '''
        Registers a function in the callback.

        :param object func:
            Method or function that will be called later.

        :param list(object) extra_args:
            A list with the objects to be used
        '''
        if isinstance(func, mock.MagicMock):
            # Because mock objects always return an
            # object when an attribute is accessed, we will end up calling it incorrectly later on
            # because we check for that attribute (see _GetKey
            # and _GetInfo) to decide if "func" is either a function, method or general callable.
            # Removing "im_func" from the mock will make Callback treat it as a general callable,
            # which is what we want during testing.
            del func.im_self
        if extra_args is not self._EXTRA_ARGS_CONSTANT:
            extra_args = tuple(extra_args)

        key = self._GetKey(func)
        callbacks = self._callbacks
        callbacks.pop(key, None) #Remove if it exists
        callbacks[key] = (self._GetInfo(func), extra_args)


    def Contains(self, func):
        '''
        :param object func:
            The function that may be contained in this callback.

        :rtype: bool
        :returns:
            True if the function is already registered within the callbacks and False
            otherwise.
        '''
        key = self._GetKey(func)

        callbacks = self._callbacks

        info_and_extra_args = callbacks.get(key)
        if info_and_extra_args is None:
            return False

        #We must check if it's actually the same, because it may be that the ids we've gotten for
        #this object were actually from a garbage-collected function that was previously registered.

        info = info_and_extra_args[0]
        func_obj = info[self.INFO_POS_FUNC_OBJ]
        func_func = info[self.INFO_POS_FUNC_FUNC]
        if func_obj is not None:
            #Ok, we have a self.
            func_obj = func_obj()
            if func_obj is None:
                #self is dead
                del callbacks[key]
                return False
            else:
                return func == new.instancemethod(
                    func_func, func_obj, info[self.INFO_POS_FUNC_CLASS])
        else:
            if func_func.__class__ == _CallbackWrapper:
                #The instance of the _CallbackWrapper already died! (func_obj is None)
                original_method = func_func.OriginalMethod()
                if original_method is None:
                    del callbacks[key]
                    return False
                return original_method == func

            if func_func == func:
                return True
            try:
                f = func.im_func
            except AttributeError:
                return False
            else:
                return f == func_func

        raise AssertionError('Should not get here!')


    def Unregister(self, func):
        '''
        Unregister a function previously registered with Register.

        :param object func:
            The function to be unregistered.
        '''
        key = self._GetKey(func)

        try:
            #As there can only be 1 instance with the same id alive, it should be OK just
            #deleting it directly (because if there was a dead reference pointing to it it will
            #be already dead anyways)
            del self._callbacks[key]
        except (KeyError, AttributeError):
            # Even when unregistering some function that isn't registered we shouldn't trigger an
            # exception, just do nothing
            pass


    def UnregisterAll(self):
        '''
        Unregisters all functions
        '''
        self._callbacks.clear()


    def __len__(self):
        return len(self._callbacks)


