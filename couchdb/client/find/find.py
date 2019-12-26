from ..__common__ import requests
from .response import FindResponse
from .iterator import FindIterator
from .query import FindQuery


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

