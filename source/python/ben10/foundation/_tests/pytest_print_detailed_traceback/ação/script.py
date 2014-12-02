from ben10.foundation.print_detailed_traceback import PrintDetailedTraceback
import io
try:
    assert False
except:
    PrintDetailedTraceback(stream=io.StringIO())
    print 'COMPLETE'
