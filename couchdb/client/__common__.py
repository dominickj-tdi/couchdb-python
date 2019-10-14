import itertools
import mimetypes
import os
from types import FunctionType
from inspect import getsource
from textwrap import dedent
import warnings
import sys
import socket
import requests
import json
from ..http_util import urljoin
from urllib.parse import urlsplit, urlunsplit, urlencode, urlparse
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from .. import  util




DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')