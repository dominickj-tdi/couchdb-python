"""
Simple peformance tests.
"""

import sys
import time

import couchdb


def main(username=None, password=None):

    tests = [create_doc, create_bulk_docs]
    if len(sys.argv) > 1:
        tests = [test for test in tests if test.__name__ in sys.argv[1:]]

    server = couchdb.Server()

    if username is not None and password is not None:
        server.login(username, password)

    for test in tests:
        _run(server, test)


def _run(server, func):
    """Run a test in a clean db and log its execution time."""
    print("* [%s] %s ... " % (func.__name__, func.__doc__.strip()))

    db_name = 'couchdb-python-perftest'
    db = server.create(db_name)
    try:
        try:
            start = time.time()
            func(db)
            stop = time.time()
            print("%0.2fs\n" % (stop - start,))

        except Exception as e:
            print("FAILED - %r\n" % (str(e),))
    finally:
        server.delete(db_name)


def create_doc(db):
    """Create lots of docs, one at a time"""
    for i in range(1000):
        db.save({'_id': str(i)})


def create_bulk_docs(db):
    """Create lots of docs, lots at a time"""
    batch_size = 100
    num_batches = 1000
    for i in range(num_batches):
        db.update([{'_id': str((i * batch_size) + j)} for j in range(batch_size)])


if __name__ == '__main__':
    main(*sys.argv[1:])
