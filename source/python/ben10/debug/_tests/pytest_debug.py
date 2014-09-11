from __future__ import unicode_literals
from ben10.debug import IsPythonDebug



def testIsPythonDebug():
    assert IsPythonDebug() in (True, False)
