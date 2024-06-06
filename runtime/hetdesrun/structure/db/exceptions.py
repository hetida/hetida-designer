class DBError(Exception):
    pass


class DBIntegrityError(DBError):
    pass


class DBNotFoundError(DBError):
    pass
