from collections import deque
from .find import Find


class FindIterator:
    def __init__(self, find: Find):
        self.find = find
        self.bookmark = None
        self.warning = None
        self.execution_stats = None
        self.queue = deque()
        self.fetch_more()
    

    def fetch_more(self):
        """Fetch more data from the server using the bookmark from the last call"""
        results = self.find.execute(bookmark = self.bookmark)
        self.bookmark = results.bookmark
        self.queue.extend(results.docs)
        self.hasMorePages = self.bookmark is not None and results.count == (self.find.query.get('limit') or 25)
        return self
        

    def __next__(self):
        try:
            return self.queue.popleft()
        except IndexError:
            if self.find.auto_paginate and self.hasMorePages:
                self.fetch_more()
                return self.__next__()
            else:
                raise StopIteration()


    

