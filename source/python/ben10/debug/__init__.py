def IsPythonDebug():
    '''
    Returns True if it is running under a debug version of the python interpreter
    (i.e., compiled with macro Py_DEBUG defined, generally the python_d executable).
    '''
    import sys



    return hasattr(sys, 'gettotalrefcount')  # Only exists in debug versions
