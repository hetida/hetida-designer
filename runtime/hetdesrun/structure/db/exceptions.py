class DBError(Exception):
    pass


class DBIntegrityError(DBError):
    pass


class DBNotFoundError(DBError):
    pass


class DBUpdateError(DBError):
    pass


class DBAssociationError(DBError):
    pass


class DBFetchError(DBError):
    pass


class DBInsertError(DBError):
    pass
