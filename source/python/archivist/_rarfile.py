from __future__ import unicode_literals



#===================================================================================================
# Rarfile
#===================================================================================================
class Rarfile(object):

    UNRAR_TOOL = 'unrar'

    def CreateRarFile(self, *args, **kwargs):
        '''
        Wrapper function to create a properly configured rarfile.RarFile

        .. seealso:: rarfile.RarFile
            For params

        :rtype: rarfile.RarFile
        '''
        import rarfile

        # Fix path to unrar
        rarfile.UNRAR_TOOL = self.UNRAR_TOOL
        return rarfile.RarFile(*args, **kwargs)
