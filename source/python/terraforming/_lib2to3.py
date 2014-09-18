# Priority Import: changes lib2to3
from terraformer import _lib2to3

# Normal Imports:
from lib2to3.fixer_base import BaseFix
from lib2to3.refactor import FixerError, RefactoringTool
import operator



#===================================================================================================
# MyRefactoringTool
#===================================================================================================
class MyRefactoringTool(RefactoringTool):
    '''
    Some small changes in code in order to work with our kind of transformations.
    '''

    def traverse_by(self, fixers, traversal):
        '''
        Override to make a copy of nodes before traversing them.
        '''
        if not fixers:
            return
        nodes = [i for i in traversal]  # <-- our change
        for node in nodes:
            for fixer in fixers[node.type]:
                results = fixer.match(node)
                if results:
                    new = fixer.transform(node, results)
                    if new is not None:
                        node.replace(new)
                        node = new

    def get_fixers(self):
        '''
        Override to handle fixers as classes.
        '''
        pre_order_fixers = []
        post_order_fixers = []
        for fix_mod_path in self.fixers:
            assert issubclass(fix_mod_path, BaseFix)
            fix_name = fix_mod_path.__name__
            fixer = fix_mod_path(self.options, self.fixer_log)
            if (
                fixer.explicit
                and self.explicit is not True
                and fix_mod_path not in self.explicit
            ):
                self.log_message("Skipping implicit fixer: %s", fix_name)
                continue

            self.log_debug("Adding transformation: %s", fix_name)
            if fixer.order == "pre":
                pre_order_fixers.append(fixer)
            elif fixer.order == "post":
                post_order_fixers.append(fixer)
            else:
                raise FixerError("Illegal fixer order: %r" % fixer.order)

        key_func = operator.attrgetter("run_order")
        pre_order_fixers.sort(key=key_func)
        post_order_fixers.sort(key=key_func)
        return (pre_order_fixers, post_order_fixers)
