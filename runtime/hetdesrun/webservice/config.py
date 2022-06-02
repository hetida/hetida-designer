import os
from enum import Enum
from typing import Optional, Union

# pylint: disable=no-name-in-module
from pydantic import (
    BaseSettings,
    Field,
    SecretStr,
    validator,
)

from sqlalchemy.engine import URL as SQLAlchemy_DB_URL


class LogLevel(str, Enum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


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

    is_backend_service: bool = Field(
        True,
        env="HD_IS_BACKEND_SERVICE",
        description="Whether backend service endpoints should be active.",
    )

    is_runtime_service: bool = Field(
        True,
        env="HD_IS_RUNTIME_SERVICE",
        description="Whether runtime service endpoints should be active.",
    )

    ensure_db_schema: bool = Field(
        True,
        env="HD_ENSURE_DB_SCHEMA",
        description=("Currently not in use!"),
    )

    allowed_origins: str = Field(
        (
            "http://localhost:4200,http://localhost:80,localhost"
            ",http://localhost,hetida-designer-demo-adapter-python"
        ),
        description=(
            "Comma separated allowed origins (CORS)"
            " (relevant for adapters in runtime like local file adapter)"
        ),
        env="ALLOWED_ORIGINS",
        example="http://exampledomain.com,http://anotherexampledomain.de",
    )

    sqlalchemy_db_host: str = Field(
        "hetida-designer-db", env="HD_DB_HOST", example="hetida-designer-db"
    )

    sqlalchemy_db_port: int = Field(5432, env="HD_DATABASE_PORT", example=5432)

    sqlalchemy_db_database: str = Field(
        "hetida_designer_db", env="HD_DB_DATABASE", example="hetida_designer_db"
    )

    sqlalchemy_db_drivername: str = Field(
        "postgresql+psycopg2", env="HD_DB_DRIVERNAME", example="postgresql+psycopg2"
    )

    sqlalchemy_db_user: str = Field("hetida_designer_dbuser", env="HD_DB_USER")

    sqlalchemy_db_password: SecretStr = Field(
        SecretStr("hetida_designer_dbpasswd"), env="HD_DB_PASSWORD"
    )

    sqlalchemy_connection_string: Optional[Union[SecretStr, SQLAlchemy_DB_URL]] = Field(
        None,
        description=(
            "Rfc 1738 database url. Not set by default."
            " If set, takes precedence over sqlalchemy_db_* attributes!"
            " Otherwise will be constructed from the sqlalchemy_db_* attributes"
        ),
        env="HD_DATABASE_URL",
        example=(
            "postgresql+psycopg2://hetida_designer_dbuser:"
            "hetida_designer_dbpasswd@hetida-designer-db:5432/hetida_designer_db"
        ),
    )

    sqlalchemy_pool_size: int = Field(
        100, description="Database pool size", env="HD_DATABASE_POOL_SIZE", gt=0
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

    hd_adapters: str = Field(
        "demo-adapter-python|Python-Demo-Adapter"
        "|http://localhost:8092"
        "|http://hetida-designer-demo-adapter-python:8092,"
        "demo-adapter-java|Java-Demo-Adapter"
        "|http://localhost:8091/adapter"
        "|http://hetida-designer-demo-adapter-java:8091/adapter,"
        "local-file-adapter|Local-File-Adapter"
        "|http://localhost:8090/adapters/localfile"
        "|http://hetida-designer-runtime:8090/adapters/localfile",
        env="HETIDA_DESIGNER_ADAPTERS",
        description="list of the installed adapters",
    )

    hd_runtime_engine_url: str = Field(
        "http://hetida-designer-runtime:8090/engine/",
        env="HETIDA_DESIGNER_RUNTIME_EGINE_URL",
        description="URL to runtime",
    )

    hd_runtime_verify_certs: bool = Field(
        True, env="HETIDA_DESIGNER_RUNTIME_VERIFY_CERTS"
    )

    # For scripts (e.g. transformation deployment)
    hd_backend_api_url: str = Field(
        "http://hetida-designer-backend:8090/api/",
        env="HETIDA_DESIGNER_BACKEND_API_URL",
        description=(
            "URL to backend. Necessary for transformation deployment "
            "and to allow runtime to access adapters endpoint."
        ),
    )
    hd_backend_use_basic_auth: bool = Field(
        False,
        env="HETIDA_DESIGNER_BACKEND_USE_BASIC_AUTH",
        description=(
            "Whether Backend is protected via Basic Auth."
            " Only necessary for transformation deployment."
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
    hd_backend_autodeploy_base_transformations: bool = Field(
        True, env="HETIDA_DESIGNER_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS"
    )
    hd_backend_overwrite_on_autodeploy: bool = Field(
        False, env="HETIDA_DESIGNER_BACKEND_OVERWRITE_ON_AUTODEPLOY"
    )
    hd_adapters_verify_certs: bool = Field(
        True, env="HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS"
    )

    hd_kafka_consumer_enabled: bool = Field(
        False,
        description="Whether a Kafka consumer for executing workflows/components is enabled",
        env="HETIDA_DESIGNER_KAFKA_ENABLED",
    )

    hd_kafka_consumer_topic: str = Field(
        "hd-execution-topic",
        description="The topic to which the execution consumer will listen",
        env="HETIDA_DESIGNER_KAFKA_CONSUMER_TOPIC",
    )

    hd_kafka_consumer_options: dict = Field(
        {"bootstrap_servers": "kafka:19092", "group_id": "hd_kafka_consumer_group"},
        description=(
            "Intialization parameters for the aiokafka consumer class."
            " The most important ones set here are probably bootstrap_servers"
            " and group_id."
            " These options will be passed directly to the class init method."
            " The environment variable expects this to be a mapping as json string."
            " Note that some of the available options need different code to work"
            " properly, so not all available options / combinations are viable"
            " for the hetida designer consumer."
        ),
        example={
            "bootstrap_servers": "kafka:19092",
            "group_id": "hd_kafka_consumer_group",
            "auto_commit_interval_ms": 1000,
            "auto_offset_reset": "earliest",
        },
        env="HETIDA_DESIGNER_KAFKA_CONSUMER_OPTIONS",
    )

    hd_kafka_producer_options: dict = Field(
        {"bootstrap_servers": "kafka:19092"},
        description=(
            "Intialization parameters for the aiokafka consumer class."
            " The most important one set here is probably bootstrap_servers."
            " These options will be passed directly to the class init method."
            " The environment variable expects this to be a mapping as json string."
            " Note that some of the available options need different code to work"
            " properly, so not all available options / combinations are viable"
            " for the hetida designer consumer."
        ),
        example={"bootstrap_servers": "kafka:19092"},
        env="HETIDA_DESIGNER_KAFKA_PRODUCER_OPTIONS",
    )

    hd_kafka_response_topic: str = Field(
        "hd-execution-response-topic",
        description="The topic to which the execution consumer send execution results",
        env="HETIDA_DESIGNER_KAFKA_RESPONSE_TOPIC",
    )

    # pylint: disable=no-self-argument,no-self-use
    @validator("is_runtime_service")
    def must_be_at_least_backend_or_runtime(cls, v: bool, values: dict) -> bool:

        is_backend_service = values["is_backend_service"]

        if not (v or is_backend_service):
            msg = (
                "At least one of is_backend_service or is_runtime_service must be true. "
                "It does not make sense to start the service with no active endpoints."
            )
            raise ValueError(msg)
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("hd_backend_api_url")
    def backend_api_url_ends_with_slash(cls, v: str) -> str:
        """make it end with a slash"""
        if not v.endswith("/"):
            v += "/"
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("sqlalchemy_connection_string")
    def database_url(
        cls, v: Optional[Union[SecretStr, SQLAlchemy_DB_URL]], values: dict
    ) -> Optional[Union[SecretStr, SQLAlchemy_DB_URL]]:

        if v is None:
            pw_secret = values["sqlalchemy_db_password"]
            return SQLAlchemy_DB_URL.create(
                drivername=values["sqlalchemy_db_drivername"],
                username=values["sqlalchemy_db_user"],
                password=(
                    pw_secret.get_secret_value()
                    if isinstance(pw_secret, SecretStr)
                    else pw_secret
                ),
                host=values["sqlalchemy_db_host"],
                port=values["sqlalchemy_db_port"],
                database=values["sqlalchemy_db_database"],
            )
        return v


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

runtime_config = RuntimeConfig(_env_file=environment_file if environment_file else None)
