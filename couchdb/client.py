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
from .http_util import urljoin
from urllib.parse import urlsplit, urlunsplit, urlencode, urlparse
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote

from . import  util

__all__ = ['Server', 'Database', 'Document', 'ViewResults', 'Row']
__docformat__ = 'restructuredtext en'


DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')


class Server(object):
    """Representation of a CouchDB server.

    >>> server = Server() # connects to the local_server
    >>> remote_server = Server('http://example.com:5984/')
    >>> secure_remote_server = Server('https://username:password@example.com:5984/')

    This class behaves like a dictionary of databases. For example, to get a
    list of database names on the server, you can simply iterate over the
    server object.

    New databases can be created using the `create` method:

    >>> db = server.create('python-tests')
    >>> db
    <Database 'python-tests'>

    You can access existing databases using item access, specifying the database
    name as the key:

    >>> db = server['python-tests']
    >>> db.name
    'python-tests'

    Databases can be deleted using a ``del`` statement:

    >>> del server['python-tests']
    """

    def __init__(self, url=DEFAULT_BASE_URL, full_commit=None, session=None, throw_exceptions=True):
        """Initialize the server object.

        :param url: the URI of the server (for example
                    ``http://localhost:5984/``)
        :param full_commit: turn on the X-Couch-Full-Commit header
        :param session: an requests.Session instance or None for a default session
        :param throw_exceptions: If False, HTTP errors will fail silently
        """
        self.session = session or requests.Session()
        self.url = url
        self.throw_exceptions = throw_exceptions
        
        if full_commit is not None:
            self.session.headers.update({
                'X-Couch-Full-Commit': 
                'true' if full_commit else 'false'
            })

        self._version_info = None

    def __contains__(self, name):
        """Return whether the server contains a database with the specified
        name.

        :param name: the database name
        :return: `True` if a database with the name exists, `False` otherwise
        """
        response = self.session.head(urljoin(self.url, name))
        return response.ok

    def __iter__(self):
        """Iterate over all databases."""
        return iter(self.all_dbs())

    def __len__(self):
        """Return the number of databases."""
        response = self.session.get(urljoin(self.url, '_all_dbs'))
        if self.throw_exceptions: response.raise_for_status()
        return len(response.json())

    def __nonzero__(self):
        """Return whether the server is available."""
        return self.session.head(self.url).ok

    def __bool__(self):
        """Return whether the server is available."""
        return self.session.head(self.url).ok

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.url)

    def __delitem__(self, name):
        """Remove the database with the specified name.

        :param name: the name of the database
        :raise HTTPError: if no database with that name exists
        """
        response = self.session.delete(urljoin(self.url, name))
        if self.throw_exceptions: response.raise_for_status()

    def __getitem__(self, name):
        """Return a `Database` object representing the database with the
        specified name.

        :param name: the name of the database
        :return: a `Database` object representing the database
        :rtype: `Database`
        :raise HTTPError: if no database with that name exists
        """
        dbUrl = urljoin(self.url, name)
        # actually make a request to the database, to see if it exists
        response = self.session.head(dbUrl) 
        if self.throw_exceptions: response.raise_for_status()
        if response.ok: return Database(dbUrl, name, self.session)
    

    def all_dbs(self):
        """Generator to interate of all databases"""
        response = self.session.get(urljoin(self.url, '_all_dbs'))
        if self.throw_exceptions: response.raise_for_status()
        for dbName in response.json():
            yield Database(urljoin(self.url, dbName), dbName, self.session, self.throw_exceptions)

    def config(self):
        """The configuration of the CouchDB server.

        The configuration is represented as a nested dictionary of sections and
        options from the configuration files of the server, or the default
        values for options that are not explicitly configured.

        :rtype: `dict`
        """
        response = self.session.get(urljoin(self.url, '_config'))
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def version(self):
        """The version string of the CouchDB server.

        Note that this results in a request being made, and can also be used
        to check for the availability of the server.

        :rtype: `unicode`"""
        response = self.session.get(self.url)
        if self.throw_exceptions: response.raise_for_status()
        return response.json()['version']

    def version_info(self):
        """The version of the CouchDB server as a tuple of ints.

        Note that this results in a request being made only at the first call.
        Afterwards the result will be cached.

        :rtype: `tuple(int, int, int)`"""
        if self._version_info is None:
            version = self.version()
            self._version_info = tuple(map(int, version.split('.')))
        return self._version_info

    def stats(self, name=None):
        """Server statistics.

        :param name: name of single statistic, e.g. httpd/requests
                     (None -- return all statistics)
        """
        url = urljoin(self.url, '_local/_stats')
        if name: url = urljoin(url, name)
        
        response = self.session.get(url)
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def tasks(self):
        """A list of tasks currently active on the server."""
        response = self.session.get(urljoin(self.url, '_active_tasks'))
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def uuids(self, count=None):
        """Retrieve a batch of uuids

        :param count: a number of uuids to fetch
                      (None -- get as many as the server sends)
        :return: a list of uuids
        """
        response = self.session.get(
            urljoin(self.url, '_uuids'), 
            params = {'count': count} if count is not None else None
        )
        if self.throw_exceptions: response.raise_for_status()
        return response.json()['uuids']

    def create(self, name):
        """Create a new database with the given name.

        :param name: the name of the database
        :return: a `Database` object representing the created database
        :rtype: `Database`
        :raise HTTPError: if a database with that name already exists
        """
        dbUrl = urljoin(self.url, name)
        response = self.session.put(dbUrl) 
        if self.throw_exceptions: response.raise_for_status()
        if response.ok: return Database(dbUrl, name, self.session, self.throw_exceptions)

    def delete(self, name):
        """Delete the database with the specified name.

        :param name: the name of the database
        :raise ResourceNotFound: if a database with that name does not exist
        :since: 0.6
        """
        del self[name]

    def replicate(self, source, target, **options):
        """Replicate changes from the source database to the target database.

        :param source: URL of the source database
        :param target: URL of the target database
        :param options: optional replication args, e.g. continuous=True
        """
        data = {'source': source, 'target': target}
        data.update(options)
        response = self.session.post(urljoin(self.url, '_replicate'), data=data)
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def add_user(self, name, password, roles=None):
        """Add regular user in authentication database.

        :param name: name of regular user, normally user id
        :param password: password of regular user
        :param roles: roles of regular user
        :return: (id, rev) tuple of the registered user
        :rtype: `tuple`
        """
        user_db = self['_users']
        return user_db.save({
            '_id': 'org.couchdb.user:' + name,
            'name': name,
            'password': password,
            'roles': roles or [],
            'type': 'user',
        })

    def remove_user(self, name):
        """Remove regular user in authentication database.

        :param name: name of regular user, normally user id
        """
        user_db = self['_users']
        doc_id = 'org.couchdb.user:' + name
        del user_db[doc_id]

    def login(self, name, password):
        """Login regular user in couch db. This saves the authentication 
        token in the requests.Session object for this server

        :param name: name of regular user, normally user id
        :param password: password of regular user
        :return: user data dict
        """
        response = self.session.post(urljoin(self.url, '_session'), data={
            'name': name,
            'password': password,
        })
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def logout(self, token):
        """Logout regular user in couch db

        :param token: token of login user
        :return: True if successfully logout
        :rtype: bool
        """
        header = {
            'Accept': 'application/json'
        }
        response = self.session.delete(urljoin(self.url, '_session'), headers=header)
        if self.throw_exceptions: response.raise_for_status()
        return response.ok

    def verify_token(self, token=None):
        """Verify user token

        :param token: authentication token
        :return: True if authenticated ok
        :rtype: bool
        """
        if token is not None:
            self.session.cookies.set('AuthSession', token)
            
        response = self.session.get(urljoin(self.url, '_session'))

        return response.ok
    

    def renew_session(self, token=None):
        """ Same as `verify_token`, but returns a user data dict instead of 
        a boolean, and can throw an exception if the request fails and 
        `throw_exceptions` is True
        """
        if token is not None:
            self.session.cookies.set('AuthSession', token)

        response = self.session.get(urljoin(self.url, '_session'))

        if self.throw_exceptions: response.raise_for_status()
        return response.json()['userCtx']
    

    def get_token(self):
        """ Returns the current authentication token for the current session """
        return self.session.cookies.get('AuthSession', domain=self.url)


class Database(object):
    """Representation of a database on a CouchDB server.

    >>> server = Server()
    >>> db = server.create('python-tests')

    New documents can be added to the database using the `save()` method:

    >>> doc_id, doc_rev = db.save({'type': 'Person', 'name': 'John Doe'})

    This class provides a dictionary-like interface to databases: documents are
    retrieved by their ID using item access

    >>> doc = db[doc_id]
    >>> doc                 #doctest: +ELLIPSIS
    <Document u'...'@... {...}>

    Documents are represented as instances of the `Row` class, which is
    basically just a normal dictionary with the additional attributes ``id`` and
    ``rev``:

    >>> doc.id, doc.rev     #doctest: +ELLIPSIS
    (u'...', ...)
    >>> doc['type']
    u'Person'
    >>> doc['name']
    u'John Doe'

    To update an existing document, you use item access, too:

    >>> doc['name'] = 'Mary Jane'
    >>> db[doc.id] = doc

    The `save()` method creates a document with a random ID generated by
    CouchDB (which is not recommended). If you want to explicitly specify the
    ID, you'd use item access just as with updating:

    >>> db['JohnDoe'] = {'type': 'person', 'name': 'John Doe'}

    >>> 'JohnDoe' in db
    True
    >>> len(db)
    2

    >>> del server['python-tests']
    """

    def __init__(self, url, name, session, throw_exceptions=True):
        if isinstance(url, util.strbase):
            if not url.startswith('http'):
                url = DEFAULT_BASE_URL + url
        self.url = url
        self.session = session
        self._name = name
        self.throw_exceptions = throw_exceptions

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.name)

    def __contains__(self, id):
        """Return whether the database contains a document with the specified
        ID.

        :param id: the document ID
        :return: `True` if a document with the ID exists, `False` otherwise
        """
        response = self.session.head(urljoin(self.url, id))
        return response.ok

    def __iter__(self):
        """Return the IDs of all documents in the database."""
        return iter([item.id for item in self.view('_all_docs')])

    def __len__(self):
        """Return the number of documents in the database."""
        response = self.session.get(self.url)
        if self.throw_exceptions: response.raise_for_status()
        return data['doc_count']

    def __nonzero__(self):
        """Return whether the database is available."""
        return self.session.head(self.url).ok

    def __bool__(self):
        return self.session.head(self.url).ok

    def __delitem__(self, id):
        """Remove the document with the specified ID from the database.

        Fetches the latest rev from the database to do the deletion.

        WARNING! This bypasses CouchDB's rev-based data integrity constraints,
        meaning it will delete the document even if someone else has edited
        the document since you last fetched it from the DB

        :param id: the document ID
        """
        docUrl = urljoin(self.url, id)
        response1 = self.session.head(docUrl)
        rev = response1.headers['ETag'].strip('"')
        response2 = self.session.delete(docUrl, params={'rev': rev})
        if self.throw_exceptions: response2.raise_for_status()

    def __getitem__(self, id):
        """Return the document with the specified ID.

        :param id: the document ID
        :return: a `Row` object representing the requested document
        :rtype: `Document`
        """
        response = self.session.get(urljoin(self.url, id))
        if self.throw_exceptions: response.raise_for_status()
        if response.ok: return Document(response.json())

    def __setitem__(self, id, data):
        """Create or update a document with the specified ID.

        :param id: the document ID
        :param content: the document content; either a plain dictionary for
                        new documents, or a `Row` object for existing
                        documents
        """
        response = self.session.put(urljoin(self.url, id), data=data)
        if self.throw_exceptions: response.raise_for_status()
        if response.ok: data.update({'_id': data['id'], '_rev': data['rev']})
    

    def all_docs(self, wrapper=None, **options):
        return self.view('_all_docs', wrapper, **options)
        

    @property
    def name(self):
        """The name of the database.

        Note that this may require a request to the server unless the name has
        already been cached by the `info()` method.

        :rtype: basestring
        """
        if self._name is None:
            self.info()
        return self._name

    @property
    def security(self):
        response = self.session.get(urljoin(self.url, '_security'))
        if self.throw_exceptions: response.raise_for_status()
        if response.ok: return response.json()

    @security.setter
    def security(self, doc):
        response = self.session.put('_security', data=doc)
        if self.throw_exceptions: response.raise_for_status()



    def save(self, doc, **params):
        """Create a new document or update an existing document.

        If doc has no _id then the server will allocate a random ID and a new
        document will be created. Otherwise the doc's _id will be used to
        identify the document to create or update. Trying to update an existing
        document with an incorrect _rev will raise a ResourceConflict exception.

        Note that it is generally better to avoid saving documents with no _id
        and instead generate document IDs on the client side. This is due to
        the fact that the underlying HTTP ``POST`` method is not idempotent,
        and an automatic retry due to a problem somewhere on the networking
        stack may cause multiple documents being created in the database.

        To avoid such problems you can generate a UUID on the client side.
        Python (since version 2.5) comes with a ``uuid`` module that can be
        used for this::

            from uuid import uuid4
            doc = {'_id': uuid4().hex, 'type': 'person', 'name': 'John Doe'}
            db.save(doc)

        :param doc: the document to store
        :param options: optional args, e.g. batch='ok'
        :return: (id, rev) tuple of the save document
        :rtype: `tuple`
        """
        if '_id' in doc:
            url = urljoin(self.url, doc['_id'])
        else:
            url = self.url
        
        response = self.session.put(url, data=doc, params=params)
        if self.throw_exceptions: response.raise_for_status()
        elif not response.ok: return

        data = response.json()
        id, rev = data['id'], data.get('rev')
        doc['_id'] = id
        if rev is not None: # Not present for batch='ok'
            doc['_rev'] = rev
        return id, rev

    def cleanup(self):
        """Clean up old design document indexes.

        Remove all unused index files from the database storage area.

        :return: a boolean to indicate successful cleanup initiation
        :rtype: `bool`
        """
        response = self.session.post(urljoin(self.url, '_view_cleanup'))
        if self.throw_exceptions: response.raise_for_status()
        return response.ok

    def commit(self):
        """If the server is configured to delay commits, or previous requests
        used the special ``X-Couch-Full-Commit: false`` header to disable
        immediate commits, this method can be used to ensure that any
        non-committed changes are committed to physical storage.
        """
        response = self.session.post(urljoin(self.url, '_ensure_full_commit'))
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def compact(self, ddoc=None):
        """Compact the database or a design document's index.

        Without an argument, this will try to prune all old revisions from the
        database. With an argument, it will compact the index cache for all
        views in the design document specified.

        :return: a boolean to indicate whether the compaction was initiated
                 successfully
        :rtype: `bool`
        """
        url = urljoin(self.url, '_compact')
        if ddoc:
            url = urljoin(url, ddoc)
        
        response = self.session.post(url)
        if self.throw_exceptions: response.raise_for_status()
        return response.ok

    def copy(self, src, dest):
        """Copy the given document to create a new document.

        :param src: the ID of the document to copy, or a dictionary or
                    `Document` object representing the source document.
        :param dest: either the destination document ID as string, or a
                     dictionary or `Document` instance of the document that
                     should be overwritten.
        :return: the new revision of the destination document
        :rtype: `str`
        :since: 0.6
        """
        if not isinstance(src, util.strbase):
            if not isinstance(src, dict):
                if hasattr(src, 'items'):
                    src = dict(src.items())
                else:
                    raise TypeError('expected dict or string, got %s' %
                                    type(src))
            src = src['_id']

        if not isinstance(dest, util.strbase):
            if not isinstance(dest, dict):
                if hasattr(dest, 'items'):
                    dest = dict(dest.items())
                else:
                    raise TypeError('expected dict or string, got %s' %
                                    type(dest))
            if '_rev' in dest:
                dest = '%s?%s' % (urlquote(dest['_id']),
                                  urlencode({'rev': dest['_rev']}))
            else:
                dest = urlquote(dest['_id'])

        response = self.session.request('COPY', src, headers={'Destination': dest})
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        return data['rev']

    def delete(self, doc):
        """Delete the given document from the database.

        Use this method in preference over ``__del__`` to ensure you're
        deleting the revision that you had previously retrieved. In the case
        the document has been updated since it was retrieved, this method will
        raise a `ResourceConflict` exception.

        >>> server = Server()
        >>> db = server.create('python-tests')

        >>> doc = dict(type='Person', name='John Doe')
        >>> db['johndoe'] = doc
        >>> doc2 = db['johndoe']
        >>> doc2['age'] = 42
        >>> db['johndoe'] = doc2
        >>> db.delete(doc) # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        ResourceConflict: (u'conflict', u'Document update conflict.')

        >>> del server['python-tests']

        :param doc: a dictionary or `Document` object holding the document data
        :return: a bool indicaating if the deleting was a success
        :raise ResourceConflict: if the document was updated in the database
        :since: 0.4.1
        """
        if doc['_id'] is None:
            raise ValueError('document ID cannot be None')
        response = self.session.delete(urljoin(self.resource, doc['_id']), rev=doc['_rev'])
        if self.throw_exceptions: response.raise_for_status()
        return response.ok

    def get(self, id, default=None, **options):
        """Return the document with the specified ID.

        :param id: the document ID
        :param default: the default value to return when the document is not
                        found. If set, this prevents an exception from being
                        thrown for 404 errors even if self.throw_exceptions is True
        :return: a `Document` object representing the requested document, or `None`
                 if no document with the ID was found
        :rtype: `Document`
        """
        response = self.session.get(urljoin(self.url, id))
        if not response.status_code == 404 and default is not None: return default
        if self.throw_exceptions: response.raise_for_status()
        return Document(response.json())

    def revisions(self, id, **options):
        """Generator to yield all available revisions of the given document.

        :param id: the document ID
        :return: an iterator over Document objects, each a different revision,
                 in reverse chronological order, if any were found
        """
        data = self.get(id, revs=True)

        #TODO I don't know that the following code is correct with current version of CouchDB
        startrev = data['_revisions']['start']
        for index, rev in enumerate(data['_revisions']['ids']):
            options['rev'] = '%d-%s' % (startrev - index, rev)
            revision = self.get(id, **options)
            if revision is None:
                return
            yield revision

    def info(self, ddoc=None):
        """Return information about the database or design document as a
        dictionary.

        Without an argument, returns database information. With an argument,
        return information for the given design document.

        The returned dictionary exactly corresponds to the JSON response to
        a ``GET`` request on the database or design document's info URI.

        :return: a dictionary of database properties
        :rtype: ``dict``
        :since: 0.4
        """
        url = self.url
        if ddoc is not None:
            url = urljoin(url, '_design', ddoc, '_info')

        response = self.session.get(url)
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()

        if ddoc is None:
            self._name = data['db_name']
        return data

    def delete_attachment(self, doc, filename):
        """Delete the specified attachment.

        Note that the provided `doc` is required to have a ``_rev`` field.
        Thus, if the `doc` is based on a view row, the view row would need to
        include the ``_rev`` field.

        :param doc: the dictionary or `Document` object representing the
                    document that the attachment belongs to
        :param filename: the name of the attachment file
        :since: 0.4.1
        """
        url = urljoin(self.url, doc['_id'], filename)
        response = self.session.get(url, params={'rev': doc['_rev']})
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        doc['_rev'] = data['rev']

    def get_attachment(self, id_or_doc, filename, default=None):
        """Return an attachment from the specified doc id and filename.

        :param id_or_doc: either a document ID or a dictionary or `Document`
                          object representing the document that the attachment
                          belongs to
        :param filename: the name of the attachment file
        :param default: default value to return when the document or attachment
                        is not found
        :return: a file-like object with read and close methods, or the value
                 of the `default` argument if the attachment is not found
        :since: 0.4.1
        """
        if isinstance(id_or_doc, util.strbase):
            id = id_or_doc
        else:
            id = id_or_doc['_id']
        
        url = urljoin(self.url, id, filename)
        response = self.session.get(url)
        if response.status_code == 404 and default is not None: return default
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def put_attachment(self, doc, content, filename=None, content_type=None):
        """Create or replace an attachment.

        Note that the provided `doc` is required to have a ``_rev`` field. Thus,
        if the `doc` is based on a view row, the view row would need to include
        the ``_rev`` field.

        :param doc: the dictionary or `Document` object representing the
                    document that the attachment should be added to
        :param content: the content to upload, either a file-like object or
                        a string
        :param filename: the name of the attachment file; if omitted, this
                         function tries to get the filename from the file-like
                         object passed as the `content` argument value
        :param content_type: content type of the attachment; if omitted, the
                             MIME type is guessed based on the file name
                             extension
        :since: 0.4.1
        """
        if filename is None:
            if hasattr(content, 'name'):
                filename = os.path.basename(content.name)
            else:
                raise ValueError('no filename specified for attachment')
        if content_type is None:
            content_type = ';'.join(
                filter(None, mimetypes.guess_type(filename))
            )

        url = urljoin(self.url, doc['_id'], filename)
        response = self.session.put(
            url, 
            content, 
            headers={
                'Content-Type': content_type
            },
            params={
                'rev': doc['_rev']
            }
        )
        
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        doc['_rev'] = data['rev']

    def find(self, mango_query, wrapper=None):
        """Execute a mango find-query against the database.

        Note: only available for CouchDB version >= 2.0.0

        More information on the `mango_query` structure can be found here:
          http://docs.couchdb.org/en/master/api/database/find.html#find-selectors

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> db['johndoe'] = dict(type='Person', name='John Doe')
        >>> db['maryjane'] = dict(type='Person', name='Mary Jane')
        >>> db['gotham'] = dict(type='City', name='Gotham City')
        >>> mango = {'selector': {'type': 'Person'},
        ...          'fields': ['name'],
        ...          'sort':[{'name': 'asc'}]}
        >>> for row in db.find(mango):                          # doctest: +SKIP
        ...    print(row['name'])                               # doctest: +SKIP
        John Doe
        Mary Jane
        >>> del server['python-tests']

        :param mango_query: a dictionary describing criteria used to select
                            documents
        :param wrapper: an optional callable that should be used to wrap the
                        resulting documents
        :return: the query results as a list of `Document` (or whatever `wrapper` returns)
        """
        response = self.session.post(urljoin(self.url, '_find'), json=mango_query, headers = {'Content-Type': 'application/json'})
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        return map(wrapper or Document, data.get('docs', []))

    def explain(self, mango_query):
        """Explain a mango find-query.

        Note: only available for CouchDB version >= 2.0.0

        More information on the `mango_query` structure can be found here:
          http://docs.couchdb.org/en/master/api/database/find.html#db-explain

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> db['johndoe'] = dict(type='Person', name='John Doe')
        >>> db['maryjane'] = dict(type='Person', name='Mary Jane')
        >>> db['gotham'] = dict(type='City', name='Gotham City')
        >>> mango = {'selector': {'type': 'Person'}, 'fields': ['name']}
        >>> db.explain(mango)                          #doctest: +ELLIPSIS +SKIP
        {...}
        >>> del server['python-tests']

        :param mango_query: a `dict` describing criteria used to select
                            documents
        :return: the query results as a list of `Document` (or whatever
                 `wrapper` returns)
        :rtype: `dict`
        """
        response = self.session.post(urljoin(self.url, '_explain'), mango_query)
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def index(self): #TODO need to update the Indexes class first
        """Get an object to manage the database indexes.

        :return: an `Indexes` object to manage the databes indexes
        :rtype: `Indexes`
        """
        return Indexes(self.resource('_index'))



    def bulk_update(self, documents, **options):
        """Perform a bulk update or insertion of the given documents using a
        single HTTP request.

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> for doc in db.update([
        ...     Document(type='Person', name='John Doe'),
        ...     Document(type='Person', name='Mary Jane'),
        ...     Document(type='City', name='Gotham City')
        ... ]):
        ...     print(repr(doc)) #doctest: +ELLIPSIS
        (True, u'...', u'...')
        (True, u'...', u'...')
        (True, u'...', u'...')

        >>> del server['python-tests']

        The return value of this method is a list containing a tuple for every
        element in the `documents` sequence. Each tuple is of the form
        ``(success, docid, rev_or_exc)``, where ``success`` is a boolean
        indicating whether the update succeeded, ``docid`` is the ID of the
        document, and ``rev_or_exc`` is either the new document revision, or
        an exception instance (e.g. `ResourceConflict`) if the update failed.

        If an object in the documents list is not a dictionary, this method
        looks for an ``items()`` method that can be used to convert the object
        to a dictionary. Effectively this means you can also use this method
        with `mapping.Document` objects.

        :param documents: a sequence of dictionaries or `Document` objects, or
                          objects providing a ``items()`` method that can be
                          used to convert them to a dictionary
        :return: The decoded JSON response from CouchDB
        :rtype: ``list``

        :since: version 0.2
        """
        docs = []
        for doc in documents:
            if isinstance(doc, dict):
                docs.append(doc)
            elif hasattr(doc, 'items'):
                docs.append(dict(doc.items()))
            else:
                raise TypeError('expected dict, got %s' % type(doc))

        content = options
        content.update(docs=docs)
        response = self.session.post('_bulk_docs', content)
        if self.throw_exceptions: response.raise_for_status()
        return reponse.json()

    def purge(self, docs):
        """Perform purging (complete removing) of the given documents.

        Uses a single HTTP request to purge all given documents. Purged
        documents do not leave any meta-data in the storage and are not
        replicated.
        """
        content = {}
        for doc in docs:
            if isinstance(doc, dict):
                content[doc['_id']] = [doc['_rev']]
            elif hasattr(doc, 'items'):
                doc = dict(doc.items())
                content[doc['_id']] = [doc['_rev']]
            else:
                raise TypeError('expected dict, got %s' % type(doc))
        response = self.session.post(urljoin(self.url, '_purge'), content)
        if self.throw_exceptions: response.raise_for_status()
        return response.json()

    def view(self, name, wrapper=None, **options): #TODO rewrite the PermanentView class before touchthing this method
        """Execute a predefined view.

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> db['gotham'] = dict(type='City', name='Gotham City')

        >>> for row in db.view('_all_docs'):
        ...     print(row.id)
        gotham

        >>> del server['python-tests']

        :param name: the name of the view; for custom views, use the format
                     ``design_docid/viewname``, that is, the document ID of the
                     design document and the name of the view, separated by a
                     slash
        :param wrapper: an optional callable that should be used to wrap the
                        result rows
        :param options: optional query string parameters
        :return: the view results
        :rtype: `ViewResults`
        """
        
        response = self.session.get(urljoin(self.url, name), params=options)
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        
        include_docs = 'include_docs' in options and options['include_docs']
        wrapper = wrapper or Document

        for row in data.get('rows', []):
            if include_docs:
                yield wrapper(row['doc'])
            else:
                yield row

    def iterview(self, name, batch, wrapper=None, **options):
        """Iterate the rows in a view, fetching rows in batches and yielding
        one row at a time.

        Since the view's rows are fetched in batches any rows emitted for
        documents added, changed or deleted between requests may be missed or
        repeated.

        :param name: the name of the view; for custom views, use the format
                     ``design_docid/viewname``, that is, the document ID of the
                     design document and the name of the view, separated by a
                     slash.
        :param batch: number of rows to fetch per HTTP request.
        :param wrapper: an optional callable that should be used to wrap the
                        result rows
        :param options: optional query string parameters
        :return: row generator
        """
        # Check sane batch size.
        if batch <= 0:
            raise ValueError('batch must be 1 or more')
        # Save caller's limit, it must be handled manually.
        limit = options.get('limit')
        if limit is not None and limit <= 0:
            raise ValueError('limit must be 1 or more')
        while True:

            loop_limit = min(limit or batch, batch)
            # Get rows in batches, with one extra for start of next batch.
            options['limit'] = loop_limit + 1
            rows = list(self.view(name, wrapper, **options))

            # Yield rows from this batch.
            for row in itertools.islice(rows, loop_limit):
                yield row

            # Decrement limit counter.
            if limit is not None:
                limit -= min(len(rows), batch)

            # Check if there is nothing else to yield.
            if len(rows) <= batch or (limit is not None and limit == 0):
                break

            # Update options with start keys for next loop.
            options.update(startkey=rows[-1]['key'],
                           startkey_docid=rows[-1]['id'], skip=0)

    def show(self, name, docid=None, **options):
        """Call a 'show' function.

        :param name: the name of the show function in the format
                     ``designdoc/showname``
        :param docid: optional ID of a document to pass to the show function.
        :param options: optional query string parameters
        :return: (headers, body) tuple, where headers is a dict of headers
                 returned from the show function and body is a readable
                 file-like instance
        """
        path = _path_from_name(name, '_show')
        if docid:
            path.append(docid)
        status, headers, body = self.resource(*path).get(**options)
        return headers, body

    def list(self, name, view, **options):
        """Format a view using a 'list' function.

        :param name: the name of the list function in the format
                     ``designdoc/listname``
        :param view: the name of the view in the format ``designdoc/viewname``
        :param options: optional query string parameters
        :return: (headers, body) tuple, where headers is a dict of headers
                 returned from the list function and body is a readable
                 file-like instance
        """
        path = _path_from_name(name, '_list')
        path.extend(view.split('/', 1))
        _, headers, body = _call_viewlike(self.resource(*path), options)
        return headers, body

    def update_doc(self, name, docid=None, **options):
        """Calls server side update handler.

        :param name: the name of the update handler function in the format
                     ``designdoc/updatename``.
        :param docid: optional ID of a document to pass to the update handler.
        :param options: additional (optional) params to pass to the underlying
                        http resource handler, including ``headers``, ``body``,
                        and ```path```. Other arguments will be treated as
                        query string params. See :class:`couchdb.http.Resource`
        :return: (headers, body) tuple, where headers is a dict of headers
                 returned from the list function and body is a readable
                 file-like instance
        """
        path = _path_from_name(name, '_update')
        if docid is None:
            func = self.resource(*path).post
        else:
            path.append(docid)
            func = self.resource(*path).put
        _, headers, body = func(**options)
        return headers, body

    def _changes(self, **opts):
        # use streaming `get` and `post` methods
        if opts.get('filter') == '_selector':
            selector = opts.pop('_selector', None)
            _, _, data = self.resource.post('_changes', selector, **opts)
        else:
            _, _, data = self.resource.get('_changes', **opts)
        lines = data.iterchunks()
        for ln in lines:
            if not ln: # skip heartbeats
                continue
            doc = json.decode(ln.decode('utf-8'))
            if 'last_seq' in doc: # consume the rest of the response if this
                for ln in lines:  # was the last line, allows conn reuse
                    pass
            yield doc

    def changes(self, **opts):
        """Retrieve a changes feed from the database.

        :param opts: optional query string parameters
        :return: an iterable over change notification dicts
        """
        if opts.get('feed') == 'continuous':
            return self._changes(**opts)

        if opts.get('filter') == '_selector':
            selector = opts.pop('_selector', None)
            _, _, data = self.resource.post_json('_changes', selector, **opts)
        else:
            _, _, data = self.resource.get_json('_changes', **opts)
        return data


def _doc_resource(base, doc_id):
    """Return the resource for the given document id.
    """
    # Split an id that starts with a reserved segment, e.g. _design/foo, so
    # that the / that follows the 1st segment does not get escaped.
    if doc_id[:1] == '_':
        return base(*doc_id.split('/', 1))
    return base(doc_id)


def _path_from_name(name, type):
    """Expand a 'design/foo' style name to its full path as a list of
    segments.
    """
    if name.startswith('_'):
        return name.split('/')
    design, name = name.split('/', 1)
    return ['_design', design, type, name]


class Document(dict):
    """Representation of a document in the database.

    This is basically just a dictionary with the two additional properties
    `id` and `rev`, which contain the document ID and revision, respectively.
    """

    def __repr__(self):
        return '<%s %r@%r %r>' % (type(self).__name__, self.id, self.rev,
                                  dict([(k,v) for k,v in self.items()
                                        if k not in ('_id', '_rev')]))

    @property
    def id(self):
        """The document ID.

        :rtype: basestring
        """
        return self.get('_id')


    @property
    def rev(self):
        """The document revision.

        :rtype: basestring
        """
        return self.get('_rev')


class View(object):
    """Abstract representation of a view or query."""

    def __init__(self, url, wrapper=None, session=None):
        if isinstance(url, util.strbase):
            self.resource = http.Resource(url, session)
        else:
            self.resource = url
        self.wrapper = wrapper

    def __call__(self, **options):
        return ViewResults(self, options)

    def __iter__(self):
        return iter(self())

    def _exec(self, options):
        raise NotImplementedError


class PermanentView(View):
    """Representation of a permanent view on the server."""

    def __init__(self, uri, name, wrapper=None, session=None):
        View.__init__(self, uri, wrapper=wrapper, session=session)
        self.name = name

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.name)

    def _exec(self, options):
        _, _, data = _call_viewlike(self.resource, options)
        return data


class TemporaryView(View):
    """Representation of a temporary view."""

    def __init__(self, uri, map_fun, reduce_fun=None,
                 language='javascript', wrapper=None, session=None):
        View.__init__(self, uri, wrapper=wrapper, session=session)
        if isinstance(map_fun, FunctionType):
            map_fun = getsource(map_fun).rstrip('\n\r')
        self.map_fun = dedent(map_fun.lstrip('\n\r'))
        if isinstance(reduce_fun, FunctionType):
            reduce_fun = getsource(reduce_fun).rstrip('\n\r')
        if reduce_fun:
            reduce_fun = dedent(reduce_fun.lstrip('\n\r'))
        self.reduce_fun = reduce_fun
        self.language = language

    def __repr__(self):
        return '<%s %r %r>' % (type(self).__name__, self.map_fun,
                               self.reduce_fun)

    def _exec(self, options):
        body = {'map': self.map_fun, 'language': self.language}
        if self.reduce_fun:
            body['reduce'] = self.reduce_fun
        if 'keys' in options:
            options = options.copy()
            body['keys'] = options.pop('keys')
        content = json.encode(body).encode('utf-8')
        _, _, data = self.resource.post_json(body=content, headers={
            'Content-Type': 'application/json'
        }, **_encode_view_options(options))
        return data


def _encode_view_options(options):
    """Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}
    for name, value in options.items():
        if name in ('key', 'startkey', 'endkey') \
                or not isinstance(value, util.strbase):
            value = json.encode(value)
        retval[name] = value
    return retval


def _call_viewlike(resource, options):
    """Call a resource that takes view-like options.
    """
    if 'keys' in options:
        options = options.copy()
        keys = {'keys': options.pop('keys')}
        return resource.post_json(body=keys, **_encode_view_options(options))
    else:
        return resource.get_json(**_encode_view_options(options))


class ViewResults(object):
    """Representation of a parameterized view (either permanent or temporary)
    and the results it produces.

    This class allows the specification of ``key``, ``startkey``, and
    ``endkey`` options using Python slice notation.

    >>> server = Server()
    >>> db = server.create('python-tests')
    >>> db['johndoe'] = dict(type='Person', name='John Doe')
    >>> db['maryjane'] = dict(type='Person', name='Mary Jane')
    >>> db['gotham'] = dict(type='City', name='Gotham City')
    >>> map_fun = '''function(doc) {
    ...     emit([doc.type, doc.name], doc.name);
    ... }'''
    >>> results = db.query(map_fun)

    At this point, the view has not actually been accessed yet. It is accessed
    as soon as it is iterated over, its length is requested, or one of its
    `rows`, `total_rows`, or `offset` properties are accessed:

    >>> len(results)
    3

    You can use slices to apply ``startkey`` and/or ``endkey`` options to the
    view:

    >>> people = results[['Person']:['Person','ZZZZ']]
    >>> for person in people:
    ...     print(person.value)
    John Doe
    Mary Jane
    >>> people.total_rows, people.offset
    (3, 1)

    Use plain indexed notation (without a slice) to apply the ``key`` option.
    Note that as CouchDB makes no claim that keys are unique in a view, this
    can still return multiple rows:

    >>> list(results[['City', 'Gotham City']])
    [<Row id=u'gotham', key=[u'City', u'Gotham City'], value=u'Gotham City'>]

    >>> del server['python-tests']
    """

    def __init__(self, view, options):
        self.view = view
        self.options = options
        self._rows = self._total_rows = self._offset = self._update_seq = None

    def __repr__(self):
        return '<%s %r %r>' % (type(self).__name__, self.view, self.options)

    def __getitem__(self, key):
        options = self.options.copy()
        if type(key) is slice:
            if key.start is not None:
                options['startkey'] = key.start
            if key.stop is not None:
                options['endkey'] = key.stop
            return ViewResults(self.view, options)
        else:
            options['key'] = key
            return ViewResults(self.view, options)

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def _fetch(self):
        data = self.view._exec(self.options)
        wrapper = self.view.wrapper or Row
        self._rows = [wrapper(row) for row in data['rows']]
        self._total_rows = data.get('total_rows')
        self._offset = data.get('offset', 0)
        self._update_seq = data.get('update_seq')

    @property
    def rows(self):
        """The list of rows returned by the view.

        :rtype: `list`
        """
        if self._rows is None:
            self._fetch()
        return self._rows

    @property
    def total_rows(self):
        """The total number of rows in this view.

        This value is `None` for reduce views.

        :rtype: `int` or ``NoneType`` for reduce views
        """
        if self._rows is None:
            self._fetch()
        return self._total_rows

    @property
    def offset(self):
        """The offset of the results from the first row in the view.

        This value is 0 for reduce views.

        :rtype: `int`
        """
        if self._rows is None:
            self._fetch()
        return self._offset

    @property
    def update_seq(self):
        """The database update sequence that the view reflects.

        The update sequence is included in the view result only when it is
        explicitly requested using the `update_seq=true` query option.
        Otherwise, the value is None.

        :rtype: `int` or `NoneType` depending on the query options
        """
        if self._rows is None:
            self._fetch()
        return self._update_seq


class Row(dict):
    """Representation of a row as returned by database views."""

    def __repr__(self):
        keys = 'id', 'key', 'doc', 'error', 'value'
        items = ['%s=%r' % (k, self[k]) for k in keys if k in self]
        return '<%s %s>' % (type(self).__name__, ', '.join(items))

    @property
    def id(self):
        """The associated Document ID if it exists. Returns `None` when it
        doesn't (reduce results).
        """
        return self.get('id')

    @property
    def key(self):
        return self['key']

    @property
    def value(self):
        return self.get('value')

    @property
    def error(self):
        return self.get('error')

    @property
    def doc(self):
        """The associated document for the row. This is only present when the
        view was accessed with ``include_docs=True`` as a query parameter,
        otherwise this property will be `None`.
        """
        doc = self.get('doc')
        if doc:
            return Document(doc)


class Indexes(object):
    """Manage indexes in CouchDB 2.0.0 and later.

    More information here:
        http://docs.couchdb.org/en/2.0.0/api/database/find.html#db-index
    """

    def __init__(self, url, session=None):
        if isinstance(url, util.strbase):
            self.resource = http.Resource(url, session)
        else:
            self.resource = url

    def __setitem__(self, ddoc_name, index):
        """Add an index to the database.

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> db['johndoe'] = dict(type='Person', name='John Doe')
        >>> db['maryjane'] = dict(type='Person', name='Mary Jane')
        >>> db['gotham'] = dict(type='City', name='Gotham City')
        >>> idx = db.index()
        >>> idx['foo', 'bar'] = [{'type': 'asc'}]                #doctest: +SKIP
        >>> list(idx)                                           #doctest: +SKIP
        [{'ddoc': None,
          'def': {'fields': [{'_id': 'asc'}]},
          'name': '_all_docs',
          'type': 'special'},
         {'ddoc': '_design/foo',
          'def': {'fields': [{'type': 'asc'}]},
          'name': 'bar',
          'type': 'json'}]
        >>> idx[None, None] = [{'type': 'desc'}]      #doctest: +SKIP
        >>> list(idx)                                 #doctest: +SKIP, +ELLIPSIS
        [{'ddoc': None,
          'def': {'fields': [{'_id': 'asc'}]},
          'name': '_all_docs',
          'type': 'special'},
         {'ddoc': '_design/...',
          'def': {'fields': [{'type': 'desc'}]},
          'name': '...',
          'type': 'json'},
         {'ddoc': '_design/foo',
          'def': {'fields': [{'type': 'asc'}]},
          'name': 'bar',
          'type': 'json'}]
        >>> del server['python-tests']

        :param index: `list` of indexes to create
        :param ddoc_name: `tuple` or `list` containing first the name of the
                          design document, in which the index will be created,
                          and second name of the index. Both can be `None`.
        """
        query = {'index': {'fields': index}}
        ddoc, name = ddoc_name  # expect ddoc / name to be a slice or list
        if ddoc:
            query['ddoc'] = ddoc
        if name:
            query['name'] = name
        self.resource.post_json(body=query)

    def __delitem__(self, ddoc_name):
        """Remove an index from the database.

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> db['johndoe'] = dict(type='Person', name='John Doe')
        >>> db['maryjane'] = dict(type='Person', name='Mary Jane')
        >>> db['gotham'] = dict(type='City', name='Gotham City')
        >>> idx = db.index()
        >>> idx['foo', 'bar'] = [{'type': 'asc'}]                #doctest: +SKIP
        >>> del idx['foo', 'bar']                                #doctest: +SKIP
        >>> list(idx)                                            #doctest: +SKIP
        [{'ddoc': None,
          'def': {'fields': [{'_id': 'asc'}]},
          'name': '_all_docs',
          'type': 'special'}]
        >>> del server['python-tests']

        :param ddoc: name of the design document containing the index
        :param name: name of the index that is to be removed
        :return: `dict` containing the `id`, the `name` and the `result` of
                 creating the index
        """
        self.resource.delete_json([ddoc_name[0], 'json', ddoc_name[1]])

    def _list(self):
        _, _, data = self.resource.get_json()
        return data

    def __iter__(self):
        """Iterate all indexes of the associated database.

        >>> server = Server()
        >>> db = server.create('python-tests')
        >>> idx = db.index()
        >>> list(idx)                                            #doctest: +SKIP
        [{'ddoc': None,
          'def': {'fields': [{'_id': 'asc'}]},
          'name': '_all_docs',
          'type': 'special'}]
        >>> del server['python-tests']

        :return: iterator yielding `dict`'s describing each index
        """
        return iter(self._list()['indexes'])
