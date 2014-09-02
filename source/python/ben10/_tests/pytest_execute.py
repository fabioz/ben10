from ben10.execute import Execute, ExecuteNoWait, PrintEnvironment
from ben10.filesystem import CreateFile
from ben10.foundation.string import Dedent
from cStringIO import StringIO
from txtout.txtout import TextOutput
import os
import pytest
import time



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def _AssertExecute(self, expected_output, *args, **kwargs):
        obtained_output = Execute(*args, **kwargs)
        self._AssertOutput(obtained_output, expected_output)


    def _AssertOutput(self, obtained_output, expected_output):
        # Removes known debug files:
        # - Coverage.py warning (travis-ci)
        # - pydev debugging: (inside PyCharm IDE)
        obtained_output = [i for i in obtained_output if not i.startswith("Coverage.py warning:")]
        obtained_output = [i for i in obtained_output if not i.startswith("pydev debugger: ")]
        obtained_output = '\n'.join(obtained_output)
        obtained_output = obtained_output.lstrip('\n')

        assert obtained_output == expected_output


    def testExecute(self, embed_data):
        execute_py = os.path.normcase(embed_data['testExecute.py_'])
        self._AssertExecute(
            Dedent(
                '''
                    testExecute
                    Arguments:
                    - 0 - %s
                    - 1 - alpha
                    - 2 - bravo
                ''' % execute_py
            ),
            ['python', execute_py, 'alpha', 'bravo']
        )

        # Tests string argument (instead of list) and its splitting algorithm.
        self._AssertExecute(
            Dedent(
                r'''
                    testExecute
                    Arguments:
                    - 0 - %s
                    - 1 - alpha
                    - 2 - bravo
                    - 3 - charlie is number three
                    - 4 - delta
                '''.replace('\\n', os.linesep) % execute_py
            ),
            'python %(testExecute.py_)s alpha bravo "charlie is number three" delta' % embed_data,
        )


    @pytest.mark.skipif('sys.platform != "win32"')
    def testExecuteBat(self, embed_data):

        def DoTest(slash):
            python_filename = os.path.normcase(embed_data.GetDataFilename('testExecute.py_', absolute=True))
            cmd_filename = embed_data.GetDataDirectory() + slash + 'testExecute.bat'
            self._AssertExecute(
                Dedent(
                    r'''
                        testExecute
                        Arguments:
                        - 0 - %s
                        - 1 - alpha
                        - 2 - bravo
                    '''.replace('\\n', os.linesep) % python_filename
                ),
                '%s alpha bravo' % cmd_filename,
            )

        DoTest('\\')

        # On Windows, we can't use local path using POSIX slashes.
        # It works for full path using POSIX slashes and local path with Windows slashes.
        # We had to change the command line if we find that case.
        DoTest('/')


    def testExecuteInput(self, embed_data):
        self._AssertExecute(
            Dedent(
                '''
                    testExecuteInput: Hello, planet earth!
                '''
            ),
            ['python', embed_data.GetDataFilename('testExecuteInput.py_')],
            input='planet earth',
        )


    def testExecuteAndEnviron(self, embed_data):
        self._AssertExecute(
            Dedent(
                '''
                    testExecuteAndEnviron: ALPHA: alpha
                    testExecuteAndEnviron: BRAVO: bravo
                '''
            ),
            ['python', embed_data.GetDataFilename('testExecuteAndEnviron.py_')],
            environ={
                'ALPHA' : 'alpha',
                'BRAVO' : 'bravo',
            },
        )


    @pytest.mark.slow
    def testExecuteNoWait(self, embed_data):
        text_filename = embed_data['testExecuteNoWait.txt']

        assert not os.path.isfile(text_filename)

        process = ExecuteNoWait(
            ['python', 'testExecuteNoWait.py_'],
            cwd=embed_data.GetDataDirectory(),
        )

        try:
            # The file was not yet generated since the scripts waits a bit to create it.
            assert not os.path.isfile(text_filename)

            # Wait for the script create the file
            for _i in xrange(50):
                time.sleep(0.1)
                if os.path.isfile(text_filename):
                    break
            else:
                # Now the file exists
                assert os.path.isfile(text_filename)
        finally:
            try:
                # Sleep again to avoid access error to the file testExecuteNotWait.txt
                time.sleep(0.3)
                process.terminate()
            except ImportError:
                raise  # Might happen if we can't find win32api
            except:
                pass  # Ignore any other errors on the kill process.


    def testPrintEnvironment(self, embed_data):
        # Create a fake environment
        environment = {
            'var1' : 'value1',
            'var2' : 'value2',
            'PATH' : os.pathsep.join(['path1', 'path2']),
            'PYTHONPATH' : os.pathsep.join(['pythonpath1', 'pythonpath2']),

        }

        # Prepare a controled text output
        stream = StringIO()
        output = TextOutput(stream)

        # Print environment
        PrintEnvironment(environment, output)

        # Save output to temp file
        obtained = embed_data.GetDataFilename('testPrintEnvironment.txt')
        CreateFile(obtained, contents=stream.getvalue())

        # Compare file contents
        embed_data.AssertEqualFiles(
            obtained,
            'testPrintEnvironment.expected.txt'
        )
