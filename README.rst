CouchDB-Python Library
======================


**This is a fork or the `original`_ Python CouchDB Library. The old library is no longer fully compatible with the current version of couchdb. This is a work in progress as the underlying code looks like it will probably need major updates.**

Original `documentation`_ 

This package currently encompasses four primary modules:

* ``couchdb.client``: the basic client library
* ``couchdb.design``: management of design documents
* ``couchdb.mapping``: a higher-level API for mapping between CouchDB documents and Python objects
* ``couchdb.view``: a CouchDB view server that allows writing view functions in Python


** Please note that this is very much a work in progress in modernizing this library. It is broken and so far I have been breaking it more as I update it. Help doing these updates is welcome of course. But don't actually try to use it right now. **

Current plans
-------------

1. Fix login. It is currently broken when attempting to connect to my couchdb instance. Library as is seems to work on public databases okay though.
2. To facillitate that, I will also be dropping support for Python 2.x and updating the library to use the Requests library. Or at very least urllib... I will also drop support for non-standard json libraries and just Python's built-in one.
3. To simplify the library, I will also drop the dump/load/replicate tools. Other tools exist for doing this stuff, we just want a simple couchdb library for python.
4. Once I have the basic updates to `couchdb.client` done, test and, if needed, update `couchdb.mapping`.
5. Low priority, but eventually I will test and, if needed, update `couchbd.design` and `couchdb.view`

.. _original: https://github.com/djc/couchdb-python
.. _documentation: http://couchdb-python.readthedocs.io/en/latest/
