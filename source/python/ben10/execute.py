from __future__ import unicode_literals
from ben10.filesystem import CanonicalPath, StandardizePath
from ben10.foundation.reraise import Reraise
from ben10.foundation.string import SafeSplit
from ben10.foundation.types_ import CheckType
from ben10.foundation.uname import GetExecutableDir
from cStringIO import StringIO
from multiprocessing.process import current_process
from txtout.txtout import TextOutput
import locale
import os
import shlex
import subprocess
import sys



#===================================================================================================
# Constants
#===================================================================================================
class COPY_FROM_ENVIRONMENT(object):
    '''
    Used as a constant for the environ dictionary value.
    See System.Execute@environ
    '''


# Default encoding for output_encoding and encoding parameters + error handler.
DEFAULT_ENCODING = locale.getpreferredencoding()
DEFAULT_ENCODING_ERRORS = 'replace'



#===================================================================================================
# PrintEnvironment
#===================================================================================================
def PrintEnvironment(environment, oss, sort_lists=True):
    '''
    Prints an environment dict into a given stream.

    :param dict(unicode->unicode) environment:
        Dictionary containing the environment
        variable_name - > value

    :param TextOutput oss:

    :param bool sort_lists:
        If True sorts the list values of environment variables.
    '''
    for i_variable_name, i_value in sorted(environment.items()):

        # Print the variable name as the header
        if sort_lists and os.pathsep in i_value:
            oss.P(i_variable_name + ' (sorted)', color='WHITE', top_margin=1)
        else:
            oss.P(i_variable_name, color='WHITE', top_margin=1)

        # Split paths to make them easier to read, if this isn't a sequence of paths, it will
        # simply be turned into a one-element list
        value_list = i_value.split(os.pathsep)

        if sort_lists:
            value_list = sorted(value_list)

        # Print all values in this variable
        for j_value in value_list:
            oss.I(j_value, indent=1)



#===================================================================================================
# EnvironmentContextManager
#===================================================================================================
class EnvironmentContextManager(object):
    '''
    Used with the 'with' statement.

    Sets the environment according to the given parameters and returns to the original environment
    once this section is over.
    '''

    def __init__(self, environ, update=False, change_sys_path=False):
        '''
        :param dict(unicode:unicode) environ:
            A dictionary of environment variables names and values

        :param bool update:
            If True only updates the current environment instead of replacing by environ.
            When exiting the update is undone and the environment is left intact.

        :param bool change_sys_path:
            If True, the sys PATH will be modified.
        '''
        self._old_environ = None
        self._old_sys_path = None

        self._new_environ = environ.copy()
        self._update = update
        self._change_sys_path = change_sys_path


    def __enter__(self):
        '''
        Copies the current environment and sets the given environment

        :param dict(unicode:unicode) environ:
            A dictionary of environment variables names and values
        '''
        self._old_environ = os.environ.copy()
        self._old_sys_path = sys.path[:]

        if not self._update:
            os.environ.clear()
            if self._change_sys_path:
                new_sys_path = sys.path[:]
                new_sys_path = map(CanonicalPath, new_sys_path)

                # Keeping python_home paths so this instance of Python continues to work.
                python_home = CanonicalPath(GetExecutableDir())
                new_sys_path = [i for i in new_sys_path if i.startswith(python_home)]

                sys.path = new_sys_path


        if self._update:
            # Merge some list variables to include new stuff
            def SetMerged(variable):
                merged_values = []

                new_value = self._new_environ.get(variable)
                if new_value is not None:
                    merged_values += new_value.split(os.pathsep)

                current_value = os.environ.get(variable)
                if current_value is not None:
                    merged_values += [
                        i for i
                        in current_value.split(os.pathsep)
                        if i not in merged_values
                    ]

                merged = os.pathsep.join(merged_values)
                if len(merged) > 0:
                    self._new_environ[variable] = merged

            SetMerged('PATH')
            SetMerged('PYTHONPATH')
            SetMerged('LD_LIBRARY_PATH')


        try:
            # Update environment variables
            os.environ.update(self._new_environ)

            if self._change_sys_path:
                sys.path += os.environ.get('PYTHONPATH', '').split(os.pathsep)

        except Exception, e:
            stream = StringIO()
            oss = TextOutput(stream)
            PrintEnvironment(self._new_environ, oss)
            Reraise(e, 'While entering an EnvironmentContextManager with:%s' % stream.getvalue())


    def __exit__(self, *args):
        '''
        Returns to the original environment.
        '''
        os.environ.clear()
        os.environ.update(self._old_environ)
        if self._change_sys_path:
            sys.path = self._old_sys_path



#===================================================================================================
# Execute
#===================================================================================================
def Execute(
        command_line,
        cwd=None,
        environ=None,
        extra_environ=None,
        input=None,  # @ReservedAssignment
        output_callback=None,
        output_encoding=None,
        output_encoding_errors=None,
        return_code_callback=None,
        shell=False,
        ignore_auto_quote=False,
        clean_eol=True,
        pipe_stdout=True,
    ):
    '''
    Executes a shell command

    :type command_line: list(unicode) or unicode
    :param command_line:
        List of command - line to execute, including the executable as the first element in the
        list.

    :param unicode cwd:
        The current working directory for the execution.

    :type environ: dict(unicode, unicode)
    :param environ:
        The environment variables available for the subprocess. This will replace the current
        environment.
        If a value is "COPY_FROM_ENVIRON" the value is replaced by the current environment
        value before executing the command - line.
        This dictionary will be modified by the Execute, so make sure that this is a copy of
        your actual data, not the original.

    :param dict(unicode:unicode) extra_environ:
        Environment variables (name, value) to add to the execution environment.

    :type input: unicode | None
    :param input:
        Text to send as input to the process.

    :param callback(unicode) output_callback:
        A optional callback called with the process output as it is generated.

    :param unicode output_encoding:
        Encoding used to decode output from subprocess.

    :param unicode output_encoding_errors:
        Error handler for output decoding (strict, ignore, replace, etc)

    :param callback(int) return_code_callback:
        A optional callback called with the execution return -code.
        The returned value is ignored.
        Because our return value is an iterator, the only way (I found) to give the user access
        to the return -code is via callback.

    :param bool shell:
        From subprocess.py:

        If shell is True, the specified command will be executed through the shell.

        On UNIX, with shell=False (default): In this case, the Popen class uses os.execvp() to
        execute the child program.  'command_line' should normally be a sequence.  A string will
        be treated as a sequence with the string as the only item (the program to execute).

        On UNIX, with shell=True: If 'command_line' is a string, it specifies the command string
        to execute through the shell.  If 'command_line' is a sequence, the first item specifies
        the command string, and any additional items will be treated as additional shell
        arguments.

    :param bool ignore_auto_quote:
        If True, passes the entire command line to subprocess as a single string, instead of
        a list of strings.

        This is useful when we want to avoid subprocess' algorithm that tries to handle quoting
        on its own when receiving a list of arguments.

        This way, we are able to use quotes as we wish, without having them escaped by subprocess.

    :param bool clean_eol:
        If True, output returned and passed to callback will be stripped of eols (\r \n)

    :param bool pipe_stdout:
        If True, pipe stdout so that it can be returned as a string and passed to the output
        callback. If False, stdout will be dumped directly to the console (preserving color),
        and the callback will not be called.

    :rtype: list(unicode)
    :returns:
        Returns the process execution output as a list of strings.
    '''
    output_encoding = output_encoding or DEFAULT_ENCODING
    output_encoding_errors = output_encoding_errors or DEFAULT_ENCODING_ERRORS

    popen = ProcessOpen(
        command_line,
        cwd=cwd,
        environ=environ,
        extra_environ=extra_environ,
        shell=shell,
        ignore_auto_quote=ignore_auto_quote,
        pipe_stdout=pipe_stdout,
    )

    try:
        result = []
        if popen.stdin:
            if input:
                try:
                    popen.stdin.write(input)
                except IOError, e:
                    import errno
                    if e.errno != errno.EPIPE and e.errno != errno.EINVAL:
                        raise
            popen.stdin.close()

        if popen.stdout:
            # TODO: EDEN-245: Refactor System.Execute and derivates (git, scons, etc)
            if clean_eol:  # Read one line at the time, and remove EOLs
                for line in iter(popen.stdout.readline, b""):
                    line = line.rstrip(b'\n\r')
                    line = line.decode(output_encoding, errors=output_encoding_errors)
                    if output_callback:
                        output_callback(line)
                    result.append(line)
            else:  # Read one char at a time, to keep \r and \n
                current_line = b''
                carriage = False
                for char in iter(lambda: popen.stdout.read(1), b""):

                    # Check if last line was \r, if not, print what we have
                    if char != b'\n' and carriage:
                        carriage = False
                        current_line = current_line.decode(output_encoding, errors=output_encoding_errors)
                        if output_callback:
                            output_callback(current_line)
                        result.append(current_line)
                        current_line = b''

                    current_line += char

                    if char == b'\r':
                        carriage = True

                    if char == b'\n':
                        current_line = current_line.decode(output_encoding, errors=output_encoding_errors)
                        if output_callback:
                            output_callback(current_line)
                        result.append(current_line)
                        carriage = False
                        current_line = b''

    finally:
        if popen.stdout:
            popen.stdout.close()

    popen.wait()
    if return_code_callback:
        return_code_callback(popen.returncode)

    return result



#===================================================================================================
# Execute2
#===================================================================================================
def Execute2(
        command_line,
        cwd=None,
        environ=None,
        extra_environ=None,
        output_callback=None,
        output_encoding=None,
        output_encoding_errors=None,
        shell=False,
        ignore_auto_quote=False,
        clean_eol=True,
        pipe_stdout=True,
    ):
    '''
    Executes a shell command.

    Use the same parameters as Execute, except callback_return_code, which is overridden in
    order to return the value.

    :rtype: tuple(list(unicode), int)
    :returns:
        Returns a 2 - tuple with the following values
            [0]: List of string printed by the process
            [1]: The execution return code
    '''
    return_code = [None]

    def CallbackReturnCode(ret):
        return_code[0] = ret

    output = Execute(
        command_line,
        cwd=cwd,
        environ=environ,
        extra_environ=extra_environ,
        output_callback=output_callback,
        output_encoding=output_encoding,
        output_encoding_errors=output_encoding_errors,
        return_code_callback=CallbackReturnCode,
        shell=shell,
        ignore_auto_quote=ignore_auto_quote,
        clean_eol=clean_eol,
        pipe_stdout=pipe_stdout,
    )

    return (output, return_code[0])



#===================================================================================================
# ExecuteNoWait
#===================================================================================================
def ExecuteNoWait(
        command_line,
        cwd=None,
        ignore_output=False,
        environ=None,
        extra_environ=None,
        new_console=False,
        **kwargs
    ):
    '''
    Execute the given command line without waiting for the process to finish its execution.

    :return:
        Returns the resulting of subprocess.Popen.
        Use result.pid for process-id.
    '''
    if cwd:
        kwargs['cwd'] = cwd

    kwargs['env'] = _GetEnviron(environ, extra_environ)

    if ignore_output:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.STDOUT

    if new_console:
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
        else:
            command_line = ['xterm', '-e'] + command_line

    try:
        return subprocess.Popen(command_line, **kwargs)
    except Exception, e:
        Reraise(
            e,
            'SystemSharedScript.ExecuteNoWait:\n'
            '  command_line: %s\n'
            '  cwd: %s\n'
            % (command_line, cwd))



#===================================================================================================
# GetSubprocessOutput
#===================================================================================================
def GetSubprocessOutput(
        command_line,
        cwd=None,
        environ=None,
        extra_environ=None,
        shell=False,
        ignore_auto_quote=False,
        binary=False,
        encoding=None,
        encoding_errors=None,
    ):
    '''
    New/simpler implementation for Execute.

    Execute a command-line returning the generated output and return code.

    :param binary:
        If True returns the process output as bytes, without handling the encoding.

    See ProcessOpen for parameter descriptions.

    :return tuple(unicode|str, int):
        Returns the sub-process output (merging stdout and stderr) and the return code.
    '''
    encoding = encoding or DEFAULT_ENCODING
    encoding_errors = encoding_errors or DEFAULT_ENCODING_ERRORS

    popen = ProcessOpen(
        command_line,
        cwd=cwd,
        environ=environ,
        extra_environ=extra_environ,
        shell=shell,
        ignore_auto_quote=ignore_auto_quote,
        pipe_stdout=True,
    )
    output, _stderr = popen.communicate()
    retcode = popen.poll()
    if not binary:
        output = output.decode(encoding, errors=encoding_errors)
    return output, retcode



def ProcessOpen(
        command_line,
        cwd=None,
        environ=None,
        extra_environ=None,
        shell=False,
        ignore_auto_quote=False,
        pipe_stdout=True,
    ):
    '''
    Executes a shell command

    :type command_line: list(unicode) or unicode
    :param command_line:
        List of command - line to execute, including the executable as the first element in the
        list.

    :param unicode cwd:
        The current working directory for the execution.

    :type environ: dict(unicode, unicode)
    :param environ:
        The environment variables available for the subprocess. This will replace the current
        environment.
        If a value is "COPY_FROM_ENVIRON" the value is replaced by the current environment
        value before executing the command - line.
        This dictionary will be modified by the Execute, so make sure that this is a copy of
        your actual data, not the original.

    :param dict(unicode:unicode) extra_environ:
        Environment variables (name, value) to add to the execution environment.

    :param bool shell:
        From subprocess.py:

        If shell is True, the specified command will be executed through the shell.

        On UNIX, with shell=False (default): In this case, the Popen class uses os.execvp() to
        execute the child program.  'command_line' should normally be a sequence.  A string will
        be treated as a sequence with the string as the only item (the program to execute).

        On UNIX, with shell=True: If 'command_line' is a string, it specifies the command string
        to execute through the shell.  If 'command_line' is a sequence, the first item specifies
        the command string, and any additional items will be treated as additional shell
        arguments.

    :param bool ignore_auto_quote:
        If True, passes the entire command line to subprocess as a single string, instead of
        a list of strings.

        This is useful when we want to avoid subprocess' algorithm that tries to handle quoting
        on its own when receiving a list of arguments.

        This way, we are able to use quotes as we wish, without having them escaped by subprocess.

    :param bool pipe_stdout:
        If True, pipe stdout so that it can be returned as a string and passed to the output
        callback. If False, stdout will be dumped directly to the console (preserving color),
        and the callback will not be called.

    :returns subprocess.Popen:
    '''
    locale_encoding = locale.getpreferredencoding()

    def CmdLineStr(cmd_line):
        if isinstance(cmd_line, unicode):
            return '    ' + cmd_line
        return '    ' + '\n    '.join(cmd_line)

    def EncodeWithLocale(value):
        if isinstance(value, unicode):
            return value.encode(locale_encoding)
        if isinstance(value, list):
            return [x.encode(locale_encoding) for x in value]

    def DecodeWithLocale(value):
        if isinstance(value, bytes):
            return value.decode(locale_encoding)
        if isinstance(value, list):
            return [x.decode(locale_encoding) for x in value]

    def EnvStr(env):
        result = ''
        for i, j in sorted(env.items()):
            if os.sep in j:
                j = '\n    * ' + '\n    * '.join(sorted(j.split(os.pathsep)))
            result += '  - %s = %s\n' % (i, j)
        return result

    # We accept strings as the command_line.
    is_string_command_line = isinstance(command_line, unicode)

    # Handle string/list command_list
    if ignore_auto_quote and not is_string_command_line:
        # ... with ignore_auto_quote we want a string command_line... but it came as a list
        #     NOTE: This simple join may cause problems since we can have spaces in a argument. The correct way of
        #           doing would be something like "shlex.join" (that does not exists, by the way).
        command_line = ' '.join(command_line)

    elif not ignore_auto_quote and is_string_command_line:
        # ... without ignore_auto_quote we want a list command_line... but it came as a string
        if sys.platform == 'win32':
            command, arguments = SafeSplit(command_line, ' ', 1)
            assert command.count('"') != 1, 'Command may have spaces in it. Use list instead of string.'

            # Always use normpath for command, because Windows does not like posix slashes
            command = StandardizePath(command)
            command = os.path.normpath(command)

            # shlex cannot handle non-ascii unicode strings
            command_line = [command] + DecodeWithLocale(shlex.split(EncodeWithLocale(arguments)))
        else:
            # shlex cannot handle non-ascii unicode strings
            command_line = DecodeWithLocale(shlex.split(EncodeWithLocale(command_line)))

    if cwd is None:
        cwd = os.getcwd()

    environ = _GetEnviron(environ, extra_environ)

    # Make sure the command line is correctly encoded. This always uses locale.getpreferredencoding()
    try:
        return subprocess.Popen(
            EncodeWithLocale(command_line),
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE if pipe_stdout else None,
            stderr=subprocess.STDOUT,
            env=environ,
            bufsize=0,
            shell=shell,
        )
    except Exception, e:
        if isinstance(e, OSError):
            # Fix encoding from OSErrors. They also come in locale.getpreferredencoding()
            # It's hard to change error messages in OSErrors, so we raise something else.
            e = RuntimeError(unicode(str(e), encoding=locale_encoding, errors='replace'))

        Reraise(
            e,
            'While executing "System.Execute":\n'
            '  environment::\n'
            '%s\n'
            '  current working dir::\n'
            '    %s\n\n'
            '  command_line::\n'
            '%s\n'
            % (EnvStr(environ), cwd, CmdLineStr(command_line))
        )


#===================================================================================================
# GetUnicodeArgv
#===================================================================================================
def GetUnicodeArgv():
    '''
    This function should be executed as early as possible (e.g. in your main function).
    If the sys.argv is not in unicode already it tries to decode it.

    Windows is a special case and we don't even look into sys.argv to get the unicode version. See
    L{_GetWindowsUnicodeArgv} for more details.

    :rtype: list(unicode)
    :returns:
        The sys.argv content in unicode.
    '''
    # The unicode argv extracted from windows is valid only for the main process.
    if current_process().name == 'MainProcess':
        if sys.platform == 'win32':
            return _GetWindowsUnicodeArgv()
        else:
            return _GetLinuxUnicodeArgv()
    # If it is a subprocess it should be already in unicode.
    else:
        _CheckIfSysArgvIsAlreadyUnicode()
        return sys.argv


def _GetWindowsUnicodeArgv():
    '''
    This code was taken from:

    http://stackoverflow.com/questions/846850/read-unicode-characters-from-command-line-arguments-in-python-2-x-on-windows

    Uses shell32.GetCommandLineArgvW to get sys.argv as a list of Unicode
    strings.

    Versions 2.x of Python don't support Unicode in sys.argv on
    Windows, with the underlying Windows API instead replacing multi-byte
    characters with '?'.

    :rtype: list(unicode)
        The sys.argv as unicode.
    '''

    from ctypes import POINTER, byref, c_int, cdll, windll
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


def _GetLinuxUnicodeArgv():
    '''
    :rtype: list(unicode)
        The sys.argv converted to unicode using utf-8.
    '''
    return [arg.decode('utf-8') for arg in sys.argv]


def _CheckIfSysArgvIsAlreadyUnicode():
    message = 'In a subprocess sys.argv should be already in unicode. sys.argv="%s"' % sys.argv
    for arg in sys.argv:
        CheckType(arg, unicode, message)



def _GetEnviron(environ=None, extra_environ=None):
    '''
    :param environ:
        .. seealso:: Execute

    :param extra_environ:
        .. seealso:: Execute

    :return dict(bytes, bytes):
        Environment dict to pass to subprocess.

        This combines `environ` and `extra_environ` and converts all strings to bytes (subprocess
        does not accept unicode).
    '''
    if environ is None:
        environ = os.environ.copy()
    else:
        for i_name, i_value in environ.items():
            if i_value is COPY_FROM_ENVIRONMENT:
                env_value = os.environ.get(bytes(i_name))
                if env_value is None:
                    del environ[i_name]
                else:
                    environ[i_name] = env_value

    if extra_environ:
        assert COPY_FROM_ENVIRONMENT not in extra_environ.values()
        environ.update(extra_environ)

    # subprocess does not accept unicode strings in the environment
    environ = {bytes(key) : bytes(value) for key, value in environ.iteritems()}

    return environ



#===================================================================================================
# ExecutePython
#===================================================================================================
def ExecutePython(
        filename,
        parameters=None,
        cwd=None,
        environ=None,
        extra_environ=None,
        python_executable='python',
    ):
    '''
    Executes a python script.

    Handle some details regarding handling Python execution such as:

    * Required environment variables
      On linux we need LD_LIBRARY_PATH copied to the sub-process in order to properly import
      non-default python modules.

    * PYTHONIOENCODING definition
      We define this environment variable in order to TRY to make both this and the sub-process talk
      with the same encoding.

    :param unicode filename:
        The name of the python script to execute

    :param bool debug:
        If True uses the debug version of Python.

    .. seealso:: ben10.execute.Execute
        For param and return doc
    '''
    import sys

    command_line = [
        python_executable,
        '-u',  # Use unbuffered mode in Python, to make sure we capture output as it arrives
        filename
    ]
    if parameters is not None:
        command_line += parameters

    extra_environ = extra_environ or {}
    # Set output encoding to our default expected encoding in Execute
    extra_environ['PYTHONIOENCODING'] = DEFAULT_ENCODING

    # Make sure we have LD_LIBRARY_PATH in the user-given environ on linux.
    if sys.platform != 'win32' and environ is not None:
        environ.setdefault('LD_LIBRARY_PATH', COPY_FROM_ENVIRONMENT)

    # TODO: Find a better way to make it work on travis-ci. Today sub-scripts can't find ben10's imports.
    if 'TRAVIS_BUILD_DIR' in os.environ:
        extra_environ['PYTHONPATH'] = os.path.expandvars(b'$TRAVIS_BUILD_DIR/source/python')

    return GetSubprocessOutput(
        command_line,
        cwd=cwd,
        environ=environ,
        extra_environ=extra_environ,
    )
