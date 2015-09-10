from __future__ import unicode_literals
from ben10.foundation.reraise import Reraise
from ben10.foundation.types_ import CheckType
from ben10.interface import IsImplementation
from copy import deepcopy
from .namespace_types import (INamespaceType, MergedTypesDontMatchException, NamespaceTypeUnmergeable, STRING)
import re
import sys



#===================================================================================================
# InvalidNamespaceKeyName
#===================================================================================================
class InvalidNamespaceKeyName(RuntimeError):

    def __init__(self, namespace_key):
        self.namespace_key = namespace_key
        RuntimeError.__init__(self, 'Invalid namespace key name "%s"' % namespace_key)



#===================================================================================================
# NamespaceKeyError
#===================================================================================================
class NamespaceKeyError(Exception):
    '''
    Exception raised when a namespace key is not found
    '''
    def __init__(self, key):
        '''
        :param unicode key:
            The missing key
        '''
        self.key = key
        Exception.__init__(self, 'Namespace variable "%s" not found.' % self.key)



#===================================================================================================
# NoMatchForFlagsError
#===================================================================================================
class NoMatchForFlagsError(Exception):
    '''
    Error raised when trying to access a variable that exists, but has no matching value for the
    current flags
    '''


#===================================================================================================
# CantFindBestMatchException
#===================================================================================================
class CantFindBestMatchException(Exception):
    '''
    Error raised when trying to access a variable that exists, but has no matching value for the
    current flags
    '''
    def __init__(self, match_flags):
        self.match_flags = match_flags
        Exception.__init__(
            self,
            'Found two variables with the same number of flag matches for the given flags.\n' + \
            'Matching with flags: [%s]' % ', '.join(match_flags)
        )


#===================================================================================================
# Flag
#===================================================================================================
class Flags(object):

    def __init__(self, yes_flags, not_flags):
        self.yes_flags = set(yes_flags)
        self.not_flags = set(not_flags)


    def ReplaceFlag(self, original_flag, new_flag):
        '''
        Replaces a flag with another flag.

        If original_flag is not included in this object, nothing happens.

        This is used for flag 'aliases', such as 'self', which is replaced in runtime to determine
        it's real name.

        :param unicode original_flag:
            Flag being replaced

        :param unicode new_flag:
            New flag taking over
        '''
        for i_flag_set in [self.yes_flags, self.not_flags]:
            if original_flag in i_flag_set:
                i_flag_set.remove(original_flag)
                i_flag_set.add(new_flag)


    def __repr__(self):
        result = sorted(self.yes_flags)
        result += ["!%s" % i for i in sorted(self.not_flags)]
        return '<Flags %s>' % ':'.join(result)


    def __eq__(self, other):
        return self.yes_flags == other.yes_flags and self.not_flags == other.not_flags


    def __ne__(self, other):
        return not self.__eq__(other)


    @classmethod
    def CreateFromFlags(cls, flag_list):
        '''
        Create a new instance of Flags from the given list of flags.

        :type flag_list: list(unicode) | None
        :param flag_list:
            List of flags. This list can have both yes and not flags. Not flags are prefixed with
            the exclamation symbol (!)
            Ex.
                ['one', 'two'] - ->Flags(['one', 'two'], [])
                ['one', '!two'] - ->Flags(['one'], ['two'])

        :rtype: Flags | None
        :returns:
            Returns a new Flags instance.
            If the flags is None, returns None.
        '''
        if flag_list is None:
            return None

        yes_flags, not_flags = Flags.SplitYesAndNotFlags(flag_list)
        return Flags(yes_flags, not_flags)


    def MatchPointsForFlags(self, match_flags):
        '''
        :param list(unicode) match_flags:
            List of flags

        :rtype: int
        :returns:
            Return a value indicating how much the given yes and 'not-flags' match the given
            match_flags. The greater the value the better the match.
        '''

        def MatchPointsForYesFlags(yes_flags, match_flags):
            result = len(yes_flags.intersection(match_flags))
            if result == len(yes_flags):
                return result
            return None

        def MatchPointsForNotFlags(not_flags, match_flags):
            result = len(not_flags.intersection(match_flags))
            if result > 0:
                return None
            return len(not_flags)

        yes_match_point = MatchPointsForYesFlags(self.yes_flags, match_flags)
        if yes_match_point is None:
            return -1
        not_match_point = MatchPointsForNotFlags(self.not_flags, match_flags)
        if not_match_point is None:
            return -1
        return yes_match_point + not_match_point


    def Match(self, match_flags):
        '''
        :param list(unicode) match_flags:
            List of flags

        :rtype: bool
        :returns:
            Returns True if this flags matches the given flags.
        '''
        result = self.MatchPointsForFlags(match_flags)
        return result >= 0


    @staticmethod
    def SplitYesAndNotFlags(flags):
        '''
        @param: list(flags)
            List of flags, containing 'yes-flags' and 'not-flags' (ex: "!win32").

        :rtype: list(unicode), list(unicode)
        :returns:
            Given a list of flags, returns two list of flags: one with the 'yes-flags' and the second
            with the 'not-flags'.
            The returning 'not-flags' list does not contain "!".

            Ex:
                SplitYesAndNotFlags(["win32", "!debug"])
                >>> (["win32"], ["debug"])
        '''
        yes_flags = set([i for i in flags if "!" not in i])
        not_flags = set([i[1:] for i in flags if "!" in i])
        return yes_flags, not_flags


    @staticmethod
    def SplitNamespaceKey(namespace_key):
        '''
        Split the namespace - key into its components: flags and name
        '''
        parts = namespace_key.split(':')
        if len(parts) == 1:
            return (), parts[0]
        elif parts[0] == '':
            return None, parts[-1]
        else:
            return tuple(parts[:-1]), parts[-1]



#===================================================================================================
# NamespaceKey
#===================================================================================================
class NamespaceKey(object):

    def __init__(self, namespace_key):
        '''
        Create a new instance of Flags from the given namespace_key.

        :param namespace_key text:
            A string containing flags AND a name at the end.
            Ex.
                'one:two:alpha' - ->(Flags(['one', 'two'], []), "alpha")
                'one:!two:alpha' - ->(Flags(['one'], ['two']), "alpha")

        :rtype: (Flags, key)
        :returns:
            Returns a new Flags instance and the "key"
        '''
        flags, self.key = Flags.SplitNamespaceKey(namespace_key)
        self.flags = Flags.CreateFromFlags(flags)


#===================================================================================================
# NamespaceValue
#===================================================================================================
class NamespaceValue(object):
    '''
    Store a namespace value, keeping a value associated with a set of flags.

    :ivar dict(unicode->object) _values:
        Stores the values, mapping the flags to values
    '''

    def __init__(self):
        self._values = []


    def __str__(self):
        return unicode(self._values)


    def SetValueWithFlags(self, flags, value):
        '''
        Set a value considering the given flags:

        :param tuple(unicode) flags:
            Tuple of flags, both 'yes-flags' and 'not-flags' (Ex; ['win32', '!debug'])

        :param object value:
            The value to associate with the given flags
        '''
        CheckType(flags, tuple)

        yes_flags, not_flags = Flags.SplitYesAndNotFlags(flags)

        for i_value_list in self._values:
            i_yes_flags, i_not_flags, _value = i_value_list
            if i_yes_flags == yes_flags and i_not_flags == not_flags:
                i_value_list[2] = value
                break
        else:
            self._values.append([yes_flags, not_flags, value])


    def GetValueWithFlags(self, flags):
        '''
        Return a value associated with (precisely) the given flags.

        :param tuple(unicode) flags:
            Tuple of flags, both 'yes-flags' and 'not-flags' (Ex; ['win32', '!debug'])

        :rtype: <object> | None
        :returns:
            Returns the value associated with the given flag or None if the value is not found.
        '''
        CheckType(flags, tuple)

        yes_flags, not_flags = Flags.SplitYesAndNotFlags(flags)

        for i_yes_flags, i_not_flags, i_value in self._values:
            if i_yes_flags == yes_flags and i_not_flags == not_flags:
                return i_value

        return None


    def Clear(self):
        '''
        Clears all the values associated with the namespace-value.
        '''
        self._values = []


    def DelValueWithFlags(self, flags):
        '''
        Deletes the value associated with the given flag (exact match)

        Use Clear to delete all the values associated with this namespace-value.

        :param tuple(unicode) flags:

        :rtype: boolean
        :returns:
            Returns True if we found and successfully deleted a value and False otherwise.
        '''
        if '*' in flags:
            self.Clear()
            return True

        CheckType(flags, tuple)

        yes_flags, not_flags = Flags.SplitYesAndNotFlags(flags)

        for i, (i_yes_flags, i_not_flags, _value) in enumerate(self._values):
            if i_yes_flags == yes_flags and i_not_flags == not_flags:
                del self._values[i]
                return True

        return False


    def GetMatchingValue(self, implicit_flags, explicit_flags):
        '''
        :param list(unicode) implicit_flags:
            List of implicit - flags, that is, the flags that are defined globally for the namespace.

        :param list(unicode) explicit_flags:
            List of explicit_flags, that is, the flags passed when asking the value.
            Ex: "win32:!debug:self.name"

        :rtype: INamespaceType
        :returns:
            Returns the value that matches the given implicit and explicit flags.
        '''
        # macthes: tuple(int, unicode) points, value
        POINTS = 0
        VALUE = 1
        matches = []

        imp_flags = Flags.CreateFromFlags(implicit_flags)
        if len(imp_flags.not_flags) > 0:
            raise RuntimeError(
                'Implicit flags should never have negative flags: %s' % implicit_flags
            )

        exp_flags = Flags.CreateFromFlags(explicit_flags)
        match_flags = set(implicit_flags)
        match_flags = match_flags.union(exp_flags.yes_flags)
        match_flags = match_flags.difference(exp_flags.not_flags)

        for i_yes_flags, i_not_flags, i_value in self._values:
            flags = Flags(i_yes_flags, i_not_flags)

            points = flags.MatchPointsForFlags(match_flags)
            if points < 0:
                continue

            matches.append((points, i_value))

        if len(matches) == 0:
            raise NoMatchForFlagsError()

        # Merge or select the best match
        try:
            # Variables are mergeable
            values = [match[VALUE] for match in matches]
            merged_value = reduce(lambda a, b: a.Merge(b), values)
            return merged_value
        except NamespaceTypeUnmergeable:
            # Finding best match
            matches.sort()
            # Check if we had a tie between the two highest rated values
            if len(matches) >= 2 and matches[-1][POINTS] == matches[-2][POINTS]:
                raise CantFindBestMatchException(match_flags)
            return matches[-1][VALUE]


    # Print ----------------------------------------------------------------------------------------
    def Print(self, title, oss=None):
        '''
        :param unicode title:
            The title for the value. Usually the variable name.

        :param file oss:
            The file where to write. Default to sys.stdout

        Prints the value with the given title.
        '''
        if oss is None:
            oss = sys.stdout

        normalized_values = []
        for i_yes_flags, i_not_flags, i_value in self._values:
            flags = i_yes_flags
            flags.update(['!%s' % i for i in i_not_flags])
            flags = sorted(flags)
            normalized_values.append((flags, i_value))
        normalized_values.sort()

        indent = None
        for i_flags, i_value in normalized_values:

            # Prints the title (first time) or the indentation
            if indent is None:
                oss.write( '  %s' % title)
                indent = ' ' * len(title)
            else:
                oss.write( '  %s' % indent)

            # Prints the value
            try:
                if len(i_flags) == 0:
                    oss.write(i_value.AsString(template=' = $t:$v') + '\n')
                else:
                    oss.write(i_value.AsString(template=' = ($f) $t:$v', flags=i_flags) + '\n')
            except:
                oss.write("= <ERROR WHILE PRINTING NAMESPACE VALUE>\n")



#===================================================================================================
# Namespace
#===================================================================================================
class Namespace(object):
    '''
    Namespace is a dictionary like object with extended expansion syntax.
    '''

    ABORT = 'abort'
    RETRY = 'retry'

    # @cvar NAMESPACE_VARIABLE_PATTERN: unicode
    #    Pattern that matches valid namespace variable names, use with re.VERBOSE
    NAMESPACE_VARIABLE_PATTERN = """
    \A        # Start of string
    (\S)*     # Any amount of non-whitespace characters (this includes : for flags)
    [^\s\:]+  # At least one non-whitespace, non : char (variable name)
    \Z        # End of string
    """

    def __init__(self, flags=None):
        self._values = {}
        self._callbacks = {}

        self._declared_flags = {}
        if flags is None:
            self._implicit_flags = []
        else:
            self._implicit_flags = flags[:]


    def __copy__(self, *args):
        '''
        Overridden to make sure that modifications to a copied namespace won't affect other
        namespaces
        '''
        new = Namespace.__new__(Namespace)

        new._values = self._values.copy()
        new._callbacks = self._callbacks.copy()
        new._declared_flags = self._declared_flags.copy()
        new._implicit_flags = self._implicit_flags[:]

        return new


    # Setting values -------------------------------------------------------------------------------
    def ClearValue(self, namespace_key):
        '''
        Clears a value, effectively removing its key from the namespace.

        This removes all flag variations of the value too.

        :param unicode key:
            The key of the value, cannot contain flags.
        '''
        flags, key = Flags.SplitNamespaceKey(namespace_key)
        assert len(flags) == 0

        if key in self._values:
            self._values[key].Clear()


    def __setitem__(self, namespace_key, value):
        '''
        Sets a value in this namespace.

        :param unicode namespace_key:

        :type value: INamespaceType | object
        :param value:
        '''
        return self.SetValue(namespace_key, value)


    def SetValue(self, namespace_key, value, force_clear=False):
        '''
        Set a namespace.

        :param unicode namespace_key:
            A string composed by a variable name and optionally a set of flags.

        :type value: callable | INamespaceType | unicode | int
        :param value:
            The value to associate with the key, or a callable if declaring a callback.
        '''
        # Checking for valid variable names --------------------------------------------------------
        if not re.match(self.NAMESPACE_VARIABLE_PATTERN, namespace_key, re.VERBOSE):
            raise InvalidNamespaceKeyName(namespace_key)

        # Callback register ------------------------------------------------------------------------
        if namespace_key.startswith('@'):
            return self._DeclareCallback(namespace_key, value)

        # Flag declaration -------------------------------------------------------------------------
        if namespace_key[0] == ":":
            return self._DeclareFlag(namespace_key, value)

        # Setting a proper value -------------------------------------------------------------------
        if isinstance(value, (basestring, int)):
            value = STRING(value)  # Convert type to STRING

        flags, name = Flags.SplitNamespaceKey(namespace_key)

        # Override flags syntax --------------------------------------------------------------------
        if flags == ('*',):
            force_clear = True
            flags = ()

        return self._SetValueWithFlags(flags, name, value, force_clear=force_clear)


    def _SetValueWithFlags(self, flags, key, value, force_clear=False):
        '''
        Set the value associated with the given key and flags.

        :param list(unicode) flags:
            List of flags (both 'yes-flags' and 'not-flags').

        :param unicode key:
            The variable key to associated the value.

        :param INamespaceType value:
            The value to associated with the key.
        '''
        # Create a new namespace value if needed
        namespace_value = self._values.get(key)

        # Obtain the old value (to send to the callback)
        if namespace_value is None:
            self._values[key] = namespace_value = NamespaceValue()
            old_value = None
        else:
            old_value = namespace_value.GetValueWithFlags(flags)

            # If a value already exists, and we have more than 3 references to this value, create a
            # copy of it. This can happen in cases where we created a copy of this namespace, and
            # we don't want changes in one copy to affect others.

            # 3 references:
            #    1 for local `namespace_value`
            #    1 for internal var used in `sys.getrefcount`
            #    1 for being inside a list in a Namespace (`self._values`)
            if sys.getrefcount(namespace_value) > 3:
                self._values[key] = namespace_value = deepcopy(namespace_value)


        if force_clear:
            # Clears the value HERE, not elsewhere so we keep the "old_value" valid for the
            # callback.
            namespace_value.Clear()
        namespace_value.SetValueWithFlags(flags, value)

        # Call the callback associated with this value, if any.
        callback = self._callbacks.get(key)
        if callback is not None:
            callback(self, old_value, value)


    def _DeclareCallback(self, key, callback):
        '''
        Declares a callback associated with the given namespace key

        :param unicode key:
            The name of the variable to be associated with the callback.

            Declared as @varname, e.g.
                '@name' = name_callback

        :param callable callback:
            Callback to be associated with the given namespace key.
            Whenever this key's value is changed, the callback will be triggered
        '''
        # Remove the '@'
        key = key.replace('@', '')

        # Create and register the callback
        self._callbacks[key] = callback


    # Obtaining values -----------------------------------------------------------------------------
    def __getitem__(self, namespace_key):
        '''
        Obtains a value from this namespace

        :param unicode namespace_key:
            A namespace key, possibly preceded by some explicit flags

        :rtype: unicode
        :returns:
            The string value associated with the given key
        '''
        return self.GetValue(namespace_key, evaluated=True, as_string=True)


    def GetValue(
        self,
        namespace_key,
        explicit_flags=(),
        evaluated=True,
        as_string=False,
        on_missing_callback=None):
        '''
        Returns the value associated with the given name, considering both the implicit flags and
        explicit flags (defined in the namespace_key).

        :param unicode namespace_key:
            A string composed by a variable name and optionally a set of flags.
            Examples:
            - flag1:flag2:name
            - name

        :ptype explicit_flags: list(unicode) | None
        :param explicit_flags:
            List of additional flags to be considered when obtaining the value

        :param bool evaluated:
            If the variable should be evaluated (all strings within it are evaluated)

        :param bool as_string:
            If True, returns the string representation of the value

        :param callable on_missing_callback:
            Callback called when a missing variable is detected.
            This callback will take proper action to solve the problem, and return either
            Namespace.STOP or Namespace.RETRY, indicating the action to be taken

            If the result is Namespace.STOP, a NamespaceKeyError is raised

        :rtype: INamespaceType | unicode
        :returns:
            INamespaceType if as_string is False
            unicode if as_string is True

        :raises NamespaceKeyError:
            When the given namespace key, or one of its sub-expression variables was not found
        '''
        # Add additional explicit flags obtained from key
        key_explicit_flags, name = Flags.SplitNamespaceKey(namespace_key)
        if key_explicit_flags is not None:
            explicit_flags = explicit_flags + key_explicit_flags

        # Try to return the value for this namespace key, should any error occur, call the
        # on_missing_callback to take proper action, and try again, or, abort and fail.
        while True:
            try:
                return self._GetValue(namespace_key, name, explicit_flags, evaluated, as_string)
            except NamespaceKeyError:
                missing_variable_exception = sys.exc_info()[1]
                # If we have no callback, fail
                if on_missing_callback is None:
                    Reraise(
                        missing_variable_exception,
                        '[Namespace.GetValue] While reading variable "%s"' % namespace_key
                    )

                try:
                    action = on_missing_callback(missing_variable_exception.key)
                except Exception:
                    callback_exception = sys.exc_info()[1]
                    # Raise the exception that occured in the callback, but also add the original
                    # Exception's message to it (it is most likely a sequence of Reraises containing
                    # the evaluation trace)
                    Reraise(callback_exception, unicode(missing_variable_exception))


                if action == Namespace.ABORT:
                    Reraise(
                        missing_variable_exception,
                        '[Namespace.GetValue] While reading variable "%s"' % namespace_key
                    )

                elif action == Namespace.RETRY:
                    pass  # Assuming callback handled our problem, try again


    @classmethod
    def SplitNameAndVariation(cls, name_and_variation):
        '''
        Identify and return the variation from the variable name.
        The variations are the following:

           alpha$ : Environment variation: Format to use in the environment. This is the main reason
                    for the variation. This allows PATH to be formated accordinly with the platform.
           alpha# : IO variation: Include the variable type in the string to perform I/O

        :param unicode name_and_variation:
            A namespace variable with or without a variation suffix.

        :rtype: tuple(unicode,unicode):
        :returns:
            The name and variation:
            - name: the given string without the variation char.
            - variation: one of VARIATION_XXX constants.
        '''
        if name_and_variation[-1] in (INamespaceType.VARIATION_ENV, INamespaceType.VARIATION_IO):
            return (name_and_variation[:-1], name_and_variation[-1])

        return (name_and_variation, INamespaceType.VARIATION_STR)


    def _GetValue(self, namespace_key, name, explicit_flags, evaluated, as_string):
        '''
        Sub-routine that does the heavy work while also handling errors.

        .. seealso:: GetValue for param doc.
        '''
        name, variation = Namespace.SplitNameAndVariation(name)

        # Get values matching any flags ------------------------------------------------------------
        try:
            namespace_value = self._values[name]
        except KeyError:
            e = sys.exc_info()[1]
            missing_key = e[0]
            # If this namespace_var was not found, raise NamespaceKeyError, using the missing key as
            # the first value of the trace
            raise NamespaceKeyError(missing_key)

        # Get only values that match current flags -------------------------------------------------
        try:
            result = namespace_value.GetMatchingValue(self._implicit_flags, explicit_flags)
        except NoMatchForFlagsError:
            raise NamespaceKeyError(namespace_key)
        except MergedTypesDontMatchException:
            e = sys.exc_info()[1]
            Reraise(e, '[Namespace._GetValue] While reading variable "%s"' % namespace_key)
        except CantFindBestMatchException:
            e = sys.exc_info()[1]
            Reraise(e, '[Namespace._GetValue] While reading variable "%s"' % namespace_key)

        # Evaluate the result ----------------------------------------------------------------------
        if evaluated:
            result = result.Evaluate(self, explicit_flags)

        # Convert to string ------------------------------------------------------------------------
        if as_string:
            return result.GetValue(variation=variation)

        return result


    def GetMatchingVariables(self, pattern, explicit_flags=()):
        '''
        :param unicode pattern:
            The pattern to be matched. Uses python's regular expression module.

        :rtype: dict(unicode->INamespaceType)
        :returns:
            A dictionary mapping variables names to their values
        '''
        compiled = re.compile(pattern)

        matches = {}
        for i_key, i_value in self._values.iteritems():
            match = compiled.match(i_key)
            if match:
                try:
                    value = i_value.GetMatchingValue(self._implicit_flags, explicit_flags)
                except NoMatchForFlagsError:
                    pass  # No value for our current flags, ignore it
                else:
                    matches[i_key] = value

        result = {}
        for i_key, i_value in matches.iteritems():
            try:
                result[i_key] = i_value.Evaluate(self, explicit_flags)
            except Exception as e:
                Reraise(e, '[Namespace.GetMatchingVariables] While evaluating variable "%s"' % i_key)

        return result


    __evaluate_regex = re.compile('`(.*?)`')

    def Evaluate(self, value, explicit_flags=(), on_missing_callback=None):
        '''
        Expand namespace variables in the given value.

        :type value: INamespaceType or unicode
        :param value:
            Either a special variable type (that knows how to evaluate itself)

            or

            A string with namespace variables in it. The variables must be enclosed inside
            backquotes. e.g.:

                Evaluate('`var1`/folder/folder2/`my_name`')

        .. seealso:: GetValue for other params doc

        :rtype: unicode
        :returns:
            The evaluated value
        '''
        if IsImplementation(value, INamespaceType):
            return value.Evaluate(self, explicit_flags)

        def Replacer(matchobj):
            key = matchobj.group(1)

            # This handles double grave as a escape sequence to output the grave accent.
            if key == '':
                return '`'

            return self.GetValue(
                key,
                explicit_flags,
                evaluated=True,
                as_string=True,
                on_missing_callback=on_missing_callback
            )

        def Sub(s):
            if s is None:
                return None
            return self.__evaluate_regex.sub(Replacer, s)

        if type(value) == list:
            return map(Sub, value)
        elif type(value) == tuple:
            return tuple(map(Sub, value))
        else:
            return self.__evaluate_regex.sub(Replacer, value)


    def __delitem__(self, namespace_key):
        '''
        Deletes a namespace variable.

        @see Namespace.DelValue
        '''
        return self.DelValue(namespace_key)


    def DelValue(self, namespace_key):
        '''
        Deletes a key from the namespace.

        :param unicode namespace_key:
            A namespace_key to delete, including or not flags.

            Acceptable namespace-keys include:
                <flag>:<key>
                    Deletes only the value associated with the given key and flag.
                *:<key>
                    Deletes all flag variations associated with the given key.
                <key>
                    Deletes only the value associated with the key WITHOUT any flag specification.
                    Any value associated with the key with a flag are kept.

        :rtype: boolean
        :returns:
            Returns True if we found and successfully deleted a value and False otherwise.
        '''
        flags, name = Flags.SplitNamespaceKey(namespace_key)

        try:
            namespace_value = self._values[name]
        except KeyError:
            e = sys.exc_info()[1]
            missing_key = e[0]
            raise NamespaceKeyError(missing_key)

        # Call the callback associated with this value.
        callback = self._callbacks.get(name)
        if callback is not None:
            # Since we might be deleting for all values, remove '*' from the list of flags we use
            # to obtain the old value, since it isn't a real flag.
            get_flags = tuple(f for f in flags if f != '*')

            # Obtain the old value (to send to the callback)
            old_value = namespace_value.GetValueWithFlags(get_flags)

            # New value is None, since we are deleting
            callback(self, old_value, None)

        return namespace_value.DelValueWithFlags(flags)


    # Flags ----------------------------------------------------------------------------------------
    def SetFlag(self, flag):
        '''
        Sets a flag as active. The flag must have been previously declared.

        Does nothing if the flag was already set.

        :param unicode flag:
        '''
        if flag not in self._implicit_flags:
            self._implicit_flags.append(flag)


    def UnsetFlag(self, flag):
        '''
        Disables a flag. The flag must have been previously declared.

        Does nothing if the flag was not set.

        :param unicode flag:
        '''
        if flag in self._implicit_flags:
            self._implicit_flags.remove(flag)


    def ClearFlags(self):
        '''
        Clears all the flags
        '''
        self._implicit_flags = []


    def GetFlags(self):
        '''
        :rtype: list(unicode)
        :returns:
            Returns a copy of the current flags (implicit).
        '''
        return self._implicit_flags[:]


    def _DeclareFlag(self, name, description):
        '''
        Declare a new flag in the namespace.

        :param unicode name:
            The name of the flag.

        :param unicode description:
            The description of the flag.
        '''
        assert name not in self._declared_flags

        if name.startswith(':'):
            name = name[1:]

        self._declared_flags[name] = description


    def EvaluateFlags(self, flags):
        '''
        :param unicode flags:
            List of flags, separated by ':'
            Includes both yes and not flags ('!flag_name').

        :rtype: bool
        :returns:
            Returns true if the given flags match the implicit flags.
        '''
        match_flags = set(self._implicit_flags)

        if flags:
            namespace_key = "%s:_DUMMY_" % flags
        else:
            return True

        flags, _name = Flags.SplitNamespaceKey(namespace_key)

        flags = Flags.CreateFromFlags(flags)
        match_points = flags.MatchPointsForFlags(match_flags)
        return match_points > -1


    # Print ----------------------------------------------------------------------------------------
    def PrintImplicitFlags(self, oss=None):
        '''
        Print the implicit flags and their descriptions.

        :param file oss:
            The output stream to print on. Use stdout by default.
        '''
        if oss is None:
            oss = sys.stdout

        oss.write('\n')
        for i_name in sorted(self._implicit_flags):
            oss.write('  %s' % i_name)


    def PrintDeclaredFlags(self, oss=None):
        '''
        Print the declared flags and their descriptions.

        :param file oss:
            The output stream to print on. Use stdout by default.
        '''
        if oss is None:
            oss = sys.stdout

        oss.write('\n')
        for i_name, i_description in sorted(self._declared_flags.items()):
            oss.write('  %s = %s\n' % (i_name, i_description))


    def Print(self, oss=None, evaluate=False, pattern=None):
        '''
        Prints the contents of this namespace in the given output stream

        :param unicode pattern:
            The pattern to filter the namespace variables (As in fnmatch module).
            If None prints all symbols.

        :param file oss:
            The output stream to print on. Use stdout by default.

        :param bool evaluate:
            If True evaluate each variable with the current flags setting. Otherwise prints the
            original variable values, including its flagged variations.

        :rtype: list(unicode)
        :returns:
            List of strings with the namespace contents.
        '''
        if oss is None:
            oss = sys.stdout

        oss.write('\n')
        for i_name, i_value in sorted(self._values.items()):
            if pattern is not None:
                if not re.match(pattern, i_name):
                    continue

            if evaluate:
                try:
                    value = self.GetValue(i_name, as_string=True)
                except Exception:
                    e = sys.exc_info()[1]
                    value = "*** Exception raised while obtaining the value: %s" % e.__class__.__name__

                oss.write('  %s = %s\n' % (i_name, value))
            else:
                i_value.Print(i_name, oss)
