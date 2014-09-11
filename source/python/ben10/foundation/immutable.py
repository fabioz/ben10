from __future__ import unicode_literals
'''
    Defines types and functions to generate immutable structures.

    USER: The cache-manager uses this module to generate a valid KEY for its cache dictionary.
'''
from types import NoneType

_IMMUTABLE_TYPES = set((int, long, float, unicode, bool, NoneType))

#===================================================================================================
# RegisterAsImmutable
#===================================================================================================
def RegisterAsImmutable(immutable_type):
    '''
    Registers the given class as being immutable. This makes it be immutable for this module and
    also registers a faster copy in the copy module (to return the same instance being copied).

    :param type immutable_type:
        The type to be considered immutable.
    '''
    _IMMUTABLE_TYPES.add(immutable_type)

    # Fix it for the copy too!
    import copy
    copy._copy_dispatch[immutable_type] = copy._copy_immutable


#===================================================================================================
# AsImmutable
#===================================================================================================
def AsImmutable(value, return_str_if_not_expected=True):
    '''
    Returns the given instance as a immutable object:
        - Converts lists to tuples
        - Converts dicts to ImmutableDicts
        - Converts other objects to unicode
        - Does not convert basic types (int/float/unicode/bool)

    :param object value:
        The value to be returned as an immutable value

    :param bool return_str_if_not_expected:
        If True, a string representation of the object will be returned if we're unable to match the
        type as a known type (otherwise, an error is thrown if we cannot handle the passed type).

    :rtype: object
    :returns:
        Returns an immutable representation of the passed object
    '''

    #Micro-optimization (a 40% improvement on the AsImmutable function overall in a real case
    #using sci20 processes).
    #Checking the type of the class before going to the isinstance series and added
    #SemanticAssociation as an immutable object.
    value_class = value.__class__

    if value_class in _IMMUTABLE_TYPES:
        return value

    if value_class == dict:
        return ImmutableDict((i, AsImmutable(j)) for i, j in value.iteritems())

    if value_class in (tuple, list):
        return tuple(AsImmutable(i) for i in value)

    if value_class in (set, frozenset):
        return frozenset(value)


    #Now, on to the isinstance series...
    if isinstance(value, (int, long, float, unicode, bool)):
        return value

    if isinstance(value, dict):
        return ImmutableDict((i, AsImmutable(j)) for i, j in value.iteritems())

    if isinstance(value, (tuple, list)):
        return tuple(AsImmutable(i) for i in value)

    if isinstance(value, (set, frozenset)):
        return frozenset(value)

    if return_str_if_not_expected:
        return unicode(value)

    else:
        raise RuntimeError('Cannot make %s immutable (not supported).' % value)




#===================================================================================================
# ImmutableDict
#===================================================================================================
class ImmutableDict(dict):
    '''A hashable dict.'''

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self._hash = None
    def __deepcopy__(self, memo):
        return self #it's immutable, so, there's no real need to make any copy
    def __setitem__(self, key, value):
        raise NotImplementedError, "dict is immutable"
    def __delitem__(self, key):
        raise NotImplementedError, "dict is immutable"
    def clear(self):
        raise NotImplementedError, "dict is immutable"
    def setdefault(self, k, default=None):
        raise NotImplementedError, "dict is immutable"
    def popitem(self):
        raise NotImplementedError, "dict is immutable"
    def update(self, other):
        raise NotImplementedError, "dict is immutable"
    def __hash__(self):
        if self._hash is None:
            #must be sorted (could give different results for dicts that should be the same
            #if it's not).
            self._hash = hash(tuple(sorted(self.iteritems())))

        return self._hash

    def AsMutable(self):
        '''
            :rtype: this dict as a new dict that can be changed (without altering the state
            of this immutable dict).
        '''
        return dict(self.iteritems())

