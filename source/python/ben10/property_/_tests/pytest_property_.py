from __future__ import unicode_literals
from ben10 import property_
import pytest



class PropertyTestFixture(object):

    def __init__(self):
        class C(object):
            property_.Create(x=10, y=None)

            def __eq__(self, other):
                return property_.Eq(self, other)

        self.C = C
        self.c = C()
        self.a = C()
        self.b = C()

        class A(object):
            property_.Create(a=0)


        class B(A):
            property_.Create(b=1)

        a = A()
        b = B()

        assert a.a == 0
        assert b.a == 0
        assert b.b == 1

        assert {'a':0} == a.__properties__
        assert {'a':0} == a.__all_properties__
        assert {'b':1} == b.__properties__
        assert {'b':1, 'a':0} == b.__all_properties__

        def error():
            a.__all_properties__ = 1

        with pytest.raises(AttributeError):
            error()


@pytest.fixture
def property_test_fixture():
    return PropertyTestFixture()


def testCreate(property_test_fixture):
    c = property_test_fixture.c

    def testX(val):
        assert c.x == val
        assert c._x == val
        assert c.GetX() == val

    assert c.x == 10
    assert c.GetX() == 10

    c.SetX(12)
    testX(12)

    c.x = 1

    testX(1)

    def testY(val):
        assert c.y == val
        assert c._y == val
        assert c.GetY() == val

    assert c.y == None
    c.y = [1]
    testY([1])

    c.SetY([2])
    testY([2])

    c.y.append(1)
    testY([2, 1])


def testMutable(property_test_fixture):
    'coilib40.basic:'

    class C(object):
        property_.Create(list=[])

    c = C()
    d = C()
    assert c.list == d.list
    c.list.append(1)
    assert c.list == [1]
    assert d.list != c.list
    d.list.append(1)
    assert c.list == d.list
    d.list[:] = []
    assert d.list != c.list


def testEquality(property_test_fixture):
    'coilib40.basic:'
    a = property_test_fixture.a
    b = property_test_fixture.b
    assert a == b
    b.x = 0
    assert a != b
    # make sure property.eq only tests for what it claims
    class T: pass
    t = T()
    assert a != t
    t.x = a.x
    t.y = a.y
    assert a != t
    T.__properties__ = a.__properties__.copy()
    assert a == t


def testCopy(property_test_fixture):
    'coilib40.basic:'
    property_test_fixture.a.x = 0
    property_test_fixture.a.y = 0
    # add a attribute to a that its not a property, to make sure it
    # isnt touched
    property_test_fixture.a.z = 1
    property_test_fixture.b.x = 10
    property_test_fixture.b.y = 20
    property_.Copy(property_test_fixture.a, property_test_fixture.b)
    assert property_test_fixture.a.x == property_test_fixture.b.x
    assert property_test_fixture.a.y == property_test_fixture.b.y
    assert property_test_fixture.a.z == 1


def testDeepCopy(property_test_fixture):
    'coilib40.basic:'
    b = property_test_fixture.C()
    b.x = 1
    b.y = 2
    property_test_fixture.a.x = b # hold another object that has properties
    property_test_fixture.a.y = 1
    c = property_test_fixture.C()

    c.x = inner_c = property_test_fixture.C()
    c.y = 0
    property_.DeepCopy(property_test_fixture.a, c)
    assert c.x.x == b.x
    assert c.x.y == b.y
    assert c.x is inner_c


def test_del(property_test_fixture):
    'coilib40.basic:'
    c = property_test_fixture.C()
    assert hasattr(c, 'x')

    with pytest.raises(AttributeError):
        del c.x


def testDefaultInheritance():
    'coilib40.basic:'
    class A(object):
        property_.Create(
            name='foo',
        )

    class B(A):
        property_.Create(
            name='bar',
        )

    b = B()
    assert b.__all_properties__ == dict(name='bar')


def testCreateForwardProperty():

    class Inner(object):
        def __init__(self):
            self.x = 0

    class Main(object):

        def __init__(self):
            self._inner = Inner()

        property_.CreateForwardProperties(
            yy='_inner.x',
        )


    main = Main()
    assert main.yy == 0
    main.yy = 5
    assert main.yy == 5
    assert main._inner.x == 5


def test_ToCamelCase():
    assert (
        property_.ToCamelCase('alpha_bravo_charlie')
        == 'AlphaBravoCharlie'
    )
    assert (
        property_.ToCamelCase('alpha_bravo_charlie2')
        == 'AlphaBravoCharlie2'
    )

def test_FromCamelCase():
    assert (
        property_.FromCamelCase('AlphaBravoCharlie')
        == 'alpha_bravo_charlie'
    )
    assert (
        property_.FromCamelCase('AlphaBravoCharlie2')
        == 'alpha_bravo_charlie_2'
    )


def test_MakeGetName():
    assert (
        property_.MakeGetName('alpha')
        == 'GetAlpha'
    )
    assert (
        property_.MakeGetName('alpha_too')
        == 'GetAlphaToo'
    )


def test_MakeSetName():
    assert (
        property_.MakeSetName('alpha')
        == 'SetAlpha'
    )
    assert (
        property_.MakeSetName('alpha_too')
        == 'SetAlphaToo'
    )


def testProperty():
    from ben10.property_ import Property

    class Alpha(object):

        def __init__(self):
            self._value = 999

        def GetValue(self):
            return self._value

        def SetValue(self, value):
            self._value = value

        def DelValue(self):
            pass

        value1 = Property(GetValue, SetValue, DelValue, 'The Value')
        value2 = Property.FromNames('GetValue', 'SetValue', 'DelValue', 'The Value')

    assert repr(Alpha.value1) == 'Property(fget=GetValue, fset=SetValue, fdel=DelValue, doc=u\'The Value\')'
    assert repr(Alpha.value2) == 'Property(fget=GetValue, fset=SetValue, fdel=DelValue, doc=u\'The Value\')'


def testPropertiesStr():
    from ben10.property_ import PropertiesStr

    class Alpha(object):

        def __init__(self):
            self._value = 999

        def GetValue(self):
            return self._value

        def SetValue(self, value):
            self._value = value

        def DelValue(self):
            pass

        value1 = Property(GetValue, SetValue, DelValue, 'The Value')
        value2 = Property.FromNames('GetValue', 'SetValue', 'DelValue', 'The Value')

    assert repr(Alpha.value1) == 'Property(fget=GetValue, fset=SetValue, fdel=DelValue, doc=u\'The Value\')'
    assert repr(Alpha.value2) == 'Property(fget=GetValue, fset=SetValue, fdel=DelValue, doc=u\'The Value\')'
