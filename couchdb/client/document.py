
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
    def id(self) -> str:
        """The document ID.

        :rtype: basestring
        """
        return self.get('_id')


    @property
    def rev(self) -> str:
        """The document revision.

        :rtype: basestring
        """
        return self.get('_rev')
