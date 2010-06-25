def string(string):
    try:
        # py3k has not unicode builtin
        unicode
    except NameError:
        return string.decode('utf-8')
    else:
        return string
