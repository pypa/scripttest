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


setuptools.setup(
    name='scripttest',
    version="1.3",
    description="Helper to test command-line scripts",
    long_description=open("README.rst").read(),
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
    py_modules=["scripttest"],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    zip_safe=True,
)
