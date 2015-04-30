from __future__ import unicode_literals



#===================================================================================================
# UnknownPlatform
#===================================================================================================
class UnknownPlatform(NotImplementedError):
    '''
    An unknown platform is found, either converting from platform naming conventions or obtaining
    the current platform.

    :ivar unicode platform:
        The unknown platform string.
    '''
    def __init__(self, platform):
        self.platform = platform
        msg = 'Unknown platform "%s"' % platform
        NotImplementedError.__init__(self, msg)



#===================================================================================================
# Platform
#===================================================================================================
class Platform(object):
    '''
    Holds information about platforms names.

    The platforms format is the following:

        <name><bits><debug>

    Where:
        name: win | redhat
        bits: 32 | 64
        debug: "" | "d"

    Examples:
        win32
        win64d
        redhat64

    Alternative formats:

        Old format (SimplePlatform):
            i686.win32
            amd64.win32
            amd64.redhat

        Mneumonic:
            w32
            w64d
            r64

        Long Format:
            Windows 32-bit
            Windows 64-bit DEBUG
            RedHat Linux 32-bit
    '''
    WIN = 'win'
    REDHAT = 'redhat'
    UBUNTU = 'ubuntu'
    DARWIN = 'darwin'
    DEBIAN = 'debian'
    CENTOS = 'centos'

    FLAVOUR_WINDOWS = 'windows'
    FLAVOUR_LINUX = 'linux'
    FLAVOUR_DARWIN = 'darwin'

    _VALID_NAMES = [WIN, REDHAT, DEBIAN, UBUNTU, DARWIN, CENTOS]
    _VALID_BITS = ['32', '64']
    _VALID_DEBUG = [True, False]


    def __init__(self, name, bits, debug=False):
        '''
        :param unicode name:
            Platform name. One of _VALID_NAMES

        :param unicode bits:
            Platform bits. One of _VALID_BITS

        :param bool debug:
            True if it's a debug platform.

        :raises ValueError:
            Raises if one of the parameters is not expected value (self._VALID_XXX)
        '''
        def _AssertValidValue(value, valid_values):
            if value not in valid_values:
                raise ValueError("Value %r not valid. Valid ones are: %s" % (value, valid_values))

        _AssertValidValue(name, self._VALID_NAMES)
        _AssertValidValue(bits, self._VALID_BITS)
        _AssertValidValue(debug, self._VALID_DEBUG)

        self.name = name
        self.bits = bits
        self.debug = debug


    @classmethod
    def Create(cls, seed=None):
        '''
        Returns a Platform instance from the given seed.

        :param unicode|None|Platform seed:
            If unicode, create a Platform based on the given string
            If None, returns the current platform
            If Platform, returns the seed
        '''
        if isinstance(seed, unicode):
            try:
                return cls.CreateFromString(seed)
            except UnknownPlatform:
                return cls.CreateFromSimplePlatform(seed)
        elif seed is None:
            return cls.GetCurrentPlatform()
        elif isinstance(seed, Platform):
            return seed
        else:
            raise UnknownPlatform(seed)


    @classmethod
    def GetValidPlatforms(cls):
        '''
        :rtype: list(unicode)
        :returns:
            List of all valid platform names
        '''
        platforms = []
        for name in cls._VALID_NAMES:
            for bits in cls._VALID_BITS:
                for debug in cls._VALID_DEBUG:
                    platforms.append(name + bits + debug * 'd')

        return platforms


    @classmethod
    def CreateFromString(cls, text):
        '''
        :param unicode text:
            The platform name (Ex.: win32d, redhat64)

        :rtype: Platform

        :raises UnknownPlatform:
            Raises if the text (parameter) is an unknown platform.
        '''
        RESULT = {
            'win32' : (cls.WIN, '32', False),
            'win32d' : (cls.WIN, '32', True),
            'win64' : (cls.WIN, '64', False),
            'win64d' : (cls.WIN, '64', True),
            'redhat64' : (cls.REDHAT, '64', False),
            'fedora64' : (cls.REDHAT, '64', False),
            'centos64' : (cls.CENTOS, '64', False),
            'ubuntu64' : (cls.UBUNTU, '64', False),
            'debian64' : (cls.DEBIAN, '64', False),
            'darwin32' : (cls.DARWIN, '32', False),
        }
        try:
            params = RESULT[text]
        except KeyError:
            raise UnknownPlatform(text)
        else:
            return cls(*params)


    @classmethod
    def CreateFromSimplePlatform(cls, simple_platform, debug=False):
        '''
        :param unicode simple_platform:

        :param bool debug:

        :rtype: Platform

        :raises UnknownPlatform:
            Raises if the simple_platform (parameter) is an unknown platform.
        '''
        RESULT = {
            'amd64.centos' : (cls.CENTOS, '64'),
            'amd64.debian' : (cls.DEBIAN, '64'),
            'amd64.redhat' : (cls.REDHAT, '64'),
            'amd64.ubuntu' : (cls.UBUNTU, '64'),
            'amd64.win32' : (cls.WIN, '64'),
            'i686.darwin' : (cls.DARWIN, '32'),
            'i686.win32' : (cls.WIN, '32'),
        }
        try:
            params = RESULT[simple_platform]
        except KeyError:
            raise UnknownPlatform(simple_platform)
        else:
            return cls(debug=debug, *params)


    @classmethod
    def GetCurrentPlatform(cls):
        '''
        :rtype: Platform
        :returns:
            Returns the current machine platform.

        @raise UnknownPlatform
            Raises if the current system is an unknown platform.
        '''
        import platform
        import sys

        if sys.platform == 'win32':
            if 'AMD64' in platform.python_compiler():
                return cls(cls.WIN, '64')
            else:
                return cls(cls.WIN, '32')
        elif sys.platform == cls.DARWIN:
            return cls(cls.DARWIN, '64')
        else:
            dist = platform.dist()[0]
            if dist not in ['', None, '0', ' ']:
                DIST_MAP = {
                    'fedora' : 'redhat',
                    'Ubuntu' : 'ubuntu',
                    'Debian' : 'debian',
                }
                MACHINE_MAP = {
                    'i686' : '32',
                    'i386' : '32',
                    'x86_64' : '64',
                    'amd64' : '64',
                }
                dist = DIST_MAP.get(dist, dist)
                bits = MACHINE_MAP[platform.machine()]
                return cls(dist, bits)


    @classmethod
    def GetOSPlatform(cls):
        '''
        :returns Platform:
            The real OS platform. This should correctly indicate x86 vs x64 bits, in any version
            of Python
        '''
        # GetCurrentPlatform will give me the Python interpreter platform
        current_platform = cls.GetCurrentPlatform()

        # We have to find out if we are running Python32 in a 64bit machine
        if unicode(current_platform) == 'win32':
            import ctypes
            i = ctypes.c_int()
            kernel32 = ctypes.windll.kernel32
            process = kernel32.GetCurrentProcess()
            kernel32.IsWow64Process(process, ctypes.byref(i))
            is64bit = (i.value != 0)

            if is64bit:
                return cls(cls.WIN, '64')

            return cls(cls.WIN, '32')

        # Otherwise, return whatever GetCurrentPlatform gave us
        return current_platform


    @classmethod
    def GetDefaultPlatform(cls):
        '''
        The default platform differs from the current platform on win64 machines, when, even with
        the 64-bits present, we use win32 by default.

        :rtype: Platform
        :returns:
            Returns the default platform considering the current platform.
        '''
        RESULT = {
            'win64' : 'win32'
        }
        current = cls.GetCurrentPlatform()
        result = RESULT.get(unicode(current))
        if result is None:
            return current
        return cls.CreateFromString(result)


    @classmethod
    def GetCurrentFlavour(cls):
        '''
        Shortcut to obtain platform flavour from current platform.

        :rtype: unicode
        :returns:
            @see: Platform.GetPlatformFlavour
        '''
        return cls.GetCurrentPlatform().GetPlatformFlavour()


    def AsString(self, ignore_debug=False):
        '''
        :param bool ignore_debug:
            If true, ignores the debug flag in the platform name.

        :rtype: unicode
        :returns:
            Returns the platform as a string.
        '''
        if self.debug and not ignore_debug:
            suffix = 'd'
        else:
            suffix = ''

        return '%s%s%s' % (
            self.name,
            self.bits,
            suffix,
        )


    def GetPlatformFlavour(self):
        '''
        Returns the platform flavour associated with this platform.

        :rtype: unicode
        :returns:
            The platform flavour, which is a supper set of the platform name itself.
            The possible values are:
                windows: For all windows variations (for now, only win)
                linux: For all linux variations (redhat, fedora)
                darwin: For all darwin (mac) variations (for now, only darwin)
        '''
        RESULT = {
            self.WIN : self.FLAVOUR_WINDOWS,
            self.REDHAT : self.FLAVOUR_LINUX,
            self.UBUNTU : self.FLAVOUR_LINUX,
            self.DEBIAN : self.FLAVOUR_LINUX,
            self.CENTOS : self.FLAVOUR_LINUX,
            self.DARWIN : self.FLAVOUR_DARWIN,
        }
        try:
            return RESULT[self.name]
        except KeyError:
            raise UnknownPlatform(self.name)


    def GetPlatformDistroFlags(self):
        '''
        Returns a set of (linux) distro flags.

        :returns set(unicode):
        '''
        RESULT = {
            self.WIN : set(),
            self.DARWIN : set(),
            self.REDHAT : {self.REDHAT, 'centos5'},
            self.UBUNTU : {self.UBUNTU, 'ubuntu1404', 'new-linuxes'},
            self.DEBIAN : {self.DEBIAN, 'new-linuxes'},
            self.CENTOS : {self.CENTOS, 'centos7', 'new-linuxes'},
        }
        try:
            return RESULT[self.name]
        except KeyError:
            raise UnknownPlatform(self.name)


    def __str__(self):
        '''
        String representation of the platform.
        '''
        return self.AsString()


    def IsDebug(self):
        '''
        :rtype: bool
        :returns:
            True if this platform is DEBUG (ends with d)
                 e.g.: win32d, win64
        '''
        return unicode(self).endswith('d')


    def GetBaseName(self):
        '''
        :rtype: unicode
        :returns:
            Returns the base platform name (ignores debug)
        '''
        platform = unicode(self)

        if self.IsDebug():
            return platform[:-1]
        return platform


    def GetSimplePlatform(self):
        '''
        :rtype: unicode
        :returns:
            Returns the platform in the old format (simple-platform)

        .. note::
            The old format does not have the debug information in the platform.

        :raises UnknownPlatform:
            Raises if there is no map between the platform and simple-platform naming convention.
        '''
        RESULT = {
            'win32' : 'i686.win32',
            'win32d' : 'i686.win32',
            'win64' : 'amd64.win32',
            'win64d' : 'amd64.win32',
            'redhat64' : 'amd64.redhat',
            'centos64' : 'amd64.centos',
            'ubuntu64' : 'amd64.ubuntu',
            'debian64' : 'amd64.debian',
            'darwin32' : 'i686.darwin',
        }
        try:
            plat = unicode(self)
            return RESULT[plat]
        except KeyError:
            raise UnknownPlatform(plat)


    def GetMneumonic(self):
        '''
        :rtype: unicode
        :returns:
            Returns the mneumonic name (3 chars) for the platform.
        '''
        return '%s%s' % (self.name[0], self.bits)


    def GetLongName(self):
        '''
        :rtype: unicode
        :returns:
            Returns the long name for the platform.

        :raises UnknownPlatform:
            Raises if there is no map between the platform and long-platform naming convention.
        '''
        RESULT = {
            'win32' : 'Windows 32-bit',
            'win32d' : 'Windows 32-bit DEBUG',
            'win64' : 'Windows 64-bit',
            'win64d' : 'Windows 64-bit DEBUG',
            'redhat64' : 'RedHat Linux 64-bit',
            'centos64' : 'CentOS Linux 64-bit',
            'ubuntu64' : 'Ubuntu Linux 64-bit',
            'debian64' : 'Debian Linux 64-bit',
            'darwin32' : 'Darwin 32-bit',
        }
        try:
            plat = unicode(self)
            return RESULT[plat]
        except KeyError:
            raise UnknownPlatform(plat)


    @classmethod
    def GetAllFlags(cls):
        '''
        Returns a set with all possible platform flags.

        :return set(unicode):
        '''
        result = {cls.FLAVOUR_WINDOWS, cls.FLAVOUR_LINUX, cls.FLAVOUR_DARWIN}
        for i_platform in cls.GetValidPlatforms():
            result.add(i_platform)
        return result


    def GetFlags(self):
        '''
        Returns the flags correspondent with the current platform.
        The resulting set is always a sub-set of GetAllFlags.

        :return set(unicode):
        '''
        result = {
            unicode(self),  # Example: The exact name of the platform: win32, win32d, win64, win64d
            self.GetBaseName(),  # Example: "win32" (for both win32d and win32)
            self.GetPlatformFlavour(),  # Example: "windows" (for all windows variations)
        }
        result.update(self.GetPlatformDistroFlags())
        if self.debug:
            result.add('debug')
        return result
