from __future__ import unicode_literals
from ben10.foundation.reraise import Reraise
import pytest



#===================================================================================================
# TestReraise
#===================================================================================================
class TestReraise(object):
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


#===================================================================================================
# TestReraiseSpecial
#===================================================================================================
class TestReraiseSpecial(object):
    '''
    Test reraising some special exceptions.

    .. seealso:: ben10.foundation.reraise.__ReraiseSpecial
    '''
    def testOserror(self):
        def foo():
            raise OSError(2, 'Hellow')

        def bar():
            try:
                foo()
            except Exception, exception:
                Reraise(exception, "While doing 'bar'")

        with pytest.raises(OSError) as e:
            try:
                bar()
            except OSError, exception:
                Reraise(exception, "While doing x:")

        obtained_msg = unicode(e.value)
        expected_msg = "\nWhile doing x:\nWhile doing 'bar'\n[Errno 2] Hellow"
        assert obtained_msg == expected_msg


    def testSyntaxError(self):
        def foo():
            raise SyntaxError('InitialError')

        def bar():
            try:
                foo()
            except SyntaxError, exception:
                Reraise(exception, "SecondaryError")

        with pytest.raises(SyntaxError) as e:
            try:
                bar()
            except SyntaxError, exception:
                Reraise(exception, "While doing x:")

        obtained = unicode(e.value)
        expected = '\nWhile doing x:\nSecondaryError\nInitialError'
        assert obtained == expected


    def testReraiseKeyError(self):
        with pytest.raises(Exception) as e:
            try:
                raise KeyError('key')
            except KeyError as exception:
                Reraise(exception, "Reraising")

        assert unicode(e.value) == "\nReraising\nu'key'"


#===================================================================================================
# TestReraiseEnvironmentErrors
#===================================================================================================
class TestReraiseEnvironmentErrors(object):

    def testEncodingError(self):

        class ExceptionWithStr(EnvironmentError):
            '''
            An exception that isn't in unicode.
            '''
        # Python
        import locale
        encoding = locale.getpreferredencoding()

        exception_message = u'Po\xe7o'
        with pytest.raises(ExceptionWithStr) as reraised_exception:
            try:
                raise ExceptionWithStr(exception_message.encode(encoding))
            except ExceptionWithStr as exception:
                Reraise(exception, "Reraising")

        obtained_message = reraised_exception.value.message
        expected_message = '\nReraising\n' + exception_message
        assert obtained_message == expected_message
        assert type(obtained_message) is unicode



