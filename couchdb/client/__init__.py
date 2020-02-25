# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Christopher Lenz
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

"""Python client API for CouchDB.

>>> server = Server()
>>> db = server.create('python-tests')
>>> doc_id, doc_rev = db.save({'type': 'Person', 'name': 'John Doe'})
>>> doc = db[doc_id]
>>> doc['type']
u'Person'
>>> doc['name']
u'John Doe'
>>> del db[doc.id]
>>> doc.id in db
False

>>> del server['python-tests']
"""

__all__ = ['Server', 'Database', 'Document', 'FindQuery']#, 'ViewResults', 'Row']
__docformat__ = 'restructuredtext en'

from .server import Server
from .database import Database
from .document import Document
from .find import FindQuery
from .exceptions import CouchDBException, UnauthorizedException, DocumentConflictException, NotFoundException
# TODO import index and view after I have them actually working

