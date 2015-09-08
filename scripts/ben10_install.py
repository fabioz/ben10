from __future__ import unicode_literals
from ben10.foundation.decorators import Override
from sharedscripts10.commands.install_command import BaseInstallCommand  # @UnresolvedImport



#===================================================================================================
#  Ben10InstallCommand
#===================================================================================================
class Ben10InstallCommand(BaseInstallCommand):

    SHARED_SCRIPT = 'ben10'

    @Override(BaseInstallCommand.Install)
    def Install(self, command_line_args):
        self.InstallCog('`self.python_dir`/ben10')



#===================================================================================================
# Entry Point
#===================================================================================================
if __name__ == '__main__':
    Ben10InstallCommand.Main()
