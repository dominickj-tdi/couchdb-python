from .__common__ import *
from .database import Database
from .exceptions import *
from typing import Generator, Iterable

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

    def __init__(self, url: str = DEFAULT_BASE_URL, full_commit: bool = None, session: requests.Session = None):
        """Initialize the server object.

        :param url: the URI of the server (for example
                    ``http://localhost:5984/``)
        :param full_commit: turn on the X-Couch-Full-Commit header
        :param session: an requests.Session instance or None for a default session
        """
        self.session = session or requests.Session()
        self.url = url
        
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
        if not response.ok: raise CouchDBException.auto(response.json())
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
        if not response.ok: raise CouchDBException.auto(response.json())

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
        if not response.ok: raise CouchDBException.auto(response.json())
        return Database(dbUrl, name, self.session)
    

    def all_dbs(self) -> Generator[Database, None, None]:
        """Generator to interate of all databases"""
        response = self.session.get(urljoin(self.url, '_all_dbs'))
        if not response.ok: raise CouchDBException.auto(response.json())
        for dbName in response.json():
            yield Database(urljoin(self.url, dbName), dbName, self.session)

    def config(self) -> dict:
        """The configuration of the CouchDB server.

        The configuration is represented as a nested dictionary of sections and
        options from the configuration files of the server, or the default
        values for options that are not explicitly configured.
        """
        response = self.session.get(urljoin(self.url, '_config'))
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()

    def version(self) -> str:
        """The version string of the CouchDB server.

        Note that this results in a request being made, and can also be used
        to check for the availability of the server.
        """
        response = self.session.get(self.url)
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()['version']

    def version_info(self) -> (int, int, int):
        """The version of the CouchDB server as a tuple of ints.

        Note that this results in a request being made only at the first call.
        Afterwards the result will be cached.
        """
        if self._version_info is None:
            version = self.version()
            self._version_info = tuple(map(int, version.split('.')))
        return self._version_info

    def stats(self, name: str = None):
        """Server statistics.

        :param name: name of single statistic, e.g. httpd/requests
                     (None -- return all statistics)
        """
        url = urljoin(self.url, '_local/_stats')
        if name: url = urljoin(url, name)
        
        response = self.session.get(url)
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()

    def tasks(self) -> dict:
        """A list of tasks currently active on the server."""
        response = self.session.get(urljoin(self.url, '_active_tasks'))
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()

    def uuids(self, count=None) -> Iterable[str]:
        """Retrieve a batch of uuids

        :param count: a number of uuids to fetch
                      (None -- get as many as the server sends)
        :return: a list of uuids
        """
        response = self.session.get(
            urljoin(self.url, '_uuids'), 
            params = {'count': count} if count is not None else None
        )
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()['uuids']

    def create(self, name) -> Database:
        """Create a new database with the given name.

        :param name: the name of the database
        :return: a `Database` object representing the created database
        """
        dbUrl = urljoin(self.url, name)
        response = self.session.put(dbUrl) 
        if not response.ok: raise CouchDBException.auto(response.json())
        return Database(dbUrl, name, self.session)

    def delete(self, name):
        """Delete the database with the specified name.

        :param name: the name of the database
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
        response = self.session.post(urljoin(self.url, '_replicate'), json=data)
        if not response.ok: raise CouchDBException.auto(response.json())
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
        response = self.session.post(urljoin(self.url, '_session'), json={
            'name': name,
            'password': password,
        })
        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()

    def logout(self, token):
        """Logout regular user in couch db

        :param token: token of login user
        """
        header = {
            'Accept': 'application/json'
        }
        response = self.session.delete(urljoin(self.url, '_session'), headers=header)
        if not response.ok: raise CouchDBException.auto(response.json())

    def verify_token(self, token=None):
        """Verify user token

        :param token: authentication token
        :return: True if authenticated ok
        :rtype: bool
        """
        if token is not None:
            self.session.cookies.set('AuthSession', token, domain=urlparse(self.url).hostname)
            
        response = self.session.get(urljoin(self.url, '_session'))

        return response.ok
    

    def renew_session(self, token=None):
        """ Same as `verify_token`, but returns a user data dict instead of 
        a boolean
        """
        if token is not None:
            self.session.cookies.set('AuthSession', token, domain=urlparse(self.url).hostname)

        response = self.session.get(urljoin(self.url, '_session'))

        if not response.ok: raise CouchDBException.auto(response.json())
        return response.json()['userCtx']
    

    def get_token(self):
        """ Returns the current authentication token for the current session """
        return self.session.cookies.get('AuthSession', domain=urlparse(self.url).hostname)
