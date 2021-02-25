import os
from enum import Enum
from typing import Optional
from pydantic import BaseSettings, Field, validator  # pylint: disable=no-name-in-module


class LogLevel(str, Enum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTESET = "NOTSET"


class RuntimeConfig(BaseSettings):
    """Configuration for Hetida Designer Runtime

    There is an example .env file /runtime/settings/example.env
    """

    log_level: LogLevel = Field(
        LogLevel.INFO,
        env="LOG_LEVEL",
        description="Python logging level as string, i.e. one of "
        + ", ".join(['"' + x.value + '"' for x in list(LogLevel)]),
    )
    swagger_prefix: str = Field(
        "",
        env="OPENAPI_PREFIX",
        description="root path (necessary for OpenAPI UI if behind proxy)",
    )
    model_repo_path: str = Field(
        "/mnt/obj_repo",
        env="MODEL_REPO_PATH",
        description=(
            "The path were serialized objects from the simple built-in object store"
            " (e.g. trained models) will be stored."
        ),
    )

    # HD Keycloak auth
    hd_auth_use_keycloak: bool = Field(
        False,
        env="HD_AUTH_USE_KEYCLOAK",
        description="Whether Keycloak is used for verifying requests to runtime service endpoints",
    )
    hd_keycloak_auth_url: Optional[str] = Field(None, env="HD_KEYCLOAK_AUTH_URL")
    hd_keycloak_realm: Optional[str] = Field("Hetida", env="HD_KEYCLOAK_REALM")
    hd_keycloak_runtime_audience: Optional[str] = Field(
        "account", env="HD_KEYCLOAK_RUNTIME_AUDIENCE"
    )
    hd_keycloak_runtime_client_id: Optional[str] = Field(
        None, env="HD_KEYCLOAK_RUNTIME_CLIENT_ID"
    )
    hd_keycloak_runtime_username: Optional[str] = Field(
        None, env="HD_KEYCLOAK_RUNTIME_USERNAME"
    )
    hd_keycloak_runtime_password: Optional[str] = Field(
        None,
        env="HD_KEYCLOAK_RUNTIME_PASSWORD",
        description="the password of the service user",
    )

    # Keycloak Auth for generic rest adapters
    hd_generic_rest_adapter_auth_use_keycloak: bool = Field(
        False,
        env="HD_GENERIC_REST_ADAPTER_AUTH_USE_KEYCLOAK",
        description=(
            "Whether Keycloak is used for requests from runtime to generic rest adapter endpoints"
        ),
    )
    hd_generic_rest_adapter_keycloak_auth_url: Optional[str] = Field(
        None, env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_AUTH_URL"
    )
    hd_generic_rest_adapter_keycloak_realm: Optional[str] = Field(
        None, env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_REALM"
    )
    hd_generic_rest_adapter_keycloak_runtime_client_id: Optional[str] = Field(
        None, env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_RUNTIME_CLIENT_ID"
    )
    hd_generic_rest_adapter_keycloak_runtime_username: Optional[str] = Field(
        None, env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_RUNTIME_USERNAME"
    )
    hd_generic_rest_adapter_keycloak_runtime_password: Optional[str] = Field(
        None,
        env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_RUNTIME_PASSWORD",
        description="the password of the service user",
    )
    hd_generic_rest_adapter_keycloak_runtime_audience: Optional[str] = Field(
        "account", env="HD_GENERIC_REST_ADAPTER_KEYCLOAK_RUNTIME_AUDIENCE"
    )

    # For scripts (e.g. component deployment)
    hd_backend_api_url: str = Field(
        "http://hetida-designer-backend:8080/api/",
        env="HETIDA_DESIGNER_BACKEND_API_URL",
        description="URL to backend. Only necessary for component deployment.",
    )
    hd_backend_use_basic_auth: bool = Field(
        False,
        env="HETIDA_DESIGNER_BACKEND_USE_BASIC_AUTH",
        description=(
            "Whether Backend is protected via Basic Auth."
            " Only necessary for component deployment."
            " If Backend is protected via Keycloak instead "
            " use the corresponding keycloak environment variables!"
        ),
    )
    hd_backend_basic_auth_user: Optional[str] = Field(
        None,
        env="HETIDA_DESIGNER_BASIC_AUTH_USER",
        description="Basic Auth User",
    )
    hd_backend_basic_auth_password: Optional[str] = Field(
        None,
        env="HETIDA_DESIGNER_BASIC_AUTH_PASSWORD",
        description="Basic Auth User",
    )
    hd_backend_verify_certs: bool = Field(
        True, env="HETIDA_DESIGNER_BACKEND_VERIFY_CERTS"
    )
    hd_adapters_verify_certs: bool = Field(
        True, env="HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS"
    )

    # pylint: disable=no-self-argument,no-self-use
    @validator("hd_backend_api_url")
    def backend_api_url_ends_with_slash(cls, v: str) -> str:
        """make it end with a slash"""
        if not v.endswith("/"):
            v += "/"
        return v


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

runtime_config = RuntimeConfig(_env_file=environment_file if environment_file else None)
