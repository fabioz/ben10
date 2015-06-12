from __future__ import unicode_literals
from StringIO import StringIO
from ben10.foundation.hash import DumpDirHashToStringIO, GetRandomHash, IterHashes, Md5Hex
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testGetRandomHash(self):
        '''
        Tests that GetRandomHash gives a hexadecimal hash of the target length
        '''
        import re
        hash_ = GetRandomHash(length=10)
        assert re.match('[0-9a-f]{10}', hash_) is not None


    def testIterHashesGenerator(self):
        '''
        Tests that IterHashes returns a generator
        '''
        import types
        hashes = IterHashes(5)
        assert isinstance(hashes, types.GeneratorType) == True


    def testIterHashesLength(self):
        '''
        Tests that IterHashes has the given size
        '''
        assert len(list(IterHashes(5))) == 5


    def testIterHashesValues(self):
        '''
        Tests that IterHashes gives hexadecimal hashes of the target length
        '''
        import re
        for hash_ in IterHashes(5, hash_length=10):
            assert re.match('[0-9a-f]{10}', hash_) is not None


    def testIterHashesReceivesInteger(self):
        with pytest.raises(TypeError):
            list(IterHashes('50'))


    def testMd5Hash(self, embed_data):
        stringio = StringIO()
        DumpDirHashToStringIO(embed_data.GetDataDirectory(), stringio, 'bin')
        val = stringio.getvalue()
        assert (
            set(val.splitlines())
            == {
                'bin/file1.txt=4124bc0a9335c27f086f24ba207a4912',
                'bin/file2.txt=633de4b0c14ca52ea2432a3c8a5c4c31',
            }
        )

        stringio = StringIO()
        DumpDirHashToStringIO(embed_data.GetDataDirectory(), stringio, 'bin', exclude='*1.txt')
        val = stringio.getvalue()
        assert (
            set(val.splitlines())
            == {
                'bin/file2.txt=633de4b0c14ca52ea2432a3c8a5c4c31',
            }
        )

        stringio = StringIO()
        DumpDirHashToStringIO(embed_data.GetDataDirectory(), stringio, '', exclude='*1.txt')
        val = stringio.getvalue()
        assert (
            set(val.splitlines())
            == {
                'file2.txt=633de4b0c14ca52ea2432a3c8a5c4c31',
            }
        )


    def testMd5Hex(self):
        assert Md5Hex(contents='alpha, bravo') == '2c0d78abb6e32d1614a17c6d0e4391c0'
