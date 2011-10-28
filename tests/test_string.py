# -*- coding: utf-8 -*-

import sys

from scripttest.backwardscompat import string
from nose.plugins.skip import SkipTest


ascii_str = ''.join([
    'This is just some plain ol\' ASCII text with none of those ',
    'funny "Unicode" characters.\n\nJust good ol\' ASCII text.',
])

if sys.version_info.major <= 2:
    utf8_str = ''.join([
        'Bj\xc3\xb6rk Gu\xc3\xb0mundsd\xc3\xb3ttir ',
        '[\xcb\x88pj\xc5\x93r\xcc\xa5k ', 
        '\xcb\x88kv\xca\x8f\xc3\xb0m\xca\x8fnts\xcb\x8cto\xca\x8aht\xc9\xaar]',
    ])
else:
    utf8_str = 'Björk Guðmundsdóttir [ˈpjœr̥k ˈkvʏðmʏntsˌtoʊhtɪr]'


def skip_test_if_not_python_2():
    if sys.version_info.major != 2:
        raise SkipTest


def skip_test_if_not_python_3():
    if sys.version_info.major != 3:
        raise SkipTest


#-----------------------------------------
# Python 2 tests
#-----------------------------------------


def test_python_2_string_with_ascii_str():
    skip_test_if_not_python_2()

    assert isinstance(ascii_str, str)

    result = string(ascii_str)

    assert isinstance(result, unicode)
    assert result == ascii_str


def test_python_2_string_with_utf8_str():
    skip_test_if_not_python_2()

    assert isinstance(utf8_str, str)

    result = string(utf8_str)

    assert isinstance(result, unicode)
    assert result == utf8_str.decode('utf-8')


def test_python_2_string_with_ascii_unicode():
    skip_test_if_not_python_2()

    ascii_unicode = ascii_str.decode('utf-8')
    assert isinstance(ascii_unicode, unicode)

    result = string(ascii_unicode)

    assert isinstance(result, unicode)
    assert result == ascii_unicode


def test_python_2_string_with_utf8_unicode():
    skip_test_if_not_python_2()

    utf8_unicode = utf8_str.decode('utf-8')
    assert isinstance(utf8_unicode, unicode)

    result = string(utf8_unicode)

    assert isinstance(result, unicode)
    assert result == utf8_unicode


#-----------------------------------------
# Python 3 tests
#-----------------------------------------


def test_python_3_string_with_ascii_bytes():
    skip_test_if_not_python_3()

    ascii_bytes = ascii_str.encode('utf-8')
    assert isinstance(ascii_bytes, bytes)

    result = string(ascii_bytes)

    assert isinstance(result, str)
    assert result == ascii_bytes.decode('utf-8')


def test_python_3_string_with_utf8_bytes():
    skip_test_if_not_python_3()

    utf8_bytes = utf8_str.encode('utf-8')

    assert isinstance(utf8_bytes, bytes)

    result = string(utf8_bytes)

    assert isinstance(result, str)
    assert result == utf8_bytes.decode('utf-8')


def test_python_3_string_with_ascii_str():
    skip_test_if_not_python_3()

    assert isinstance(ascii_str, str)

    result = string(ascii_str)

    assert isinstance(result, str)
    assert result == ascii_str


def test_python_3_string_with_utf8_str():
    skip_test_if_not_python_3()

    assert isinstance(utf8_str, str)

    result = string(utf8_str)

    assert isinstance(result, str)
    assert result == utf8_str

