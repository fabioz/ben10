from ben10.filesystem import FindFiles, IsDir, StandardizePath
from clikit.app import App
from functools import partial
import sys



app = App('terraforming')



EXTENSIONS = {'.py', '.cpp', '.c', '.h', '.hpp', '.hxx', '.cxx', '.java', '.js'}
PYTHON_EXT = '.py'


@app
def Symbols(console_, filename):
    '''
    List all symbols in the given python source code. Currently only lists IMPORTS.

    :param filename: Python source code.
    '''
    from terraformer import TerraFormer

    terra = TerraFormer(filename=filename)
    for i_import_symbol in terra.symbols:
        console_.Print('%d: IMPORT %s' % (i_import_symbol.lineno, i_import_symbol.symbol))



@app
def FixFormat(console_, source, refactor=None, python_only=False, single_job=False, sorted=False):
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

    :param source: Source directory or file.
    :param refactor: Refactor ini file mapping source imports to target imports.
    :param python_only: Only handle python sources (.py).
    :param single_job: Avoid using multithread (for testing purposes).
    :param sorted: Sort the output.
    '''
    from functools import partial

    def GetFilenames(paths, extensions):
        result = []
        for i_path in paths:
            if IsDir(i_path):
                extensions = ['*%s' % i for i in extensions]
                result += FindFiles(i_path, extensions)
            else:
                result += [i_path]
        result = map(StandardizePath, result)
        return result

    def GetRefactorDict(refactor_filename):
        from sharedscripts10.string_dict_io import StringDictIO

        result = None
        if refactor is not None:
            result = StringDictIO.Load(refactor_filename)
        return result

    extensions = _GetExtensions(python_only)
    filenames = GetFilenames((source,), extensions)
    refactor = GetRefactorDict(refactor)
    partial_fix_format = partial(_FixFormat, refactor=refactor)
    _Map(console_, partial_fix_format, filenames, sorted, single_job)


@app
def AddImportSymbol(console_, source, import_symbol, single_job=False):

    def GetFilenames(paths, extensions):
        result = []
        for i_path in paths:
            if IsDir(i_path):
                extensions = ['*%s' % i for i in extensions]
                result += FindFiles(i_path, extensions)
            else:
                result += [i_path]
        result = map(StandardizePath, result)
        return result

    filenames = GetFilenames((source,), [PYTHON_EXT])
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

        r_working_dir = git.GetWorkingDir(cwd)
        staged_filenames = git.Execute('diff --name-only --diff-filter=ACM --staged', repo_path=r_working_dir)
        changed_filenames = git.Execute('diff --name-only --diff-filter=ACM', repo_path=r_working_dir)

        r_filenames = staged_filenames + changed_filenames
        r_filenames = set(r_filenames)
        r_filenames = sorted(r_filenames)
        r_filenames = _FilterFilenames(r_filenames)
        return r_working_dir, r_filenames

    working_dir, filenames = GetFilenames(source)
    partial_fix_commit = partial(_FixCommit, cwd=working_dir)
    _Map(console_, partial_fix_commit, filenames, sorted, single_job)



def _FixFormat(filename, refactor):
    '''
    Perform the operation in a multi-threading friendly global function.
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



def _FixCommit(filename, cwd):
    '''
    Perform the operation in a multi-threading friendly global function.
    '''
    from terraforming.refactor import TerraForming

    terra = TerraForming()
    try:
        fullname = cwd + '/' + filename
        changed = terra.FixAll(fullname)
        if filename.endswith(PYTHON_EXT):
            changed = terra.ReorganizeImports(fullname) or changed
    except Exception, e:
        result = '- %s: ERROR:\n  %s' % (filename, e)
    else:
        if changed:
            result = '- %s: FIXED' % filename
        else:
            result = '- %s: skipped' % filename
    return result


def _AddImportSymbol(filename, import_symbol):
    from terraformer import ImportSymbol, TerraFormer

    terra = TerraFormer(filename=filename)
    terra.AddImportSymbol(import_symbol)
    changed = terra.Save()

    if changed:
        result = '- %s: FIXED' % filename
    else:
        result = '- %s: skipped' % filename

    return result


def _FilterFilenames(filenames, extensions=EXTENSIONS):
    import os

    if extensions is None:
        return filenames
    else:
        return [
            i for i in filenames
            if os.path.splitext(i)[1] in extensions
        ]



#===================================================================================================
# _GetStatusColor
#===================================================================================================
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
    if python_only:
        return {PYTHON_EXT}
    else:
        return EXTENSIONS


def _Map(console_, func, func_params, _sorted, single_job):

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


if __name__ == '__main__':
    sys.exit(app.Main())
