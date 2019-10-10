CouchDB-Python Library
======================


**This is a fork or the `original`_ Python CouchDB Library. The old library is no longer fully compatible with the current version of couchdb. This is a work in progress as the underlying code looks like it will probably need major updates.**

Original `documentation`_ 

This package currently encompasses four primary modules:

* ``couchdb.client``: the basic client library
* ``couchdb.design``: management of design documents
* ``couchdb.mapping``: a higher-level API for mapping between CouchDB documents and Python objects
* ``couchdb.view``: a CouchDB view server that allows writing view functions in Python


**Please note that this is very much a work in progress in modernizing this library. The basics seem to all be functioning for me now, but it is far from being done or well tested. Please feel free to use and to help fix bugs! But be aware some things are almost certainly still broken.**

Completed Tasks
---------------

1. Fixed ``Server.login()``. You can now actually log into the server
2. Basic tasks such as fetching a document or creating a database work again after I broke them during item 1
3. Queries and _all_docs seem to work now, with limited testing
4. ``couchdb.mapping`` was tested, seems to work without much modification.

In-Progress Tasks
-----------------

1. Remove legacy code for Python 2.x
2. Migrate code to uses the Requests library rather than having its own HTTP Client 
3. Views and _all_docs need updated

Future Tasks
-------------

1. Once I have the basic updates to ``couchdb.client`` done, test and, if needed, update ``couchdb.mapping``.
2. Update documentation
3. Update automated tests
4. Low priority, but eventually I will test and, if needed, update ``couchbd.design``

.. _original: https://github.com/djc/couchdb-python
.. _documentation: http://couchdb-python.readthedocs.io/en/latest/
