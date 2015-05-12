from __future__ import unicode_literals
from ben10.filesystem import NormStandardPath, NormalizePath, StandardizePath
from ben10.foundation.decorators import Implements, Override
from ben10.foundation.memoize import Memoize
from ben10.foundation.reraise import Reraise
from ben10.interface import ImplementsInterface, Interface
import os



#===================================================================================================
# Constants
#===================================================================================================

# OVERRIDE is used as a priority handle for merging variables
OVERRIDE = 'override'
DEFAULT_PRIORITY = 100
MIXED_PRIORITY = 'MIXED'


#===================================================================================================
# NamespaceTypeMergeException
#===================================================================================================
class NamespaceTypeMergeException(RuntimeError):

    def __init__(self, a, b, message):
        self.a = a
        self.b = b
        message += '\n' + \
            '\ta: %s("%s")\n' % (self.a.__class__.__name__, self.a.value) + \
            '\tb: %s("%s")\n' % (self.b.__class__.__name__, self.b.value)
        Exception.__init__(self, message)



#===================================================================================================
# MergedTypesDontMatchException
#===================================================================================================
class MergedTypesDontMatchException(NamespaceTypeMergeException):

    def __init__(self, a, b):
        NamespaceTypeMergeException.__init__(
            self,
            a,
            b,
            'Types for variables being merged do not match.'
        )


#===================================================================================================
# NamespaceTypeUnmergeable
#===================================================================================================
class NamespaceTypeUnmergeable(NamespaceTypeMergeException):
    '''
    Raised when trying to merge a variable type that can't be merged.
    '''
    def __init__(self, a, b):
        message = 'Trying to merge variables that cannot be merged.\n'
        'Values: "%s" and "%s"' % (unicode(a), unicode(b))

        NamespaceTypeMergeException.__init__(self, a, b, message)



#===================================================================================================
# INamespaceType
#===================================================================================================
class INamespaceType(Interface):
    '''
    Interface that represents special types used as NAMESPACE_VARIABLES value in Namespace.
    '''

    VARIATION_NONE = None
    VARIATION_ENV = '$'
    VARIATION_IO = '#'
    VARIATION_STR = 'STR'


    def GetValue(self, variation=VARIATION_NONE):
        '''
        :param VARIATION_XXX variation:
            The variable allows the namespace-type to alter the value depending on the usage.
            This is used today to allow PATH and PATHLIST types to fix the slashes on Windows systems.

        :rtype: object
        :returns:
            Returns the value inside this type.

            Some implementations might want to return a string, others a list, etc
        '''


    def ExpandScopeInExpression(self, shared_script_name):
        '''
        Expands 'self.' in this type's expression, replacing it with '<shared_script_name>.'

        :param unicode shared_script_name:
            The name of the shared_script we want to use as the scope

        :rtype: INamespaceType
        :returns:
            A copy of this type with the scope expanded.
        '''

    def Evaluate(self, namespace, explicit_flags=()):
        '''
        Evaluates string within this value, without losing its original type

        :param Namespace namespace:
            The namespace that contains this value and any other values this might depend on

        :param list(unicode) explicit_flags:
            .. seealso:: Namespace.Evaluate

        :rtype: INamespaceType
        :returns:
            A copy of this type with expanded expressions.
        '''

    @classmethod
    def CreateFromString(cls, s):
        '''
        Create an instance of this class from the given string.

        :param unicode s:
            The string to create a namespace type instance from.
        '''


#===================================================================================================
# RAW
#===================================================================================================
class RAW(object):
    '''
    Represents a Raw value, this can be any Python object.

    Unlike other namespace types, this is only a placeholder for variables that don't actually
    behave the same as other (they cannot be evaluated, they have no scope and so on)
    '''
    ImplementsInterface(INamespaceType)

    def __init__(self, value):
        '''
        :param object value:
            Any object
        '''
        self.value = value


    @Implements(INamespaceType.GetValue)
    def GetValue(self, variation=INamespaceType.VARIATION_NONE):
        return self.value


    @Implements(INamespaceType.ExpandScopeInExpression)
    def ExpandScopeInExpression(self, shared_script_name):
        return self


    @Implements(INamespaceType.Evaluate)
    def Evaluate(self, namespace, explicit_flags=()):
        return self


    @classmethod
    @Implements(INamespaceType.CreateFromString)
    def CreateFromString(cls, s):
        raise NotImplementedError


#===================================================================================================
# _BaseNamespaceType
#===================================================================================================
class _BaseNamespaceType(object):
    '''
    Base class for namespace types
    '''
    ImplementsInterface(INamespaceType)

    def __init__(self, value, priority=DEFAULT_PRIORITY):
        '''
        :param tuple(object) args:
            Tuple of objects that will represent this type

        :param dict(unicode->object) kwargs:
            Additional keyword arguments:

                priority: int or OVERRIDE
                    Defined the priority of this value, used when merging with over values.
        '''
        self.value = value
        self.priority = priority


    @Implements(INamespaceType.GetValue)
    def GetValue(self, variation=INamespaceType.VARIATION_NONE):
        if variation == INamespaceType.VARIATION_STR:
            return self._GetValueAsString()
        if variation == INamespaceType.VARIATION_IO:
            return self._GetValueAsIO()
        if variation == INamespaceType.VARIATION_ENV:
            return self._GetValueAsEnvironment()
        return self._GetValue()


    def _GetValueRepr(self):
        '''
        Representation of self.value

        :rtype: unicode
        :returns:
            Returns the value with no variation.
        '''
        return self.value


    def _GetValue(self):
        '''
        Actually implementation for GetValue for the VARIATION_NONE.

        :rtype: unicode
        :returns:
            Returns the value with no variation.
        '''
        return self.value


    def _GetValueAsString(self):
        '''
        Actually implementation for GetValue for the VARIATION_STR.

        :rtype: unicode
        :returns:
            Returns the value as a string
        '''
        return unicode(self._GetValue())


    def _GetValueAsEnvironment(self):
        '''
        Actually implementation for GetValue for the VARIATION_ENV.

        :rtype: unicode
        :returns:
            Returns the value ready for the OS shell.
        '''
        return self._GetValue()


    def _GetValueAsIO(self):
        '''
        Actually implementation for GetValue for the VARIATION_IO.

        :rtype: unicode
        :returns:
            Returns the value for I/O.
        '''
        return self.AsString(template="$t:$v")


    @Implements(INamespaceType.ExpandScopeInExpression)
    def ExpandScopeInExpression(self, shared_script_name):
        return self.__class__(
            self._ExpandScopeInExpression(unicode(self), shared_script_name),
            priority=self.priority
        )


    @Implements(INamespaceType.Evaluate)
    def Evaluate(self, namespace, explicit_flags=()):
        return self.__class__(
            namespace.Evaluate(unicode(self), explicit_flags),
            priority=self.priority
        )


    def __str__(self):
        return self.AsString()


    def __repr__(self):
        return self.AsString(template="$t('$r')")


    def __eq__(self, other):
        return self.GetValue() == other.GetValue()


    def AsString(self, template='$v', justify=0, flags=[]):
        '''
        Returns this variable representation as a string.

        :param int justify:
            The number of character to justify. This will have effect only if using $j variable on
            the template.

        :param unicode template:
            The template with the following available variables:
                $f: The flags (as given by the flags parameter)
                $j: A number of character enough to justify the type ($t) with the given justify
                    (parameter) value.
                $r: Raw value of the variable (usually the string representation of parameters used
                    in __init__
                $t: The type of the variable
                $v: The value of the variable

            Defaults to "$v"

        :rtype: unicode

        .. note::
            The __str__ also uses this method with a different template.
            The idea is that all string representations for the namespace-type would be implemented
            by this method. Please add functionality as needed.
        '''
        import string
        result = string.Template(template)

        substitutes = {
            'f' : ':'.join(flags),
            'j' : ' ' * (justify - len(self.__class__.__name__)),
            't' : self.__class__.__name__,
        }

        # These dynamic values might fail when being obtained. If that happens, we do not add the
        # to the list of substitutes. This allows us to print certain representations of
        # ENVIRON('USERNAME'), even if `GetValue` for it fails in linux.
        try:
            substitutes['r'] = self._GetValueRepr()
        except:
            pass

        try:
            substitutes['v'] = self.GetValue(variation=INamespaceType.VARIATION_STR)
        except:
            pass

        return result.substitute(**substitutes)


    def CreateCopy(self):
        '''
        Creates a copy of this instance and returns it.

        :rtype: <This Type>
        :returns: Returns a copy of this instance.
        '''
        return self.__class__(self.value, priority=self.priority)


    def Merge(self, other):
        '''
        Merges this and other object and returns a new instance of the same class.

        :param  other:
            Other object of the same type as this

        :rtype: <This Type>
        :returns:
            An object of the same type as this one with the merged contents.
        '''

        # Ensure that other type is the same class as this
        if (self.priority == OVERRIDE) and (other.priority == OVERRIDE):
            raise NamespaceTypeMergeException(self, other, 'Merging two values marked for OVERRIDE')

        # Find the result based on priority system
        if other.priority == OVERRIDE:
            return other.CreateCopy()

        if self.priority == OVERRIDE:
            return self.CreateCopy()

        if self.__class__ != other.__class__:
            raise MergedTypesDontMatchException(self, other)

        else:
            # Let class handle priorities
            return self.DoMerge(other)


    def DoMerge(self, other):
        '''
        Implementation method for Merge.

        By default, the namespace-types do not implement a merge algorithm.

        :param _BaseNamespaceType other:
            Another instance of the "same type"? of this instance

        :rtype: __class__
        :returns:
            A new instance of the same type of this one with the merged values.
        '''
        raise NamespaceTypeUnmergeable(self, other)


    def Add(self, other):
        '''
        Returns a copy of this object with all the elements of both this object and the given one.

        This interface is only valid for list-like classes.

        This is used to implement Aasimar command that appends values to a list, more specifically
        the system.flags configuration.

        :param __class__ other:
            Another instance of the "same type" of this instance

        :rtype: __class__
        '''
        raise NamespaceTypeUnmergeable(self, other)


    def Remove(self, other):
        '''
        Returns a copy of this object without the elements in the given object.

        This interface is only valid for list-like classes.

        This is used to implement Aasimar command that removes values to a list, more specifically
        the system.flags configuration.

        :param __class__ other:
            Another instance of the "same type" of this instance

        :rtype: __class__
        '''
        raise NamespaceTypeUnmergeable(self, other)


    @classmethod
    @Implements(INamespaceType.CreateFromString)
    def CreateFromString(cls, s):
        return cls(s)


    # FIFO because it's faster than LRU and 1000 should be enough for all evaluated expressions.
    @classmethod
    @Memoize(1000, Memoize.FIFO)
    def _ExpandScopeInExpression(cls, expression, self_name):
        '''
        Expands the given expression, replacing 'self.' the given self_name.

        e.g: (assume self_name is 'system')
            'self.var' -> 'system.var'

        :param unicode expression:
            A string representing a namespace variable

        :param unicode self_name:
            The name of the SharedScript we want to use for this variable

        :rtype: unicode
        :returns:
            The expression expanded with the given name.
        '''
        if 'self.' in expression:
            assert self_name is not None
            return expression.replace('self.', self_name + '.')

        return expression



#===================================================================================================
# STRING
#===================================================================================================
class STRING(_BaseNamespaceType):

    @Override(_BaseNamespaceType.__init__)
    def __init__(self, value, priority=DEFAULT_PRIORITY):
        _BaseNamespaceType.__init__(self, unicode(value), priority=priority)



#===================================================================================================
# PATH
#===================================================================================================
class PATH(STRING):

    @Override(_BaseNamespaceType.__init__)
    def __init__(self, value, priority=DEFAULT_PRIORITY):
        STRING.__init__(self, NormStandardPath(StandardizePath(value)), priority=priority)


    @Override(_BaseNamespaceType._GetValueAsEnvironment)
    def _GetValueAsEnvironment(self):
        return NormalizePath(self._GetValue())



#===================================================================================================
# CALLABLE
#===================================================================================================
class CALLABLE(_BaseNamespaceType):
    '''
    Represent a callable type variable.

    `self.value` (a callable) is executed whenever we try to obtain the value of this type.
    '''
    ImplementsInterface(INamespaceType)


    @Override(_BaseNamespaceType._GetValueRepr)
    def _GetValueRepr(self):
        return self.value.__name__


    @Override(_BaseNamespaceType._GetValue)
    def _GetValue(self):
        return self.value()


    @Override(_BaseNamespaceType._GetValueAsIO)
    def _GetValueAsIO(self):
        # CALLABLE can't properly be represented as IO, so we just represent the value of our
        # callable as a STRING.
        return STRING(self.value(), self.priority).GetValue(variation=INamespaceType.VARIATION_IO)


    @Override(_BaseNamespaceType.ExpandScopeInExpression)
    def ExpandScopeInExpression(self, shared_script_name):
        return self  # Callables cannot expand their scope, since they are functions, and not strings


    @Override(_BaseNamespaceType.Evaluate)
    def Evaluate(self, namespace, explicit_flags=()):
        return self  # Callables are not evaluated, since they are functions, and not strings



#===================================================================================================
# ENVIRON
#===================================================================================================
class ENVIRON(_BaseNamespaceType):
    '''
    Represent an environment variable. Simply returns the os.environ variable associated with
    its value whenever it is queried.
    '''

    @Override(_BaseNamespaceType.__init__)
    def __init__(self, value, default=None, priority=100, mandatory=False):
        '''
        :type default: unicode or None
        :param default:
            Default value to be returned when a variable is not found in the environemnt, and
            'mandatory' is set to False

        :param bool mandatory:
            If True and a variable is not found, a KeyError is raised

            If False and a variable is not found, the 'default' value is returned.

        '''
        assert (mandatory and default != None) == False, 'A variable cannot be mandatory and ' + \
            'have a default value at the same time.'

        _BaseNamespaceType.__init__(self, value, priority=priority)
        self.__default = default
        self.__mandatory = mandatory


    @Override(_BaseNamespaceType._GetValue)
    def _GetValue(self):
        try:
            return os.environ[self.value]
        except KeyError:
            # If mandatory, we must return from the environment
            if self.__mandatory:
                raise

            # If optional, we return the default value (either set by the user, or None, which
            # means this variable was not found.
            return self.__default


    @Implements(INamespaceType.ExpandScopeInExpression)
    def ExpandScopeInExpression(self, shared_script_name):
        default = self.__default
        if default is not None:
            default = self._ExpandScopeInExpression(default, shared_script_name)

        return self.__class__(
            self.value,
            default=default,
            priority=self.priority
        )


    @Implements(INamespaceType.Evaluate)
    def Evaluate(self, namespace, explicit_flags=()):
        # We override Evaluate to properly create an instance of this class, including the
        # default value
        default = self.__default
        if default is not None:
            default = namespace.Evaluate(default, explicit_flags)

        return self.__class__(
            self.value,
            default=default,
            priority=self.priority,
        )


#===================================================================================================
# LIST
#===================================================================================================
class LIST(_BaseNamespaceType):

    # Additional kwargs to be used when merging
    _MERGE_KWARGS = {}

    @Override(_BaseNamespaceType.__init__)
    def __init__(self, *args, **kwargs):
        '''
        .. seealso:: _BaseNamespaceType.__init__

        :type args: list(string) | list(list) with one element
        :param args:
            Values in the list.

        :type priority_list: None | list(int)
        :keyword priority_list:
            Priority list used for merging, this is used to ensure that merged lists will keep track
            of all priorities after merging.

            If None, uses kwparam 'priority' as the priority for all of its elements
        '''
        # If we received a priority list
        if 'priority_list' in kwargs:
            # User the given priority list
            self.priority_list = kwargs.pop('priority_list')
        else:
            # Set priority list
            self.priority_list = len(args) * [kwargs.get('priority', DEFAULT_PRIORITY)]

        # Initialize superclass
        if isinstance(args, tuple):
            args = list(args)
        assert isinstance(args, list)

        _BaseNamespaceType.__init__(self, args, **kwargs)


    def __iter__(self):
        '''
        Makes this list iterable
        '''
        return iter(self.value)


    @Override(_BaseNamespaceType.__repr__)
    def __repr__(self):
        '''
        Overridden to better represent lists
        '''
        t = self.__class__.__name__
        values = ["'%s'" % v for v in self.value]
        return t + '(' + ', '.join(values) + ')'


    @Override(_BaseNamespaceType.ExpandScopeInExpression)
    def ExpandScopeInExpression(self, shared_script_name):
        # Expand scope for each string in this list
        try:
            args = [self._ExpandScopeInExpression(i, shared_script_name) for i in self.value]
            kwargs = {'priority':self.priority}
        except Exception, e:
            Reraise(e, 'While expanding "%s", in the list "%s"' % (unicode(i), unicode(self.value)))

        return self.__class__(*args, **kwargs)


    @Override(_BaseNamespaceType.Evaluate)
    def Evaluate(self, namespace, explicit_flags=()):
        # Evaluate each string in this list
        try:
            args = [namespace.Evaluate(i, explicit_flags) for i in self.value]
        except Exception, e:
            Reraise(e, 'While expanding "%s", in the list "%s"' % (unicode(i), unicode(self.value)))
        kwargs = {'priority':self.priority, 'priority_list':self.priority_list}

        return self.__class__(*args, **kwargs)


    @Override(_BaseNamespaceType.CreateCopy)
    def CreateCopy(self):
        return self.__class__(priority=self.priority, *self.value)


    @Override(_BaseNamespaceType.DoMerge)
    def DoMerge(self, other):
        # Exceptional handling for 2 empty lists
        if len(self.value) + len(other.value) == 0:
            return self.__class__(priority=MIXED_PRIORITY, priority_list=[])

        # Zip priorities and values
        mine = zip(self.priority_list, self.value)
        others = zip(other.priority_list, other.value)

        # Sort items by priority
        result = []
        unique_priorities = set(self.priority_list).union(set(other.priority_list))
        for i_priority in sorted(unique_priorities):
            # Always add my values first, even with the same priority
            for j_priority, j_value in mine:
                if j_priority == i_priority:
                    result.append((i_priority, j_value))

            for j_priority, j_value in others:
                if j_priority == i_priority:
                    result.append((i_priority, j_value))

        # Transpose tuples, now with sorted priorities and values
        priority_list, values = zip(*result)

        # Create new class with values, indicate that now we have mixed priorities
        args = values
        kwargs = {'priority' : MIXED_PRIORITY, 'priority_list' : priority_list}
        kwargs.update(self.__class__._MERGE_KWARGS)

        return self.__class__(*args, **kwargs)


    @Override(_BaseNamespaceType.Add)
    def Add(self, other):
        # Only add values that are not already in this list
        added_values = []

        for value in other.value:
            if value not in self.value and value not in added_values:
                added_values.append(value)

        values = self.value + added_values
        return self.__class__(priority=self.priority, *values)


    @Override(_BaseNamespaceType.Remove)
    def Remove(self, other):
        values = filter(
            lambda x: x not in other.value,
            self.value
        )
        return self.__class__(
            priority=self.priority,
            *values
        )


    @Override(_BaseNamespaceType._GetValueAsString)
    def _GetValueAsString(self):
        return ','.join(self.GetValue())


    @Override(_BaseNamespaceType._GetValueAsEnvironment)
    def _GetValueAsEnvironment(self):
        return ','.join(self.GetValue())


    @classmethod
    @Implements(INamespaceType.CreateFromString)
    def CreateFromString(cls, s):
        '''
        Lists are stored as string in the form:
            "item,item,item"
        '''
        if s == '':
            return cls()
        args = s.split(',')
        return cls(*args)



#===================================================================================================
# PATH
#===================================================================================================
class PATHLIST(LIST):
    '''
    Represents a path. Variables of this type can be merged with other paths, and they are in charge
    of correctly printing a path (using os.pathsep to join values, using a normalized path and
    expanding environment variables)
    '''
    # Additional kwargs to be used when merging
    # There is no need to normalize paths after a merge, since both sources are already normalized.
    _MERGE_KWARGS = {'normalized' : True}

    @Override(_BaseNamespaceType.__init__)
    def __init__(self, *args, **kwargs):
        args = [i for i in args if i]  # Clears empty strings and Nones.
        if args and isinstance(args[0], (list, tuple)):
            raise DeprecationWarning(
                'PATHLIST creation with a list is deprecated. Use *args instead.'
            )

        if not kwargs.pop('normalized', False):
            args = map(NormalizePath, args)
            args = map(StandardizePath, args)

        LIST.__init__(self, *args, **kwargs)


    @Override(_BaseNamespaceType._GetValueAsEnvironment)
    def _GetValueAsEnvironment(self):
        return os.pathsep.join(map(NormalizePath, self._GetValue()))


#===================================================================================================
# NamespaceTypeFactory
#===================================================================================================
class NamespaceTypeFactory(object):

    CLASSES = [
        PATHLIST,
        LIST,
        ENVIRON,
        # #CALLABLE, Not available in factory
        PATH,
        STRING,
    ]

    @classmethod
    def CreateFromString(cls, s, default_type=STRING):
        '''
        Analyzes a string value and convert it to a special namespace type, if necessary.

        This applies to PATH and ENVIRON, which must follow this syntax:
            'PATH:xxxx,zzzz' == PATH('xxxx', 'zzzz')
            'ENVIRON:yyyy' == ENVIRON('yyyy')

        :param unicode s:
            String representation of a value in the configuration file

        :rtype: INamespaceType
        '''
        assert default_type in cls.CLASSES, 'default_type  must be in ' + \
            repr(sorted([x.__name__ for x in cls.CLASSES])) + ' (received ' + \
            default_type.__name__ + ')'

        value = s.split(':', 1)

        if len(value) == 1:
            return default_type(s)

        var_type, var_value = value

        if var_type == CALLABLE.__name__:
            raise RuntimeError('CALLABLE not available in NamespaceTypeFactory')

        for i_class in cls.CLASSES:
            if var_type == i_class.__name__:
                return i_class.CreateFromString(var_value)

        return default_type(s)
