from ben10.filesystem import OpenReadOnlyFile, CreateFile
from ben10.filesystem._fileutils import FILE_FLAG_SEQUENTIAL, FILE_FLAG_BINARY
import mock
import os
import pytest



@pytest.mark.serial
def testOpenReadOnlyFile(embed_data):

    filename = embed_data['test_fileutils.tst']
    CreateFile(filename, 'empty')

    with mock.patch('os.open', autospec=True, side_effect=os.open) as mock_os_open:
        open_file = OpenReadOnlyFile(filename)
        assert open_file.mode == 'r'
        open_file.close()
        assert mock_os_open.called == False

    with mock.patch('os.open', autospec=True, side_effect=os.open) as mock_os_open:
        open_file = OpenReadOnlyFile(filename, binary=True)
        assert open_file.mode == 'rb'
        open_file.close()
        assert mock_os_open.called == False

    with mock.patch('os.open', autospec=True, side_effect=os.open) as mock_os_open:
        open_file = OpenReadOnlyFile(filename, sequential=True)
        assert open_file.mode == 'r'
        open_file.close()
        mock_os_open.assert_called_once_with(filename, os.O_RDONLY | FILE_FLAG_SEQUENTIAL)

    with mock.patch('os.open', autospec=True, side_effect=os.open) as mock_os_open:
        open_file = OpenReadOnlyFile(filename, binary=True, sequential=True)
        assert open_file.mode == 'rb'
        open_file.close()
        mock_os_open.assert_called_once_with(filename, os.O_RDONLY | FILE_FLAG_SEQUENTIAL | FILE_FLAG_BINARY)
