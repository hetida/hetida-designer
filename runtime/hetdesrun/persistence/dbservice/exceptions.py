class DBError(Exception):
    pass


class DBIntegrityError(DBError):
    pass


class DBNotFoundError(DBError):
    pass


class DBBadRequestError(DBError):
    pass


class DBTypeError(DBError):
    pass


class DBUpdateForbidden(DBError):
    pass
