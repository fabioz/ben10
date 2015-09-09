from __future__ import unicode_literals



def IsPythonDebug():
    '''
    Returns True if it is running under a debug version of the python interpreter
    (i.e., compiled with macro Py_DEBUG defined, generally the python_d executable).
    '''
    import sys

    return hasattr(sys, 'gettotalrefcount')  # Only exists in debug versions


def StripDebugRefs(text, end_only=True):
    """
    Strips the ref count text that is printed by the debug version of the python interpreter after
    program exit ("[1209 refs]" for example).

    Should be used by tests that capture output from a debug python interpreter, because it will
    print this characters resulting in different output when compared to the output produced
    by the release version of the interpreter.

    :param str text: text to strip debug information

    :param bool end_only: if True, only strips debug info from the end of the string, otherwise will
        search and strip the entire string from debug references.

    :rtype: str
    :return: stripped text
    """
    import re
    if IsPythonDebug():
        pattern = r'(\[\d+ refs\]\n?)'
        if end_only:
            pattern += '$'
        return re.sub(pattern, '', text)
    return text