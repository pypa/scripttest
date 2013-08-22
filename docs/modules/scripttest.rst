:mod:`scripttest` -- test command-line scripts
==============================================

.. automodule:: scripttest

Module Contents
---------------

.. autoclass:: TestFileEnvironment

Objects that are returned
~~~~~~~~~~~~~~~~~~~~~~~~~

These objects are returned when you use ``env.run(...)``.  The
`ProcResult` object is returned, and it has ``.files_updated``,
``.files_created``, and ``.files_deleted`` which are dictionaries of
`FoundFile` and `FoundDir`.  The files in ``.files_deleted`` represent
the pre-deletion state of the file; the other files represent the
state of the files after the command is run.

 and ``.files_deleted``.  These objects dictionary

.. autoclass:: ProcResult

.. autoclass:: FoundFile

.. autoclass:: FoundDir

