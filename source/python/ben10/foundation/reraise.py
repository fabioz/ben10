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

    try:
        # Handling for special case, some exceptions have different behaviors.
        exception = _SPECIAL_EXCEPTION_MAP[exception.__class__](message, exception.args)
    except KeyError:
        # In Python 2.5 overriding the exception "__str__" has no effect in "unicode()". Instead, we
        # must change the "args" attribute which is used to build the string representation.
        # Even though the documentation says "args" will be deprecated, it uses its first argument
        # in unicode() implementation and not "message".
        exception.message = message
        exception.args = (exception.message,)

    # Reraise the exception with the EXTRA message information
    raise exception, None, sys.exc_info()[-1]



#===================================================================================================
# SPECIAL_EXCEPTIONS
#===================================================================================================
# [[[cog
# SPECIAL_EXCEPTIONS = (
#     KeyError,
#     OSError,
#     SyntaxError,
#     UnicodeDecodeError,
#     UnicodeEncodeError,
# )
# from ben10.foundation.string import Dedent
# exception_map = []
# for exception_class in SPECIAL_EXCEPTIONS:
#     superclass_name = exception_class.__name__
#     exception_map.append('\n        ' + superclass_name + ' : Reraised' + superclass_name + ',')
#     cog.out(Dedent(
#         '''
#         class Reraised%(superclass_name)s(%(superclass_name)s):
#             def __init__(self, message, original_args):
#                 %(superclass_name)s.__init__(self, *original_args)
#                 self.message = message
#
#             def __str__(self):
#                 return self.message
#
#
#         '''% locals()
#     ))
# cog.out(Dedent(
#     '''
#     _SPECIAL_EXCEPTION_MAP = {%s
#     }
#     ''' % ''.join(exception_map)
# ))
# ]]]
class ReraisedKeyError(KeyError):
    def __init__(self, message, original_args):
        KeyError.__init__(self, *original_args)
        self.message = message

    def __str__(self):
        return self.message

class ReraisedOSError(OSError):
    def __init__(self, message, original_args):
        OSError.__init__(self, *original_args)
        self.message = message

    def __str__(self):
        return self.message

class ReraisedSyntaxError(SyntaxError):
    def __init__(self, message, original_args):
        SyntaxError.__init__(self, *original_args)
        self.message = message

    def __str__(self):
        return self.message

class ReraisedUnicodeDecodeError(UnicodeDecodeError):
    def __init__(self, message, original_args):
        UnicodeDecodeError.__init__(self, *original_args)
        self.message = message

    def __str__(self):
        return self.message

class ReraisedUnicodeEncodeError(UnicodeEncodeError):
    def __init__(self, message, original_args):
        UnicodeEncodeError.__init__(self, *original_args)
        self.message = message

    def __str__(self):
        return self.message

_SPECIAL_EXCEPTION_MAP = {
    KeyError : ReraisedKeyError,
    OSError : ReraisedOSError,
    SyntaxError : ReraisedSyntaxError,
    UnicodeDecodeError : ReraisedUnicodeDecodeError,
    UnicodeEncodeError : ReraisedUnicodeEncodeError,
}
# [[[end]]] (checksum: 3e2d0264f057a4a0d871c0eba1b5b4a4)
