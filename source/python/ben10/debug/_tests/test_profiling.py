from __future__ import unicode_literals
from StringIO import StringIO
from UserList import UserList
from ben10.debug.profiling import ObtainStats, PrintProfile, PrintProfileMultiple, ProfileMethod
import os
import pstats
import pytest
import re
import sys



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testProfile(self, embed_data):
        embed_data.CreateDataDir()

        test_filename = embed_data.GetDataFilename('test.prof')
        test3_filename = embed_data.GetDataFilename('test3.prof')

        class Dummy:

            @ProfileMethod(test_filename)
            def SlowMethod(self, start):
                reals = UserList()
                for x in range(start, 30000):
                    r = x / float(x + 1)
                    reals.append(r)
                return reals

        class Dummy2:

            @ProfileMethod(None, sort=('cumul',))
            def SlowMethod(self, start):
                reals = UserList()
                for x in range(start, 30000):
                    r = x / float(x + 1)
                    reals.append(r)
                return reals

        class Dummy3:

            @ProfileMethod(test3_filename)
            def SlowMethod(self, start):
                reals = UserList()
                for x in range(start, 30000):
                    r = x / float(x + 1)
                    reals.append(r)
                return reals

        dummy = Dummy()
        r = dummy.SlowMethod(5)
        assert len(r) == 29995
        assert os.path.exists(test_filename)

        original = sys.stdout
        try:
            sys.stdout = StringIO()
            dummy = Dummy2()
            r = dummy.SlowMethod(5)
            assert len(r) == 29995

            def CheckOutput(expected_in, output_stream=None):
                if output_stream is None:
                    output_stream = sys.stdout.getvalue()

                if not re.search(expected_in, output_stream):
                    assert False, '>>%s<< not found in >>%s<<' % (expected_in, output_stream)

            # Tests CheckOutput failing
            with pytest.raises(AssertionError) as exception:
                CheckOutput("MISSING")
            assert unicode(exception.value).startswith('>>MISSING<< not found in >>')

            CheckOutput("UserList.py:\d+\(append\)")

            sys.stdout = StringIO()
            dummy = Dummy3()
            dummy.SlowMethod(5)
            PrintProfile(test3_filename)
            CheckOutput("test3.prof")
            CheckOutput("UserList.py:\d+\(append\)")

            s = StringIO()
            PrintProfileMultiple(test3_filename, streams=[s])
            CheckOutput("UserList.py:\d+\(append\)", s.getvalue())

        finally:
            sys.stdout = original


    def testObtainStats(self, embed_data):

        def SlowFunction(start):
            reals = UserList()
            for x in range(start, 30000):
                r = x / float(x + 1)
                reals.append(r)
            return reals

        stats = ObtainStats(SlowFunction, 10000)
        assert stats.__class__ == pstats.Stats
