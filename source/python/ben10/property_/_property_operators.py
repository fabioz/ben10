from __future__ import unicode_literals
import copy



#===================================================================================================
# Eq
#===================================================================================================
def Eq(left, right):
    '''Compares the properties created with Create() of the two objects.

    Uses the __properties__ list of each object to compare their properties.
    This method is useful to implement __eq__ operators in classes that make use
    of properties.create().
    If the __properties__ of both objects is different, return False, otherwise
    test each attribute, and return False if any of them differ. Otherwise, return
    True.
    If either operand doesn't have a __properties__ list, return False. Likewise,
    return False if any of the object doesn't have an attribute.
    '''
    try:
        lprops = left.__properties__
        rprops = right.__properties__
    except AttributeError:
        return False
    if lprops != rprops:
        return False
    for name in lprops:
        try:
            if getattr(left, name) != getattr(right, name):
                return False
        except AttributeError:
            return False
    return True



#===================================================================================================
# Copy
#===================================================================================================
def Copy(from_obj, to_obj):
    '''Copies the values of the properties of object from_obj to object to_obj.
    '''
    for prop_name in from_obj.__properties__:
        value = getattr(from_obj, prop_name)
        setattr(to_obj, prop_name, value)



#===================================================================================================
# DeepCopy
#===================================================================================================
def DeepCopy(from_obj, to_obj):
    '''Like copy_from_to, but if the value of a property from from_obj has the
    attribute __properties__, apply deepcopy_from_to on it too.
    '''
    for prop_name in from_obj.__properties__:
        from_value = getattr(from_obj, prop_name)
        if hasattr(from_value, '__properties__'):
            # if from_value has properties, deepcopy them
            to_value = getattr(to_obj, prop_name)
            DeepCopy(from_value, to_value)
        else:
            setattr(to_obj, prop_name, from_value)
