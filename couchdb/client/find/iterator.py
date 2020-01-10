from collections import deque
from .find import Find


class FindIterator:
    def __init__(self, find: Find):
        self.find = find
        self.bookmark = None
        self.queue = deque()
        self.fetch_more()
    

    def fetch_more(self):
        """Fetch more data from the server using the bookmark from the last call"""
        results = self.find.execute(bookmark = self.bookmark)
        self.bookmark = results.bookmark
        self.queue.extend(results.docs)
        self.has_next_page = results.has_next_page
        return self
        

    def __next__(self):
        try:
            return self.queue.popleft()
        except IndexError:
            if self.find.auto_paginate and self.has_next_page:
                self.fetch_more()
                try:
                    return self.queue.popleft()
                except IndexError:
                    pass
        raise StopIteration()


    

