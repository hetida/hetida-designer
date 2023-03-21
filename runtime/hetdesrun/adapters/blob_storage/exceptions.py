from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)


class MissingHierarchyError(AdapterHandlingException):
    """Raise if the hierarchy json cannot be found"""


class StorageAuthenticationError(AdapterConnectionError):
    """Errors around obtaining and refreshing credentials from Storage"""


class StructureObjectNotFound(AdapterHandlingException):
    """Errors around not finding a sink / source / thingnode"""
