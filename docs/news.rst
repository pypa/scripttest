News
====


1.3
---

* Use CRC32 to protect against a race condition where if a run took less than
  1 second updates files would not appear to be updated.


1.2
---

* Python 3 support (thanks Marc Abramowitz!)

1.1.1
-----

* Python 3 fixes

1.1
---

* Python 3 compatibility, from Hugo Tavares
* More Windows fixes, from Hugo Tavares

1.0.4
-----

* Windows fixes (thanks Dave Abrahams); including an option for more careful
  string splitting (useful when testing a script with a space in the path),
  and more careful handling of environmental variables.

1.0.3
-----

* Added a ``capture_temp`` argument to
  :class:`scripttest.TestFileEnvironment` and ``env.assert_no_temp()``
  to test that no temporary files are left over.

1.0.2
-----

* Fixed regression with ``FoundDir.invalid``

1.0.1
-----

* Windows fix for cleaning up scratch files more reliably

* Allow spaces in the ``script`` name, e.g., ``C:/program
  files/some-script`` (but you must use multiple arguments to
  ``env.run(script, more_args)``).

* Remove the resolution of scripts to an absolute path (just allow the
  OS to do this).

* Don't fail if there is an invalid symlink

1.0
---

* ``env.run()`` now takes a keyword argument ``quiet``.  If quiet is
  false, then if there is any error (return code != 0, or stderr
  output) the complete output of the script will be printed.

* ScriptTest puts a marker file in scratch directories it deletes, so
  that if you point it at a directory not created by ScriptTest it
  will raise an error.  Without this, unwitting developers could point
  ScriptTest at the project directory, which would cause the entire
  project directory to be wiped.

* ProcResults now no longer print the absolute path of the script
  (which is often system dependent, and so not good for doctests).

* Added :func:`scripttest.ProcResults.wildcard_matches` which returns file
  objects based on a wildcard expression.

0.9
---

Initial release
