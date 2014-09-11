from __future__ import unicode_literals
from ben10.foundation.memoize import Memoize

def ToCamelCase(prop_name):
    '''
        Returns the name of the given property in CamelCase.
        Example: "data_set" becomes "DataSet".
    '''
    return prop_name.title().replace('_', '')


def FromCamelCase(prop_name):
    '''
        Returns the name of the given property in lower_case.
        Example: "DataSet" becomes "data_set".
    '''
    result = ''
    for i in prop_name:
        if result and (i.isupper() or i.isdigit()):
            result += '_'
        result += i.lower()
    return result


def MakeGetName(prop_name):
    '''
        Return the name of the get method of a property with the given name.
        Example: "data_set" becomes "GetDataSet".
    '''
    return 'Get' + ToCamelCase(prop_name)


def MakeSetName(prop_name):
    '''
        Return the name of the set method of a property with the given name.
        .. see:: L{MakeGetName}.
    '''
    return 'Set' + ToCamelCase(prop_name)

@Memoize(200) #Add a cache here as this is called a lot on the property mechanisms
def MakeSetGetName(prop_name):
    '''
        Return the name of the set method of a property with the given name.
        .. see:: L{MakeGetName}.
    '''
    result = ToCamelCase(prop_name)
    return ('Set' + result, 'Get' + result)
