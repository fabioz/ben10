from __future__ import unicode_literals
from ben10.foundation.immutable import AsImmutable, ImmutableDict
from copy import copy, deepcopy
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testImmutable(self):

        class MyClass(object):
            pass

        d = AsImmutable(dict(a=1, b=dict(b=2)))
        assert d == {'a': 1, 'b': {'b': 2}}
        with pytest.raises(NotImplementedError):
            d.__setitem__('a', 2)

        assert d['b'].AsMutable() == dict(b=2)
        AsImmutable(d, return_str_if_not_expected=False)
        d = d.AsMutable()
        d['a'] = 2

        c = deepcopy(d)
        assert c == d

        c = copy(d)
        assert c == d
        assert AsImmutable(set([1, 2, 3])) == set([1, 2, 3])
        assert AsImmutable(([1, 2], [2, 3])) == ((1, 2), (2, 3))
        assert AsImmutable(None) is None
        assert isinstance(AsImmutable(set([1, 2, 4])), frozenset)
        assert isinstance(AsImmutable(frozenset([1, 2, 4])), frozenset)
        assert isinstance(AsImmutable([1, 2, 4]), tuple)
        assert isinstance(AsImmutable((1, 2, 4)), tuple)

        # Dealing with derived values
        a = MyClass()
        assert AsImmutable(a, return_str_if_not_expected=True) == unicode(a)
        with pytest.raises(RuntimeError):
            AsImmutable(a, return_str_if_not_expected=False)

        # Derived basics
        class MyStr(unicode):
            pass
        assert AsImmutable(MyStr('alpha')) == 'alpha'

        class MyList(list):
            pass
        assert AsImmutable(MyList()) == ()

        class MySet(set):
            pass
        assert AsImmutable(MySet()) == frozenset()


    def testImmutableDict(self):
        d = ImmutableDict(alpha=1, bravo=2)

        with pytest.raises(NotImplementedError):
            d['charlie'] = 3

        with pytest.raises(NotImplementedError):
            del d['alpha']

        with pytest.raises(NotImplementedError):
            d.clear()

        with pytest.raises(NotImplementedError):
            d.setdefault('charlie', 3)

        with pytest.raises(NotImplementedError):
            d.popitem()

        with pytest.raises(NotImplementedError):
            d.update({'charlie':3})

