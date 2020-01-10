from ..__common__ import requests
from ..exceptions import *
from .response import FindResponse
from .query import FindQuery


class Find:
    def __init__(
        self, 
        url, 
        query, 
        wrapper=None, 
        session: requests.Session = None,
        auto_paginate: bool = False
        ):
        self.query = query
        self.url = url
        self.wrapper = wrapper
        self.session = session or requests.Session()
        self.auto_paginate = auto_paginate
    

    def __iter__(self):
        return FindIterator(self)


    def execute(self, bookmark=None) -> FindResponse:
        if bookmark is None:
            q = self.query
        else:
            q = FindQuery(**self.query)
            q.bookmark = bookmark
        

        response = self.session.post(self.url, json=q, headers = {'Content-Type': 'application/json'})
        if not response.ok: raise CouchDBException.auto(response.json())
        data = response.json()
        return FindResponse(data, self.wrapper)

# This must be imported after the class definition because cyclical imports
from .iterator import FindIterator