from aasimar10.shared_commands import BuildCommand
from ben10.foundation.decorators import Override



#===================================================================================================
# Ben10BuildCommand
#===================================================================================================
class Ben10BuildCommand(BuildCommand):

    PLATFORMS = ['win32', 'win64', 'redhat64']

    @Override(BuildCommand.EvBuild)
    def EvBuild(self, args):
        self.RunTests(jobs=6, xml=True)


    @Override(BuildCommand.EvPublish)
    def EvPublish(self, args):
        self.CiPublish(installer=False, all_platforms=','.join(self.PLATFORMS))
