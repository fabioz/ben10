from __future__ import unicode_literals

#===================================================================================================
# Property
#===================================================================================================
class Property(object):
    '''
    Creates an property just like a built-in property, except that the lookup for the methods is one
    at runtime, which allows subclasses of a class that defines a property to overwrite one of the
    property's methods.

    Note that we set the attribute name to an empty string when it's not available so that any calls
    using that attribute will give an attribute error (as an empty attribute should always give an
    AttributeError)
    '''

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        '''
        :param callable|None fget: The get function.
        :param callable(obj)|None fset: The set function.
        :param callable|None fdel: The del function.
        :param unicode|None doc: This is the docstring of the property.
        '''
        if fget is None:
            self.fget_name = '' #Will give attribute error when accessed with getattr.
        else:
            self.fget_name = fget.__name__

        if fset is None:
            self.fset_name = '' #Will give attribute error when accessed with getattr.
        else:
            self.fset_name = fset and fset.__name__

        if isinstance(fdel, str):
            doc = fdel
            fdel = None

        if fdel is None:
            self.fdel_name = '' #Will give attribute error when accessed with getattr.
        else:
            self.fdel_name = fdel and fdel.__name__

        self.doc = doc or ''


    @classmethod
    def FromNames(cls, fget_name, fset_name=None, fdel_name=None, doc=None):
        '''
        Create a Property instance from the methods names instead of using their references.

        :param unicode fget_name: The name of the get method.
        :param unicode fset_name: The name of the set method.
        :param unicode fdel_name: The name of the del method.
        :param unicode doc: Property documentation.
        :return Property:
        '''
        result = cls()
        result.fget_name = fget_name or ''
        result.fset_name = fset_name or ''
        result.fdel_name = fdel_name or ''
        result.doc = doc or ''
        return result


    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.fget_name)()


    def __set__(self, obj, value):  # @DontTrace
        getattr(obj, self.fset_name)(value)


    def __delete__(self, obj):
        getattr(obj, self.fdel_name)()


    def __repr__(self):
        p = []
        if self.fget_name:
            p.append('fget=%s' % self.fget_name)
        if self.fset_name:
            p.append('fset=%s' % self.fset_name)
        if self.fdel_name:
            p.append('fdel=%s' % self.fdel_name)
        if self.doc:
            p.append('doc=%s' % repr(self.doc))
        return 'Property(%s)' % ', '.join(p)

