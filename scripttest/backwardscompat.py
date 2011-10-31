import sys

def string(string):
    if sys.version_info >= (3,):
        if isinstance(string, str):
            return string
        return str(string, "utf-8")
    else:
        if isinstance(string, unicode):
            return string
        return string.decode('utf-8')
