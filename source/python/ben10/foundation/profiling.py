import cProfile as profile
import os
import pstats
import subprocess
import sys



#===================================================================================================
# ObtainStats
#===================================================================================================
def ObtainStats(method, *args, **kwargs):
    '''
    Runs the method in profile mode and returns the pstats.Stats method relative to that run.

    :param callable method:
        The method that should be profiled.

    @param args and kwargs: object
        Parameters to be passed to call the method.

    :rtype: pstats.Stats
    :returns:
        The stats that was generated from running the method in profile mode.
    '''
    prof = profile.Profile()
    prof.runcall(method, *args, **kwargs)
    stats = pstats.Stats(prof)
    return stats



#===================================================================================================
# ProfileMethod
#===================================================================================================
def ProfileMethod(filename, rows=50, sort=(('cumul',), ('time',)), show_graph=False):
    '''Decorator to profile the decorated function or method.

    :parm str filename:
        Where to save the profiling information. If None, profile information will be printed to the
        output.

    :param int rows:
        If the profile will be printed to the output, how many rows of data to print.

    :param tuple sort:
        If the profile will be printed to the output, how to sort the stats.

        It may be a list of strings or a list of lists of strings (in which case it will print
        the result multiple times, one for each inner list. E.g.: (('time',), ('cumul',))

    :param bool show_graph:
        Whether a graph should be generated. Note: the computer should have an .svg viewer
        associated to the extension so that the file is properly opened.

    Flags accepted in sort:
        ['tim', 'stdn', 'p', 'ca', 'module', 'pcalls', 'file', 'cumu', 'st', 'cu', 'pcall',
        'pc', 'na', 'lin', 'cumulative', 'nf', 'nam', 'stdna', 'cumul', 'call', 'time', 'cum',
        'mod', 'modul', 'fil', 'pcal', 'cumula', 'modu', 'stdnam', 'cumulati', 'fi', 'line',
        'cumulativ', 'std', 'pca', 'name', 'calls', 'f', 'mo', 'nfl', 'm', 'l', 'stdname', 's',
        'li', 't', 'cal', 'ti', 'cumulat']

        Available from:
        stats = pstats.Stats(prof)
        print stats.get_sort_arg_defs().keys()
    '''

    def wrapper(method):
        def inner(*args, **kwargs):
            prof = profile.Profile()
            result = prof.runcall(method, *args, **kwargs)

            if filename is None:
                assert not show_graph, 'Cannot show dot output if filename is not provided.'
            else:
                prof.dump_stats(filename)

                if show_graph:
                    ShowGraph(filename)

            # Show text output regardless of showing graph.
            tup_sort = sort
            s = tup_sort[0]
            if isinstance(s, str):
                tup_sort = [tup_sort]

            stats = pstats.Stats(prof)
            for s in tup_sort:
                stats.strip_dirs().sort_stats(*s).print_stats(int(rows))


            return result
        return inner
    return wrapper



#===================================================================================================
# ShowGraph
#===================================================================================================
def ShowGraph(filename):
    '''
    Creates an .svg from the profile generated file and opens it (a proper association to .svg
    files must be already defined in the machine).

    @param str filename:
        This is the file generated from ProfileMethod.
    '''
    import gprof2dot
    initial = sys.argv[:]
    output_filename = filename + '.dot'
    sys.argv = ['', '-o', output_filename, '-f', 'pstats', filename]
    try:
        gprof2dot.Main().main()
    finally:
        sys.argv = initial

    try:
        dot = os.environ['GRAPHVIZ_DOT']
    except KeyError:
        raise AssertionError('The GRAPHVIZ_DOT environment variable must be defined to show graph.')

    assert os.path.exists(dot), "Expected: %s to exist and point to dot.exe.\nDid you run 'aa eden.install graphviz'?" % dot
    subprocess.call([dot, '-Tsvg', '-O', output_filename])

    print 'Opening svg created at:', os.path.realpath((output_filename + '.svg'))
    import desktop
    desktop.open(output_filename + '.svg')



#===================================================================================================
# PrintProfile
#===================================================================================================
def PrintProfile(filename, rows=30, sort=('time', 'calls'), streams=None):
    '''
        Prints the profiling info for a given function.

        :type filename: the filename with the stats we want to load.
        :param filename:
        :type rows: the number of rows that we want to print.
        :param rows:
        :type sort: list with strings for the way we want to sort the results.
        :param sort:
    '''
    PrintProfileMultiple(filename, rows, [sort], streams)



#===================================================================================================
# PrintProfileMultiple
#===================================================================================================
def PrintProfileMultiple(filename, rows=30, sort=(('cumulative', 'time'), ('time', 'calls')),
    streams=None):
    '''
        Prints multiple profile outputs at once.

        :type filename: the filename with the stats we want to load.
        :param filename:
        :type rows: the number of rows that we want to print.
        :param rows:
        :type sort: list of tuples with the types of sorting for the outputs we want
        :param sort:
            (see defaults for example)

        the available sorting options (from Stats.sort_arg_dict_default)
        calls     cumulative     file        line        module
        name      nfl            pcalls      stdname     time

        :type streams: if specified, the output will be print to the given streams (otherwise it'll
        :param streams:
            be print to stdout).
    '''
    stats = pstats.Stats(filename)
    stats.strip_dirs()
    if streams is None:
        streams = [sys.stdout]

    initial = sys.stdout
    for s in sort:
        stats.sort_stats(*s)
        for stream in streams:
            sys.stdout = stream
            stats.stream = stream
            try:
                stats.print_stats(int(rows))
            finally:
                sys.stdout = initial
