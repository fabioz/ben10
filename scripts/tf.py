from ben10.filesystem import FindFiles, IsDir, StandardizePath
from clikit.app import App
from functools import partial
import sys


app = App('terraforming')


# Valid extensions for fix-format.
EXTENSIONS = {'.py', '.cpp', '.c', '.h', '.hpp', '.hxx', '.cxx', '.java', '.js'}

# Python extensions.
# This is overridden for test purposes.
PYTHON_EXT = '.py'


@app
def Symbols(console_, filename):
    '''
    List all symbols in the given python source code. Currently only lists IMPORTS.

    :param filename: Python source code.
    '''
    from terraformer import TerraFormer

    terra = TerraFormer.Factory(filename)
    for i_import_symbol in terra.symbols:
        console_.Print('%d: IMPORT %s' % (i_import_symbol.lineno, i_import_symbol.symbol))



@app
def FixFormat(console_, refactor=None, python_only=False, single_job=False, sorted=False, inverted_refactor=False, *sources):
    '''
    Perform the format fixes on sources files, including tabs, eol, eol-spaces and imports.

    Fix-format details:
        - tabs: Fix for tabs in the code. We always use spaces.
        - eol: Fix for EOL style. We use UNIX-EOL
        - eol-spaces: Fix for spaces in the end of the lines. We don't want them.
        - imports: Sort imports statements

    Local Imports Fix:
        Replaces global imports by local imports when the symbol is available locally.
        Ex.
            alpha/bravo/__init__.py:
                from zulu import ZuluClass

            alpha/bravo/module.py:
                from alpha.bravo import ZuluClass ==> from zulu import ZuluClass

        REQUIREMENT: The package must be available on python path.

    :param refactor: Refactor ini file mapping source imports to target imports.
    :param python_only: Only handle python sources (.py).
    :param single_job: Avoid using multithread (for testing purposes).
    :param sorted: Sort the output.
    :param inverted_refactor: Invert refactor names and values loaded from refactor file.
    :param sources: Source directories or files.
    '''
    from functools import partial

    def GetRefactorDict(refactor_filename, inverted):
        from ben10.foundation.types_ import StringDictIO

        result = None
        if refactor is not None:
            result = StringDictIO.Load(refactor_filename, inverted=inverted)
        return result

    extensions = _GetExtensions(python_only)
    filenames = _GetFilenames(sources, extensions)
    refactor = GetRefactorDict(refactor, inverted_refactor)
    partial_fix_format = partial(_FixFormat, refactor=refactor)
    _Map(console_, partial_fix_format, filenames, sorted, single_job)


@app
def AddImportSymbol(console_, source, import_symbol, single_job=False):
    '''
    Adds an import-symbol in all files.
    The import statement is added in the first line of the code, before comments and string docs.

    :param source: Source directory or file.
    :param import_symbol: The symbol to import. Ex. "__future__.unicode_literals"
    :param single_job: Avoid using multithread (for testing purposes).
    '''
    filenames = _GetFilenames((source,), [PYTHON_EXT])
    partial_add_import_symbol = partial(_AddImportSymbol, import_symbol=import_symbol)
    _Map(console_, partial_add_import_symbol, filenames, sorted, single_job)


@app
def FixCommit(console_, source, single_job=False):
    '''
    Perform the format fixes on sources files on a git repository modified files.

    :param source: A local git repository working directory.
    :param single_job: Avoid using multithread (for testing purposes).
    '''

    def GetFilenames(cwd):
        from gitit.git import Git

        git = Git.GetSingleton()

        working_dir = git.GetWorkingDir(cwd)
        staged_filenames = git.Execute('diff --name-only --diff-filter=ACM --staged', repo_path=working_dir)
        changed_filenames = git.Execute('diff --name-only --diff-filter=ACM', repo_path=working_dir)

        r_filenames = staged_filenames + changed_filenames
        r_filenames = set(r_filenames)
        r_filenames = sorted(r_filenames)
        r_filenames = _FilterFilenames(r_filenames)
        r_filenames = [working_dir + '/' + i for i in r_filenames]
        return r_filenames

    filenames = GetFilenames(source)
    partial_fix_format = partial(_FixFormat, refactor={})
    _Map(console_, partial_fix_format, filenames, sorted, single_job)


@app
def FixIsFrozen(console_, path):
    from ben10.filesystem import CreateFile, EOL_STYLE_UNIX, FindFiles, GetFileContents

    FIND_REPLACE = [
        ('coilib50.IsFrozen', 'IsFrozen', 'from ben10.foundation.is_frozen import IsFrozen'),
        ('coilib50.IsDevelopment', 'IsDevelopment', 'from ben10.foundation.is_frozen import IsDevelopment'),
        ('coilib50.SetIsFrozen', 'SetIsFrozen', 'from ben10.foundation.is_frozen import SetIsFrozen'),
        ('coilib50.SetIsDevelopment', 'SetIsDevelopment', 'from ben10.foundation.is_frozen import SetIsDevelopment'),

        ('coilib40.basic.IsInstance', 'IsInstance', 'from ben10.foundation.klass import IsInstance'),
    ]

    PROPERTY_MODULE_SYMBOLS = [
        'PropertiesDescriptor',
        'Property',
        'Create',
        'CreateDeprecatedProperties',
        'CreateForwardProperties',
        'FromCamelCase',
        'MakeGetName',
        'MakeSetGetName',
        'MakeSetName',
        'ToCamelCase',
        'Copy',
        'DeepCopy',
        'Eq',
        'PropertiesStr',
    ]
    for i_symbol in PROPERTY_MODULE_SYMBOLS:
        FIND_REPLACE.append(
            ('property.%s' % i_symbol, 'property_.%s' % i_symbol, 'from ben10 import property_'),
        )

    for i_filename in FindFiles(path, ['*.py']):
        contents = GetFileContents(i_filename)
        imports = set()
        for i_find, i_replace, i_import in FIND_REPLACE:
            if i_find in contents:
                contents = contents.replace(i_find, i_replace)
                imports.add(i_import)

        if imports:
            console_.Item(i_filename)
            lines = contents.split('\n')
            index = None
            top_doc = False
            for i, i_line in enumerate(lines):
                if i == 0:
                    for i_top_doc in ("'''", '"""'):
                        if i_top_doc in i_line:
                            console_.Print('TOPDOC START: %d' % i, indent=1)
                            top_doc = i_top_doc
                            break
                    continue
                elif top_doc:
                    if i_top_doc in i_line:
                        console_.Print('TOPDOC END: %d' % i, indent=1)
                        index = i + 1
                        break
                    continue

                elif i_line.startswith('import ') or i_line.startswith('from '):
                    index = i - 1
                    break

                elif i_line.strip() == '':
                    continue

                console_.Print('ELSE: %d: %s' % (i, i_line))
                index = i
                break

            assert index is not None
            lines = lines[0:index] + list(imports) + lines[index:]
            contents = '\n'.join(lines)
            CreateFile(i_filename, contents, eol_style=EOL_STYLE_UNIX)


def _GetFilenames(paths, extensions):
    '''
    Lists filenames matching the given paths and extensions.

    :param paths:
        List of paths or filenames to match.
    :param extensions:
        List of extensions to match. Ex.: .py, .cpp.
    :return list:
        Returns a list of matching paths.
    '''
    result = []
    for i_path in paths:
        if IsDir(i_path):
            extensions = ['*%s' % i for i in extensions]
            result += FindFiles(i_path, extensions)
        else:
            result += [i_path]
    result = map(StandardizePath, result)
    return result


def _FixFormat(filename, refactor):
    '''
    Perform the operation in a multi-threading friendly global function.

    The operation is to perform format fixes in the given python source code.
    '''
    from terraforming.refactor import TerraForming

    terra = TerraForming()
    try:
        changed = terra.FixAll(filename)
        if filename.endswith(PYTHON_EXT):
            changed = terra.ReorganizeImports(filename, refactor=refactor) or changed
    except Exception, e:
        result = '- %s: ERROR:\n  %s' % (filename, e)
    else:
        if changed:
            result = '- %s: FIXED' % filename
        else:
            result = '- %s: skipped' % filename
    return result


def _AddImportSymbol(filename, import_symbol):
    '''
    Perform the operation in a multi-threading friendly global function.

    The operation is add a import-symbol to a filename.
    '''
    from terraformer import TerraFormer

    terra = TerraFormer.Factory(filename)
    terra.AddImportSymbol(import_symbol)
    changed = terra.Save()

    if changed:
        result = '- %s: FIXED' % filename
    else:
        result = '- %s: skipped' % filename

    return result


def _FilterFilenames(filenames, extensions=EXTENSIONS):
    '''
    Filters the given filenames that don't match the given extensions.

    :param list(str) filenames:
        List of filenames.

    :param list(str) extensions:
        List of extensions.

    :return:
        List of filename.
    '''
    import os

    if extensions is None:
        return filenames
    else:
        return [
            i for i in filenames
            if os.path.splitext(i)[1] in extensions
        ]


def _GetStatusColor(output):
    """
    Returns the color to be used in the console for the given output from a TerraForming command.

    Used to easily highlight which files were terra-formed and those that were skipped.

    :param str output:
        Output from the terra-forming command.

    :return: color string name.
    """
    if 'skipped' in output:
        return 'YELLOW'
    elif 'FIXED' in output:
        return 'GREEN'
    elif 'ERROR' in output:
        return 'RED'
    else:
        return 'WHITE'


def _GetExtensions(python_only):
    '''
    Returns a list of extensions based on command line options.

    :param bool python_only:
        Command line option to consider only python files.

    :return list(str):
        List of extensions selected by the user.
    '''
    if python_only:
        return {PYTHON_EXT}
    else:
        return EXTENSIONS


def _Map(console_, func, func_params, _sorted, single_job):
    '''
    Executes func in parallel considering some options.

    :param callable func:
        The function to call.

    :param list func_params:
        List of parameters to execute the function with.

    :param _sorted:
        Sorts the output.

    :param single_job:
        Do not use multiprocessing algorithm.
        This is used for debug purposes.
    :return:
    '''

    if single_job:
        import itertools
        imap = itertools.imap
    else:
        import concurrent.futures
        executor = concurrent.futures.ProcessPoolExecutor()
        imap = executor.map

    output = []
    for i_result in imap(func, func_params):
        if _sorted:
            output.append(i_result)
        else:
            console_.Print(i_result)  #, color=_GetStatusColor(i_result))

    for i_output_line in sorted(output):
        console_.Print(i_output_line)  #, color=_GetStatusColor(i_output_line))



#===================================================================================================
# Entry Point
#===================================================================================================
if __name__ == '__main__':
    sys.exit(app.Main())
