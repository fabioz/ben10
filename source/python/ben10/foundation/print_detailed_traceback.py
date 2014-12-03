from __future__ import unicode_literals
import locale
import sys



#===================================================================================================
# PrintDetailedTraceback
#===================================================================================================
def PrintDetailedTraceback(exc_info=None, stream=None, max_levels=None, max_line_width=120, omit_locals=False):
    '''
    Prints a more detailed traceback than Python's original one showing, for each frame, also the
    locals at that frame and their values.

    :type exc_info: (type, exception, traceback)
    :param exc_info:
        The type of the exception, the exception instance and the traceback object to print. Exactly
        what is returned by sys.exc_info(), which is used if this param is not given.

    :type stream: file-like object
    :param stream:
        File like object to print the traceback to.

    :param int max_levels:
        The maximum levels up in the traceback to display. If None, print all levels.

    :param int max_line_width:
        The maximum line width for each line displaying a local variable in a stack frame. Each
        line displaying a local variable will be truncated at the middle to avoid cluttering
        the display;

    :param bool omit_locals:
        If true it will omit function arguments and local variables from traceback. It is an option
        especially interesting if an error during a function may expose sensitive data, like an user
        private information as a password. Defaults to false as most cases won't be interested in
        this feature.
    '''
    if stream is None:
        stream = sys.stderr

    if exc_info is None:
        exc_info = sys.exc_info()

    exc_type, exception, tb = exc_info

    if exc_type is None or tb is None:
        # if no exception is given, or no traceback is available, let the print_exception deal
        # with it.
        import traceback
        traceback.print_exception(exc_type, exception, tb, max_levels, stream)
        return

    # find the bottom node of the traceback
    while True:
        if not tb.tb_next:
            break
        tb = tb.tb_next

    # obtain the stack frames, up to max_levels
    stack = []
    f = tb.tb_frame
    levels = 0
    while f:
        stack.append(f)
        f = f.f_back
        levels += 1
        if max_levels is not None and levels >= max_levels:
            break
    stack.reverse()

    stream.write('Traceback (most recent call last):\n')

    for frame in stack:
        params = dict(
            name=frame.f_code.co_name.decode(locale.getpreferredencoding()),
            filename=frame.f_code.co_filename.decode(locale.getpreferredencoding()),
            lineno=frame.f_lineno,
        )
        stream.write('  File "%(filename)s", line %(lineno)d, in %(name)s\n' % params)
        try:
            lines = file(frame.f_code.co_filename).readlines()
            line = lines[frame.f_lineno - 1]
        except:
            pass  # don't show the line source
        else:
            stream.write('    %s\n' % line.strip())

        if not omit_locals:
            # string used to truncate string representations of objects that exceed the maximum
            # line size
            trunc_str = '...'
            for key, value in sorted(frame.f_locals.iteritems()):
                ss = '            %s = ' % key
                # be careful to don't generate any exception while trying to get the string
                # representation of the value at the stack, because raising an exception here
                # would shadow the original exception
                try:
                    val_repr = repr(value).decode(locale.getpreferredencoding())
                except:
                    val_repr = '<ERROR WHILE PRINTING VALUE>'
                else:
                    # if the val_pre exceeds the maximium size, we truncate it in the middle
                    # using trunc_str, showing the start and the end of the string:
                    # "[1, 2, 3, 4, 5, 6, 7, 8, 9]" -> "[1, 2, ...8, 9]"
                    if len(ss) + len(val_repr) > max_line_width:
                        space = max_line_width - len(ss) - len(trunc_str)
                        middle = int(space / 2)
                        val_repr = val_repr[:middle] + trunc_str + val_repr[-(middle + len(trunc_str)):]

                stream.write(ss + val_repr + '\n')

    #
    # Replaced "exception" by "exception.message" because "unicode(exception)" generate an
    # UnicodeEncodeError when the exception is encoding using unicode (utf-8).
    # That problem occurred with Apache + Django translation.
    #
    if hasattr(exception, 'message'):
        message = exception.message

    else:
        message = unicode(exception)  # Default behavior

    stream.write('%s: %s\n' % (exc_type.__name__, message))
