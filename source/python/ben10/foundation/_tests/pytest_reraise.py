from __future__ import unicode_literals
from ben10.foundation.reraise import Reraise, ReraiseKeyError
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testReraise(self):
        def foo():
            raise AttributeError('Test')

        def bar():
            try:
                foo()
            except Exception, exception:
                Reraise(exception, "While doing 'bar'")

        expected = "\nWhile doing y:\nWhile doing x:\nWhile doing 'bar'\nTest"

        try:
            try:
                try:
                    bar()
                except Exception, exception:
                    Reraise(exception, "While doing x:")
            except Exception, exception:
                Reraise(exception, "While doing y:")
        except Exception, exception:
            obtained = unicode(exception)
            assert type(exception) == AttributeError

        assert obtained == expected


    def testOserror(self):
        '''
        Reraise converts OSError to RuntimeError
        '''

        def foo():
            raise OSError(2, 'Hellow')

        def bar():
            try:
                foo()
            except Exception, exception:
                Reraise(exception, "While doing 'bar'")

        expected = "\nWhile doing x:\nWhile doing 'bar'\n[Errno 2] Hellow"

        try:
            try:
                bar()
            except Exception, exception:
                Reraise(exception, "While doing x:")
        except Exception, exception:
            obtained = unicode(exception)
            assert type(exception) == RuntimeError

        assert obtained == expected


    def testSyntaxError(self):
        '''
        Properly give info on syntax error
        '''

        def foo():
            raise SyntaxError('InitialError')

        def bar():
            try:
                foo()
            except SyntaxError, exception:
                Reraise(exception, "SecondaryError")

        obtained = 'Not Obtained yet'
        try:
            try:
                bar()
            except Exception, exception:
                Reraise(exception, "While doing x:")
        except Exception, exception:
            obtained = unicode(exception)

        assert 'SecondaryError' in obtained, 'Expected "SecondaryError" to be in: ' + obtained


    def testReraiseKey(self):
        with pytest.raises(ReraiseKeyError) as key_error:
            try:
                raise KeyError('key')
            except KeyError as exception:
                Reraise(exception, "Reraising")

        assert unicode(key_error) == '%s:96: ReraiseKeyError:' % __file__
