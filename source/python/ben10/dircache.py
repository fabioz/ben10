
from archivist import Archivist
from ben10.filesystem import (CopyFile, CreateDirectory, CreateFile, CreateLink,
    CreateTemporaryDirectory, DeleteDirectory, DeleteFile, DeleteLink, Exists, FileNotFoundError,
    IsDir, IsLink, StandardizePath)
import os



#===================================================================================================
# DirCache
#===================================================================================================
class DirCache(object):
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

    def __init__(self, remote, local_dir, cache_base_dir):
        '''
        .. seealso:: class docs for params.
        '''
        assert remote.endswith('.zip'), 'Remote target must be a .zip file'

        self.__remote = remote
        self.__local_dir = local_dir

        self.__filename = os.path.basename(self.__remote)
        self.__name = os.path.splitext(self.__filename)[0]

        self.__cache_base_dir = StandardizePath(os.path.abspath(cache_base_dir))
        self.__cache_dir = self.__cache_base_dir + '/' + self.__name

        self.__complete_cache_tag = self.__cache_dir + '/.cache'


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
        return self.__remote


    @property
    def remote_filename(self):
        return self.__filename


    @property
    def local_dir(self):
        return self.__local_dir


    @property
    def cache_base_dir(self):
        return self.__cache_base_dir


    @property
    def cache_dir(self):
        return self.__cache_dir


    @property
    def cache_name(self):
        return self.__name


    # Functions ------------------------------------------------------------------------------------
    def CreateCache(self, force=False):
        '''
        Downloads the remote resource into the local cache.
        This method does not touch the local_dir.

        :param bool force:
            Forces the download, even if the local cache already exists.
        '''
        if self.CacheExists():
            if not force:
                return

            DeleteDirectory(self.cache_dir)

        self._DownloadRemote(self.cache_dir)


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
        Makes a remote resource locally available, downloading it if necessary.
        '''
        self.DeleteLocal()

        try:
            self.CreateCache()
        except FileNotFoundError:
            CreateDirectory(self.cache_dir)

        self._CreateLocalLink()


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


    def TagCompleteCache(self):
        '''
        Tags a cache as complete.

        This is done manually, or automatically when uploading the cache to a
        remote directory.

        If this file is not present, a cache is considered incomplete (i.e.,
        CacheExists will return False)
        '''
        if not Exists(self.__complete_cache_tag):
            CreateFile(
                self.__complete_cache_tag,
                contents='This file indicates that this cache was created correctly.'
            )


    def RemoteExists(self):
        '''
        Checks if the remote resource exists.

        :returns bool:
        '''
        return Exists(self.remote)


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
        # Check for at least two files, since one is our `self.__complete_cache_tag`
        return Exists(self.__complete_cache_tag) and len(os.listdir(self.cache_dir)) > 1


    def _DownloadRemote(self, target_dir):
        '''
        Internal method that actually downloads the remote resource.

        :param str extract_dir:
            A temporary directory where to extract archive remote resources.

        :param str target_dir:
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


    def _CreateLocalLink(self):
        '''
        Creates a link `cache_dir` to `local_dir`.

        This method is usually called internally and does not require an explicit call.
        '''
        CreateLink(self.cache_dir, self.local_dir)
