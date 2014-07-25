from aasimar10.shared_commands import BuildCommand
from ben10.foundation.decorators import Override



#===================================================================================================
# Ben10BuildCommand
#===================================================================================================
class Ben10BuildCommand(BuildCommand):

    PLATFORMS = ['win32', 'win64', 'redhat64']

    @Override(BuildCommand.EvBuild)
    def EvBuild(self, args):
        self.Clean()
        self.RunTests(
            jobs=self.shared_script['hudson_test_jobs'],
            xml=True,
            verbose=4
        )


    @Override(BuildCommand.EvPublish)
    def EvPublish(self, args):
        # Do nothing until we find a way to solve aasimar/ben dependency cycle
        # self.CiPublish(installer=False, all_platforms=','.join(self.PLATFORMS))
        pass
