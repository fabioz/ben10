from __future__ import unicode_literals
from archivist import Archivist
from ben10.filesystem import (CopyFile, CreateDirectory, CreateFile, CreateLink,
    CreateTemporaryDirectory, DeleteDirectory, DeleteFile, DeleteLink, Exists, IsDir, IsLink,
    StandardizePath)
from ben10.filesystem._filesystem_exceptions import FileNotFoundError
from ben10.foundation.decorators import Override
import os



#===================================================================================================
# DirCacheLocal
#===================================================================================================
class DirCacheLocal(object):
    '''
    Creates symlinks between directories to "cache" content in a single directory.

    This is very useful when you need the same data in two different paths and want to avoid
    using up disk space (and duplicating data)

    e.g.
        DirCacheLocal(
            local_dir='workspace_1/alpha_artifacts',
            cache_base_dir='SHARED',
            cache_dirname='alpha_hash'
        )

        Will allow you to create a link from 'workspace_1/alpha_artifacts' to 'SHARED/alpha_hash'.
        If you have another workspace that need the same data, you just need another DirCacheLocal
        with local_dir='workspace_2/alpha_artifacts' and they both will point to the same directory
        inside the cache.

    :ivar unicode local_dir:
        The local directory to place a link with this name pointing to the
        real contents available on `cache_dir`.

    :ivar unicode cache_base_dir:
        A base directory to store the actual remote content.

    :ivar str cache_dirname:
        Basename of `cache_dir` (just the final directory)

    :ivar str cache_tag_contents:
        Contents of the '.cache' tag file. This should be something useful to determine how the
        cache was created.
    '''

    def __init__(self, local_dir, cache_base_dir, cache_dirname, cache_tag_contents=''):
        '''
        .. seealso:: class docs for params.
        '''
        self._local_dir = local_dir

        self._name = cache_dirname

        self._cache_base_dir = StandardizePath(os.path.abspath(cache_base_dir))
        self._cache_dir = self._cache_base_dir + '/' + self._name

        self._cache_tag_filename = self._cache_dir + '/.cache'
        self._cache_tag_contents = cache_tag_contents




    # Properties -----------------------------------------------------------------------------------
    # .. seealso:: class docs for property docs
    @property
    def remote(self):
        return self._remote


    @property
    def remote_filename(self):
        return self._filename


    @property
    def local_dir(self):
        return self._local_dir


    @property
    def cache_base_dir(self):
        return self._cache_base_dir


    @property
    def cache_dir(self):
        return self._cache_dir


    @property
    def cache_name(self):
        return self._name


    # Functions ------------------------------------------------------------------------------------
    def CreateCache(self, force=False):
        '''
        Creates cache directory.

        :param bool force:
            Forces re-creation of the directory if the local cache already exists.

        :return bool:
            True if directory was created. (self.cache_dir is now an empty dir)
            False if cache already existed. (self.cache_dir is already filled with a cache)
        '''
        if self.CacheExists():
            if not force:
                return False

            DeleteDirectory(self.cache_dir)

        CreateDirectory(self.cache_dir)
        return True


    def DeleteCache(self):
        '''
        Deletes the local cache.

        :return bool:
            True if cache was deleted, False if it did not exist and no change was required.
        '''
        if Exists(self.cache_dir):
            DeleteDirectory(self.cache_dir)
            return True
        return False


    def CreateLocal(self):
        '''
        Creates local directory (actually a link to self.cache_dir)
        '''
        self.DeleteLocal()
        self.CreateCache()
        self.CreateLink()


    def CreateLink(self):
        '''
        Create a link from `self.local_dir` to `self.cache_dir`
        '''
        CreateLink(self.cache_dir, self.local_dir)


    def DeleteLocal(self):
        '''
        Deletes the local resource.

        The remote and cache content are not touched.
        '''
        if Exists(self.local_dir):
            # Delete must be in this order (first links, then dirs) because links also count as
            # directories.
            if IsLink(self.local_dir):
                DeleteLink(self.local_dir)
            elif IsDir(self.local_dir):
                DeleteDirectory(self.local_dir)
            else:
                raise RuntimeError("%s: The local directory is expected to be a link or dir." % self.local_dir)


    def TagCompleteCache(self):
        '''
        Tags a cache as complete.

        This is done manually, or automatically by subclasses that call this method when uploading
        the cache to a remote directory.

        If this file is not present, a cache is considered incomplete (i.e.,
        CacheExists will return False)
        '''
        if not Exists(self._cache_tag_filename):
            CreateFile(self._cache_tag_filename, self._cache_tag_contents)


    def LocalExists(self):
        '''
        Checks if the local resource exists.

        :returns bool:
        '''
        return Exists(self.local_dir)


    def CacheExists(self):
        '''
        Checks if the local cache exists, is valid, and not empty.

        Cache is valid if it was tagged as complete. .. seealso:: TagCompleteCache

        :returns bool:
        '''
        # Check for at least two files, since one is our `self._cache_tag_filename`
        return Exists(self._cache_tag_filename) and len(os.listdir(self.cache_dir)) > 1



#===================================================================================================
# DirCache
#===================================================================================================
class DirCache(DirCacheLocal):
    '''
    DirCache is an utility that make a remote archive available locally using a local cache.

    Use case:
    You want to have some remote resource, say 'http://.../remote.zip' contents available in a local
    directory (local):

        dir_cache = DirCache(
            'http://.../remote.zip',
            'local',
            'c:/dircache',
        )
        dir_cache.CreateLocal()
        os.path.isdir('local')

    This will make the contents of remote.zip available inside the "local" directory. Behind the
    scenes we have an indirection, where the contents are stored in the cache directory
    c:/dircache/remote and "local" is actually a link to c:/dircache/remote.

        c:/dircache/remote.zip
        c:/dircache/remote

        ./local [c:/dircache/remote]

    The local cache directory (c:/dircache) is handy when you have many local directories from the
    same remote resource. This is the case of a Continuous Integration slave machine, that can
    execute many jobs that requires the same resources.

    :ivar str remote:
        Path to a remote archive.
        This can be a local directory, ftp or http url.

    :ivar str remote_filename:
        The filename portion of `remote`.
        This may differ from the resource local directory.

    :ivar str local_dir:
        The local directory to place a link with this name pointing to the
        real contents available on `cache_dir`.

    :ivar str cache_base_dir:
        A base directory to store the actual remote content.

    :ivar str cache_dir:
        Directory containing remote content in the local machine.
        `local_dir` is a link pointing to this directory.

    :ivar str cache_name:
        Basename of `cache_dir` (just the final directory_
    '''

    def __init__(self, remote, local_dir, cache_base_dir, cache_tag_contents=''):
        '''
        .. seealso:: class docs for params.
        '''
        assert remote.endswith('.zip'), 'Remote target must be a .zip file'
        self._remote = remote

        self._filename = os.path.basename(self._remote)
        cache_dirname = os.path.splitext(self._filename)[0]

        DirCacheLocal.__init__(self, local_dir, cache_base_dir, cache_dirname, cache_tag_contents)


    @classmethod
    def GetAllCacheDirs(cls, remote_dir, cache_base_dir):
        '''
        :param str remote_dir:
            Path to a remote directory where cache archives are stored

        :param str cache_base_dir:
            .. seealso:: class docs

        :return list(DirCache):
            A list of DirCache objects, one for each directory found in `cache_base_dir`.

            All caches point to their mirror in `remote_dir`.
        '''
        dircaches = []
        for dirname in sorted(os.listdir(cache_base_dir)):
            if not os.path.isdir(cache_base_dir + '/' + dirname):
                continue

            dircaches.append(DirCache(
                remote=remote_dir + '/' + dirname + '.zip',
                local_dir=None,
                cache_base_dir=cache_base_dir,
            ))

        return dircaches


    # Properties -----------------------------------------------------------------------------------
    # .. seealso:: class docs for property docs
    @property
    def remote(self):
        return self._remote


    @property
    def remote_filename(self):
        return self._filename



    # Functions ------------------------------------------------------------------------------------
    @Override(DirCacheLocal.CreateCache)
    def CreateCache(self, force=False):
        '''
        Overridden to download cache from remote after creating directory.

        :param bool force:
            Forces the download, even if the local cache already exists.
        '''
        created = DirCacheLocal.CreateCache(self, force=force)
        if created:
            try:
                self._DownloadRemote(self.cache_dir)
            except FileNotFoundError:
                pass


    def CreateRemote(self):
        '''
        Creates the remote cache from the contents of `local_dir`.

        Does nothing if remote already exists.

        :raise RuntimeError:
            If `self.cache_dir` is empty (nothing to upload).
        '''
        if self.RemoteExists():
            return

        self.TagCompleteCache()

        self._UploadRemote()


    def RemoteExists(self):
        '''
        Checks if the remote resource exists.

        :returns bool:
        '''
        return Exists(self.remote)


    def _DownloadRemote(self, target_dir):
        '''
        Internal method that actually downloads the remote resource.

        :param unicode extract_dir:
            A temporary directory where to extract archive remote resources.

        :param unicode target_dir:
            The final destination of the remote resource.
        '''
        with CreateTemporaryDirectory() as tmp_dir:
            tmp_archive = os.path.join(tmp_dir, self.remote_filename)
            CopyFile(self.remote, tmp_archive)
            archivist = Archivist()
            archivist.ExtractArchive(tmp_archive, target_dir)
            DeleteFile(tmp_archive)


    def _UploadRemote(self):
        '''
        Uploads the contents of `self.cache_dir` to `self.remote`.
        '''
        with CreateTemporaryDirectory() as tmp_dir:
            tmp_archive = os.path.join(tmp_dir, self.remote_filename)
            Archivist().CreateArchive(tmp_archive, [('', '+' + self.cache_dir + '/*')])
            CopyFile(tmp_archive, self.remote)
            DeleteFile(tmp_archive)
