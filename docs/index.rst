ScriptTest
==========

.. toctree::

   news
   license
   modules/scripttest

.. contents::

Status & License
----------------

ScriptTest is an extraction of ``paste.fixture.TestFileEnvironment``
from the `Paste <http://pythonpaste.org>`_ project.  It was originally
written to test `Paste Script <http://pythonpaste.org/script/>`_.

It is licensed under an `MIT-style permissive license
<license.html>`_.

Discussion happens on the `Paste mailing list </community/>`_,
and bugs should go in the `Github issue list
<https://github.com/pypa/scripttest/issues>`_.

It is available on `pypi <https://pypi.python.org/pypi/scripttest/>`_ 
or in a `git repository <https://github.com/pypa/scripttest>`_.
You can get a checkout with::

    $ git clone https://github.com/pypa/scripttest.git

Purpose & Introduction
----------------------

This library helps you test command-line scripts.  It runs a script
and watches the output, looks for non-zero exit codes, output on
stderr, and any files created, deleted, or modified.

To start you instantiate ``TestFileEnvironment``, which is the context
in which all your scripts are run.  You give it a base directory
(typically a scratch directory), or if you don't it will guess
``call_module_dir/test-output/``.  Example::

    >>> from scripttest import TestFileEnvironment
    >>> env = TestFileEnvironment('./test-output')

.. note::

   Everything in ``./test-output`` will be deleted every test run.  To
   make sure you don't point at an important directory, the scratch
   directory must be created by ScriptTest (a hidden file is written
   by ScriptTest to confirm that it created the directory).  If the
   directory already exists, you must delete it manually.

Then you run scripts with ``env.run(script, arg1, arg2, ...)``::

    >>> print(env.run('echo', 'hey'))
    Script result: echo hey
    -- stdout: --------------------
    hey
    <BLANKLINE>

There's several keyword arguments you can use with ``env.run()``:

``debug``: (default False)
    Don't pipe output. Note that this will cause the returned object's
    ``stdout`` and ``stderr`` attributes to be emtpy strings.
``expect_error``: (default False)
    Don't raise an exception in case of errors
``expect_stderr``: (default ``expect_error``)
    Don't raise an exception if anything is printed to stderr
``stdin``: (default ``""``)
    Input to the script
``cwd``: (default ``self.cwd``)
    The working directory to run in (default ``base_dir``)

As you can see from the options, if the script indicates anything
error-like it is, by default, turned into an exception.  This of
course includes a non-zero response code.  Also any output on stderr
also counts as an error (unless turned off with
``expect_stderr=True``).

The object you get back from a run represents what happened during the
script.  It has a useful ``str()`` (as you can see in the previous
example) that shows a summary and can be useful in a doctest.  It also
has several useful attributes:

``stdout``, ``stderr``:
    What is produced on those streams

``returncode``:
    The return code of the script.

``files_created``, ``files_deleted``, ``files_updated``:
    Dictionaries mapping filenames (relative to the ``base_dir``)
    to `FoundFile <class-scripttest.FoundFile.html>`_ or
    `FoundDir <class-scripttest.FoundDir.html>`_ objects.

Of course by default ``stderr`` must be empty, and ``returncode`` must
be zero, since anything else would be considered an error.

Of particular interest are the dictionaries ``files_created``, etc.
These show just what files were handled by the script.  Each
dictionary points to another helper object for inspecting the files
(``.files_deleted`` contains the files as they existed *before* the
script ran).

Each file or directory object has useful attributes:

``path``:
    The path of the file, relative to the ``base_path``

``full``:
    The full path

``stat``:
    The results of ``os.stat``.  Also ``mtime`` and ``size``
    contain the ``.st_mtime`` and ``st_size`` of the stat.
    (Directories have no ``size``)

``bytes``:
    The contents of the file (does not apply to directories).

``file``, ``dir``:
    ``file`` is true for files, ``dir`` is true for directories.

You may use the ``in`` operator with the file objects (tested against
the contents of the file), and the ``.mustcontain()`` method, where
``file.mustcontain('a', 'b')`` means ``assert 'a' in file; assert 'b'
in file``.
