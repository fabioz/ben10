#===================================================================================================
# Placeholder for the "tr" function
# The "tr" function is implemented by xgui20.translate
# BEN10 should not depend on Qt, but regarding translation, it depends indirectly because of the use
# of Qt translation mechanism.
#
# The "tr" function must be defined and used solely as a builtin symbol and *never* as a direct
# import. Failing to do so will break the transation mechanism.
#===================================================================================================
def _tr(text, context=None):
    return text

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

if not hasattr(builtins, 'tr'):
    builtins.tr = _tr
