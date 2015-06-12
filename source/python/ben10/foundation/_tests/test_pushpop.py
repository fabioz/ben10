from __future__ import unicode_literals
from ben10.foundation.pushpop import PushPopAttr, PushPopItem



#===================================================================================================
# Test
#===================================================================================================
class Test():

    def testPushPopAttr(self):

        class MyObject:

            class_value = 1

            def __init__(self, value):
                self.value = value

        obj = MyObject(1)

        assert obj.value == 1
        with PushPopAttr(obj, 'value', 2) as value:
            assert obj.value == 2
            assert value == 2
        assert obj.value == 1

        assert MyObject.class_value == 1
        assert obj.class_value == 1
        with PushPopAttr(MyObject, 'class_value', 2) as value:
            assert MyObject.class_value == 2
            assert obj.class_value == 2
            assert value == 2
        assert MyObject.class_value == 1
        assert obj.class_value == 1


    def testPushPopItem(self):
        obj = {'key' : 1}

        assert obj['key'] == 1
        with PushPopItem(obj, 'key', 2):
            assert obj['key'] == 2
        assert obj['key'] == 1

        assert 'other_key' not in obj
        with PushPopItem(obj, 'other_key', 1):
            assert obj['other_key'] == 1
        assert 'other_key' not in obj
