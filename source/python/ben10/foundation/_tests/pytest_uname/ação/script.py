from ben10.foundation.uname import GetApplicationDir, GetUserHomeDir
import sys

option = sys.argv[1]
if option == 'app':
    dir_name = GetApplicationDir()

elif option == 'home':
    app_dir = GetApplicationDir()

    import locale
    import os
    if sys.platform == 'win32':
        drive, path = os.path.splitdrive(app_dir)
        os.environ['HOMEDRIVE'] = drive.encode(locale.getpreferredencoding())

        os.environ['HOMEPATH'] = path.encode(locale.getpreferredencoding())

    else:
        os.environ['HOME'] = app_dir.encode(locale.getpreferredencoding())

    dir_name = GetUserHomeDir()

print dir_name.encode('utf-8')
