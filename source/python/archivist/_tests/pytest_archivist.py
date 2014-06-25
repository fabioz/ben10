from ben10.filesystem import FileAlreadyExistsError



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testExtractRar(self, embed_data):
        self._TestArchive(embed_data, embed_data['root_dir.rar'], extract_only=True)


    def testCreateAndExtractZip(self, embed_data):
        self._TestArchive(embed_data, embed_data['root_dir.zip'])


    def testCreateAndExtract7Zip(self, embed_data):
        self._TestArchive(embed_data, embed_data['7zip.zip'], extract_only=True)


    def testCreateAndExtractBz2(self, embed_data):
        self._TestArchive(embed_data, embed_data['alpha.tar.bz2'])


    def testCreateAndExtractTarGz(self, embed_data):
        self._TestArchive(embed_data, embed_data['alpha.tar.gz'])


    def testCreateAndExtractTbz2(self, embed_data):
        self._TestArchive(embed_data, embed_data['alpha.tbz2'])


    def testCreateAndExtractTgz(self, embed_data):
        self._TestArchive(embed_data, embed_data['alpha.tgz'])


    def testExceptions(self, embed_data):
        from archivist import Archivist
        from ben10.filesystem import CreateDirectory, CreateFile
        import os
        import pytest

        CreateFile(embed_data['alpha.INVALID'], '')
        CreateDirectory(embed_data['CREATE/root_dir/empty_dir'])

        archive = Archivist()

        with pytest.raises(NotImplementedError):
            archive.ExtractZip(embed_data['alpha.INVALID'], embed_data.GetDataDirectory())

        with pytest.raises(RuntimeError):
            # Unknown format
            archive.CreateArchive(
                embed_data['alpha.UNKNOWN'],
                embed_data.GetDataDirectory()
            )

        with pytest.raises(FileAlreadyExistsError):
            # File already exists
            # File is kept
            archive.CreateArchive(
                embed_data['alpha.INVALID'],
                embed_data.GetDataDirectory(),
                overwrite=False
            )
        assert os.path.isfile(embed_data['alpha.INVALID'])

        with pytest.raises(RuntimeError):
            archive.ExtractArchive(
                embed_data['alpha.INVALID'],
                embed_data.GetDataDirectory()
            )

        with pytest.raises(RuntimeError):
            # Unknown format
            # File is deleted: this may not be a good default behavior, but it is what we have now.
            archive.CreateArchive(
                embed_data['alpha.INVALID'],
                embed_data.GetDataDirectory(),
            )
        assert not os.path.isfile(embed_data['alpha.INVALID'])


    def _TestArchive(self, embed_data, filename, extract_only=False):
        from archivist import Archivist
        import os

        archive = Archivist()

        assert not os.path.isfile(embed_data['root_dir/alpha.txt'])
        assert not os.path.isfile(embed_data['root_dir/bravo.txt'])
        assert not os.path.isfile(embed_data['root_dir/sub_dir/charlie.txt'])
        assert not os.path.isfile(embed_data['root_dir/apache_pb.gif'])

        if not extract_only:
            assert not os.path.isfile(filename)
            archive.CreateArchive(
                filename,
                archive_mapping=[(
                    'root_dir',
                    '+' + embed_data['CREATE/root_dir/*']
                )]
            )

        assert os.path.isfile(filename)
        archive.ExtractArchive(filename, target_dir=embed_data.GetDataDirectory())

        assert os.path.isfile(embed_data['root_dir/alpha.txt'])
        assert os.path.isfile(embed_data['root_dir/bravo.txt'])
        assert os.path.isfile(embed_data['root_dir/sub_dir/charlie.txt'])
        assert os.path.isfile(embed_data['root_dir/apache_pb.gif'])

        embed_data.AssertEqualFiles(
            'root_dir/alpha.txt',
            'CREATE/root_dir/alpha.txt',
        )
        embed_data.AssertEqualFiles(
            'root_dir/apache_pb.gif',
            'CREATE/root_dir/apache_pb.gif',
        )


    def testWarns(self):
        from archivist import Archivist
        import warnings

        with warnings.catch_warnings(record=True) as reported_warnings:
            warnings.simplefilter("always")

            archive = Archivist()
            archive._ZipFileListing([('folder_in_zip', '+non_matching_mask/*')])

            assert len(reported_warnings) == 1
            assert reported_warnings[0].message.message == 'NO FILES LISTED in "extended path mask": \'+non_matching_mask/*\''


