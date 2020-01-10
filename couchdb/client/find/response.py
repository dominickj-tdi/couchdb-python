from ..document import Document


class FindResponse:

    def __init__(self, response, wrapper=None, page_size=25):
        self._docs = response['docs']
        self.bookmark = response.get('bookmark')
        self.warning = response.get('warning')
        self.execution_stats = response.get('execution_stats')
        self.wrapper = wrapper
        self.has_next_page = self.bookmark is not None and self.count == page_size
    

    @property
    def docs(self):
        return map(self.wrapper or Document, self._docs)
    
    def __iter__(self):
        return iter(self.docs)
    
    @property
    def count(self):
        return len(self._docs)





