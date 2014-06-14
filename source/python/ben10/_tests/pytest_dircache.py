from ben10.dircache import CacheDisabled, DirCache
from ben10.filesystem import CreateFile, IsFile, IsLink
import os
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testDownloadRemote(self, embed_data):
        '''
        Tests the method DownloadRemote with a normal directory as the remote.
        '''
        dir_cache = DirCache(
            embed_data['remotes/alpha'],
            embed_data['local/zulu'],
            embed_data['cache_dir'],
        )
        assert dir_cache.GetFilename() == 'alpha'
        assert dir_cache.GetName() == 'alpha'

        assert dir_cache.RemoteExists()
        assert not dir_cache.CacheExists()
        assert not dir_cache.LocalExists()

        dir_cache.CreateCache()
        # DownloadRemote extracts the archive contents into a directory with the same basename of
        # the archive.
        assert os.path.isdir(embed_data['cache_dir/alpha'])
        assert os.path.isfile(embed_data['cache_dir/alpha/file.txt'])

        assert dir_cache.RemoteExists()
        assert dir_cache.CacheExists()
        assert not dir_cache.LocalExists()

        # Calling it twice does nothing.
        CreateFile(embed_data['cache_dir/alpha/new_file.txt'], 'This is new')
        assert IsFile(embed_data['cache_dir/alpha/new_file.txt'])
        dir_cache.CreateCache()
        assert IsFile(embed_data['cache_dir/alpha/new_file.txt'])
        assert dir_cache.RemoteExists()
        assert dir_cache.CacheExists()
        assert not dir_cache.LocalExists()

        # Forcing cache download will override new created file.
        CreateFile(embed_data['cache_dir/alpha/new_file.txt'], 'This is new')
        assert IsFile(embed_data['cache_dir/alpha/new_file.txt'])
        dir_cache.CreateCache(force=True)
        assert not IsFile(embed_data['cache_dir/alpha/new_file.txt'])


    def testDownloadRemoteArchive(self, embed_data):
        '''
        Tests the method DownloadRemote with a archive as the remote.
        '''
        dir_cache = DirCache(
            embed_data['remotes/alpha.zip'],
            embed_data['local/zulu'],
            embed_data['cache_dir'],
        )
        assert dir_cache.GetFilename() == 'alpha.zip'
        assert dir_cache.GetName() == 'alpha'

        dir_cache.CreateCache()

        # DownloadRemote copies the archive locally
        assert os.path.isfile(embed_data['cache_dir/alpha.zip'])

        # DownloadRemote extracts the archive contents into a directory with the same basename of
        # the archive.
        assert os.path.isdir(embed_data['cache_dir/alpha'])


    @pytest.mark.symlink
    def testMakeLocallyAvailable(self, embed_data):
        '''
        Tests the MakeLocallyAvailable method.
        '''
        dir_cache = DirCache(
            embed_data['remotes/alpha.zip'],
            embed_data['local/zulu'],
            embed_data['cache_dir'],
        )
        assert dir_cache.RemoteExists()

        # Local directory must NOT exist.
        # The following assertions are equivalent
        assert not dir_cache.CacheExists()
        assert not os.path.isdir(embed_data['cache_dir/alpha'])

        # Local directory/link must NOT exist.
        # The following assertions are equivalent
        assert not dir_cache.LocalExists()
        assert not os.path.isdir(embed_data['local/zulu'])

        dir_cache.CreateLocal()
        assert dir_cache.CacheExists()
        assert os.path.isfile(embed_data['cache_dir/alpha/file.txt'])

        assert dir_cache.LocalExists()
        # note: isdir returns true even if zulu is a directory.
        assert os.path.isdir(embed_data['local/zulu'])
        assert IsLink(embed_data['local/zulu'])
        assert os.path.isfile(embed_data['local/zulu/file.txt'])

        dir_cache.DeleteLocal()
        assert dir_cache.RemoteExists()
        assert dir_cache.CacheExists()
        assert not dir_cache.LocalExists()


    def testMakeLocallyAvailableWithoutCache(self, embed_data):
        '''
        Tests the MakeLocallyAvailable method without cache.
        '''
        dir_cache = DirCache(
            embed_data['remotes/alpha.zip'],
            embed_data['local/zulu'],
        )
        assert dir_cache.RemoteExists()

        # Local directory must NOT exist.
        # The following assertions are equivalent
        with pytest.raises(CacheDisabled):
            assert not dir_cache.CacheExists()
        assert not os.path.isdir(embed_data['cache_dir/alpha'])

        # Local directory/link must NOT exist.
        # The following assertions are equivalent
        assert not dir_cache.LocalExists()
        assert not os.path.isdir(embed_data['local/zulu'])

        dir_cache.CreateLocal()
        with pytest.raises(CacheDisabled):
            assert not dir_cache.CacheExists()

        assert dir_cache.LocalExists()
        assert os.path.isdir(embed_data['local/zulu'])
        assert not IsLink(embed_data['local/zulu'])
        assert os.path.isfile(embed_data['local/zulu/file.txt'])

        dir_cache.DeleteLocal()
        assert dir_cache.RemoteExists()
        assert not dir_cache.LocalExists()
