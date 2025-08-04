class DBError(Exception):
    pass


class DBIntegrityError(DBError):
    pass


class DBNestingCycleDetected(DBError):
    pass


class DBNotFoundError(DBError):
    pass
