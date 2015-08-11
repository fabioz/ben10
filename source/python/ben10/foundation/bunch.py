from __future__ import unicode_literals
'''Bunch utility class.

Implemented by Alex Martelli (http://mail.python.org/pipermail/python-list/2002-July/112007.html), but
with a few modifications:

- allow Bunches to define methods besides special-methods.
- include default comparison.
- performance improvement on __init__: checking before copy.
'''
from ben10.foundation.decorators import Override
import copy



#===================================================================================================
# _IsBunchAttribute
#===================================================================================================
def _IsBunchAttribute(name, value):
    '''
    Returns whether the given combination of attribute name and value classifies it as a bunch
    attribute.

    :param str name: The attribute name.
    :param object value: The attribute itself.
    :return boolean:
    '''
    import inspect

    result = name.startswith('__') \
        or inspect.isfunction(value) \
        or type(value) in (classmethod, staticmethod, property)
    return not result



#===================================================================================================
# MetaBunch
#===================================================================================================
class MetaBunch(type):
    '''
    metaclass for new and improved "Bunch": implicitly defines
    __slots__, __init__ and __repr__ from variables bound in class scope.

    An instance of metaMetaBunch (a class whose metaclass is metaMetaBunch)
    defines only class-scope variables (and possibly special methods, but
    NOT __init__ and __repr__!).  metaMetaBunch removes those variables from
    class scope, snuggles them instead as items in a class-scope dict named
    __defaults__, and puts in the class a __slots__ listing those variables'
    names, an __init__ that takes as optional keyword arguments each of
    them (using the values in __defaults__ as defaults for missing ones), and
    a __repr__ that shows the repr of each attribute that differs from its
    default value (the output of __repr__ can be passed to __eval__ to make
    an equal instance, as per the usual convention in the matter).
    '''

    def __new__(cls, classname, bases, classdict):
        ''' Everything needs to be done in __new__, since type.__new__ is
            where __slots__ are taken into account.
        '''
        from types import NoneType

        # define as local functions the __init__ and __repr__ that we'll
        # use in the new class

        def __init__(self, **kw):
            ''' Simplistic __init__: first set all attributes to default
                values, then override those explicitly passed in kw.
            '''
            for k, (value, copy_op) in self.__defaults__.iteritems():
                if k not in kw:  # No need to set value to be overridden later on.
                    if copy_op is None:
                        # No copy op (immutable value)
                        setattr(self, k, value)
                    else:
                        setattr(self, k, copy_op(value))
            for k, value in kw.iteritems():
                setattr(self, k, value)

        def __repr__(self):
            '''
            repr operator.
            '''
            rep = ['%s=%r' % (k, getattr(self, k)) for k in sorted(self.__defaults__)]
            return '%s(%s)' % (classname, ', '.join(rep))


        def __eq__(self, other):
            '''Basic __eq__.
            '''
            if not isinstance(other, type(self)):
                return False
            for attr in self.__defaults__:
                if getattr(self, attr) != getattr(other, attr):
                    return False
            return True

        def __ne__(self, other):
            return not self == other

        def __getstate__(self):
            state = {}
            for attr in self.__defaults__:
                state[attr] = getattr(self, attr)
            return state

        def __setstate__(self, state):
            for attr in self.__defaults__:
                setattr(self, attr, state.pop(attr))
            assert len(state) == 0

        # build the newdict that we'll use as class-dict for the new class
        newdict = dict(
            __slots__=classdict.pop('__slots__', []),
            __defaults__={},
            __init__=__init__,
            __repr__=__repr__,
            __eq__=__eq__,
            __ne__=__ne__,
            __getstate__=__getstate__,
            __setstate__=__setstate__,
        )

        # update the dafaults dict with the contents of the bases's defaults, so they're
        # properly initialized during __init__
        for base in bases:
            newdict['__defaults__'].update(getattr(base, '__defaults__', {}))


        from weak_ref import WeakList

        for k, value in classdict.iteritems():
            if _IsBunchAttribute(k ,value):
                # class variables, store name in __slots__ and name and
                # value as an item in __defaults__

                # Default for each value is deepcopy, but we may optimize that (if the copy op is
                # None, the value is considered immutable).
                copy_op = copy.deepcopy

                if value.__class__ in (
                    bool, int, float, long, unicode, NoneType
                    ):
                    copy_op = None
                else:
                    if value.__class__ in (tuple, frozenset):
                        if not value:
                            copy_op = None
                        else:
                            copy_op = copy.copy

                    if value.__class__ in (list, set, dict, WeakList):
                        if not value:
                            copy_op = copy.copy


                newdict['__slots__'].append(k)
                newdict['__defaults__'][k] = (value, copy_op)
            else:
                # methods: copy to newdict
                newdict[k] = value

        # finally delegate the rest of the work to type.__new__
        return type.__new__(cls, classname, bases, newdict)



#===================================================================================================
# Bunch
#===================================================================================================
class Bunch(object):
    ''' For convenience: inheriting from Bunch can be used to get
        the new metaclass (same as defining __metaclass__ yourself).
    '''
    __metaclass__ = MetaBunch


#===================================================================================================
# MetaHashableBunch
#===================================================================================================
class MetaHashableBunch(MetaBunch):
    '''
    Implements a hashable Bunch.

    A hashable bunch is created exactly the same as a normal bunch, but the attributes are read-only
    (immutable) and the bunches created this way can be used as keys in dicts and sets.

    Each property defined will have a private attribute and a public read-only property, as well
    as hash and equality methods as expected.

    @note: take care when creating methods for hashable bunches, they should not change the internal
        attributes, because this way the hash will change and will create chaos if those bunches are
        being used as keys in dicts or sets.
    '''

    @Override(MetaBunch.__new__)
    def __new__(cls, classname, bases, classdict):

        def __init__(self, **kw):
            '''
            Overwrite Bunch's __init__ to initialize the private attributes instead of the public
            ones.
            '''
            self._p_hash_value = None
            newkw = dict(('_' + k, v) for (k, v) in kw.iteritems())
            original_init(self, **newkw)


        def __hash__(self):
            '''
            Basic __hash__: create a tuple with the attributes and hash it.
            '''
            if self._p_hash_value is None:
                self._p_hash_value = hash(tuple(getattr(self, attr) for attr in self.__defaults__))

            return self._p_hash_value


        def __repr__(self):
            '''
            repr operator. Overwritten to generate the string using the public name
            '''
            # strip "_" from the attr names
            rep = ['%s=%r' % (k[1:], getattr(self, k)) for k in sorted(self.__defaults__)]
            return '%s(%s)' % (classname, ', '.join(rep))

        # build the newdict that we'll use as class-dict for the new class
        newdict = dict(
            __slots__=['_p_hash_value'],
            __hash__=__hash__,
        )

        for k, value in classdict.iteritems():
            if _IsBunchAttribute(k, value):
                # put the attribute using the private name
                private_k = '_' + k
                newdict[private_k] = value

                # create get method and put the property into the Bunch's dict; note that the
                # get method itself is not put into the class namespace, only the property itself
                get_func = cls._MakeGetter(private_k)
                newdict[k] = property(get_func)
            else:
                # methods: copy to newdict
                newdict[k] = value


        result = MetaBunch.__new__(cls, classname, bases, newdict)

        # overwrite __init__ and __repr__
        original_init = getattr(result, '__init__')
        setattr(result, '__init__', __init__)
        setattr(result, '__repr__', __repr__)
        return result


    @classmethod
    def _MakeGetter(cls, name):
        '''
        :param unicode name:
            The name of the property to create the get method for.

        :rtype: function
        :returns:
            Return a Get method for the property with the given name for use with the builtin
            "property".
        '''

        def Get(self):
            return getattr(self, name)

        return Get


#===================================================================================================
# HashableBunch
#===================================================================================================
class HashableBunch(object):
    '''
    Same idea as the Bunch class, but used to create hashable Bunch instances.
    '''
    __metaclass__ = MetaHashableBunch


#===================================================================================================
# ConvertToDict
#===================================================================================================
def ConvertToDict(bunch):
    '''
    Converts the contents of a bunch to a dictionary. Every attribute name of the bunch is converted
    to a string which maps to its respective attribute value. For instance, given the bunch

    class ThisBunchIsAnExample(Bunch):
        foo = 'cake'
        bar = 0

    the conversion to dict would result in:

    this_dict_is_an_example = {
        'foo' : 'cake'
        'bar' : 0
    }

    Note that attribute values have their original types kept intact in the dict.

    :param Bunch bunch:
        A bunch.

    :rtype: dict(unicode -> object)
    :returns:
        The bunch mapped as a dict.
    '''
    result = {}

    # Gets the dictionary keys from the bunch defaults map
    defaults = bunch.__defaults__
    for key in defaults.iterkeys():
        result[key] = getattr(bunch, key)

    return result
