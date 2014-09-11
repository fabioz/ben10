from __future__ import unicode_literals
#===================================================================================================
# PropertiesDict
#===================================================================================================
class PropertiesDict(dict):
    '''
    Class to hold the properties. It acts as a list and has options to set/get the defaults for some
    name.

    It's used instead of a dict directly as it was before to keep backward compatibility with
    coilib30.
    '''

    SetDefault = dict.__setitem__
    GetDefault = dict.__getitem__
    AddToDefaults = dict.update


#===================================================================================================
# PropertiesDescriptor
#===================================================================================================
class PropertiesDescriptor(object):
    '''
    Like PropertiesDescriptor, but returns a dict of property -> default value.
    '''

    _cache = {}

    def __get__(self, obj, cls=None):
        '''
        :rtype: dict(str->object)
        :returns:
            Returns a dict with all the properties/default values available in the hierarchy.
            E.g.: {'a': 0, 'b': 0.0, 'name': '<None>', 'id': '', 'pool': None}
        '''
        if cls is None:
            cls = obj.__class__

        result = PropertiesDescriptor._cache.get(cls)
        if result is None:
            # loop over the hierarchy taking the __properties__ of each class
            result = PropertiesDict()
            for c in reversed(cls.__mro__):
                update_with = getattr(c, '__properties__', None)
                if update_with is not None:
                    result.update(update_with)

            PropertiesDescriptor._cache[cls] = result

        return result


    def __set__(self, obj, value):
        raise AttributeError("__all_properties__ is read-only!")


    @staticmethod
    def ClearCache():
        '''
        Clears the cache.
        '''
        PropertiesDescriptor._cache.clear()
