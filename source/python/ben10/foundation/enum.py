from __future__ import unicode_literals
'''
    An enumeration is a set of symbolic names bound to unique, constant integer values. Within an
    enumeration, the values can be compared by identity, and the enumeration itself can be iterated
    over. Enumeration items can be converted to and from their integer equivalents, supporting use
    cases such as storing enumeration values in a database.

    The properties of an enumeration are useful for defining an immutable, related set of constant
    values that have a defined sequence but no inherent semantic meaning. Classic examples are days
    of the week (Sunday through Saturday) and school assessment grades ('A' through 'D', and 'F').
    Other examples include error status values and states within a defined process.

    It is possible to simply define a sequence of values of some other basic type, such as int or
    unicode, to represent discrete arbitrary values. However, an enumeration ensures that such values
    are distinct from any others, and that operations without meaning ("Wednesday times two") are
    not defined for these values.

    Enumerations are created using the class syntax, which makes them easy to read and write.
    Every enumeration value must have a unique integer value and the only restriction on their
    names is that they must be valid Python identifiers. To define an enumeration, derive from the
    Enum class and add attributes with assignment to their integer values.

    >>> from ben10.foundation.enum import Enum
    >>> class Colors(Enum):
    ...     red = 0
    ...     green = 1
    ...     blue = 2


    Adaptation of flufl.enum
    Credit: Barry A. Warsaw
'''
from ben10.foundation.odict import odict
from operator import itemgetter


#===================================================================================================
# EnumValue
#===================================================================================================
class EnumValue(tuple):
    '''
    Base class for the representation of all enumeration values.

    EnumValue(Color, 'red', 12) prints as 'Color.red' and can be converted
    to the integer 12.
    '''

    __slots__ = ()

    def __new__(cls, Enumcls, value, name):
        # Note: deriving from tuple for efficiency
        #
        # self[0] is the Enum class
        # self[1] is the integer value (int)
        # self[2] is the name of this enumerate value (unicode)

        return tuple.__new__(cls, (Enumcls, value, name))


    def __repr__(self):
        return '<%s.%s [%d]>' % (
            self[0].__name__, self[2], self[1])


    def __str__(self):
        return '%s.%s' % (self[0].__name__, self[2])


    def __int__(self):
        return self[1]


    def __reduce__(self):
        return getattr, (self[0], self[2])


    @property
    def enum(self):
        '''
        @return the class associated with the enum value.
        '''
        return self[0]


    @property
    def name(self):
        '''
        @return the name of the enum value.
        '''
        return self[2]


    def __eq__(self, other):
        return self is other


    def __ne__(self, other):
        return self is not other


    def __lt__(self, other):
        return self[1] < other[1]


    def __gt__(self, other):
        return self[1] > other[1]


    def __le__(self, other):
        return self[1] <= other[1]


    def __ge__(self, other):
        return self[1] >= other[1]


    __hash__ = object.__hash__



#===================================================================================================
# EnumMetaclass
#===================================================================================================
class EnumMetaclass(type):

    def __new__(self, *args, **kwargs):
        # Convert first arg to bytes, since type does not accept unicode for class names.
        args = (bytes(args[0]),) + args[1:]
        return type.__new__(self, *args, **kwargs)


    def __init__(cls, name, bases, attributes):
        '''
        Creates an Enum class.

        :param type cls:
            The class being defined.

        :param unicode name:
            The name of the class.

        :param list(type) bases:
            The class's base classes.

        :type attributes: dict(unicode -> object)
        :param attributes:
            The class attributes.
        '''
        super(EnumMetaclass, cls).__init__(name, bases, attributes)

        # Store EnumValues here for easy access.
        enums = odict()

        # Figure out the set of enum values on the base classes, to ensure
        # that we don't get any duplicate values (which would screw up
        # conversion from integer).
        for basecls in cls.__mro__:
            if hasattr(basecls, '_enums'):
                enums.update(basecls._enums)

        # Creates a class for the enumerate values
        Enumvalue_class = type(bytes(name + 'Value'), (EnumValue,), {})
        cls._value_type = Enumvalue_class

        # For each class attribute, create an EnumValue and store that back on
        # the class instead of the int.  Skip Python reserved names.  Also add
        # a mapping from the integer to the instance so we can return the same
        # object on conversion.

        for attr, intval in sorted(attributes.items(), key=itemgetter(1)):
            if not (attr.startswith('__') and attr.endswith('__')):
                intval = attributes[attr]
                if not isinstance(intval, (int, long)):
                    raise TypeError('Enum value is not an integer: %s=%r' % (attr, intval))
                Enumvalue = Enumvalue_class(cls, intval, unicode(attr))
                if intval in enums:
                    raise TypeError('Multiple enum values: %s' % intval)
                # Store as an attribute on the class, and save the attr name
                setattr(cls, attr, Enumvalue)
                enums[intval] = attr

        cls._enums = enums


    def __repr__(self):
        enums = ['%s: %d' % (
            self._enums[k], k) for k in sorted(self._enums)]
        return '<%s {%s}>' % (self.__name__, ', '.join(enums))


    def __iter__(self):
        for i in sorted(self._enums):
            yield getattr(self, self._enums[i])


    def __getitem__(self, i):
        # i can be an integer or a string
        attr = self._enums.get(i)
        if attr is None:
            # It wasn't an integer -- try attribute name
            try:
                return getattr(self, i)
            except (AttributeError, TypeError):
                raise ValueError(i)
        return getattr(self, attr)


    def __len__(self):
        return len(self._enums)


    def GetValueType(self):
        return self._value_type


    # Support both MyEnum[i] and MyEnum(i)
    __call__ = __getitem__



Enum = EnumMetaclass(
    'Enum',  # name
    (),  # bases
    {  # attributes
        '__doc__': 'The public API Enum class.',
    }
)


#===================================================================================================
# __IsAnyBoostPythonEnum
#===================================================================================================
def __IsAnyBoostPythonEnum(enum_class_list):
    '''
    Meant to be used by _IsBoostPythonEnum only.
    '''
    for class_ in enum_class_list:
        if class_.__module__ == 'Boost.Python' and class_.__name__ == 'enum':
            return True
        return __IsAnyBoostPythonEnum(class_.__bases__)
    return False


#===================================================================================================
# _IsBoostPythonEnum
#===================================================================================================
def _IsBoostPythonEnum(enum_class):
    '''
    @return bool:
        True if the class is or descends from a Boost.Python enum.
    '''
    return __IsAnyBoostPythonEnum([enum_class])


#===================================================================================================
# IterEnumValues
#===================================================================================================
def IterEnumValues(enum_class):
    '''
    Helper function to iterate on enumerate values for a given class, that should work identically
    with both Enum and with C++ enums exported with Boost.Python.
    '''
    if isinstance(enum_class, type) and _IsBoostPythonEnum(enum_class):
        return (enum_value for _integer_value, enum_value in sorted(enum_class.values.iteritems()))
    else:
        return iter(enum_class)


#===================================================================================================
# MakeEnum
#===================================================================================================
def MakeEnum(name, enum_list):
    '''
    This is a convenience function for defining a new enumeration given an existing sequence.
    When a sequence is used, it is iterated over to get the enumeration value items. The sequence
    iteration can either return strings or 2-tuples. When strings are used, values are
    automatically assigned starting from 0. When 2-tuples are used, the first item of the tuple is
    a string and the second item is the integer value.

    :param unicode name:
        The enum class name.

    :type enum_list: list((unicode, int) | (unicode))
    :param enum_list:
        A list with the names of the enumerate values, or tuples with the name and the integer
        value.
    '''

    values_are_unique = False
    lookup = {}
    reverse_lookup = {}
    index = 0
    for item in enum_list:
        if type(item) is tuple:
            try:
                item, index = item
            except ValueError:
                raise EnumException, "tuple doesn't have 2 items: %r" % item
        if type(item) is not unicode:
            raise EnumException, "enum name is not a string: %r" % item
        if type(index) is not int:
            raise EnumException, "enum value is not an integer: %r" % index
        if item in lookup:
            raise EnumException, "enum name is not unique: %r" % item
        if values_are_unique and index in reverse_lookup:
            raise EnumException, "enum value %r not unique for %r" % (index, item)
        lookup[item] = index
        reverse_lookup[index] = item
        index += 1

    return EnumMetaclass(unicode(name), (Enum,), lookup)



class EnumException(Exception):
    pass

