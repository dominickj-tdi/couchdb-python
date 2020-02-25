#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys
from setuptools import setup


setup(
    name = 'CouchDB',
    version = '2.0a1',
    description = 'Python library for working with CouchDB',
    long_description = \
"""This is a Python library for CouchDB. It provides a convenient high level
interface for the CouchDB server.""",
    author = 'Christopher Lenz',
    author_email = 'cmlenz@gmx.de',
    maintainer = 'Dirkjan Ochtman',
    maintainer_email = 'dirkjan@ochtman.nl',
    license = 'BSD',
    url = 'https://github.com/djc/couchdb-python/',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages = ['couchdb', 'couchdb.tests'],
    install_requires = ['requests'],
    test_suite = 'couchdb.tests.__main__.suite',
    zip_safe = True,
)
