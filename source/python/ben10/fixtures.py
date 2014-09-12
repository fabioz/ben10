'''
Collection of fixtures for pytests.

.. note::
    Coverage for this file gives a lot of misses, just like calling coverage from module's main.
'''
import os
import pytest



#===================================================================================================
# MultipleFilesNotFound
#===================================================================================================
class MultipleFilesNotFound(RuntimeError):
    '''
    Raised when a file is not found, including variations of filename.
    '''

    def __init__(self, filenames):
        RuntimeError.__init__(self)
        self._filenames = filenames

    def __str__(self):
        return 'Files not found: %s' % ','.join(self._filenames)



#===================================================================================================
# embed_data
#===================================================================================================

class _EmbedDataFixture(object):
    '''
    This fixture create a temporary data directory for the test.
    The contents of the directory is a copy of a 'data-directory' with the same name of the module
    (without the .py extension).

    :ivar boolean delete_dir:
        Determines if the data-directory is deleted at finalization. Default to True.
        This may be used for debugging purposes to examine the data-directory as left by the test.
        Remember that each test recreates the entire data directory.
    '''

    def __init__(self, request):

        # @ivar _module_dir: str
        # The module name.
        self._module_name = request.module.__name__.split('.')[-1]
        self._function_name = request.function.__name__

        # @ivar _source_dir: str
        # The source directory name.
        # The contents of this directories populates the data-directory
        # This name is create based on the module_name
        self._source_dir = request.fspath.dirname + '/' + self._module_name

        # @ivar _data_dir: str
        # The data directory name
        # This name is created based on the module_name
        # Adding the function name to enable parallel run of tests in the same module (pytest_xdist)
        self._data_dir = self._module_name.replace('pytest_', 'data_')
        self._data_dir += '__' + self._function_name

        # @ivar _created: boolean
        # Internal flag that controls whether we created the data-directory or not.
        # - False: Initial state. The data-directory was not created yet
        # - True: The directory was created. The directory is created lazily, that is, when needed.
        self._created = False

        # @ivar _finalize: boolean
        # Whether we have finalized.
        self._finalized = False

        self.delete_dir = True


    def CreateDataDir(self):
        '''
        Creates the data-directory as a copy of the source directory.

        :rtype: str
        :returns:
            Path to created data dir
        '''
        from ben10.filesystem import CopyDirectory, CreateDirectory, DeleteDirectory, IsDir
        from ben10.foundation.is_frozen import IsFrozen

        assert not self._finalized, "Oops. Finalizer has been called in the middle. Something is wrong."
        if self._created:
            return self._data_dir

        if os.path.isdir(self._data_dir):
            DeleteDirectory(self._data_dir)

        if IsFrozen():
            raise RuntimeError("_EmbedDataFixture is not ready for execution inside an executable.")

        if IsDir(self._source_dir):
            CopyDirectory(self._source_dir, self._data_dir)
        else:
            CreateDirectory(self._data_dir)

        self._created = True
        return self._data_dir


    def GetDataDirectory(self, absolute=False, create_dir=True):
        '''
        :param bool absolute:
            If True, returns the path as an abspath

        :param bool create_dir:
            If True (default) creates the data directory.

        :rtype: str
        :returns:
            Returns the data-directory name.

        @remarks:
            This method triggers the data-directory creation.
        '''
        if create_dir:
            self.CreateDataDir()

        if absolute:
            from ben10.filesystem import StandardizePath
            return StandardizePath(os.path.abspath(self._data_dir))

        return self._data_dir


    def GetDataFilename(self, *parts, **kwargs):
        '''
        Returns a full filename in the data-directory.

        @params parts: list(str)
            Path parts. Each part is joined to form a path.

        :keyword bool absolute:
            If True, returns the filename as an abspath

        :rtype: str
        :returns:
            The full path prefixed with the data-directory.

        @remarks:
            This method triggers the data-directory creation.
        '''
        # Make sure the data-dir exists.
        self.CreateDataDir()

        result = [self._data_dir] + list(parts)
        result = '/'.join(result)

        if 'absolute' in kwargs and kwargs['absolute']:
            from ben10.filesystem import StandardizePath
            result = StandardizePath(os.path.abspath(result))

        return result

    def __getitem__(self, index):
        return self.GetDataFilename(index)


    def Finalizer(self):
        '''
        Deletes the data-directory upon finalizing (see FixtureRequest.addfinalizer)
        '''
        from ben10.filesystem._filesystem import DeleteDirectory

        if self.delete_dir:
            DeleteDirectory(self._data_dir, skip_on_error=True)
        self._finalized = True


    def AssertEqualFiles(self, filename1, filename2, fix_callback=lambda x:x):
        '''
        Compare two files contents, showing a nice diff view if the files differs.

        Searches for the filenames both inside and outside the data directory (in that order).

        :param str filename1:
        :param str filename2:
        :param callable fix_callback:
            A callback to "fix" the contents of the obtained (first) file.
            This callback receives a list of strings (lines) and must also return a list of lines,
            changed as needed.
            The resulting lines will be used to compare with the contents of filename2.
        '''
        from ben10.filesystem import GetFileLines

        def FindFile(filename):
            # See if this path exists in the data dir
            data_filename = self.GetDataFilename(filename)
            if os.path.isfile(data_filename):
                return data_filename

            # If not, we might have already received a full path
            if os.path.isfile(filename):
                return filename

            # If we didn't find anything, raise an error
            raise MultipleFilesNotFound([filename, data_filename])

        filename1 = FindFile(filename1)
        filename2 = FindFile(filename2)

        obtained = fix_callback(GetFileLines(filename1))
        expected = GetFileLines(filename2)

        if obtained != expected:
            import difflib
            diff = ['*** FILENAME: ' + filename1]
            diff += difflib.context_diff(obtained, expected)
            diff = '\n'.join(diff)
            raise AssertionError(diff)


@pytest.fixture  # pylint: disable=E1101
def embed_data(request):  # pylint: disable=C0103
    '''
    Create a temporary directory with input data for the test.
    The directory contents is copied from a directory with the same name as the module located in
    the same directory of the test module.
    '''
    result = _EmbedDataFixture(request)
    request.addfinalizer(result.Finalizer)
    return result


@pytest.fixture
def platform():
    from ben10.foundation.platform_ import Platform
    return Platform.GetCurrentPlatform()
