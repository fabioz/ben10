from __future__ import unicode_literals
#===================================================================================================
# Placeholder for the "tr" function
# The "tr" function is implemented by xgui20.translate
# BEN10 should not depend on Qt, but regarding translation, it depends indirectly because of the use
# of Qt translation mechanism.
#
# The "tr" function must be defined and used solely as a builtin symbol and *never* as a direct
# import. Failing to do so will break the transation mechanism.
#===================================================================================================
def _tr(text, context=None):
    return text

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

if not hasattr(builtins, 'tr'):
    builtins.tr = _tr



# Adding an alias to `open`: since use of bare `open` is deprecated since we ported to unicode-only
# strings, this alias exists so code that can't work with io.open (usually because it passes the file
# object to C++, which won't work with the wrapper object returned by io.open) use this to
# communicate this intention
builtins.builtin_open = open

import sys

def win32_unicode_argv():
    """Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
    strings.

    Versions 2.x of Python don't support Unicode in sys.argv on
    Windows, with the underlying Windows API instead replacing multi-byte
    characters with '?'.
    """

    from ctypes import POINTER, byref, cdll, c_int, windll
    from ctypes.wintypes import LPCWSTR, LPWSTR

    GetCommandLineW = cdll.kernel32.GetCommandLineW
    GetCommandLineW.argtypes = []
    GetCommandLineW.restype = LPCWSTR

    CommandLineToArgvW = windll.shell32.CommandLineToArgvW
    CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
    CommandLineToArgvW.restype = POINTER(LPWSTR)

    cmd = GetCommandLineW()
    argc = c_int(0)
    argv = CommandLineToArgvW(cmd, byref(argc))
    if argc.value > 0:
        # Remove Python executable and commands if present
        start = argc.value - len(sys.argv)
        return [argv[i] for i in
                xrange(start, argc.value)]

sys.argv = win32_unicode_argv()
