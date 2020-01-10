from collections import defaultdict

class CouchDBException(Exception):
    def __init__(self, error, reason, message=None):
        self.error = error
        self.reason = reason
        super().__init__(message or reason)

    @classmethod
    def auto(cls, data, message=None):
        error = data.get('error')
        reason = data.get('reason')
        return cls.lookup_table[reason](error, reason, message)




class UnauthorizedException(CouchDBException):
    pass

class DocumentConflictException(CouchDBException):
    pass

class NotFoundException(CouchDBException):
    pass


CouchDBException.lookup_table = defaultdict(
    lambda: CouchDBException,
    conflict = DocumentConflictException,
    unauthorized = UnauthorizedException,
    not_found = NotFoundException
)