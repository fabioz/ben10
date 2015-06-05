from __future__ import unicode_literals
import pytest


pytest_plugins = [b'pytester']


@pytest.mark.parametrize('is_debug', [True, False])
def testSlowMark(testdir, is_debug):
    debug_factor = 3.0 if is_debug else 1.0

    source = '''
        import pytest
        import ben10.debug

        pytest_plugins = [b'ben10.fixtures']

        ben10.debug.IsPythonDebug = lambda: {is_debug}

        def test_no_mark(request):
            assert request.node.get_marker('timeout') is not None
            assert request.node.get_marker('timeout').args[0] == 1.0 * {debug_factor}

        @pytest.mark.timeout(3)
        def test_timeout_marker(request):
            assert request.node.get_marker('timeout').args[0] == 3.0 * {debug_factor}

        @pytest.mark.slow
        def test_slow(request):
            assert request.node.get_marker('timeout').args[0] == 5.0 * {debug_factor}

        @pytest.mark.slow
        @pytest.mark.timeout(3)
        def test_slow_with_explicit_timeout_1(request):
            assert request.node.get_marker('timeout').args[0] == 5 * 3.0 * {debug_factor}

        @pytest.mark.timeout(3)
        @pytest.mark.slow
        def test_slow_with_explicit_timeout_2(request):
            assert request.node.get_marker('timeout').args[0] == 5 * 3.0 * {debug_factor}
    '''

    source = source.format(is_debug=is_debug, debug_factor=debug_factor)

    testdir.makepyfile(test_slow_mark=source)
    result = testdir.runpytest('-v', '--timeout=1')
    result.stdout.fnmatch_lines([
        '*::test_no_mark PASSED*',
        '*::test_timeout_marker PASSED*',
        '*::test_slow PASSED*',
        '*::test_slow_with_explicit_timeout_1 PASSED*',
        '*::test_slow_with_explicit_timeout_2 PASSED*',
    ])


def testNoTimeoutParameter(testdir):
    source = '''
        import pytest

        pytest_plugins = [b'ben10.fixtures']

        def test_no_mark(request):
            assert request.node.get_marker('timeout') is None

        @pytest.mark.timeout(3)
        def test_timeout_marker(request):
            assert request.node.get_marker('timeout').args[0] == 3.0

        @pytest.mark.slow
        def test_slow(request):
            assert request.node.get_marker('timeout') is None
    '''

    testdir.makepyfile(test_slow_mark=source)
    result = testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        '*::test_no_mark PASSED*',
        '*::test_timeout_marker PASSED*',
        '*::test_slow PASSED*',
    ])
