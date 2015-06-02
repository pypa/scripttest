# -*- coding: utf-8 -*-

import sys

import pytest

from scripttest import string


ascii_str = ''.join([
    'This is just some plain ol\' ASCII text with none of those ',
    'funny "Unicode" characters.\n\nJust good ol\' ASCII text.',
])

if sys.version_info < (3, 0):
    utf8_str = ''.join([
        'Bj\xc3\xb6rk Gu\xc3\xb0mundsd\xc3\xb3ttir ',
        '[\xcb\x88pj\xc5\x93r\xcc\xa5k ',
        '\xcb\x88kv\xca\x8f\xc3\xb0m\xca\x8fnts\xcb\x8cto\xca\x8aht\xc9\xaar]',
    ])
else:
    utf8_str = 'Björk Guðmundsdóttir [ˈpjœr̥k ˈkvʏðmʏntsˌtoʊhtɪr]'


py2only = pytest.mark.skipif("sys.version_info >= (3, 0)",reason="Python 2.x Only")
py3only = pytest.mark.skipif("sys.version_info < (3, 0)",reason="Python 3.x Only")


# -----------------------------------------
# Python 2 tests
# -----------------------------------------


@py2only
def test_python_2_string_with_ascii_str():
    assert isinstance(ascii_str, str)

    result = string(ascii_str)

    assert isinstance(result, unicode)  # noqa
    assert result == ascii_str


@py2only
def test_python_2_string_with_utf8_str():
    assert isinstance(utf8_str, str)

    result = string(utf8_str)

    assert isinstance(result, unicode)  # noqa
    assert result == utf8_str.decode('utf-8')


@py2only
def test_python_2_string_with_ascii_unicode():
    ascii_unicode = ascii_str.decode('utf-8')
    assert isinstance(ascii_unicode, unicode)  # noqa

    result = string(ascii_unicode)

    assert isinstance(result, unicode)  # noqa
    assert result == ascii_unicode


@py2only
def test_python_2_string_with_utf8_unicode():
    utf8_unicode = utf8_str.decode('utf-8')
    assert isinstance(utf8_unicode, unicode)  # noqa

    result = string(utf8_unicode)

    assert isinstance(result, unicode)  # noqa
    assert result == utf8_unicode


# ------------------------------------------
# Python 3 tests
# ----------------------------------------


@py3only
def test_python_3_string_with_ascii_bytes():
    ascii_bytes = ascii_str.encode('utf-8')
    assert isinstance(ascii_bytes, bytes)

    result = string(ascii_bytes)

    assert isinstance(result, str)
    assert result == ascii_bytes.decode('utf-8')


@py3only
def test_python_3_string_with_utf8_bytes():
    utf8_bytes = utf8_str.encode('utf-8')

    assert isinstance(utf8_bytes, bytes)

    result = string(utf8_bytes)

    assert isinstance(result, str)
    assert result == utf8_bytes.decode('utf-8')


@py3only
def test_python_3_string_with_ascii_str():
    assert isinstance(ascii_str, str)

    result = string(ascii_str)

    assert isinstance(result, str)
    assert result == ascii_str


@py3only
def test_python_3_string_with_utf8_str():
    assert isinstance(utf8_str, str)

    result = string(utf8_str)

    assert isinstance(result, str)
    assert result == utf8_str
