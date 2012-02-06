try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys, os

version = '1.2'

setup(name='ScriptTest',
      version=version,
      description="Helper to test command-line scripts",
      long_description="""\
ScriptTest is a library to help you test your interactive command-line
applications.

With it you can easily run the command (in a subprocess) and see the
output (stdout, stderr) and any file modifications.

* The `source repository <http://bitbucket.org/ianb/scripttest/>`_.
""",
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Testing",
      ],
      keywords='test unittest doctest command line scripts',
      author='Ian Bicking',
      author_email='ianb@colorstudy.com',
      url='http://pythonpaste.org/scripttest/',
      license='MIT',
      packages=["scripttest"],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=True,
      )
