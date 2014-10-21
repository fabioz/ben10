'''
Examples of using logging:


#To log to a given logger:
logger = log.GetLogger('handler_name')
logger.Warn('Test')


#To log to the root:
log.Error('Some error')


#To log an exception:
try:
    raise FooError()
except:
    logger = log.GetLogger('handler_name')
    logger.Exception('Something bad happened')



#Show log in stderr (for anything logged).
AddDebugStreamHandler()
'''
from __future__ import unicode_literals
from io import StringIO
import logging



# Levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


# Methods that log to the root
Debug = logging.debug
Info = logging.info
Warn = logging.warn
Error = logging.error
Exception = logging.exception  # Error + exception info
Critical = logging.critical


# Methods for the logger
logging.Logger.Debug = logging.Logger.debug
logging.Logger.Info = logging.Logger.info
logging.Logger.Warn = logging.Logger.warn
logging.Logger.Error = logging.Logger.error
logging.Logger.Exception = logging.Logger.exception  # Error + exception info
logging.Logger.Critical = logging.Logger.critical

logging.Logger.AddHandler = logging.Logger.addHandler
logging.Logger.RemoveHandler = logging.Logger.removeHandler


# Get a given logger
GetLogger = logging.getLogger

import logging.handlers

StreamHandler = logging.StreamHandler
FileHandler = logging.FileHandler
RotatingFileHandler = logging.handlers.RotatingFileHandler
Handler = logging.Handler
Handler.SetLevel = Handler.setLevel


#===================================================================================================
# NullHandler
#===================================================================================================
class NullHandler(Handler):
    '''
    This handler will simply ignore anything that arrives.
    '''

    def emit(self, record):
        '''
        Ignore anything.
        '''


#===================================================================================================
# AddDebugStreamHandler
#===================================================================================================
def AddDebugStreamHandler(logger=''):
    '''
    Helper to add a default stream handler (that'll log to stderr) into a given logger.

    :param unicode logger:
        The logger to which the handler should be added.
    '''
    result = GetLogger(logger)
    result.AddHandler(StreamHandler())
    return result


#===================================================================================================
# _LogHandle
#===================================================================================================
class _LogHandle(object):
    '''
    Helper to use a log with a with statement.
    '''

    def __init__(self, logger, stream_handler, string_io):
        '''
        :param unicode logger:
            The logger context.

        :param StreamHandler stream_handler:
            The stream handler added to the log context.

        :param StringIO string_io:
            The string io used to record the log.
        '''
        self.logger = logger
        self.stream_handler = stream_handler
        self.string_io = string_io


    def __enter__(self):
        '''
        Context Management protocol method.
        '''
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        '''
        Context Management protocol method.

        Parameters are any exception occurred during the "with" block, or all None.

        :rtype: bool
        :returns:
            Return True if the exception should be suppressed
        '''
        GetLogger(self.logger).RemoveHandler(self.stream_handler)
        return False


    def GetRecordedLog(self):
        '''
        :rtype: unicode
        :returns:
            Returns the contents logged so far.
        '''
        return self.string_io.getvalue()


#===================================================================================================
# StartLogging
#===================================================================================================
def StartLogging(logger=''):
    '''
    To be used as:
        with StartLogging() as logger:
            ... Do something
            log = logger.GetRecordedLog()
            ... check the log.

    :param unicode logger:
        The logger context to be logged.
    '''
    string_io = StringIO()
    stream_handler = StreamHandler(string_io)
    GetLogger(logger).AddHandler(stream_handler)
    return _LogHandle(logger, stream_handler, string_io)


# By default add a NullHandler to the logging, otherwise, when something is logged the first time,
# it'll print to stderr (if such a logger is wanted, it has to be explicitly added).
GetLogger('').AddHandler(NullHandler())



#===================================================================================================
# _ExceptionWithDetailedTraceback
#===================================================================================================
def _ExceptionWithDetailedTraceback(logger, msg):
    '''
    Writes the current exception as a detailed traceback into the log.

    It is similar to exception, but using coilib's detailed traceback.

    :param unicode msg:
        Message to display before traceback.
    '''
    from .print_detailed_traceback import PrintDetailedTraceback
    stream = StringIO()
    PrintDetailedTraceback(stream=stream)
    logger.error(msg + '\n' + stream.getvalue())


logging.Logger.ExceptionWithDetailedTraceback = _ExceptionWithDetailedTraceback
