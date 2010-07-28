import sys
def string(s):
    if sys.version_info >= (3,):
        if isinstance(s, bytes):
            return s.decode('latin-1')
    return s
