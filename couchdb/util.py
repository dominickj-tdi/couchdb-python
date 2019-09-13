import sys


__all__ = [
    'StringIO', 'urlsplit', 'urlunsplit', 'urlquote', 'urlunquote',
    'urlencode', 'utype', 'btype', 'ltype', 'strbase', 'funcode', 'urlparse',
    'funcode', 'pyexec'
]

utype = str
btype = bytes
ltype = int
strbase = str, bytes

from io import BytesIO as StringIO
from urllib.parse import urlsplit, urlunsplit, urlencode, urlparse
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote


def funcode(fun):
    return fun.__code__


def pyexec(code, gns, lns):
    # http://bugs.python.org/issue21591
    exec(code, gns, lns)
