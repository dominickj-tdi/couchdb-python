from .__common__ import *
from .document import Document

class View(object):
    """Abstract representation of a view or query."""

    def __init__(self, url, wrapper=None, session=None):
        self.url = url
        self.wrapper = wrapper
        self.session = session or requests.Session()

    def __call__(self, **options):
        return ViewResults(self, options)

    def __iter__(self):
        return iter(self())

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.url)

    def _exec(self, options):
        return _call_viewlike(self.url, self.session, options)


def _encode_view_options(options):
    """Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}
    for name, value in options.items():
        if name in ('key', 'startkey', 'endkey') \
                or not isinstance(value, util.strbase):
            value = json.dumps(value)
        retval[name] = value
    return retval


def _call_viewlike(url: str, session: requests.Session, options):
    """Call a resource that takes view-like options.
    """
    if 'keys' in options:
        options = options.copy()
        keys = {'keys': options.pop('keys')}
        response = session.post(url, json=keys, params=_encode_view_options(options))
    else:
        response = session.get(url, params = _encode_view_options(options))
    return response.json()


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
