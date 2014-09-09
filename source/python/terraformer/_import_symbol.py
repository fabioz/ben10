from ben10.foundation.decorators import Comparable



#===================================================================================================
# ImportSymbol
#===================================================================================================
@Comparable
class ImportSymbol(object):
    '''
    Represents an import symbol.

    Examples:
        import alpha
        from alpha import Alpha
        from alpha import Alpha as MyAlpha

    :cvar str symbol:
        The symbol being imported.

    :cvar KIND_IMPORT_XXX kind:
        Either import-name (import XXX) or import-from (from XXX import YYY)

    :cvar str import_as:
        Optional rename of the import (import XXX as YYY)
    '''

    KIND_IMPORT_NAME = 298
    KIND_IMPORT_FROM = 297

    def __init__(self, symbol, import_as=None, comment='', kind=KIND_IMPORT_NAME, lineno=None):
        '''
        :param str symbol:
            The import-symbol.

        :param str|None import_as:
            Optional alias for the symbol.

        :param str comment:
            A comment associated with the import
            Ex. # @UnusedImport

        :param KIND_IMPORT_XXX kind:
            The kind of import.
        '''
        assert isinstance(symbol, (str, unicode))
        assert isinstance(comment, (str, unicode))
        assert kind in (self.KIND_IMPORT_NAME, self.KIND_IMPORT_FROM)

        self.symbol = symbol
        self.import_as = import_as
        self.comment = comment
        self.kind = kind
        self.lineno = lineno


    def __repr__(self):
        return '<ImportSymbol "%s">' % self.symbol


    def GetPackageName(self):
        '''
        Returns the import-symbol prefix.

        This is only valid for import-symbols of type import-from, in which case it returns
        the "from" part of the import. Returns None if kind is import-name.

        Example:
            >s = ImportSymbol("Alpha", 'alpha')  # from alpha import Alpha
            >s.GetPackageName()
            'alpha'

        :return str:
        '''
        if self.kind == self.KIND_IMPORT_FROM:
            return self.symbol.rsplit('.', 1)[0]
        else:
            return None


    def GetToken(self):
        '''
        Returns the import token of a import-symbol of kind import-from.
        Returns the symbol if kind is import-name.

        :return str:
        '''
        if self.kind == self.KIND_IMPORT_FROM:
            assert '.' in self.symbol, "ERROR: Import-symbol 'from' has no dot in it: \"%s\"" % self.symbol
            return self.symbol.rsplit('.', 1)[1]
        else:
            return self.symbol


    def _cmpkey(self):
        '''
        Implements @Comparable._cmpkey.
        '''
        return (self.symbol, self.kind)
