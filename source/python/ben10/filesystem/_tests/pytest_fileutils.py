from ben10.filesystem import OpenReadOnlyFile, CreateFile
import os
import sys
import pytest



#=======================================================================================================================
# Test
#=======================================================================================================================
class Test:

    @pytest.mark.windows
    @pytest.mark.serial
    def testOpenReadOnlyFile__serial(self, monkeypatch, embed_data):

        if sys.platform == 'win32':

            filename = embed_data['test_fileutils.tst']
            CreateFile(filename, 'empty')

            def ResetFlags():
                self.binary_flag = None
                self.sequential_flag = None

            self.original_open = os.open
            def MockOpen(filename, flags):
                self.binary_flag = flags & os.O_BINARY
                self.sequential_flag = flags & os.O_SEQUENTIAL
                return self.original_open(filename, flags)


            self.open_file = None
            monkeypatch.setattr(os, 'open', MockOpen)
            try:
                # Check text, random
                ResetFlags()
                self.open_file = OpenReadOnlyFile(filename)
                assert self.open_file.mode == 'r'
                assert self.binary_flag is None
                assert self.sequential_flag is None
                self.open_file.close()

                # Check binary, random
                ResetFlags()
                self.open_file = OpenReadOnlyFile(filename, binary=True)
                assert self.open_file.mode == 'rb'
                assert self.binary_flag is None
                assert self.sequential_flag is None
                self.open_file.close()

                # Check binary, sequential
                ResetFlags()
                self.open_file = OpenReadOnlyFile(filename, binary=True, sequential=True)
                assert self.open_file.mode == 'rb'
                assert self.binary_flag is not None
                assert self.sequential_flag is not None
                self.open_file.close()
            finally:
                if self.open_file:
                    self.open_file.close()
