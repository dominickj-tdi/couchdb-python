
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
