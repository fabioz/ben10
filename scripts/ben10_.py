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
        # Install dependencies
        'ben10:cog',

        'desktop',
        'ftputil',
        'futures',
        'gprof2dot',
        'ordereddict',
        'path_py',
        'pyyaml',
        'pyftpdlib',
        'rarfile',
        'windows:pywin32',

        # Tools
        'git',

        # Tests
        # Packages associated only to test code or test fixtures.
        'faulthandler',
        'mock',
        'pytest',
        'pytest_cov',
        'pytest_localserver',
        'pytest_xdist',
        'pytest_timeout',
        'pytest_cache',
        'pytest_mock',
    ]

    NAMESPACE_VARIABLES = {
        '$PYTHON3PATH' : PATHLIST('`self.python_dir`'),

        # "session-tmp-dir" fixture  declares some hooks that must be loaded with xdist,
        # so it must be loaded during startup. Proper solution would be to move that
        # fixture to its own plugin, but this will have to do for now
        '$PYTEST_PLUGINS' : 'ben10.fixtures',


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
