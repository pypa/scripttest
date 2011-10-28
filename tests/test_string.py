import sys

from scripttest.backwardscompat import string
from nose.plugins.skip import SkipTest


ascii_str = ''.join([
    'This is just some plain ol\' ASCII text with none of those ',
    'funny "Unicode" characters.\n\nJust good ol\' ASCII text.',
])

ascii_unicode = u''.join([
    u'This is a "degenerate" unicode string with just ASCII characters',
])

utf8_str = ''.join([
    'Bj\xc3\xb6rk Gu\xc3\xb0mundsd\xc3\xb3ttir ',
    '[\xcb\x88pj\xc5\x93r\xcc\xa5k ', 
    '\xcb\x88kv\xca\x8f\xc3\xb0m\xca\x8fnts\xcb\x8cto\xca\x8aht\xc9\xaar]',
])


def skip_test_if_not_python_2():
    if sys.version_info.major != 2:
        raise SkipTest


def skip_test_if_not_python_3():
    if sys.version_info.major != 3:
        raise SkipTest


def test_python_2_string_with_ascii_str():
    skip_test_if_not_python_2()

    assert string(ascii_str) == ascii_str


def test_python_2_string_with_utf8_str():
    skip_test_if_not_python_2()

    assert string(utf8_str) == utf8_str.decode('utf-8')


def test_python_2_string_with_ascii_unicode():
    skip_test_if_not_python_2()

    assert string(ascii_unicode) == ascii_unicode


def test_python_2_string_with_utf8_unicode():
    skip_test_if_not_python_2()

    utf8_unicode = utf8_str.decode('utf-8')

    assert string(utf8_unicode) == utf8_unicode

