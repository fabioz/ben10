from ben10.filesystem import (CheckIsFile, CreateDirectory, CreateFile, DeleteFile, EOL_STYLE_NONE,
    ExtendedPathMask, FileAlreadyExistsError, FindFiles)
import os
import warnings



#===================================================================================================
# Archivist
#===================================================================================================
class Archivist(object):
    '''
    Methods for extracting and creating archive in many formats.
    '''

    #===============================================================================================
    # Creation
    #===============================================================================================
    def CreateArchive(self, archive, archive_mapping, overwrite=True):
        '''
        Creates a compressed archive (zip, rar, etc).

        :param str archive:
            The name of the target archive

        :param list(tuple(str,str)) archive_mapping:
            A list of mappings between the directory in the target and the source "extended path
            mask" description.

        :param Bool overwrite:
            If True will overwrite any existing filename.

        :raises RuntimeError:
            If a filename with the same name already exists, and overwrite is False.
        '''
        if os.path.isfile(archive):
            if overwrite:
                DeleteFile(archive)
            else:
                raise FileAlreadyExistsError(archive)

        handles_table = [
            ('.zip'     , self.CreateZip, 'w'),
            ('.tar.gz'  , self.CreateTar, 'w:gz'),
            ('.tgz'     , self.CreateTar, 'w:gz'),
            ('.tgz'     , self.CreateTar, 'w:gz'),
            ('.tar.bz2' , self.CreateTar, 'w:bz2'),
            ('.tbz2'    , self.CreateTar, 'w:bz2'),
            ('.tar'     , self.CreateTar, 'w'),
        ]

        for i_ext, i_cmd, i_mode in handles_table:
            if archive.endswith(i_ext):
                return i_cmd(archive, archive_mapping, mode=i_mode)

        raise RuntimeError('Unknown archive format: %s' % archive)


    def CreateZip(self, archive, archive_mapping, mode='w'):
        '''
        Create a zip filename using the given archive_mapping

        :param str archive:
            The name of the target archive

        :param list(tuple(str,str)) archive_mapping:
            A list of mappings between the directory in the target and the source "extended path
            mask" description.

        :param str mode:
            The file mode for the archive. Needed to maintain the interface.
            CreateZip only accepts "w".
        '''
        file_listing = self._ZipFileListing(archive_mapping)

        import zipfile
        oss = zipfile.ZipFile(archive, mode, zipfile.ZIP_DEFLATED)
        for i_archive_filename, i_filename in file_listing:
            oss.write(i_filename, i_archive_filename)
        oss.close()


    def CreateTar(self, archive, archive_mapping, mode='w'):
        '''
        Create a tar filename using the given archive_mapping

        :param str archive:
            The name of the target archive

        :param list(tuple(str,str)) archive_mapping:
            A list of mappings between the directory in the target and the source "extended path
            mask" description.

        :param str mode:
            The file mode for the archive.
            See options on tarfile.open documentation.
            http://docs.python.org/2/library/tarfile.html
        '''
        file_listing = self._ZipFileListing(archive_mapping)
        import tarfile
        oss = tarfile.open(archive, mode)
        for i_archive_filename, i_filename in file_listing:
            oss.add(i_filename, i_archive_filename)
        oss.close()


    #===============================================================================================
    # Extraction
    #===============================================================================================
    def ExtractZip(self, zip_filename, target_folder):
        '''
        Extracts a zip filename into the target folder

        :param str zip_filename:
            Path to the archive filename

        :param str target_folder:
            Folder into which contents will be extracted
        '''
        self.__ExtractArchive(zip_filename, target_folder)


    def ExtractTar(self, tar_filename, target_folder, mode='r'):
        '''
        Extracts a zip filename into the target folder

        :param str tar_filename:
            Path to the archive filename

        :param str target_folder:
            Folder into which contents will be extracted

        :param str mode:
        '''
        import tarfile
        oss = tarfile.open(tar_filename, mode)
        oss.extractall(target_folder)
        oss.close()


    def ExtractRar(self, rar_filename, target_folder):
        '''
        Extracts a rar filename into the target folder

        :param str rar_filename:
            Path to the archive filename

        :param str target_folder:
            Folder into which contents will be extracted
        '''
        self.__ExtractArchive(rar_filename, target_folder)


    def ExtractArchive(self, filename, target_dir):
        '''
        Extracts an filename into a directory

        :param str filename:
            Archive filename to extract.

        :param str target_dir:
            The directory where to extract the archives files.
        '''
        CheckIsFile(filename)

        handles_table = [
            ('.egg'     , self.ExtractZip, None),
            ('.zip'     , self.ExtractZip, None),
            ('.tar.gz'  , self.ExtractTar, 'r:gz'),
            ('.tgz'     , self.ExtractTar, 'r:gz'),
            ('.tgz'     , self.ExtractTar, 'r:gz'),
            ('.tar.bz2' , self.ExtractTar, 'r:bz2'),
            ('.tbz2'    , self.ExtractTar, 'r:bz2'),
            ('.tar'     , self.ExtractTar, 'r'),
            ('.rar'     , self.ExtractRar, None),
            ('.cbr'     , self.ExtractRar, None),
        ]

        for i_ext, i_cmd, i_mode in handles_table:
            if filename.endswith(i_ext):
                if i_mode is None:
                    i_cmd(filename, target_dir)
                else:
                    i_cmd(filename, target_dir, mode=i_mode)
                return

        raise RuntimeError('Unknown filename format: %s' % filename)



    # Internal functions ---------------------------------------------------------------------------
    def _ZipFileListing(self, archive_mapping, out_filters=()):
        '''
        Returns a list of tuples, mapping each filename found in the given archive mapping.
        Each tuple contains the zip_filename and original filename.

        :param list(tuple(str,str)) archive_mapping:
            A list of mappings between the directory in the target and the source "extended path
            mask" description.
        '''
        import os.path

        result = []
        for i_zip_path, i_path in archive_mapping:
            tree_recurse, _flat_recurse, dirname, in_filters, i_out_filters = ExtendedPathMask.Split(i_path)
            filenames = FindFiles(
                dirname,
                in_filters=in_filters,
                out_filters=i_out_filters + list(out_filters),
                recursive=tree_recurse,
            )
            if len(filenames) == 0:
                warnings.warn(
                    'NO FILES LISTED in "extended path mask": %r' % (i_path,),
                    stacklevel=2,
                )
            for i_filename in filenames:
                if not os.path.isdir(i_filename):
                    archive_filename = i_filename[len(dirname):]
                    if archive_filename.startswith('/') or archive_filename.startswith('\\'):
                        archive_filename = archive_filename[1:]
                    archive_filename = os.path.join(i_zip_path, archive_filename)
                    result.append((archive_filename, i_filename))

        return result


    def __ExtractArchive(self, archive_filename, target_dir):
        '''
        Generic implementation of Extract Archive. Handles .rar and .zip files.

        :param str archive_filename:
            The name of the archive.

        :param str target_dir:
            The target directory to extract the archive contents.
        '''
        # Get archive wrapper
        from _archive_wrapper import CreateArchiveWrapper
        archive = CreateArchiveWrapper(archive_filename)


        # Create directories needed for target
        target_dir = os.path.normpath(target_dir)
        if not target_dir.endswith(':'):
            CreateDirectory(target_dir)


        # Create archive structure
        for sub_dir in archive.ListDirs():
            curdir = os.path.join(target_dir, sub_dir)
            CreateDirectory(curdir)


        # Extract archive
        for i_name in archive.ListFilenames():
            target_filename = os.path.normpath(os.path.join(target_dir, i_name))
            if os.path.isdir(target_filename):
                continue

            CreateFile(
                target_filename,
                archive.ReadFile(i_name),
                eol_style=EOL_STYLE_NONE,
            )
