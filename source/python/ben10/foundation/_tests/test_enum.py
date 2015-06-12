from __future__ import unicode_literals
from ben10.foundation.enum import Enum, IterEnumValues, MakeEnum
import pytest



#===================================================================================================
# _PickleThings
#===================================================================================================
class _PickleThings(Enum):
    cucumber = 0
    onion = 1
    herring = 3


#===================================================================================================
# _MorePickleThings
#===================================================================================================
class _MorePickleThings(_PickleThings):
    egg = 4
    snake = 5


#===================================================================================================
# _TestEnum
#===================================================================================================
class _TestEnum(Enum):
    '''
    Identical to _coilib50._TestEnum.
    '''
    Espresso = 0
    Latte = 1
    Cappuccino = 2
    Irish = 3
    Crema = 6
    Turkish = 4


#===================================================================================================
# Test
#===================================================================================================
class Test:

    def testEnumOldTest(self):
        ducks = MakeEnum(
            'ducks',
            (
                'donald',
                ('huey', 9),
                'dewey',
                'louie',
            )
        )

        assert int(ducks.donald) == 0
        assert int(ducks.huey) == 9
        assert int(ducks.dewey) == 10
        assert int(ducks.louie) == 11

        assert type(ducks(9).name) == unicode
        assert ducks(9).name == 'huey'
        assert ducks(10).name == 'dewey'
        assert ducks(11).name == 'louie'

        assert [int(i) for i in ducks] == [0, 9, 10, 11]


    def testEnum2(self):
        class Colors(Enum):
            red = 0
            green = 1
            blue = 2

        assert int(Colors.red) == 0
        assert int(Colors.green) == 1
        assert int(Colors.blue) == 2

        assert Colors.red is Colors.red
        assert Colors.green is Colors.green
        assert Colors.green is not Colors.blue

        assert Colors.green == Colors.green
        assert Colors.green != Colors.blue

        assert unicode(Colors.red) == 'Colors.red'
        assert unicode(Colors.blue) == 'Colors.blue'

        assert repr(Colors.red) == '<Colors.red [0]>'
        assert repr(Colors.green) == '<Colors.green [1]>'

        assert type(Colors.red.name) == unicode
        assert Colors.red.name == 'red'
        assert Colors.green.name == 'green'

        # Comparing it like an int (for sorting, etc...)

        assert Colors.red < Colors.green
        assert Colors.red <= Colors.red
        assert not (Colors.red > Colors.red)
        assert Colors.blue > Colors.green
        assert not (Colors.green >= Colors.blue)

        # But you can't compare it directly to an int (an enumerate values is not an int)
        with pytest.raises(TypeError):
            Colors.red < 1

        # NOTE: You can make equality comparisons with integer values, but they will
        #       *always* compare not equal

        assert not (Colors.red == 0)
        assert not (Colors.red == 1)

        assert (Colors.red != 0)
        assert (Colors.red != 1)

        # The same with strings

        assert not (Colors.red == 'red')
        assert not (Colors.red == 'green')

        assert Colors.red != 'red'
        assert Colors.red != 'green'
        assert Colors.red != 'Colors.red'

        # Typing

        assert issubclass(Colors, Enum)

        assert type(Colors.red).__name__ == 'ColorsValue'
        assert type(Colors.blue).__name__ == 'ColorsValue'

        assert isinstance(Colors.red, Colors.GetValueType())

        assert Colors.GetValueType().__name__ == 'ColorsValue'

        assert (
            list(Colors)
            == [Colors.red, Colors.green, Colors.blue]
        )

        assert (
            tuple(c for c in Colors)
            == (Colors.red, Colors.green, Colors.blue)
        )

        # Extending

        class MoreColors(Colors):
            cyan = 4
            magenta = 5
            yellow = 6

        assert MoreColors.red is Colors.red
        assert isinstance(MoreColors.cyan, MoreColors.GetValueType())
        assert isinstance(MoreColors.cyan, Colors.GetValueType()) == False

        assert (
            list(MoreColors)
            == [Colors.red, Colors.green, Colors.blue, MoreColors.cyan, MoreColors.magenta, MoreColors.yellow]
        )

        # Other enums with similar values

        class OtherColors(Enum):
            red = 0
            blue = 1
            yellow = 2

        assert Colors.red is not OtherColors.red
        assert Colors.red != OtherColors.red
        assert type(Colors.red) != type(OtherColors.red)

        # If you have only an integer (e.g., just read it from a file), you can convert it back
        # to the enum

        assert Colors(1) is Colors.green
        assert MoreColors(0) is MoreColors.red
        assert MoreColors(5) is MoreColors.magenta

        # The same with the name

        assert Colors('green') is Colors.green
        assert MoreColors('red') is MoreColors.red
        assert MoreColors('magenta') is MoreColors.magenta

        # But not with the enum value itself

        def TryGettingEnumValueItselfFromEnum():
            return Colors(Colors.green)

        with pytest.raises(ValueError):
            TryGettingEnumValueItselfFromEnum()

        # You get exceptions if you try to use invalid arguments

        with pytest.raises(ValueError):
            Colors('magenta')
        with pytest.raises(ValueError):
            MoreColors(10)

        # You can also use it as a list (getitem semantics)

        assert Colors[0] is Colors.red
        assert MoreColors[5] is MoreColors.magenta

        # Or as a dict

        assert Colors['blue'] is Colors.blue
        assert MoreColors['yellow'] is MoreColors.yellow

        # You may not define two enumeration values with the same integer value.

        def CreateBadEnum():
            class Bad(Enum):
                cartman = 1
                stan = 2
                kyle = 3
                kenny = 3  # Oops!
                butters = 4

        with pytest.raises(TypeError) as e:
            CreateBadEnum()
        assert unicode(e).endswith('Multiple enum values: 3')

        def CreateBadEnumExtension():
            class BadColors(Colors):
                cyan = 4
                yellow = 0

        with pytest.raises(TypeError) as e:
            CreateBadEnumExtension()
        assert unicode(e).endswith('Multiple enum values: 0')

        # Enumeration values are hashable, so they can be used in dictionaries and sets.

        apples = {}
        apples[Colors.red] = 'red delicious'
        apples[Colors.green] = 'granny smith'

        assert Colors.red in apples
        assert Colors.blue not in apples


    def testPicklingEnum(self):
        from pickle import dumps, loads
        assert loads(dumps(_PickleThings.cucumber))
        assert loads(dumps(list(_MorePickleThings))) == list(_MorePickleThings)


    def testEnumShouldOnlyHaveIntAsValue(self):
        def TryToCreateBadEnum():
            class BadEnum(Enum):
                Zero = 0
                One = 1
                Apple = 'APPLE'
                Banana = 'BANANA'

        with pytest.raises(TypeError) as e:
            TryToCreateBadEnum()

        assert unicode(e).endswith("Enum value is not an integer: Apple=u'APPLE'")


    def testIterEnumValuesPython(self):
        assert (
            list(IterEnumValues(_TestEnum))
            == [
                _TestEnum.Espresso,
                _TestEnum.Latte,
                _TestEnum.Cappuccino,
                _TestEnum.Irish,
                _TestEnum.Turkish,
                _TestEnum.Crema,
            ]
        )

        assert list(int(x) for x in IterEnumValues(_TestEnum)) == [0, 1, 2, 3, 4, 6]

        assert (
            list(x.name for x in IterEnumValues(_TestEnum))
            == ['Espresso', 'Latte', 'Cappuccino', 'Irish', 'Turkish', 'Crema']
        )
