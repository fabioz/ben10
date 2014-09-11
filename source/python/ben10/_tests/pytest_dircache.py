from __future__ import unicode_literals
from ben10.dircache import DirCache
from ben10.filesystem import CreateDirectory, CreateFile, DeleteFile, IsDir, IsFile, IsLink
from ben10.filesystem._filesystem import GetFileContents
import os
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testProperties(self, dir_cache, embed_data):
        assert dir_cache.remote == embed_data['remotes/alpha.zip']
        assert dir_cache.remote_filename == 'alpha.zip'
        assert dir_cache.local_dir == embed_data['local/zulu']
        assert dir_cache.cache_base_dir == embed_data.GetDataFilename('cache_dir', absolute=True)
        assert dir_cache.cache_dir == embed_data.GetDataFilename('cache_dir/alpha', absolute=True)
        assert dir_cache.cache_name == 'alpha'


    def testDeleteCache(self, dir_cache, embed_data):
        CreateDirectory(embed_data['cache_dir/alpha'])
        CreateFile(embed_data['cache_dir/alpha/file.txt'], contents='')
        dir_cache.TagCompleteCache()

        assert dir_cache.CacheExists()
        deleted = dir_cache.DeleteCache()
        assert deleted == True
        assert not dir_cache.CacheExists()
        assert not IsDir(embed_data['cache_dir/alpha'])

        # Trying to delete again does nothing
        deleted = dir_cache.DeleteCache()
        assert deleted == False


    def testDownloadRemoteArchive(self, dir_cache, embed_data):
        '''
        Tests the method DownloadRemote with a archive as the remote.
        '''
        dir_cache.CreateCache()

        # DownloadRemote extracts the archive contents into a directory with the same basename of
        # the archive.
        assert os.path.isdir(embed_data['cache_dir/alpha'])

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


    @pytest.mark.symlink
    def testCreateLocal(self, dir_cache, embed_data):
        '''
        Tests CreateLocal, making sure it creates a link to the cache
        '''
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
        assert os.path.isfile(embed_data['cache_dir/alpha/.cache'])
        assert GetFileContents(embed_data['cache_dir/alpha/.cache']) == 'mock_contents'

        assert dir_cache.LocalExists()
        # note: isdir returns true even if zulu is a directory.
        assert os.path.isdir(embed_data['local/zulu'])
        assert IsLink(embed_data['local/zulu'])
        assert os.path.isfile(embed_data['local/zulu/file.txt'])

        dir_cache.DeleteLocal()
        assert dir_cache.RemoteExists()
        assert dir_cache.CacheExists()
        assert not dir_cache.LocalExists()


    def testCreateRemote(self, dir_cache, embed_data):
        # Create some stuff in the cache_dir
        CreateDirectory(dir_cache.cache_dir)

        # Does nothing if remote already exists
        dir_cache.CreateRemote()

        # Make sure that the remote does not exist
        DeleteFile(dir_cache.remote)
        assert not IsFile(dir_cache.remote)

        CreateFile(dir_cache.cache_dir + '/' + 'alpha.txt', contents='')
        dir_cache.CreateRemote()

        # See that the remote was created and contains what we expec
        assert IsFile(dir_cache.remote)

        from archivist import Archivist
        Archivist().ExtractArchive(dir_cache.remote, embed_data['extract'])
        assert IsFile(embed_data['extract/alpha.txt'])


    def testGetAllCacheDirs(self, embed_data):
        remote_dir = embed_data['remotes']
        cache_dir = embed_data['cache']

        CreateDirectory(cache_dir + '/alpha')
        CreateDirectory(cache_dir + '/bravo')
        CreateDirectory(cache_dir + '/charlie')
        CreateFile(cache_dir + '/delta.txt', contents='')  # Files are ignored

        caches = DirCache.GetAllCacheDirs(remote_dir, cache_dir)

        assert len(caches) == 3
        alpha, bravo, charlie = caches

        assert alpha.remote == embed_data['remotes/alpha.zip']
        assert alpha.cache_dir == embed_data.GetDataFilename('cache/alpha', absolute=True)

        assert bravo.remote == embed_data['remotes/bravo.zip']
        assert bravo.cache_dir == embed_data.GetDataFilename('cache/bravo', absolute=True)

        assert charlie.remote == embed_data['remotes/charlie.zip']
        assert charlie.cache_dir == embed_data.GetDataFilename('cache/charlie', absolute=True)



#===================================================================================================
# dir_cache
#===================================================================================================
@pytest.fixture
def dir_cache(embed_data):
    '''
    Basic pre configured DirCache used in local tests.
    '''
    return DirCache(
        embed_data['remotes/alpha.zip'],
        embed_data['local/zulu'],
        embed_data['cache_dir'],
        cache_tag_contents='mock_contents'
    )
