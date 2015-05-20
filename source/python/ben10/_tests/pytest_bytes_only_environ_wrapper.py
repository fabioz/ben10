from __future__ import unicode_literals
from ben10.bytes_only_environ_wrapper import BytesOnlyEnvironWrapper
from ben10.execute import ExecutePython
import os


VAR_NAME = 'MY_UNICODE_VAR'


def testIfOsEnvironIsReplacedByWrapper():
    '''
    Importing ben10 module should replace os.environ
    '''
    assert isinstance(os.environ, BytesOnlyEnvironWrapper)


def testIfWrapperEncodesUnicodeVariableWhenSettingDefault(unicode_samples):
    os.environ.setdefault(VAR_NAME, unicode_samples.UNICODE_MULTIPLE_LANGUAGES)
    _CheckIfEnvVarTypeIsBytes(VAR_NAME, unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


def testIfWrapperEncodesUnicodeVariableWhenSettingVariable(unicode_samples):
    os.environ[VAR_NAME] = unicode_samples.UNICODE_MULTIPLE_LANGUAGES
    _CheckIfEnvVarTypeIsBytes(VAR_NAME, unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


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


def testIfWrapperEncodesWhenUpdatingWithOtherDict(unicode_samples):
    extra_env = {VAR_NAME: unicode_samples.UNICODE_MULTIPLE_LANGUAGES}
    os.environ.update(extra_env)
    _CheckIfEnvVarTypeIsBytes(VAR_NAME, unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


def testIfWrapperEncodesWhenUpdatingWithKwargs(unicode_samples):
    os.environ.update(MY_UNICODE_VAR=unicode_samples.UNICODE_MULTIPLE_LANGUAGES)
    _CheckIfEnvVarTypeIsBytes(VAR_NAME, unicode_samples.UNICODE_MULTIPLE_LANGUAGES)


def testIfAWrapperCopyIsEqualToOriginal():
    environ_copy = os.environ.copy()

    assert os.environ == environ_copy
