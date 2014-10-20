from __future__ import unicode_literals
'''
    Definition of rich Property objects to be used instead of the builtin property.
'''
import copy
import sys

from ._properties_descriptor import PropertiesDescriptor
from ._property import Property
from ._property_naming import MakeSetGetName
from ben10.foundation.decorators import Abstract




#===================================================================================================
# _SimplePropertyCreator
#===================================================================================================
class _SimplePropertyCreator(object):
    '''
    This class is responsible for create properties and their get and set.
    '''

    @classmethod
    def MakeSetAndGet(cls, name, default=None):
        '''
        Create the get and set for the given property name.

        :param str name:
            The property name

        :type default: not used.
        :param default:
            Not used!
        '''
        def get(self):
            try:
                return getattr(self, '_' + name)
            except AttributeError:
                try:
                    value = copy.copy(default)
                except copy.Error:
                    value = default
                setattr(self, '_' + name, value)
                return value

        def set(self, value):
            setattr(self, '_' + name, value)

        return get, set



#===================================================================================================
# _AbstractPropertyCreator
#===================================================================================================
class _AbstractPropertyCreator(object):
    '''
    This class is responsible for the creation of the abstract get and set for the
    given properties.
    '''

    @classmethod
    def MakeSetAndGet(cls, name, default=None):
        '''
        Creates the abstract get and set for the given property name.

        :param str name:
            The property name

        :type default: not used.
        :param default:
            Not used!
        '''
        @Abstract
        def get(self):
            '''
            Must be implemented
            '''

        @Abstract
        def set(self, value):
            '''
            Must be implemented
            '''

        return get, set



#===================================================================================================
# _DeprecatedPropertyCreator
#===================================================================================================
class _DeprecatedPropertyCreator(object):
    '''
    This class is responsible for the creation of the get and set that'll raise
    deprecation errors for the given properties.
    '''

    @classmethod
    def MakeSetAndGet(cls, name, default=None):
        '''
        Creates the deprecated get and set for the given property name.

        :param str name:
            The property name

        :type default: not used.
        :param default:
            Not used!
        '''
        def get(self):
            raise DeprecationWarning('The property %s is deprecated' % (name,))

        def set(self, value):
            raise DeprecationWarning('The property %s is deprecated' % (name,))

        return get, set



#===================================================================================================
# _CreateSimpleProperty
#===================================================================================================
def _CreateSimpleProperty(namespace, name, property_creator, default=None):
    '''Creates a property with a simple get and set in the given namespace.

    :type create_only_abstract: if True, the default get and set implementations
    :param create_only_abstract:
    will throw NotImplementedError (because they're abstract)
    '''
    get, set = property_creator.MakeSetAndGet(name, default)

    set_name, get_name = MakeSetGetName(name)
    get.__name__ = get_name.encode('ascii')
    set.__name__ = set_name.encode('ascii')
    namespace[get_name] = get
    namespace[set_name] = set
    namespace[name] = Property(get, set)


#===================================================================================================
# Create
#===================================================================================================
def Create(**properties):
    '''Creates simple properties in the calling namespace.

    Usage:
        class C(object):
            property.Create(x=1, y=2)

    This will create two properties in the C class: x and y. Each property
    has an associated Get and Set method, named after the property. In this
    example, we would have SetX/GetX and SetY/GetY. The real instance
    attributes are named _x and _y respectively.

    A list named __properties__ is put into the class namespace with the name
    of all the properties defined in the class. The list __all_properties__
    contains the names of the properties defined in the class plus the
    ones inherited from base classes.

    Some custom parameters can be used to make the Create works according
    different needs. Following these parameters are explained:
        * __frame_to_apply_properties__: frame
            It is possible to give which frame will be used to apply the properties.

        * __custom_property_creator__: class
            It is possible to give the way the properties will be created.
            This is very handful when creating data where the properties
            follows the same pattern for get and set but it is completely
            different from the standards.

        * __create_only_abstract_properties__: bool
            With this flag the given properties will be created only
            as abstract.
            This is ignored when using the property __custom_property_creator__.

        * __add_to_namespace_properties__: bool
            If this flag is True (default), add the __properties__ namespace to the class,
            otherwise leave what's there or create an empty __properties__.

    .. note:: The instance attribute for each property is actually created
    only after the Set method is called, because the Get method is implemented
    using getattr with a default value. Doing the initialization
    of the value otherwise (modifying the class' __init__) would cause more
    problems than it is worth.
    In other words, if you try to overwrite the Get method, keep in mind that
    the default implementation is like this (example):

        def GetX(self):
            return getattr(self, '_x', 1)
    '''
    frame = properties.pop('__frame_to_apply_properties__', None)
    if frame is None:
        frame = sys._getframe().f_back

    add_to_namespace_properties = properties.pop('__add_to_namespace_properties__', True)


    try:
        property_creator = properties.pop('__custom_property_creator__', None)
        if property_creator is None:
            create_only_abstract = properties.pop('__create_only_abstract_properties__', None)
            if create_only_abstract:
                property_creator = _AbstractPropertyCreator
            else:
                property_creator = _SimplePropertyCreator

        namespace = frame.f_locals
        for name, value in properties.iteritems():
            _CreateSimpleProperty(namespace, name, property_creator, value)
        if add_to_namespace_properties:
            if '__properties__' in namespace:
                namespace['__properties__'].update(properties)
            else:
                namespace['__properties__'] = properties.copy()
        else:
            if '__properties__' not in namespace:
                namespace['__properties__'] = {}
        namespace['__all_properties__'] = PropertiesDescriptor()
    finally:
        del frame


#===================================================================================================
# _ForwardPropertyCreator
#===================================================================================================
class _ForwardPropertyCreator(object):
    '''
    PropertyCreator for CreateForwardProperties.
    '''

    @classmethod
    def MakeSetAndGet(cls, name, default=None):
        '''
        Creates the forward get/set functions.

        :param str name:
            The property name

        :param str default:
            The forward expression
        '''
        def GetObjectAndAttr(self):
            fields = default.split('.')
            obj = self
            while len(fields) > 1:
                obj = getattr(obj, fields.pop(0))
            return obj, fields[0]

        def Get(self):
            obj, attr = GetObjectAndAttr(self)
            return getattr(obj, attr)

        def Set(self, value):
            obj, attr = GetObjectAndAttr(self)
            return setattr(obj, attr, value)

        return Get, Set



#===================================================================================================
# CreateForwardProperties
#===================================================================================================
def CreateForwardProperties(**properties):
    '''
    Creates properties that only forward the get/set calls to some inner object:

    CreateForwardProperties(
        x = '_inner.x',
    )

    Where "_inner" is an internal object with an "x" property. Note that multiple inner objects
    are possible, like "_inner.x".
    '''
    frame = sys._getframe().f_back
    try:
        properties['__custom_property_creator__'] = _ForwardPropertyCreator
        properties['__frame_to_apply_properties__'] = frame
        Create(**properties)
    finally:
        del frame

#===================================================================================================
# CreateDeprecatedProperties
#===================================================================================================
def CreateDeprecatedProperties(**properties):
    '''
    Creates properties that will raise deprecation errors when accessed:

    CreateDeprecatedProperties(
        x = 'Deprecated',
    )
    '''
    frame = sys._getframe().f_back
    try:
        properties['__custom_property_creator__'] = _DeprecatedPropertyCreator
        properties['__frame_to_apply_properties__'] = frame
        # We do not want to consider the deprecated properties in the __properties__.
        properties['__add_to_namespace_properties__'] = False
        Create(**properties)
    finally:
        del frame
