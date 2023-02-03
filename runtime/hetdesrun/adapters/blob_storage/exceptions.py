from hetdesrun.adapters.exceptions import (
    AdapterConnectionError,
    AdapterHandlingException,
)


# rather AdapterConfigurationError -> in mounted hierarchy json or its path
class MissingHierarchyError(AdapterHandlingException):
    pass


# rather AdapterConfigurationError -> in docker compose yml
class InvalidEndpointError(AdapterHandlingException):
    pass


class StorageAuthenticationError(AdapterConnectionError):
    """Errors around obtaining and refreshing credentials from Storage"""


class StructureObjectNotFound(AdapterHandlingException):
    pass


class StructureObjectNotUnique(AdapterHandlingException):
    pass
