from __future__ import unicode_literals
'''
Inspired in a code obtained from http://www.thescripts.com/forum/thread46361.html
'''



#===================================================================================================
# ReraiseKeyError
#===================================================================================================
class ReraiseKeyError(KeyError):
    '''
    Replaces KeyError storing the original message. This is used to keep the EOL in the message
    '''

    def __init__(self, message):
        KeyError.__init__(self, message)
        self._message = message

    def __str__(self):
        return self._message



#===================================================================================================
# ReraiseSyntaxError
#===================================================================================================
class ReraiseSyntaxError(SyntaxError):
    '''
    Replaces SyntaxError storing the original message. This is used because a syntax error
    does not use the 'message' attribute to change the message of the error.
    '''

    def __init__(self, message):
        SyntaxError.__init__(self, message)
        self._message = message

    def __str__(self):
        return self._message



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
    current_message = unicode(exception)

    # Build the new message
    if not current_message.startswith(separator):
        current_message = separator + current_message
    message = '\n' + message + current_message

    # Handling for special case, some exceptions have different behaviors.
    if isinstance(exception, OSError):
        # Create a new exception, since OSError behaves differently from other exceptions
        exception = RuntimeError(message)
    if isinstance(exception, KeyError):
        exception = ReraiseKeyError(message)
    elif isinstance(exception, SyntaxError):
        exception = ReraiseSyntaxError(message)
    else:
        # In Python 2.5 overriding the exception "__str__" has no effect in "unicode()". Instead, we
        # must change the "args" attribute which is used to build the string representation.
        # Even though the documentation says "args" will be deprecated, it uses its first argument
        # in unicode() implementation and not "message".
        exception.message = message
        exception.args = (exception.message,)

    # Reraise the exception with the EXTRA message information
    raise exception, None, sys.exc_info()[-1]
