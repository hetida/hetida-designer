# pylint: disable=duplicate-code


from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.auth_dependency import (
    get_auth_headers as get_generic_rest_adapter_auth_headers,
)
