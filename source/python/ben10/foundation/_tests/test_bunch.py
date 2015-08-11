from __future__ import unicode_literals
from ben10.foundation.bunch import Bunch, ConvertToDict, HashableBunch
import math
import pytest



#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testBunch(self):

        class Point(Bunch):
            x = 0.0
            y = 0.0

            def Size(self):
                return math.sqrt(self.x ** 2 + self.y ** 2)

        p1 = Point()
        assert p1.x == 0
        assert p1.y == 0
        assert p1 == Point()
        assert p1 != Point(x=1.0, y=2.0)
        assert p1 != None

        p2 = Point(x=4.0, y=3.0)
        assert p2.Size() == 5


    def testBunchAndTuples(self):

        class Alpha(Bunch):
            with_value = ('one', 'two')
            without_value = ()

        alpha = Alpha()
        assert alpha.with_value == ('one', 'two')
        assert alpha.without_value == ()


    def testBunchSubclassing(self):

        class Item(Bunch):
            caption = 'Hello'

        class Root(Item):
            data = 'Input'

        root = Root()
        assert root.caption == 'Hello'
        assert root.data == 'Input'

        root = Root(data='Data', caption='Caption')
        assert root.caption == 'Caption'
        assert root.data == 'Data'

        root = Root(caption='Caption')
        assert root.caption == 'Caption'
        assert root.data == 'Input'

        root = Root(data='Data')
        assert root.caption == 'Hello'
        assert root.data == 'Data'


    def testBunchWithMutables(self):
        '''
        0018877: Bunch doesn't performs correctly with mutable data.
        '''
        class BunchWithMutable(Bunch):
            list = []
            list_with_elements = [0, 1, 2]
            dict = {}
            dict_with_elements = {
                'a' : 1,
                'b' : 2
            }

        bunch = BunchWithMutable()
        bunch.list.append(5)
        bunch.list.append(6)
        bunch.list.append(7)

        bunch.dict['c'] = 3

        assert bunch.dict == {'c':3}
        assert bunch.dict_with_elements == {'a':1, 'b':2}
        assert bunch.list, [5, 6 == 7]
        assert bunch.list_with_elements, [0, 1 == 2]

        bunch = BunchWithMutable(list_with_elements=[0], dict_with_elements={'d':4})
        assert bunch.dict == {}
        assert bunch.dict_with_elements == {'d': 4}
        assert bunch.list == []
        assert bunch.list_with_elements == [0]

        bunch = BunchWithMutable(list=[1, 2, 3], dict={'e':5, 'f':6})
        assert bunch.dict == {'e':5, 'f':6}
        assert bunch.list == [1, 2, 3]


    def testBunchDeepCopy(self):
        '''
        Validates that different stances of a same bunch do not share data in an unexpected way.
        '''
        class DummyBunch(Bunch):
            dict_of_lists = {
                'foo' : [],
                'bar' : [],
            }

        bunch_1 = DummyBunch()
        bunch_2 = DummyBunch()

        # If bunch is deeply copied, bunch_1 will have some elements while bunch_2 must be empty.
        # This is the expected behavior.
        bunch_1.dict_of_lists['foo'].append(1)
        bunch_1.dict_of_lists['foo'].append(2)
        bunch_1.dict_of_lists['foo'].append(3)
        bunch_1.dict_of_lists['bar'].append('a')

        assert len(bunch_1.dict_of_lists['foo']) == 3
        assert len(bunch_1.dict_of_lists['bar']) == 1
        assert len(bunch_2.dict_of_lists['foo']) == 0
        assert len(bunch_2.dict_of_lists['bar']) == 0

        # If bunch is deeply copied, bunch_1 and bunch_2 will have different number of elements.
        # This is the expected behavior.
        bunch_2.dict_of_lists['foo'].append(2)
        bunch_2.dict_of_lists['foo'].append(4)
        bunch_2.dict_of_lists['bar'].append('b')
        bunch_2.dict_of_lists['bar'].append('c')
        bunch_2.dict_of_lists['bar'].append('d')

        assert len(bunch_1.dict_of_lists['foo']) == 3
        assert len(bunch_1.dict_of_lists['bar']) == 1
        assert len(bunch_2.dict_of_lists['foo']) == 2
        assert len(bunch_2.dict_of_lists['bar']) == 3


    def testBunchConvertToDict(self):
        '''
        Validates the conversion of bunches to dicts behaves as expected.
        '''

        # initialized with built-in objects ---------------------------------------------------------
        class DummyBunch1(Bunch):
            dict_of_lists = {
                'foo' : [],
                'bar' : [],
            }
            foo = 'bar'

        bunch_1 = DummyBunch1()

        assert repr(bunch_1) == "DummyBunch1(dict_of_lists={u'foo': [], u'bar': []}, foo=u'bar')"

        obtained_dict_1 = ConvertToDict(bunch_1)
        expected_dict_1 = {
            'dict_of_lists' : {
                'foo' : [],
                'bar' : [],
            },
            'foo' : 'bar',
        }
        assert obtained_dict_1 == expected_dict_1

        # initialized with types, not objects ------------------------------------------------------
        class DummyBunch2(Bunch):
            a = bool
            b = unicode
            c = int

        bunch_2 = DummyBunch2()

        obtained_dict_2 = ConvertToDict(bunch_2)
        expected_dict_2 = {
            'a' : bool,
            'b' : unicode,
            'c' : int,
        }
        assert obtained_dict_2 == expected_dict_2

        # initialized with more complex objects ----------------------------------------------------
        class DummyBunch3(Bunch):
            dummy_1 = bunch_1
            dummy_2 = bunch_2

        bunch_3 = DummyBunch3()

        obtained_dict_3 = ConvertToDict(bunch_3)
        expected_dict_3 = {
            'dummy_1' : bunch_1,
            'dummy_2' : bunch_2,
        }
        assert obtained_dict_3 == expected_dict_3


    def testHashableBunch(self):

        class MyHash(HashableBunch):
            name = 'foo'
            value = 10

        my_hash1 = MyHash(name='jonh', value=20)
        assert repr(my_hash1), "MyHash(name='jonh' == value=20)"
        assert my_hash1.name == 'jonh'
        assert my_hash1.value == 20
        with pytest.raises(AttributeError):
            setattr(my_hash1, 'name', 'foo')
        with pytest.raises(AttributeError):
            setattr(my_hash1, 'value', 30)

        my_hash1b = MyHash(name='jonh', value=20)
        assert my_hash1 == my_hash1b
        assert hash(my_hash1) == hash(my_hash1b)

        my_hash2 = MyHash(name='sarah')
        assert my_hash1 != my_hash2
        assert hash(my_hash1) != my_hash2

        d = {}
        d[my_hash1] = my_hash1
        assert d[my_hash1] is my_hash1
        assert d[my_hash1b] is my_hash1

        d[my_hash1b] = my_hash1b
        assert len(d) == 1
        assert d[my_hash1] is my_hash1b
        assert d[my_hash1b] is my_hash1b

        d[my_hash2] = my_hash2
        assert len(d) == 2
        assert d[my_hash1] is my_hash1b
        assert d[my_hash1b] is my_hash1b
        assert d[my_hash2] is my_hash2


    def testBunchClassmethod(self):

        class Point(Bunch):
            x = 0.0
            y = 0.0

            @classmethod
            def Create(cls, x, y):
                return cls(x=x, y=y)

            @staticmethod
            def Sum(x, y):
                return x + y

        assert Point.Create(1.0, 2.0) == Point(x=1.0, y=2.0)

        p = Point.Create(1.0, 2.0)
        assert unicode(p) == 'Point(x=1.0, y=2.0)'



# TODO: BEN-18: Improve coverage.
#       Not executed on tests, might as well be commented. Create a test for it.
#     def probeBunchMemory(self):
#         # Slots
#         #
#         # Ellapsed Time: 0.14 seconds
#         # Memory delta: 4,38 MB (4.595.712 bytes)
#         #
#         # NoBunch
#         #
#         # Ellapsed Time: 0.31 seconds
#         # Memory delta: 17,81 MB (18.673.664 bytes)
#         #
#         # Bunch
#         # Ellapsed Time: 0.36 seconds
#         # Memory delta: 4,43 MB (4.644.864 bytes)
#
#         class BarBunch(Bunch):
#             x = 0.0
#             y = 0.0
#             width = 1.0
#             height = 1.0
#
#         class BarNoBunch(object):
#
#             def __init__(self):
#                 self.x = 0.0
#                 self.y = 0.0
#                 self.width = 1.0
#                 self.height = 1.0
#
#         class BarSlots(object):
#
#             __slots__ = ['x', 'y', 'width', 'height']
#
#             def __init__(self):
#                 self.x = 0.0
#                 self.y = 0.0
#                 self.width = 1.0
#                 self.height = 1.0
#
#         Bar = BarNoBunch  # @UnusedVariable
#         Bar = BarSlots  # @UnusedVariable
#         Bar = BarBunch
#
#         memory_probe = MemoryProbe()
#         bunches = [Bar() for x in xrange(100000)]  # @UnusedVariable
#         memory_probe.PrintMemory()
