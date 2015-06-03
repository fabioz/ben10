from __future__ import unicode_literals


pytest_plugins = [b'pytester']


def testSlowMark(testdir):
    source = '''
    import pytest

    pytest_plugins = [b'ben10.fixtures']

    def test_unmodified(request):
        assert request.node.get_marker('timeout') is None

    @pytest.mark.timeout(3)
    def test_timeout_marker(request):
        assert request.node.get_marker('timeout').args[0] == 3.0

    @pytest.mark.slow
    def test_slow(request):
        assert request.node.get_marker('timeout').args[0] == 5.0

    @pytest.mark.extra_slow
    def test_extra_slow(request):
        assert request.node.get_marker('timeout').args[0] == 20.0
'''
    testdir.makepyfile(test_slow_mark=source)
    result = testdir.runpytest('-v', '--timeout=1')
    result.stdout.fnmatch_lines([
        '*::test_unmodified PASSED*',
        '*::test_timeout_marker PASSED*',
        '*::test_slow PASSED*',
        '*::test_extra_slow PASSED*',
    ])
