# (c) 2005-2007 Ian Bicking and contributors; written for Paste
# Licensed under the MIT license:
#       http://www.opensource.org/licenses/mit-license.php
"""
Helpers for testing command-line scripts
"""
import sys
import os
import stat
import shutil
import shlex
import subprocess
import re
import zlib
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

_ExcInfo = Tuple[Type[BaseException], BaseException, TracebackType]


if sys.platform == 'win32':
    def clean_environ(e: Dict[str, str]) -> Dict[str, str]:
        ret = {
            str(k): str(v) for k, v in e.items()}
        return ret
else:
    def clean_environ(e: Dict[str, str]) -> Dict[str, str]:
        return e


def string(string: Union[bytes, str]) -> str:
    if isinstance(string, str):
        return string
    return str(string, "utf-8")


# From pathutils by Michael Foord:
#       http://www.voidspace.org.uk/python/pathutils.html
def onerror(func: Callable[..., Any], path: str, exc_info: _ExcInfo) -> None:
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``

    """
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


__all__ = ['TestFileEnvironment']


class TestFileEnvironment:

    """
    This represents an environment in which files will be written, and
    scripts will be run.
    """

    # for py.test
    disabled = True

    def __init__(
        self,
        base_path: Optional[str] = None,
        template_path: Optional[str] = None,
        environ: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        start_clear: bool = True,
        ignore_paths: Optional[Iterable[str]] = None,
        ignore_hidden: bool = True,
        ignore_temp_paths: Optional[Iterable[str]] = None,
        capture_temp: bool = False,
        assert_no_temp: bool = False,
        split_cmd: bool = True,
    ) -> None:
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
        self.temp_path: Optional[str]
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
        self.ignore_temp_paths = ignore_temp_paths or []
        self.ignore_hidden = ignore_hidden
        self.split_cmd = split_cmd

        if assert_no_temp and not self.capture_temp:
            raise TypeError(
                'You cannot use assert_no_temp unless capture_temp=True')
        self._assert_no_temp = assert_no_temp

        self.split_cmd = split_cmd

    def _guess_base_path(self, stack_level: int) -> str:
        frame = sys._getframe(stack_level + 1)
        file = frame.f_globals.get('__file__')
        if not file:
            raise TypeError(
                "Could not guess a base_path argument from the calling scope "
                "(no __file__ found)")
        dir = os.path.dirname(file)
        return os.path.join(dir, 'test-output')

    def run(self, script: str, *args: Any, **kw: Any) -> "ProcResult":
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
            When there's an error (return code != 0), do not print
            stdout/stderr

        Returns a `ProcResult
        <class-paste.fixture.ProcResult.html>`_ object.
        """
        __tracebackhide__ = True
        expect_error = kw.pop('expect_error', False)
        expect_stderr = kw.pop('expect_stderr', expect_error)
        cwd = kw.pop('cwd', self.cwd)
        stdin = kw.pop('stdin', None)
        quiet = kw.pop('quiet', False)
        debug = kw.pop('debug', False)
        if not self.temp_path:
            if 'expect_temp' in kw:
                raise TypeError(
                    'You cannot use expect_temp unless you use '
                    'capture_temp=True')
        expect_temp = kw.pop('expect_temp', not self._assert_no_temp)
        script_args = list(map(str, args))
        assert not kw, (
            "Arguments not expected: %s" % ', '.join(kw.keys()))
        if self.split_cmd and ' ' in script:
            if script_args:
                # Then treat this as a script that has a space in it
                pass
            else:
                script, script_args_s = script.split(None, 1)
                script_args = shlex.split(script_args_s)

        all = [script] + script_args

        files_before = self._find_files()

        if debug:
            proc = subprocess.Popen(all,
                                    cwd=cwd,
                                    # see http://bugs.python.org/issue8557
                                    shell=(sys.platform == 'win32'),
                                    env=clean_environ(self.environ))
        else:
            proc = subprocess.Popen(all, stdin=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    cwd=cwd,
                                    # see http://bugs.python.org/issue8557
                                    shell=(sys.platform == 'win32'),
                                    env=clean_environ(self.environ))

        if debug:
            stdout_bytes, stderr_bytes = proc.communicate()
        else:
            stdout_bytes, stderr_bytes = proc.communicate(stdin)
        stdout = string(stdout_bytes)
        stderr = string(stderr_bytes)

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
            self.assert_no_temp()
        return result

    def _find_files(self) -> Dict[str, Union["FoundDir", "FoundFile"]]:
        result: Dict[str, Union["FoundDir", "FoundFile"]] = {}
        for fn in os.listdir(self.base_path):
            if self._ignore_file(fn):
                continue
            self._find_traverse(fn, result)
        return result

    def _ignore_file(self, fn: str) -> bool:
        if fn in self.ignore_paths:
            return True
        if self.ignore_hidden and os.path.basename(fn).startswith('.'):
            return True
        return False

    def _find_traverse(
        self,
        path: str,
        result: Dict[str, Union["FoundDir", "FoundFile"]],
    ) -> None:
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

    def clear(self, force: bool = False) -> None:
        """
        Delete all the files in the base directory.
        """
        marker_file = os.path.join(self.base_path, '.scripttest-test-dir.txt')
        if os.path.exists(self.base_path):
            if not force and not os.path.exists(marker_file):
                sys.stderr.write(
                    'The directory %s does not appear to have been created by '
                    'ScriptTest\n' % self.base_path)
                sys.stderr.write(
                    'The directory %s must be a scratch directory; it will be '
                    'wiped after every test run\n' % self.base_path)
                sys.stderr.write('Please delete this directory manually\n')
                raise AssertionError(
                    "The directory %s was not created by ScriptTest; it must "
                    "be deleted manually" % self.base_path)
            shutil.rmtree(self.base_path, onerror=onerror)
        os.mkdir(self.base_path)
        f = open(marker_file, 'w')
        f.write('placeholder')
        f.close()
        if self.temp_path and not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)

    def writefile(
        self,
        path: str,
        content: Optional[bytes] = None,
        frompath: Optional[str] = None,
    ) -> "FoundFile":
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

    def assert_no_temp(self) -> None:
        """If you use ``capture_temp`` then you can use this to make
        sure no files have been left in the temporary directory"""
        __tracebackhide__ = True
        if not self.temp_path:
            raise Exception('You cannot use assert_no_error unless you '
                            'instantiate '
                            'TestFileEnvironment(capture_temp=True)')
        names = os.listdir(self.temp_path)
        if not names:
            return
        new_names = []
        for name in names:
            if name in self.ignore_temp_paths:
                continue
            if os.path.isdir(os.path.join(self.temp_path, name)):
                name += '/'
            new_names.append(name)
        raise AssertionError(
            'Temporary files left over: %s'
            % ', '.join(sorted(names)))


class ProcResult:

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

    def __init__(
        self,
        test_env: TestFileEnvironment,
        args: List[str],
        stdin: bytes,
        stdout: str,
        stderr: str,
        returncode: int,
        files_before: Dict[str, Union["FoundDir", "FoundFile"]],
        files_after: Dict[str, Union["FoundDir", "FoundFile"]],
    ) -> None:
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
            if f != files_after[path]:
                self.files_updated[path] = files_after[path]
        if sys.platform == 'win32':
            self.stdout = self.stdout.replace('\n\r', '\n')
            self.stderr = self.stderr.replace('\n\r', '\n')

    def assert_no_error(self, quiet: bool) -> None:
        __tracebackhide__ = True
        if self.returncode != 0:
            if not quiet:
                print(self)
            raise AssertionError(
                "Script returned code: %s" % self.returncode)

    def assert_no_stderr(self, quiet: bool) -> None:
        __tracebackhide__ = True
        if self.stderr:
            if not quiet:
                print(self)
            else:
                print('Error output:')
                print(self.stderr)
            raise AssertionError("stderr output not expected")

    def assert_no_temp(self, quiet: bool) -> None:
        __tracebackhide__ = True
        files = self.wildcard_matches('tmp/**')
        if files:
            if not quiet:
                print(self)
            else:
                print('Temp files:')
                print(', '.join(sorted(
                    f.path for f in sorted(files, key=lambda x: x.path)
                )))
            raise AssertionError("temp files not expected")

    def wildcard_matches(
        self, wildcard: str
    ) -> List[Union["FoundDir", "FoundFile"]]:
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
        pattern = ''.join(regex_parts) + '$'
        regex = re.compile(pattern)
        results = []
        for container in self.files_updated, self.files_created:
            for key, value in sorted(container.items()):
                if regex.match(key):
                    results.append(value)
        return results

    def __str__(self) -> str:
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
                last = ''
                for path, f in sorted(files.items()):
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


class FoundFile:

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

    def __init__(self, base_path: str, path: str) -> None:
        self.base_path = base_path
        self.path = path
        self.full = os.path.join(base_path, path)
        self.stat: Optional[os.stat_result]
        self.mtime: Optional[float]
        self.size: Union[int, str]
        if os.path.exists(self.full):
            self.stat = os.stat(self.full)
            self.mtime = self.stat.st_mtime
            self.size = self.stat.st_size
            if stat.S_ISFIFO(os.stat(self.full).st_mode):
                self.hash = None  # it's a pipe
            else:
                with open(self.full, "rb") as fp:
                    self.hash = zlib.crc32(fp.read())
        else:
            self.invalid = True
            self.stat = self.mtime = None
            self.size = 'N/A'
            self.hash = None
        self._bytes: Optional[str] = None

    def bytes__get(self) -> str:
        if self._bytes is None:
            f = open(self.full, 'rb')
            self._bytes = string(f.read())
            f.close()
        return self._bytes
    bytes = property(bytes__get)

    def __contains__(self, s: str) -> bool:
        return s in self.bytes

    def mustcontain(self, s: str) -> None:
        __tracebackhide__ = True
        bytes = self.bytes
        if s not in bytes:
            print('Could not find %r in:' % s)
            print(bytes)
            assert s in bytes

    def __repr__(self) -> str:
        return '<{} {}:{}>'.format(
            self.__class__.__name__,
            self.base_path, self.path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FoundFile):
            return NotImplemented

        return (
            self.hash == other.hash and  # noqa: W504
            self.mtime == other.mtime and  # noqa: W504
            self.size == other.size
        )


class FoundDir:

    """
    Represents a directory created by a command.
    """

    file = False
    dir = True
    invalid = False

    def __init__(self, base_path: str, path: str) -> None:
        self.base_path = base_path
        self.path = path
        self.full = os.path.join(base_path, path)
        self.stat = os.stat(self.full)
        self.size = 'N/A'
        self.mtime = self.stat.st_mtime

    def __repr__(self) -> str:
        return '<{} {}:{}>'.format(
            self.__class__.__name__,
            self.base_path, self.path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FoundDir):
            return NotImplemented

        return self.mtime == other.mtime


def _space_prefix(
    pref: str,
    full: str,
    sep: Optional[str] = None,
    indent: Optional[int] = None,
    include_sep: bool = True
) -> str:
    """
    Anything shared by pref and full will be replaced with spaces
    in full, and full returned.
    """
    if sep is None:
        sep = os.path.sep
    pref_parts = pref.split(sep)
    full_parts = full.split(sep)
    padding = []
    while pref_parts and full_parts and pref_parts[0] == full_parts[0]:
        if indent is None:
            padding.append(' ' * (len(full_parts[0]) + len(sep)))
        else:
            padding.append(' ' * indent)
        full_parts.pop(0)
        pref_parts.pop(0)
    if padding:
        if include_sep:
            return ''.join(padding) + sep + sep.join(full_parts)
        else:
            return ''.join(padding) + sep.join(full_parts)
    else:
        return sep.join(full_parts)
