import sys

import setuptools
import setuptools.command.test


class PyTest(setuptools.command.test.test):

    def finalize_options(self):
        setuptools.command.test.test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest

        sys.exit(pytest.main(self.test_args))

version = '1.2'

setuptools.setup(
    name='ScriptTest',
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
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    zip_safe=True,
)
