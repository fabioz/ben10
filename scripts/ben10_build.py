from aasimar10.shared_commands import BuildCommand
from ben10.foundation.decorators import Override



#===================================================================================================
# Ben10BuildCommand
#===================================================================================================
class Ben10BuildCommand(BuildCommand):

    @Override(BuildCommand.EvBuild)
    def EvBuild(self, args):
        self.RunTests(jobs=6, xml=True)


    @Override(BuildCommand.EvAfterBuild)
    def EvAfterBuild(self, args):
        self.CiPublish()
