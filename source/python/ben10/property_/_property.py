
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
        :type fget: function or NoneType
        :param fget:
            The get function

        :type fset: function or NoneType
        :param fset:
            The set function

        :type fdel: function or NoneType
        :param fdel:
            The del function

        :type doc: str or NoneType
        :param doc:
            This is the docstring of the property
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


    def FromNames(cls, fget_name, fset_name=None, fdel_name=None, doc=None):
        result = cls()
        result.fget_name = fget_name or ''
        result.fset_name = fset_name or ''
        result.fdel_name = fdel_name or ''
        result.doc = doc or ''
        return result

    FromNames = classmethod(FromNames)


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

