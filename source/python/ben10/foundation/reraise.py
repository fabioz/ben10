from __future__ import unicode_literals
'''
Inspired by http://www.thescripts.com/forum/thread46361.html
'''


#===================================================================================================
# Reraise
#===================================================================================================
def Reraise(exception, message, separator='\n'):
    '''
    Raised the same exception given, with an additional message.

    :param Exception exception:
        Original exception being raised with additional messages

    :param unicode message:
        Message to be added to the given exception

    :param unicode separator:
        String separating `message` from the `exception`'s original message.

    e.g.
        try:
            raise RuntimeError('original message')
        except Exception, e:
            Reraise(e, 'message')

        >>> RuntimeError:
        >>> message
        >>> original message

        try:
            raise RuntimeError('original message')
        except Exception, e:
            Reraise(e, '[message]', separator=' ')

        >>> RuntimeError:
        >>> [message] original message
    '''
    import sys

    # Get the current message
    try:
        current_message = unicode(exception)
    except UnicodeDecodeError:
        import locale
        current_message = bytes(exception).decode(locale.getpreferredencoding())

    # Build the new message
    if not current_message.startswith(separator):
        current_message = separator + current_message
    message = '\n' + message + current_message

    # Handling for special case, some exceptions have different behaviors.
    if isinstance(exception, SPECIAL_EXCEPTIONS):
        exception = __GetReraisedException(exception, message)
    else:
        # In Python 2.5 overriding the exception "__str__" has no effect in "unicode()". Instead, we
        # must change the "args" attribute which is used to build the string representation.
        # Even though the documentation says "args" will be deprecated, it uses its first argument
        # in unicode() implementation and not "message".
        exception.message = message
        exception.args = (exception.message,)

    # Reraise the exception with the EXTRA message information
    raise exception, None, sys.exc_info()[-1]



#===================================================================================================
# __GetReraisedException
#===================================================================================================
# These exception classes cannot have their message altered in the traditional way
SPECIAL_EXCEPTIONS = (
    KeyError,
    OSError,
    SyntaxError,
    UnicodeDecodeError,
    UnicodeEncodeError,
)
def __GetReraisedException(exception, message):
    '''
    Reraises 'special' exceptions by creating a new subclass with the same 'exception.args', but
    a hardcoded '__str__'

    New exception being raised is named 'Reraised' + exception.__class__.__name__

    :param Exception exception:
        .. seealso:: Reraise

    :param unicode message:
        .. seealso:: Reraise

    :return Exception:
        A new exception instance that subclasses `exception.__class__`
    '''
    new_exception = type(
        # Setting class name
        bytes('Reraised' + exception.__class__.__name__),

        # Setting superclass
        (exception.__class__,),

        # Setting class dict
        {
            '__str__': lambda *args: message,
        }
    )
    return new_exception(*exception.args)
