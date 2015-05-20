from __future__ import unicode_literals
from ben10.bytes_only_environ_wrapper import BytesOnlyEnvironWrapper
from ben10.execute import ExecutePython
import os



def testIfOsEnvironIsReplacedByWrapper():
    '''
    Importing ben10 module should replace os.environ
    '''
    assert isinstance(os.environ, BytesOnlyEnvironWrapper)


def testIfWrapperEncodesUnicodeVariableWhenSettingDefault(unicode_samples):
    os.environ.setdefault('MY_UNICODE_VAR', unicode_samples.UNICODE_MULTIPLE_LANGUAGES)
    _CheckIfEnvVarTypeIsBytes('MY_UNICODE_VAR', unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


def testIfWrapperEncodesUnicodeVariableWhenSettingVariable(unicode_samples):
    os.environ['MY_UNICODE_VAR'] = unicode_samples.UNICODE_MULTIPLE_LANGUAGES
    _CheckIfEnvVarTypeIsBytes('MY_UNICODE_VAR', unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


def _CheckIfEnvVarTypeIsBytes(name, value):
    obtained_value = os.environ[name]
    obtained_key = os.environ.keys()[os.environ.keys().index(name)]

    assert obtained_value == value.encode('utf-8')
    assert isinstance(obtained_value, bytes)
    assert isinstance(obtained_key, bytes)


def testIfAPythonProgramCanDecodeUtf8EnvVar(embed_data):
    python_script = embed_data['testIfAPythonProgramCanDecodeUtf8EnvVar.py']

    output, _retcode = ExecutePython(python_script)

    assert output == 'OK\n', "Unexpected output:\n%s" % output
