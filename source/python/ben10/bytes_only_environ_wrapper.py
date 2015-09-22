from __future__ import unicode_literals
import locale
import os
import six



#===================================================================================================
# ReplaceEnvironWithWrapper
#===================================================================================================
def ReplaceEnvironWithWrapper():
    '''
    Only needed in python2. The only purpose is to avoid unicode keys/values being set to os.environ.
    subprocess.Popen fails on windows if os.environ does not contain bytes only.
    '''
    original_environ = os.environ
    os.environ = BytesOnlyEnvironWrapper(original_environ)



#===================================================================================================
# BytesOnlyEnvironWrapper
#===================================================================================================
class BytesOnlyEnvironWrapper():
    '''
    This is used to avoid unicode strings being set to os.environ.
    When setting an unicode variable, encode it to locale preferred encoding. This seems to work on
    Linux and Windows.
    On Windows it works even when setting a variable to a russian name on portuguese systems.
    '''

    def __init__(self, original_environ):
        self.original_environ = original_environ
        self._local_encoding = locale.getpreferredencoding()


    def __iter__(self):
        return self.original_environ.__iter__()


    def has_key(self, key):
        return self.original_environ.has_key(key)


    def __contains__(self, key):
        return self.original_environ.__contains__(key)


    def iteritems(self):
        return self.original_environ.iteritems()


    def iterkeys(self):
        return self.original_environ.iterkeys()


    def itervalues(self):
        return self.original_environ.itervalues()


    def items(self):
        return self.original_environ.items()


    def keys(self):
        return self.original_environ.keys()


    def values(self):
        return self.original_environ.values()


    def clear(self):
        return self.original_environ.clear()


    def setdefault(self, key, default=None):
        if isinstance(key, unicode):
            key = key.encode(self._local_encoding)
        if isinstance(default, unicode):
            default = default.encode(self._local_encoding)
        return self.original_environ.setdefault(key, default)


    def pop(self, key, default=None):
        return self.original_environ.pop(key, default)


    def popitem(self):
        return self.original_environ.popitem()


    def update(self, other=None, **kwargs):
        if other:
            try:
                keys = other.keys()
            except AttributeError:
                # List of (key, value)
                for k, v in other:
                    self[k] = v
            else:
                # got keys
                # cannot use items(), since mappings
                # may not have them.
                for k in keys:
                    self[k] = other[k]
        if kwargs:
            # To enforce encode
            for k, v in kwargs.items():
                self[k] = v


    def get(self, key, default=None):
        return self.original_environ.get(key, default)


    def get_as_unicode(self, key, default=None):
        '''
        :rtype: unicode
        :returns:
            Value set under the given ``key`` as unicode.

        .. seealso:: :meth:`.get`
        '''
        result = self.get(key, default)
        return result.decode(locale.getpreferredencoding())


    def __getitem__(self, key):
        return self.original_environ.__getitem__(key)


    def __setitem__(self, key, item):
        if six.PY2:
            if isinstance(key, six.text_type):
                key = key.encode(self._local_encoding)
            if isinstance(item, six.text_type):
                item = item.encode(self._local_encoding)
        return self.original_environ.__setitem__(key, item)


    def __delitem__(self, key):
        return self.original_environ.__delitem__(key)


    def __repr__(self):
        return self.original_environ.__repr__()


    def __cmp__(self, other):
        return self.original_environ.__cmp__(other)


    def __len__(self):
        return self.original_environ.__len__()


    def copy(self):
        return self.original_environ.copy()

