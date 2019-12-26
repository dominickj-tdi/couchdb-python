from .__common__ import *
from .document import Document
from collections import deque

class FindQuery(dict):
    """Representation of a Mango Query. See https://docs.couchdb.org/en/stable/api/database/find.html
    for details.
    """

    def __init__(self, selector, **options):
        super().__init__(self, selector=selector, **options)
    

    @property
    def selector(self):
        """JSON object describing criteria used to select documents. Required"""
        return self['selector']
    

    @selector.setter
    def selector(self, value):
        self['selector'] = value
    

    @property
    def limit(self):
        """Maximum number of results returned. Default is 25. Optional"""
        return self.get('limit')
    

    @limit.setter
    def limit(self, value):
        if value is None:
            del self['limit']
        else:
            self['limit'] = value
    

    @property
    def skip(self):
        """Skip the first ‘n’ results, where ‘n’ is the value specified. Optional"""
        return self.get('skip')
    

    @skip.setter
    def skip(self, value):
        if value is None:
            del self['skip']
        else:
            self['skip'] = value

    
    @property
    def sort(self):
        """JSON array following sort syntax. Optional"""
        return self.get('sort')
    

    @sort.setter
    def sort(self, value):
        if value is None:
            del self['sort']
        else:
            self['sort'] = value
    

    @property
    def fields(self):
        """JSON array specifying which fields of each object should be returned. If it is 
        omitted, the entire object is returned. Optional
        """
        return self.get('fields')
    

    @fields.setter
    def fields(self, value):
        if value is None:
            del self['fields']
        else:
            self['fields'] = value
    

    @property
    def use_index(self):
        """Instruct a query to use a specific index. Specified either as "<design_document>" 
        or ["<design_document>", "<index_name>"]. Optional
        """
        return self.get('use_index')
    

    @use_index.setter
    def use_index(self, value):
        if value is None:
            del self['use_index']
        else:
            self['use_index'] = value
    

    @property
    def r(self) -> int:
        """Read quorum needed for the result. This defaults to 1, in which case 
        the document found in the index is returned. If set to a higher value,
        each document is read from at least that many replicas before it is 
        returned in the results. This is likely to take more time than using only 
        the document stored locally with the index. Optional, default: 1
        """
        return self.get('r')
    

    @r.setter
    def r(self, value: int):
        if value is None:
            del self['r']
        else:
            self['r'] = value
    

    @property
    def bookmark(self):
        """A string that enables you to specify which page of results you require. 
        Used for paging through result sets. Every query returns an opaque string 
        under the bookmark key that can then be passed back in a query to get the 
        next page of results. If any part of the selector query changes between 
        requests, the results are undefined. Optional, default: null
        """
        return self.get('bookmark')
    

    @bookmark.setter
    def bookmark(self, value):
        if value is None:
            del self['bookmark']
        else:
            self['bookmark'] = value
    

    @property
    def update(self):
        """Whether to update the index prior to returning the result. Default is true. Optional"""
        return self.get('update')
    

    @update.setter
    def update(self, value):
        if value is None:
            del self['update']
        else:
            self['update'] = value
    

    @property
    def stable(self) -> bool:
        """Whether or not the view results should be returned from a “stable” set of shards. Optional"""
        return self.get('stable')
    

    @stable.setter
    def stable(self, value: bool):
        if value is None:
            del self['stable']
        else:
            self['stable'] = value
    

    @property
    def stale(self):
        """Combination of update=false and stable=true options. Possible options: "ok", false (default). Optional"""
        return self.get('stale')
    

    @stale.setter
    def stale(self, value):
        if value is None:
            del self['stale']
        else:
            self['stale'] = value
        
    
    @property
    def execution_stats(self) -> bool:
        """Include execution statistics in the query response. Optional, default: ``false``."""
        return self.get('execution_stats')
    

    @execution_stats.setter
    def execution_stats(self, value: bool):
        if value is None:
            del self['execution_stats']
        else:
            self['execution_stats'] = value



class FindResponse:

    def __init__(self, response, wrapper=None):
        self._docs = response['docs']
        self.bookmark = response.get('bookmark')
        self.warning = response.get('warning')
        self.execution_stats = response.get('execution_stats')
        self.wrapper = wrapper
    

    @property
    def docs(self):
        return map(self.wrapper or Document, self._docs)
    
    @property
    def count(self):
        return len(self._docs)



class Find:
    def __init__(
        self, 
        url, 
        query, 
        wrapper=None, 
        session: requests.Session = None,
        auto_paginate: bool = False,
        throw_exceptions: bool = True
        ):
        self.query = query
        self.url = url
        self.wrapper = wrapper
        self.session = session or requests.Session()
        self.auto_paginate = auto_paginate
        self.throw_exceptions = throw_exceptions
    

    def __iter__(self):
        return FindIterator(self)


    def execute(self, bookmark=None) -> FindResponse:
        if bookmark is None:
            q = self.query
        else:
            q = FindQuery(**self.query)
            q.bookmark = bookmark
        

        response = self.session.post(self.url, json=q, headers = {'Content-Type': 'application/json'})
        if self.throw_exceptions: response.raise_for_status()
        data = response.json()
        return FindResponse(data, self.wrapper)


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


    

