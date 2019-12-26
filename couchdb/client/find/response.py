from ..document import Document


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





