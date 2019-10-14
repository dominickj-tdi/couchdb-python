CouchDB-Python Library
======================


**This is a fork or the `original`_ Python CouchDB Library. The old library is no longer fully compatible with the current version of couchdb. This is a work in progress as the underlying code looks like it will probably need major updates.**

Original `documentation`_ 

This package currently encompasses four primary modules:

* ``couchdb.client``: the basic client library
* ``couchdb.design``: management of design documents


**Please note that this is very much a work in progress in modernizing this library. The basics seem to all be functioning for me now, but it is far from being done or well tested. Please feel free to use and to help fix bugs! But be aware some things are almost certainly still broken.**

Completed Tasks
---------------

1. Fixed ``Server.login()``. You can now actually log into the server
2. Basic tasks such as fetching a document or creating a database work again after I broke them during item 1
3. Queries and _all_docs seem to work now, with limited testing
4. Saving documents seems to work as wel, with limited testing
5. Removed ``couchdb.mapping``. Although it seems to work okay, there already exist deidicated libraries (e.g. marshmallow, schematics) for this. Best to simplify this library to do one thing and do it well. 
6. Removed ``couchtb.tools``. You cal already handle replication through Fauxton, and replication provides a superior backup technique anyway. (Backup to another live CouchBD instance)
7. Removed ``couchdb.view``. I would rather see this as a standalone library or utility than built into the client.
8. Removed ``TemporaryView``. These are deprecated in CouchDB, so no need to support them in a new (er, remodedled?) library

In-Progress Tasks
-----------------

1. Remove legacy code for Python 2.x
2. Migrate code to uses the Requests library rather than having its own HTTP Client 
3. Views and _all_docs need updated (in client)
4. Break up the client.py file into multiple modules to make it easier to work with
5. Unify ``View`` and ``PermanentView`` into one class. There's only one type of view now anyway.

Future Tasks
-------------

1. Use type hinting on all public methods (Better usage in IDEs)
2. Update documentation
3. Update automated tests
4. Low priority, but eventually I will test and, if needed, update ``couchbd.design``
5. Once everything is working well, I'd like to implement some local caching 


.. _original: https://github.com/djc/couchdb-python
.. _documentation: http://couchdb-python.readthedocs.io/en/latest/
