import sys

import setuptools
import setuptools.command.test


class PyTest(setuptools.command.test.test):

    def finalize_options(self):
        setuptools.command.test.test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        sys.exit(pytest.main(self.test_args))


setuptools.setup(
    name='scripttest',
    version='2.0',
    description='Helper to test command-line scripts',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords='test unittest doctest command line scripts',
    author='Ian Bicking',
    author_email='ianb@colorstudy.com',
    url='https://scripttest.readthedocs.io/en/stable/',
    license='MIT',
    py_modules=['scripttest'],
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
    zip_safe=True,
)
