import os
import sys
from scripttest import TestFileEnvironment

here = os.path.dirname(__file__)
script = os.path.join(here, 'a_script.py')

def test_testscript():
    env = TestFileEnvironment()
    res = env.run(sys.executable, script, 'test-file.txt')
    assert res.stdout == 'Writing test-file.txt\n'
    assert not res.stderr
    assert 'test-file.txt' in res.files_created
    assert not res.files_deleted
    assert not res.files_updated
    assert len(res.files_created) == 1
    f = res.files_created['test-file.txt']
    assert f.path == 'test-file.txt'
    assert f.full.endswith('/test-output/test-file.txt')
    assert f.stat.st_size == f.size
    assert f.stat.st_mtime == f.mtime
    assert f.bytes == 'test'
    assert 'es' in f
    assert 'foo' not in f
    f.mustcontain('test')
    try:
        f.mustcontain('foobar')
    except AssertionError:
        pass
    else:
        assert 0
    res = env.run(sys.executable, script, 'test-file.txt')
    assert not res.files_created
    assert not res.files_updated
    res = env.run(sys.executable, script, 'error', expect_stderr=True)
    assert res.stderr == 'stderr output\n'
    try:
        env.run(sys.executable, script, 'error')
    except AssertionError:
        pass
    else:
        assert 0
    res = env.run(sys.executable, script, 'exit', '10', expect_error=True)
    assert res.returncode == 10
    try:
        env.run(sys.executable, script, 'exit', '10')
    except AssertionError:
        pass
    else:
        assert 0

def test_bad_symlink():
    env = TestFileEnvironment()
    res = env.run(sys.executable, '-c', '''\
import os
os.symlink("/does/not/exist.txt", "does-not-exist.txt")
''')
    assert 'does-not-exist.txt' in res.files_created
    assert res.files_created['does-not-exist.txt'].invalid
    # Just make sure there's no error:
    str(res)
