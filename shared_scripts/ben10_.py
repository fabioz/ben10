from __future__ import unicode_literals
from ben10.foundation.decorators import Override
from sharedscripts10.namespace.namespace_types import LIST, PATHLIST
from sharedscripts10.shared_scripts.esss import EsssProject


#===================================================================================================
# Ben10
#===================================================================================================
class Ben10(EsssProject):

    NAME = 'ben10'

    DEPENDENCIES = [
        'cog',
        'desktop',
        'ftputil',
        'futures',
        'gprof2dot',
        'ordereddict',
        'path_py',
        'pyftpdlib',
        'rarfile',
        'windows:pywin32',

        # Tools
        'git',

        # Tests
        # Packages associated only to test code or test fixtures.
        'faulthandler',
        'mock',
        'pylint',
        'pytest',
        'pytest_cov',
        'pytest_localserver',
        'pytest_xdist',
        'pytest_timeout',
    ]

    NAMESPACE_VARIABLES = {
        '$PYTHON3PATH' : PATHLIST('`self.python_dir`'),

        '>tf' : 'python `self.working_dir`/scripts/tf.py',

        'cx_freeze_expected_missing' : LIST(
            ('numpy', 'ben10.foundation.types_'),  # Optional dependency
        )
    }


    @Override(EsssProject._GetPackageFileMapping)
    def _GetPackageFileMapping(self):
        return [
            ('`self.working_dirname`/shared_scripts/', '+`self.working_dir`/shared_scripts/*.py'),
            ('`self.working_dirname`/source/python/', '+`self.python_dir`/*.py'),
        ]
