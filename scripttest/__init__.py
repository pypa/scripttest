# (c) 2005-2007 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Helpers for testing command-line scripts
"""
import sys
import os
import shutil
import shlex
import subprocess
import re
from scripttest.backwardscompat import string

if sys.platform == 'win32':
    def clean_environ(e):
        ret = dict(
            ((str(k),str(v)) for k,v in e.items()) )
        return ret
else:
    def clean_environ(e): 
        return e

# From pathutils by Michael Foord: http://www.voidspace.org.uk/python/pathutils.html
def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``

    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

__all__ = ['TestFileEnvironment']

if sys.platform == 'win32':
    def full_executable_path(invoked, environ):

        if os.path.splitext(invoked)[1]:
            return invoked
        
        explicit_dir = os.path.dirname(invoked)

        if explicit_dir:
            path = [ explicit_dir ]
        else:
            path = environ.get('PATH').split(os.path.pathsep)

        extensions = environ.get(
            'PATHEXT',
            # Use *something* in case the environment variable is
            # empty.  These come from my machine's defaults
            '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.PSC1'
            ).split(os.path.pathsep)

        for dir in path:
            for ext in extensions:
                full_path = os.path.join(dir, invoked+ext)
                if os.path.exists( full_path ):
                    return full_path

        return invoked # Not found; invoking it will likely fail

    class Popen(subprocess.Popen):
        def __init__(
            self, args, bufsize=0, executable=None,
            stdin=None, stdout=None, stderr=None,
            preexec_fn=None, close_fds=False, shell=False, 
            cwd=None, env=None, 
            *args_, **kw):

            if executable is None and not shell:
                executable = full_executable_path(args[0], env or os.environ)

            super(Popen,self).__init__(
                args, bufsize, executable, stdin, stdout, stderr, 
                preexec_fn, close_fds, shell, cwd, env, *args_, **kw)
        
else:
    from subprocess import Popen


class TestFileEnvironment(object):

    """
    This represents an environment in which files will be written, and
    scripts will be run.
    """

    # for py.test
    disabled = True

    def __init__(self, base_path=None, template_path=None,
                 environ=None, cwd=None, start_clear=True,
                 ignore_paths=None, ignore_hidden=True,
                 capture_temp=False, assert_no_temp=False, split_cmd=True):
        """
        Creates an environment.  ``base_path`` is used as the current
        working directory, and generally where changes are looked for.
        If not given, it will be the directory of the calling script plus
        ``test-output/``.

        ``template_path`` is the directory to look for *template*
        files, which are files you'll explicitly add to the
        environment.  This is done with ``.writefile()``.

        ``environ`` is the operating system environment,
        ``os.environ`` if not given.

        ``cwd`` is the working directory, ``base_path`` by default.

        If ``start_clear`` is true (default) then the ``base_path``
        will be cleared (all files deleted) when an instance is
        created.  You can also use ``.clear()`` to clear the files.

        ``ignore_paths`` is a set of specific filenames that should be
        ignored when created in the environment.  ``ignore_hidden``
        means, if true (default) that filenames and directories
        starting with ``'.'`` will be ignored.

        ``capture_temp`` will put temporary files inside the
        environment (using ``$TMPDIR``).  You can then assert that no
        temporary files are left using ``.assert_no_temp()``.
        """
        if base_path is None:
            base_path = self._guess_base_path(1)
        self.base_path = base_path
        self.template_path = template_path
        if environ is None:
            environ = os.environ.copy()
        self.environ = environ
        if cwd is None:
            cwd = base_path
        self.cwd = cwd
        self.capture_temp = capture_temp
        if self.capture_temp:
            self.temp_path = os.path.join(self.base_path, 'tmp')
            self.environ['TMPDIR'] = self.temp_path
        else:
            self.temp_path = None
        if start_clear:
            self.clear()
        elif not os.path.exists(base_path):
            os.makedirs(base_path)
        self.ignore_paths = ignore_paths or []
        self.ignore_hidden = ignore_hidden
        self.split_cmd = split_cmd

        if assert_no_temp and not self.capture_temp:
            raise TypeError(
                'You cannot use assert_no_temp unless capture_temp=True')
        self._assert_no_temp = assert_no_temp

        self.split_cmd = split_cmd

    def _guess_base_path(self, stack_level):
        frame = sys._getframe(stack_level+1)
        file = frame.f_globals.get('__file__')
        if not file:
            raise TypeError(
                "Could not guess a base_path argument from the calling scope "
                "(no __file__ found)")
        dir = os.path.dirname(file)
        return os.path.join(dir, 'test-output')

    def run(self, script, *args, **kw):
        """
        Run the command, with the given arguments.  The ``script``
        argument can have space-separated arguments, or you can use
        the positional arguments.

        Keywords allowed are:

        ``expect_error``: (default False)
            Don't raise an exception in case of errors
        ``expect_stderr``: (default ``expect_error``)
            Don't raise an exception if anything is printed to stderr
        ``stdin``: (default ``""``)
            Input to the script
        ``cwd``: (default ``self.cwd``)
            The working directory to run in (default ``base_path``)
        ``quiet``: (default False)
            When there's an error (return code != 0), do not print stdout/stderr

        Returns a `ProcResult
        <class-paste.fixture.ProcResult.html>`_ object.
        """
        __tracebackhide__ = True
        expect_error = _popget(kw, 'expect_error', False)
        expect_stderr = _popget(kw, 'expect_stderr', expect_error)
        cwd = _popget(kw, 'cwd', self.cwd)
        stdin = _popget(kw, 'stdin', None)
        quiet = _popget(kw, 'quiet', False)
        debug = _popget(kw, 'debug', False)
        if not self.temp_path:
            if 'expect_temp' in kw:
                raise TypeError(
                    'You cannot use expect_temp unless you use capture_temp=True')
        expect_temp = _popget(kw, 'expect_temp', not self._assert_no_temp)
        args = list(map(str, args))
        assert not kw, (
            "Arguments not expected: %s" % ', '.join(kw.keys()))
        if self.split_cmd and ' ' in script:
            if args:
                # Then treat this as a script that has a space in it
                pass
            else:
                script, args = script.split(None, 1)
                args = shlex.split(args)
        
        environ=clean_environ(self.environ)
        all = [script] + args

        files_before = self._find_files()

        if debug:
            proc = subprocess.Popen(all,
                                    cwd=cwd,
                                    shell=(sys.platform=='win32'), # see http://bugs.python.org/issue8557
                                    env=clean_environ(self.environ))
        else:
            proc = subprocess.Popen(all, stdin=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    stdout=subprocess.PIPE,
                                    cwd=cwd,
                                    shell=(sys.platform=='win32'), # see http://bugs.python.org/issue8557
                                    env=clean_environ(self.environ))

        if debug:
            stdout,stderr = proc.communicate()
        else:
            stdout, stderr = proc.communicate(stdin)
        stdout = string(stdout)
        stderr = string(stderr)

        stdout = string(stdout).replace('\r\n', '\n')
        stderr = string(stderr).replace('\r\n', '\n')
        files_after = self._find_files()
        result = ProcResult(
            self, all, stdin, stdout, stderr,
            returncode=proc.returncode,
            files_before=files_before,
            files_after=files_after)
        if not expect_error:
            result.assert_no_error(quiet)
        if not expect_stderr:
            result.assert_no_stderr(quiet)
        if not expect_temp:
            result.assert_no_temp(quiet)
        return result

    def _find_files(self):
        result = {}
        for fn in os.listdir(self.base_path):
            if self._ignore_file(fn):
                continue
            self._find_traverse(fn, result)
        return result

    def _ignore_file(self, fn):
        if fn in self.ignore_paths:
            return True
        if self.ignore_hidden and os.path.basename(fn).startswith('.'):
            return True
        return False

    def _find_traverse(self, path, result):
        full = os.path.join(self.base_path, path)
        if os.path.isdir(full):
            if not self.temp_path or path != 'tmp':
                result[path] = FoundDir(self.base_path, path)
            for fn in os.listdir(full):
                fn = os.path.join(path, fn)
                if self._ignore_file(fn):
                    continue
                self._find_traverse(fn, result)
        else:
            result[path] = FoundFile(self.base_path, path)

    def clear(self, force=False):
        """
        Delete all the files in the base directory.
        """
        marker_file = os.path.join(self.base_path, '.scripttest-test-dir.txt')
        if os.path.exists(self.base_path):
            if not force and not os.path.exists(marker_file):
                sys.stderr.write('The directory %s does not appear to have been created by ScriptTest\n' % self.base_path)
                sys.stderr.write('The directory %s must be a scratch directory; it will be wiped after every test run\n' % self.base_path)
                sys.stderr.write('Please delete this directory manually\n')
                raise AssertionError(
                    "The directory %s was not created by ScriptTest; it must be deleted manually" % self.base_path)
            shutil.rmtree(self.base_path, onerror=onerror)
        os.mkdir(self.base_path)
        f = open(marker_file, 'w')
        f.write('placeholder')
        f.close()
        if self.temp_path and not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)

    def writefile(self, path, content=None,
                  frompath=None):
        """
        Write a file to the given path.  If ``content`` is given then
        that text is written, otherwise the file in ``frompath`` is
        used.  ``frompath`` is relative to ``self.template_path``
        """
        full = os.path.join(self.base_path, path)
        if not os.path.exists(os.path.dirname(full)):
            os.makedirs(os.path.dirname(full))
        f = open(full, 'wb')
        if content is not None:
            f.write(content)
        if frompath is not None:
            if self.template_path:
                frompath = os.path.join(self.template_path, frompath)
            f2 = open(frompath, 'rb')
            f.write(f2.read())
            f2.close()
        f.close()
        return FoundFile(self.base_path, path)

    def assert_no_temp(self):
        """If you use ``capture_temp`` then you can use this to make
        sure no files have been left in the temporary directory"""
        __tracebackhide__ = True
        if not self.temp_path:
            raise Exception('You cannot use assert_no_error unless you '
                            'instantiate TestFileEnvironment(capture_temp=True)')
        names = os.listdir(self.temp_path)
        if not names:
            return
        new_names = []
        for name in names:
            if os.path.isdir(os.path.join(self.temp_path, name)):
                name += '/'
            new_names.append(name)
        raise AssertionError(
            'Temporary files left over: %s'
            % ', '.join(sorted(names)))

class ProcResult(object):

    """
    Represents the results of running a command in
    `TestFileEnvironment
    <class-paste.fixture.TestFileEnvironment.html>`_.

    Attributes to pay particular attention to:

    ``stdout``, ``stderr``:
        What is produced on those streams.

    ``returncode``:
        The return code of the script.

    ``files_created``, ``files_deleted``, ``files_updated``:
        Dictionaries mapping filenames (relative to the ``base_path``)
        to `FoundFile <class-paste.fixture.FoundFile.html>`_ or
        `FoundDir <class-paste.fixture.FoundDir.html>`_ objects.
    """

    def __init__(self, test_env, args, stdin, stdout, stderr,
                 returncode, files_before, files_after):
        self.test_env = test_env
        self.args = args
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.files_before = files_before
        self.files_after = files_after
        self.files_deleted = {}
        self.files_updated = {}
        self.files_created = files_after.copy()
        for path, f in files_before.items():
            if path not in files_after:
                self.files_deleted[path] = f
                continue
            del self.files_created[path]
            if f.mtime < files_after[path].mtime:
                self.files_updated[path] = files_after[path]
        if sys.platform == 'win32':
            self.stdout = self.stdout.replace('\n\r', '\n')
            self.stderr = self.stderr.replace('\n\r', '\n')

    def assert_no_error(self, quiet):
        __tracebackhide__ = True
        if self.returncode != 0:
            if not quiet:
                print(self)
            raise AssertionError(
                "Script returned code: %s" % self.returncode)

    def assert_no_stderr(self, quiet):
        __tracebackhide__ = True
        if self.stderr:
            if not quiet:
                print(self)
            else:
                print('Error output:')
                print(self.stderr)
            raise AssertionError("stderr output not expected")

    def assert_no_temp(self, quiet):
        __tracebackhide__ = True
        files = self.wildcard_matches('tmp/**')
        if files:
            if not quiet:
                print(self)
            else:
                print('Temp files:')
                print(', '.join(sorted(f.path for f in sorted(files, key=lambda x: x.path))))
            raise AssertionError("temp files not expected")

    def wildcard_matches(self, wildcard):
        """Return all the file objects whose path matches the given wildcard.

        You can use ``*`` to match any portion of a filename, and
        ``**`` to match multiple segments/directories.
        """
        regex_parts = []
        for index, part in enumerate(wildcard.split('**')):
            if index:
                regex_parts.append('.*')
            for internal_index, internal_part in enumerate(part.split('*')):
                if internal_index:
                    regex_parts.append('[^/\\\\]*')
                regex_parts.append(re.escape(internal_part))
        regex = ''.join(regex_parts) + '$'
        #assert 0, repr(regex)
        regex = re.compile(regex)
        results = []
        for container in self.files_updated, self.files_created:
            for key, value in sorted(container.items()):
                if regex.match(key):
                    results.append(value)
        return results

    def __str__(self):
        s = ['Script result: %s' % ' '.join(self.args)]
        if self.returncode:
            s.append('  return code: %s' % self.returncode)
        if self.stderr:
            s.append('-- stderr: --------------------')
            s.append(self.stderr)
        if self.stdout:
            s.append('-- stdout: --------------------')
            s.append(self.stdout)
        for name, files, show_size in [
            ('created', self.files_created, True),
            ('deleted', self.files_deleted, True),
            ('updated', self.files_updated, True)]:
            if files:
                s.append('-- %s: -------------------' % name)
                files = list(files.items())
                files.sort()
                last = ''
                for path, f in files:
                    t = '  %s' % _space_prefix(last, path, indent=4,
                                               include_sep=False)
                    last = path
                    if f.invalid:
                        t += '  (invalid link)'
                    else:
                        if show_size and f.size != 'N/A':
                            t += '  (%s bytes)' % f.size
                    s.append(t)
        return '\n'.join(s)

class FoundFile(object):

    """
    Represents a single file found as the result of a command.

    Has attributes:

    ``path``:
        The path of the file, relative to the ``base_path``

    ``full``:
        The full path

    ``bytes``:
        The contents of the file.

    ``stat``:
        The results of ``os.stat``.  Also ``mtime`` and ``size``
        contain the ``.st_mtime`` and ``.st_size`` of the stat.

    ``mtime``:
        The modification time of the file.

    ``size``:
        The size (in bytes) of the file.

    You may use the ``in`` operator with these objects (tested against
    the contents of the file), and the ``.mustcontain()`` method.
    """

    file = True
    dir = False
    invalid = False

    def __init__(self, base_path, path):
        self.base_path = base_path
        self.path = path
        self.full = os.path.join(base_path, path)
        if os.path.exists(self.full):
            self.stat = os.stat(self.full)
            self.mtime = self.stat.st_mtime
            self.size = self.stat.st_size
        else:
            self.invalid = True
            self.stat = self.mtime = None
            self.size = 'N/A'
        self._bytes = None

    def bytes__get(self):
        if self._bytes is None:
            f = open(self.full, 'rb')
            self._bytes = string(f.read())
            f.close()
        return self._bytes
    bytes = property(bytes__get)

    def __contains__(self, s):
        return s in self.bytes

    def mustcontain(self, s):
        __tracebackhide__ = True
        bytes = self.bytes
        if s not in bytes:
            print('Could not find %r in:' % s)
            print(bytes)
            assert s in bytes

    def __repr__(self):
        return '<%s %s:%s>' % (
            self.__class__.__name__,
            self.base_path, self.path)

class FoundDir(object):

    """
    Represents a directory created by a command.
    """

    file = False
    dir = True
    invalid = False

    def __init__(self, base_path, path):
        self.base_path = base_path
        self.path = path
        self.full = os.path.join(base_path, path)
        self.stat = os.stat(self.full)
        self.size = 'N/A'
        self.mtime = self.stat.st_mtime

    def __repr__(self):
        return '<%s %s:%s>' % (
            self.__class__.__name__,
            self.base_path, self.path)

def _popget(d, key, default=None):
    """
    Pop the key if found (else return default)
    """
    if key in d:
        return d.pop(key)
    return default

def _space_prefix(pref, full, sep=None, indent=None, include_sep=True):
    """
    Anything shared by pref and full will be replaced with spaces
    in full, and full returned.
    """
    if sep is None:
        sep = os.path.sep
    pref = pref.split(sep)
    full = full.split(sep)
    padding = []
    while pref and full and pref[0] == full[0]:
        if indent is None:
            padding.append(' ' * (len(full[0]) + len(sep)))
        else:
            padding.append(' ' * indent)
        full.pop(0)
        pref.pop(0)
    if padding:
        if include_sep:
            return ''.join(padding) + sep + sep.join(full)
        else:
            return ''.join(padding) + sep.join(full)
    else:
        return sep.join(full)
