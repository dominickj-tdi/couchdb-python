#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from .util import urlquote as quote


def urljoin(base, *path, **query):
    """Assemble a uri based on a base, any number of path segments, and query
    string parameters.

    >>> urljoin('http://example.org', '_all_dbs')
    'http://example.org/_all_dbs'

    A trailing slash on the uri base is handled gracefully:

    >>> urljoin('http://example.org/', '_all_dbs')
    'http://example.org/_all_dbs'

    And multiple positional arguments become path parts:

    >>> urljoin('http://example.org/', 'foo', 'bar')
    'http://example.org/foo/bar'

    All slashes within a path part are escaped:

    >>> urljoin('http://example.org/', 'foo/bar')
    'http://example.org/foo%2Fbar'
    >>> urljoin('http://example.org/', 'foo', '/bar/')
    'http://example.org/foo/%2Fbar%2F'

    >>> urljoin('http://example.org/', None) #doctest:+IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    TypeError: argument 2 to map() must support iteration
    """
    if base and base.endswith('/'):
        base = base[:-1]
    retval = [base]

    # build the path
    path = '/'.join([''] + [quote(s, '') for s in path])
    if path:
        retval.append(path)

    # build the query string
    params = []
    for name, value in query.items():
        if type(value) in (list, tuple):
            params.extend([(name, i) for i in value if i is not None])
        elif value is not None:
            if value is True:
                value = 'true'
            elif value is False:
                value = 'false'
            params.append((name, value))
    if params:
        retval.extend(['?', urlencode(params)])

    return ''.join(retval)

