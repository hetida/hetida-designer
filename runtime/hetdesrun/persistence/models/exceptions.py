class ModelConstraintViolation(Exception):
    pass


class TypeConflict(ModelConstraintViolation):
    pass


class StateConflict(ModelConstraintViolation):
    pass


class ModifyForbidden(ModelConstraintViolation):
    pass
