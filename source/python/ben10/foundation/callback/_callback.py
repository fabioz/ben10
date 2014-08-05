

#===================================================================================================
# FunctionNotRegisteredError
#===================================================================================================
class FunctionNotRegisteredError(RuntimeError):
    pass

#===================================================================================================
# ErrorNotHandledInCallback
#===================================================================================================
class ErrorNotHandledInCallback(RuntimeError):
    '''
    This class identifies an error that should not be handled in the callback.
    '''

#===================================================================================================
# HandleErrorOnCallback
#===================================================================================================
def HandleErrorOnCallback(func, *args, **kwargs):
    '''
    Called when there's some error calling a callback.

    :param object func:
        The callback called.

    :param list args:
        The arguments passed to the callback.

    :param dict kwargs:
        The keyword arguments passed to the callback.
    '''
    if hasattr(func, 'func_code'):
        name, filename, line = \
            func.func_code.co_name, func.func_code.co_filename, func.func_code.co_firstlineno
        #Use default python trace format so that we have linking on pydev.
        func = '\n  File "%s", line %s, in %s (Called from Callback)\n' % (filename, line, name)
    else:
        #That's ok, it may be that it's not really a method.
        func = '%r\n' % (func,)

    msg = 'Error while trying to call %s' % (func,)
    if args:
        msg += 'Args: %s\n' % (args,)
    if kwargs:
        msg += 'Kwargs: %s\n' % (kwargs,)

    from ben10.foundation import handle_exception
    handle_exception.HandleException(msg)

