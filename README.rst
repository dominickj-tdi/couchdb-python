Python CouchDB Client Library
=============================


**This is a fork or the `original`_ Python CouchDB Library. The old library is no longer fully compatible with the current version of couchdb. This is a work in progress as the underlying code looks like it will probably need major updates.**

Original `documentation`_ 

Unlike the original, which encompasses a range of tools and utilities, this library focuses only on being a CouchDB client for Python. Much or the functionality from the original library is available in Fauxton, and that which isn't (Such as the Python view server) I feel would be better as a serperate project.

We also modernize the library, dropping support for Python 2 and legacy versions of CouchDB

**Please note that this is very much a work in progress in modernizing this library. The basics seem to all be functioning for me now, but it is far from being done or well tested. Please feel free to use and to help fix bugs! But be aware some things are almost certainly still broken.**

In-Progress Tasks
-----------------

1. Remove legacy code for Python 2.x (Mostly Done)
2. Migrate code to uses the Requests library rather than having its own HTTP Client (Mostly Done) 


Future Tasks
-------------

1. Use type hinting on all public methods (Better usage in IDEs)
2. Update documentation
3. Update automated tests
4. Redo packaging for PyPi (Likely this will be a new library rather than a new version of the old one)
5. Low priority, but eventually I will update and re-incorperate the Design Doc and Index management capabilities from the original
6. Once the above is done and everything is working well, I'd maybe like to implement some local caching 


Looking to Help?
----------------

Areas where I could use someone to pitch in if you're interested:

1. Testing & Bug Fixing
2. Fix packaging for PyPi
3. Updating Documentation and Tests


.. _original: https://github.com/djc/couchdb-python
.. _documentation: http://couchdb-python.readthedocs.io/en/latest/
