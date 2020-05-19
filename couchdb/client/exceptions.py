from collections import defaultdict
from json.decoder import JSONDecodeError

class CouchDBException(Exception):
    def __init__(self, error, reason, message=None):
        self.error = error
        self.reason = reason
        super().__init__(message or reason)

    @classmethod
    def auto(cls, response, message=None):
        try:
            data = response.json()
            error = data.get('error')
            reason = data.get('reason')
        except JSONDecodeError:
            error = 'json'
            reason = f'Invalid data received from server, status code {response.status_code}'
        return cls.lookup_table[reason](error, reason, message)

            




class UnauthorizedException(CouchDBException):
    pass

class DocumentConflictException(CouchDBException):
    pass

class NotFoundException(CouchDBException, KeyError):
    pass


CouchDBException.lookup_table = defaultdict(
    lambda: CouchDBException,
    conflict = DocumentConflictException,
    unauthorized = UnauthorizedException,
    not_found = NotFoundException
)