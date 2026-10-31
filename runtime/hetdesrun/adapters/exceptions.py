class AdapterHandlingException(Exception):
    """Exceptions to be used by adapters derive from this exception"""


class AdapterUnknownError(AdapterHandlingException):
    pass


class AdapterConnectionError(AdapterHandlingException):
    pass


class AdapterOutputDataError(AdapterHandlingException):
    """Raise if the adapter cannot handle the data coming from the workflow output"""


class AdapterInputDataError(AdapterHandlingException):
    """Raise if the data received from an adapter for a workflow input is invalid"""


class AdapterClientWiringInvalidError(AdapterHandlingException):
    """Should be raised if wiring cannot be understood by adapter

    For example the expected filters may depend on the ref_id for an input wiring.
    """
