from scripttest import string


ascii_str = ''.join([
    'This is just some plain ol\' ASCII text with none of those ',
    'funny "Unicode" characters.\n\nJust good ol\' ASCII text.',
])

utf8_str = 'Björk Guðmundsdóttir [ˈpjœr̥k ˈkvʏðmʏntsˌtoʊhtɪr]'


def test_string_with_ascii_bytes():
    ascii_bytes = ascii_str.encode('utf-8')
    assert isinstance(ascii_bytes, bytes)

    result = string(ascii_bytes)

    assert isinstance(result, str)
    assert result == ascii_bytes.decode('utf-8')


def test_string_with_utf8_bytes():
    utf8_bytes = utf8_str.encode('utf-8')

    assert isinstance(utf8_bytes, bytes)

    result = string(utf8_bytes)

    assert isinstance(result, str)
    assert result == utf8_bytes.decode('utf-8')


def test_string_with_ascii_str():
    assert isinstance(ascii_str, str)

    result = string(ascii_str)

    assert isinstance(result, str)
    assert result == ascii_str


def test_string_with_utf8_str():
    assert isinstance(utf8_str, str)

    result = string(utf8_str)

    assert isinstance(result, str)
    assert result == utf8_str
