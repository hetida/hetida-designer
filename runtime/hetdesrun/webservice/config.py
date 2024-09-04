import datetime
import os
import re
from enum import Enum
from uuid import UUID

from pydantic import BaseSettings, Field, Json, SecretStr, validator
from sqlalchemy.engine import URL as SQLAlchemy_DB_URL

from hetdesrun.models.execution import ExecByIdBase
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.webservice.auth import FrontendAuthOptions
from hetdesrun.webservice.auth_outgoing import ServiceCredentials

maintenance_secret_pattern = re.compile("[a-zA-Z0-9]+")


class LogLevel(str, Enum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class ExternalAuthMode(str, Enum):
    OFF = "OFF"
    CLIENT = "CLIENT"
    FORWARD_OR_FIXED = "FORWARD_OR_FIXED"


class InternalAuthMode(str, Enum):
    OFF = "OFF"
    CLIENT = "CLIENT"
    FORWARD_OR_FIXED = "FORWARD_OR_FIXED"


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

    advanced_performance_measurement_active: bool = Field(
        True,
        env="HD_ADVANCED_PERFORMANCE_MEASUREMENT_INFORMATION",
        description=(
            "Whether some additional information is returned by execution requests."
            " At the moment this setting only affects the process id (PID),"
            " while time measurements are always provided."
        ),
    )

    log_execution_performance_info: bool = Field(
        False,
        description="Whether performance info (measured steps) are logged.",
        env="HD_LOG_EXECUTION_PERFORMANCE_INFO",
    )

    swagger_prefix: str = Field(
        "",
        env="OPENAPI_PREFIX",
        description="root path (necessary for OpenAPI UI if behind proxy)",
    )
    external_request_timeout: int = Field(
        90,
        env="EXTERNAL_REQUEST_TIMEOUT",
        description=(
            "The time (in seconds) to wait for a response of an external REST API "
            "such as a generic REST adapter"
        ),
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

    restrict_to_trafo_exec_service: set[UUID] = Field(
        set(),
        description=(
            "Setting this to a non-empty set of UUIDs will surpress all backend "
            "and runtime endpoints and offer only the execution of the configured "
            "transformations. This can be used to scale execution of one or more "
            "transformations as a separate webservice, which also can be exposed to "
            "3rd parties without allowing manipulations. Often this is combined with "
            "setting is_runtime_service to true in order to have the full trafo "
            "execution happen in one sacalable containerized service."
        ),
        env="HD_RESTRICT_TO_TRAFO_EXEC_SERVICE",
    )

    enable_caching_for_non_draft_trafos_for_execution: bool = Field(
        False,
        env="HD_ENABLE_CACHING_FOR_NON_DRAFT_TRAFOS_FOR_EXEC",
        description=(
            "Cache transformation revisions for execution if their state is not DRAFT. "
            "Instead of always loading them from the database. "
            "The caching mechanism is NOT thread-safe."
        ),
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

    sqlalchemy_connection_string: SecretStr | SQLAlchemy_DB_URL | None = Field(
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

    auth: bool = Field(
        True,
        description=(
            "Whether authentication checking is active. This configures"
            " ingoing auth, i.e. whether bearer tokens are checked."
        ),
        env="HD_USE_AUTH",
    )

    dashboarding_frontend_auth_settings: FrontendAuthOptions = Field(
        FrontendAuthOptions(
            auth_url="http://localhost:8081/auth/",
            client_id="hetida-designer",
            realm="hetida-designer",
        ),
        description=(
            "Settings that will be provided to keycloak-js instance in dashboards."
            "Must be set there"
        ),
        env="HD_DASHBOARDING_FRONTEND_AUTH_SETTINGS",
    )

    auth_public_key_url: str = Field(
        "http://hetida-designer-keycloak:8080/auth/realms/hetida-designer/protocol/openid-connect/certs",  # noqa: E501
        description="URL to endpoint providing public keys for verifying bearer token signature",
        env="HD_AUTH_PUBLIC_KEY_URL",
    )

    auth_verify_certs: bool = Field(True, env="HD_AUTH_VERIFY_CERTS")

    auth_role_key: str = Field(
        "roles",
        description=(
            "Under which key of the access token payload the roles will" " be expected as a list."
        ),
        env="HD_AUTH_ROLE_KEY",
    )

    auth_allowed_role: str | None = Field(
        None,
        description=(
            "Role provided in bearer access token that is allowed access."
            " If None, role is not checked / everybody is allowed."
        ),
        env="HD_AUTH_ALLOWED_ROLE",
    )

    auth_reload_public_key: bool = Field(
        True,
        description="Whether public keys for signature check will be reloaded"
        " if a verification fails and if they are old",
        env="HD_AUTH_RELOAD_PUBLIC_KEY",
    )

    auth_public_key_reloading_minimum_age: datetime.timedelta = Field(
        datetime.timedelta(seconds=15),
        description="If auth fails and auth_reload_public_key is True "
        "public keys are only tried to load again if older than this timedelta."
        " Can be either seconds as int or float or an ISO 8601 timedelta string",  # 15 seconds
        env="HD_AUTH_KEY_RELOAD_MINIMUM_AGE",
        example="P0DT00H00M15S",
    )

    auth_bearer_token_for_outgoing_requests: str | None = Field(
        None,
        description=(
            "A string containing a bearer token for making outgoing requests. "
            "If set and there is no currently handled API request with a provided access token,"
            " this will be used when making outgoing requests to adapters or runtime/backend"
            " if the corrsponding auth mode (internal/external) for outgoing request"
            " is FORWARD_OR_FIXED."
            " This setting makes export/import possible when having auth activated, i.e."
            " its intended use is for scripting using the hetdesrun Python package."
            " Make sure the expiration of the token is long enough for your script invocation."
        ),
        env="HD_BEARER_TOKEN_FOR_OUTGOING_REQUESTS",
    )

    internal_auth_mode: InternalAuthMode = Field(
        InternalAuthMode.FORWARD_OR_FIXED,
        description=(
            "How outgoing requests to internal services should be handled."
            " For example from backend to runtime if both are run as separate services."
            " One of "
            ", ".join(['"' + x.value + '"' for x in list(InternalAuthMode)])
        ),
        env="HD_INTERNAL_AUTH_MODE",
    )
    internal_auth_client_credentials: ServiceCredentials | Json[ServiceCredentials] | None = Field(
        None,
        description=(
            "Client credentials as json encoded string."
            " For details confer the ServiceCredentials model class in the auth_outgoing.py"
            " file."
        ),
        example=(
            '{"realm": "my-realm", "auth_url": "https://test.com/auth", "audience": "account",'
            ' "grant_credentials": {"grant_type": "client_credentials", "client_id": "my-client",'
            ' "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false},'
            ' "post_kwargs": {}}'
        ),
        env="HD_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS",
    )
    external_auth_mode: ExternalAuthMode = Field(
        ExternalAuthMode.FORWARD_OR_FIXED,
        description=(
            "How outgoing requests to external services should be handled."
            " For example from runtime to adapters or during export/import."
            " One of "
            ", ".join(['"' + x.value + '"' for x in list(ExternalAuthMode)])
        ),
        env="HD_EXTERNAL_AUTH_MODE",
    )
    external_auth_client_credentials: ServiceCredentials | Json[ServiceCredentials] | None = Field(
        None,
        description="Client credentials as json encoded string.",
        example=(
            '{"realm": "my-realm", "auth_url": "https://test.com/auth", "audience": "account",'
            ' "grant_credentials": {"grant_type": "client_credentials", "client_id": "my-client",'
            ' "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false},'
            ' "post_kwargs": {}}'
        ),
        env="HD_EXTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS",
    )

    maintenance_secret: SecretStr | None = Field(
        None,
        description="Secret necessary to access maintenance endpoints of the backend."
        " If this is set, the maintenance endpoints are activated."
        " To use them this secret is required as part of the payload."
        " Only alphanumeric characters are allowed",
        env="HD_MAINTENANCE_SECRET",
    )

    autoimport_directory: str = Field(
        "",
        description="Path to directory where to look for import sources during autoimport",
        env="HD_BACKEND_AUTOIMPORT_DIRECTORY",
    )

    prepopulate_virtual_structure_adapter_at_designer_startup: bool = Field(
        False,
        description="Set this flag to True, if you wish to provide a structure "
        "for the virtual structure adapter "
        "via the environment variable STRUCTURE_TO_PREPOPULATE_VST_ADAPTER.",
        env="PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP",
    )

    prepopulate_virtual_structure_adapter_via_file: bool = Field(
        False,
        description="Set this flag to True, if you wish to provide a structure "
        "for the virtual structure adapter "
        "via a filepath stored in the "
        "environment variable STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER.",
        env="PREPOPULATE_VST_ADAPTER_VIA_FILE",
    )

    completely_overwrite_an_existing_virtual_structure_at_hd_startup: bool = Field(
        True,
        description="Determines whether a potentially existent virtual structure in the database "
        "is overwritten (if set to True) or updated (if set to False) at hetida designer startup.",
        env="COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP",
    )

    structure_to_prepopulate_virtual_structure_adapter: CompleteStructure | None = Field(
        None,
        description="A JSON, used to provide a structure for the virtual structure adapter "
        "at hetida designer startup. "
        "This built-in adapter enables the user to create "
        "a flexible, abstract hierarchical structure for their data. "
        "In this JSON the user can provide names, descriptions and metadata "
        "for each element of the hierarchy. "
        "The JSON should contain definitions for all thingnodes, sources, sinks and element types "
        "representing the users data.",
        env="STRUCTURE_TO_PREPOPULATE_VST_ADAPTER",
    )

    structure_filepath_to_prepopulate_virtual_structure_adapter: str | None = Field(
        None,
        description="A JSON-filepath, used to provide a structure "
        "for the virtual structure adapter at hetida designer startup. "
        "Used analogously to 'STRUCTURE_TO_PREPOPULATE_VST_ADAPTER'.",
        env="STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER",
    )

    hd_adapters: str = Field(
        "demo-adapter-python|Python-Demo-Adapter"
        "|http://localhost:8092"
        "|http://hetida-designer-demo-adapter-python:8092,"
        "local-file-adapter|Local-File-Adapter"
        "|http://localhost:8090/adapters/localfile"
        "|http://hetida-designer-runtime:8090/adapters/localfile,"
        "sql-adapter|SQL Adapter"
        "|http://localhost:8090/adapters/sql"
        "|http://localhost:8090/adapters/sql,"
        "kafka|Kafka Adapter"
        "|http://localhost:8090/adapters/kafka"
        "|http://localhost:8090/adapters/kafka,"
        "virtual-structure-adapter|Virtual Structure Adapter"
        "|http://localhost:8090/adapters/vst"
        "|http://localhost:8090/adapters/vst",
        env="HETIDA_DESIGNER_ADAPTERS",
        description="list of the installed adapters",
    )

    hd_runtime_engine_url: str = Field(
        "http://hetida-designer-runtime:8090/engine/",
        env="HETIDA_DESIGNER_RUNTIME_ENGINE_URL",
        description="URL to runtime",
    )

    hd_runtime_verify_certs: bool = Field(True, env="HETIDA_DESIGNER_RUNTIME_VERIFY_CERTS")

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
            " Only necessary for component deployment."
            " If Backend is protected via OpenIDConnect instead "
            " use the corresponding environment variables!"
        ),
    )
    hd_backend_basic_auth_user: str | None = Field(
        None,
        env="HETIDA_DESIGNER_BASIC_AUTH_USER",
        description="Basic Auth User",
    )
    hd_backend_basic_auth_password: str | None = Field(
        None,
        env="HETIDA_DESIGNER_BASIC_AUTH_PASSWORD",
        description="Basic Auth User",
    )
    hd_backend_verify_certs: bool = Field(True, env="HETIDA_DESIGNER_BACKEND_VERIFY_CERTS")
    hd_adapters_verify_certs: bool = Field(True, env="HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS")

    hd_kafka_consumption_mode: None | ExecByIdBase = Field(
        None,
        description=(
            "If this is set, all backend, runtime and adapter webservices are deactivated. "
            "Instead a kafka consumer is started listening on the kafka topic from the kafka "
            "adapter inputs of the topic/configuration of the provided wiring (exactly one kafka "
            "config is allowed to occur in the input wirings). Whenever it receives a kafka "
            "message it will execute the transformation with the wiring forwarding the kafka "
            "message content into the kafka adapter input wirings."
        ),
        env="HETIDA_DESIGNER_KAFKA_CONSUMPTION_MODE",
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

    @validator("internal_auth_client_credentials")
    def internal_auth_client_credentials_set_if_internal_auth_mode_is_client(
        cls,
        v: Json[ServiceCredentials] | None,
        values: dict,
    ) -> Json[ServiceCredentials] | None:
        internal_auth_mode = values["internal_auth_mode"]

        if internal_auth_mode == InternalAuthMode.CLIENT and v is None:
            msg = (
                "If internal auth mode is set to CLIENT, "
                "internal auth client credentials must be configured"
            )
            raise ValueError(msg)
        return v

    @validator("external_auth_client_credentials")
    def external_auth_client_credentials_set_if_external_auth_mode_is_client(
        cls,
        v: Json[ServiceCredentials] | None,
        values: dict,
    ) -> Json[ServiceCredentials] | None:
        external_auth_mode = values["external_auth_mode"]

        if external_auth_mode == ExternalAuthMode.CLIENT and v is None:
            msg = (
                "If external auth mode is set to CLIENT, "
                "external auth client credentials must be configured"
            )
            raise ValueError(msg)
        return v

    @validator("maintenance_secret")
    def maintenance_secret_allowed_characters(cls, v: SecretStr | None) -> SecretStr | None:
        if v is None:
            return v
        if not maintenance_secret_pattern.fullmatch(v.get_secret_value()):
            raise ValueError(
                "Only numbers and alphabet letters allowed for the maintenance secret"
                " and it must have non-zero length."
            )
        return v

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

    @validator("hd_backend_api_url")
    def backend_api_url_ends_with_slash(cls, v: str) -> str:
        """make it end with a slash"""
        if not v.endswith("/"):
            v += "/"
        return v

    @validator("sqlalchemy_connection_string")
    def database_url(
        cls, v: SecretStr | SQLAlchemy_DB_URL | None, values: dict
    ) -> SecretStr | SQLAlchemy_DB_URL | None:
        if v is None:
            pw_secret = values["sqlalchemy_db_password"]
            return SQLAlchemy_DB_URL.create(
                drivername=values["sqlalchemy_db_drivername"],
                username=values["sqlalchemy_db_user"],
                password=(
                    pw_secret.get_secret_value() if isinstance(pw_secret, SecretStr) else pw_secret
                ),
                host=values["sqlalchemy_db_host"],
                port=values["sqlalchemy_db_port"],
                database=values["sqlalchemy_db_database"],
            )
        return v


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

runtime_config = RuntimeConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_config() -> RuntimeConfig:
    return runtime_config
