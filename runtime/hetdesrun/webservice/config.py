import datetime
import os
import re
from enum import StrEnum
from uuid import UUID

from pydantic import (
    AliasChoices,
    Field,
    Json,
    RootModel,
    SecretStr,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL as SQLAlchemy_DB_URL

from hetdesrun.models.execution import ExecByIdBase
from hetdesrun.webservice.auth import FrontendAuthOptions
from hetdesrun.webservice.auth_outgoing import ServiceCredentials

maintenance_secret_pattern = re.compile("[a-zA-Z0-9]+")


class LogLevel(StrEnum):
    # https://docs.python.org/3/library/logging.html#logging-levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"


class ExternalAuthMode(StrEnum):
    OFF = "OFF"
    CLIENT = "CLIENT"
    FORWARD_OR_FIXED = "FORWARD_OR_FIXED"


class InternalAuthMode(StrEnum):
    OFF = "OFF"
    CLIENT = "CLIENT"
    FORWARD_OR_FIXED = "FORWARD_OR_FIXED"


class SchedulingInternalAuthMode(StrEnum):
    """Auth mode for scheduled execution requests to the runtime service"""

    OFF = "OFF"
    CLIENT = "CLIENT"


class RoleToRuntimeEngineUrlMapping(RootModel[dict[str, str]]):
    pass


class RuntimeConfig(BaseSettings):
    """Configuration for Hetida Designer Runtime

    There is an example .env file /runtime/settings/example.env
    """

    log_level: LogLevel = Field(
        LogLevel.INFO,
        validation_alias="LOG_LEVEL",
        description="Python logging level as string, i.e. one of "
        + ", ".join(['"' + x.value + '"' for x in list(LogLevel)]),
    )

    user_component_code_log_level: LogLevel | None = Field(
        None,
        validation_alias="USER_COMPONENT_CODE_LOG_LEVEL",
        description=(
            "Log level for logging in user component code. One of "
            + ", ".join(['"' + x.value + '"' for x in list(LogLevel)])
            + "or None"
            " where None implies the same log level as the runtime's log level."
        ),
    )

    user_component_code_logs_max_len: int | None = Field(
        None,
        validation_alias="USER_COMPONENT_CODE_LOG_MAX_LEN",
        description=(
            "Maximal number of collected user component code logs."
            " Limits how many log messages are collected and returned "
            "as part of the execution response object. Set to None for no limits"
        ),
    )

    log_route_parsed_json_bodies: bool = Field(
        False,
        validation_alias="LOG_ROUTE_PARSED_JSON_BODIES",
        description=(
            "Whether in each http route the content is tried to be parsed as json and the result"
            " is logged. This may add parsing overhead and should only be activated for debugging"
        ),
    )

    log_httpx: bool = Field(
        False,
        description=(
            "Whether httpx / httpcore request logging should be activated. "
            "Note: This uses the same log level as cofigured via LOG_LEVEL. "
            "Activating this you typically want to set LOG_LEVEL to DEBUG as well. "
            "This setting may help to analyze inter service communication (runtime/backend) "
            "as well as http requests to external data sources to identify performance / networking"
            " bottlenecks."
        ),
        validation_alias="LOG_HTTPX",
    )

    log_uvicorn: bool = Field(
        True,
        description=(
            "Whether uvicorn / uvicorn.access logging should be activated. "
            "Note: This uses the same log level as cofigured via LOG_LEVEL. "
        ),
        validation_alias="LOG_UVICORN",
    )

    log_fields_to_rename: dict[str, str] = Field(
        {
            "currently_executed_job_id": "job_id",
            "currently_executed_transformation_id": "tr_id",
            "currently_executed_transformation_name": "tr_name",
            "currently_executed_transformation_tag": "tr_tag",
            "currently_executed_transformation_type": "tr_type",
            "currently_executed_operator_hierarchical_id": "op_id",
            "currently_executed_operator_hierarchical_name": "op_name",
            # "event": "message", if you do rename event, it will not be found by logfire anymore!
        },
        description="Dict of log field names to be renamed, before the log is rendered as a JSON. "
        "Keys are looked up in the event dict and replaced with the corresponding value. "
        'If "event" is renamed, it will not be found by logfire anymore and you ill not get '
        "log messages in the generated events / spans!",
        validation_alias="LOG_FIELDS_TO_RENAME",
    )

    log_technical_nodes: bool = Field(
        False,
        description=(
            "Whether technical workflow nodes execution will be logged. "
            "Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_TECHNICAL_NODES",
    )

    full_backend_exec_input_logging: bool = Field(
        False,
        description=(
            "Whether full execution input (exec_by_id_input) should be logged. "
            "Including complete wiring before virtual structure resolution. May include "
            "lots of data for direct provisioning inputs. "
            "Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_FULL_BACKEND_EXEC_INPUT",
    )

    full_execution_input_logging: bool = Field(
        False,
        description=(
            "Whether full runtime execution input should be logged. "
            "Including all code and complete wiring which may include "
            "lots of data for direct provisioning inputs. "
            "Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_FULL_EXEC_INPUT",
    )

    log_updated_trafo_revision: bool = Field(
        False,
        description=(
            "When creating or updating, whether the persisted trafo revision should be fully"
            " logged. Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_UPDATED_TRAFO_REVISION",
    )

    log_resolved_virtual_structure_wirings: bool = Field(
        False,
        description=(
            "Whether the resulting wiring after resolving virtual structure"
            " wirings should be logged"
            " logged. Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_RESOLVED_VIRTUAL_STRUCTURE_WIRINGS",
    )

    log_nestings_and_descendants: bool = Field(
        False,
        description=(
            "Whether nestings and descendants should be logged"
            " Note that it only will be logged with log level DEBUG."
        ),
        validation_alias="LOG_NESTINGS_AND_DESCENDANTS",
    )

    log_direct_provisioning_outputs: bool = Field(
        False,
        description=(
            "Whether the output_results_by_output_name field provided together with an"
            " execution result response will be logged"
        ),
        validation_alias="LOG_DIRECT_PROVISIONING_OUTPUTS",
    )

    advanced_performance_measurement_active: bool = Field(
        True,
        validation_alias="HD_ADVANCED_PERFORMANCE_MEASUREMENT_INFORMATION",
        description=(
            "Whether some additional information is returned by execution requests."
            " At the moment this setting only affects the process id (PID),"
            " while time measurements are always provided."
        ),
    )

    log_execution_performance_info: bool = Field(
        False,
        description="Whether performance info (measured steps) are logged.",
        validation_alias="HD_LOG_EXECUTION_PERFORMANCE_INFO",
    )

    swagger_prefix: str = Field(
        "",
        validation_alias="OPENAPI_PREFIX",
        description="root path (necessary for OpenAPI UI if behind proxy)",
    )
    external_request_timeout: int = Field(
        90,
        validation_alias="EXTERNAL_REQUEST_TIMEOUT",
        description=(
            "The time (in seconds) to wait for a response of an external REST API "
            "such as a generic REST adapter"
        ),
    )
    allowed_callback_url_patterns: list[str] = Field(
        default_factory=list,
        validation_alias="HD_ALLOWED_CALLBACK_URL_PATTERNS",
        description=(
            "Allowlist of URL patterns that the callback_url of the asynchronous"
            " execution endpoints (/execute-async, /execute-latest-async) must match."
            " A caller-supplied callback_url is only accepted if it matches at least one"
            " pattern here; otherwise the request is rejected. This prevents the backend"
            " from being abused to POST execution results (and, depending on the outgoing"
            " auth mode, the service's own bearer token) to arbitrary hosts (SSRF)."
            " Patterns use shell-style globbing (fnmatch): '*' matches any sequence of"
            " characters, '?' a single character. Always pin the scheme and host and"
            " include the path separator, e.g."
            " 'https://caller.example.com/hd-callback*' to permit any query string such"
            " as an identifying call id. Only http/https URLs without embedded userinfo"
            " are ever considered. The default is an empty list, which disables the"
            " asynchronous callback feature entirely (fail closed) until configured."
        ),
        examples=[["https://caller.example.com/hd-callback*"]],
    )
    model_repo_path: str = Field(
        "/mnt/obj_repo",
        validation_alias="MODEL_REPO_PATH",
        description=(
            "The path were serialized objects from the simple built-in object store"
            " (e.g. trained models) will be stored."
        ),
    )

    is_backend_service: bool = Field(
        True,
        validation_alias="HD_IS_BACKEND_SERVICE",
        description="Whether backend service endpoints should be active.",
    )

    is_runtime_service: bool = Field(
        True,
        validation_alias="HD_IS_RUNTIME_SERVICE",
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
        validation_alias="HD_RESTRICT_TO_TRAFO_EXEC_SERVICE",
    )

    enable_caching_for_non_draft_trafos_for_execution: bool = Field(
        False,
        validation_alias="HD_ENABLE_CACHING_FOR_NON_DRAFT_TRAFOS_FOR_EXEC",
        description=(
            "Cache transformation revisions for execution if their state is not DRAFT. "
            "Instead of always loading them from the database when executing. "
            "It should only be enabled in scenarios where released rafos never get overwritten "
            "by for example maintenance operations. Typically you want to activate this kind of "
            "caching in modes like Kafka consumption mode or similar streaming modes or "
            "the restricted trafo execution mode, where one or a few transformation revisions "
            "(and their nested trafos) are executed very often / continuously."
        ),
    )

    ensure_db_schema: bool = Field(
        True,
        validation_alias="HD_ENSURE_DB_SCHEMA",
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
        validation_alias="ALLOWED_ORIGINS",
        examples=["http://exampledomain.com,http://anotherexampledomain.de"],
    )

    sqlalchemy_db_host: str = Field(
        "hetida-designer-db", validation_alias="HD_DB_HOST", examples=["hetida-designer-db"]
    )

    sqlalchemy_db_port: int = Field(5432, validation_alias="HD_DATABASE_PORT", examples=[5432])

    sqlalchemy_db_database: str = Field(
        "hetida_designer_db", validation_alias="HD_DB_DATABASE", examples=["hetida_designer_db"]
    )

    sqlalchemy_db_drivername: str = Field(
        "postgresql+psycopg", validation_alias="HD_DB_DRIVERNAME", examples=["postgresql+psycopg"]
    )

    sqlalchemy_db_user: str = Field("hetida_designer_dbuser", validation_alias="HD_DB_USER")

    sqlalchemy_db_password: SecretStr = Field(
        SecretStr("hetida_designer_dbpasswd"), validation_alias="HD_DB_PASSWORD"
    )

    sqlalchemy_connection_string: SecretStr | SQLAlchemy_DB_URL | None = Field(
        None,
        description=(
            "Rfc 1738 database url. Not set by default."
            " If set, takes precedence over sqlalchemy_db_* attributes!"
            " Otherwise will be constructed from the sqlalchemy_db_* attributes"
        ),
        validation_alias="HD_DATABASE_URL",
        examples=[
            (
                "postgresql+psycopg://hetida_designer_dbuser:"
                "hetida_designer_dbpasswd@hetida-designer-db:5432/hetida_designer_db"
            )
        ],
    )

    sqlalchemy_pool_size: int = Field(
        100, description="Database pool size", validation_alias="HD_DATABASE_POOL_SIZE", gt=0
    )

    # HD Keycloak auth

    auth: bool = Field(
        True,
        description=(
            "Whether authentication checking is active. This configures"
            " ingoing auth, i.e. whether bearer tokens are checked."
        ),
        validation_alias="HD_USE_AUTH",
    )

    dashboarding_frontend_auth_settings: FrontendAuthOptions = Field(
        FrontendAuthOptions(
            auth_url="http://localhost:8081/",
            client_id="hetida-designer",
            realm="hetida-designer",
        ),
        description=(
            "Settings that will be provided to keycloak-js instance in dashboards.Must be set there"
        ),
        validation_alias="HD_DASHBOARDING_FRONTEND_AUTH_SETTINGS",
    )

    auth_public_key_url: str = Field(
        "http://hetida-designer-keycloak:8080/realms/hetida-designer/protocol/openid-connect/certs",  # noqa: E501
        description="URL to endpoint providing public keys for verifying bearer token signature",
        validation_alias="HD_AUTH_PUBLIC_KEY_URL",
    )

    auth_audience: str | None = Field(
        "account",
        description="Expected audience in tokens.",
        validation_alias=AliasChoices("HD_AUTH_AUDIENCE", "JWT_AUDIENCE"),
    )

    auth_issuer: str | None = Field(
        None,
        description="Expected issuer in tokens.",
        validation_alias=AliasChoices("HD_AUTH_ISSUER", "JWT_ISSUER"),
    )

    auth_allowed_algorithms: str = Field(
        "RS256,RS384,RS512,ES256,ES384,ES512",
        description=(
            "Comma separated list of JWT signature algorithms that are accepted when"
            " verifying bearer tokens. This MUST only contain asymmetric algorithms:"
            " the verification key is the public key obtained from the auth provider's"
            " JWKS endpoint, so allowing symmetric algorithms (HS256/HS384/HS512) would"
            " enable algorithm-confusion attacks where an attacker signs a forged token"
            " with the (public) key as an HMAC secret. The default covers the RSA and"
            " ECDSA algorithms commonly offered by OpenID Connect providers such as"
            " Keycloak; adjust it to match the algorithm(s) your provider signs with."
        ),
        validation_alias="HD_AUTH_ALLOWED_ALGORITHMS",
        examples=["RS256", "RS256,ES256"],
    )

    auth_verify_certs: bool = Field(True, validation_alias="HD_AUTH_VERIFY_CERTS")

    auth_role_key: str = Field(
        "roles",
        description=(
            "Under which key of the access token payload the roles will be expected as a list."
        ),
        validation_alias="HD_AUTH_ROLE_KEY",
    )

    auth_allowed_role: str | None = Field(
        None,
        description=(
            "Role provided in bearer access token that is allowed access."
            " If None, role is not checked / everybody is allowed."
        ),
        validation_alias="HD_AUTH_ALLOWED_ROLE",
    )

    auth_runtime_engine_url_by_role: RoleToRuntimeEngineUrlMapping | None = Field(
        None,
        description=(
            "Map roles to runtime service urls. This allows to refer multiple runtime services"
            " and delegate executions to specific runtime instances by provided role."
            " An example is to have an additonal role hd-privileged-user mapped to a runtime"
            " service with additional privileges or credentials. Note that the first matching role"
            " found in the token is used to determine the runtime url. If no match is found,"
            " hd_runtime_engine_url will be used instead."
        ),
        validation_alias="HD_AUTH_RUNTIME_ENGINE_URL_BY_ROLE",
    )

    auth_reload_public_key: bool = Field(
        True,
        description="Whether public keys for signature check will be reloaded"
        " if a verification fails and if they are old",
        validation_alias="HD_AUTH_RELOAD_PUBLIC_KEY",
    )

    auth_public_key_reloading_minimum_age: datetime.timedelta = Field(
        datetime.timedelta(seconds=15),
        description="If auth fails and auth_reload_public_key is True "
        "public keys are only tried to load again if older than this timedelta."
        " Can be either seconds as int or float or an ISO 8601 timedelta string",  # 15 seconds
        validation_alias="HD_AUTH_KEY_RELOAD_MINIMUM_AGE",
        examples=["P0DT00H00M15S"],
    )

    auth_bearer_token_for_outgoing_requests: SecretStr | None = Field(
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
        validation_alias="HD_BEARER_TOKEN_FOR_OUTGOING_REQUESTS",
    )

    internal_auth_mode: InternalAuthMode = Field(
        InternalAuthMode.FORWARD_OR_FIXED,
        description=(
            "How outgoing requests to internal services should be handled."
            " For example from backend to runtime if both are run as separate services."
            " One of "
            ", ".join(['"' + x.value + '"' for x in list(InternalAuthMode)])
        ),
        validation_alias="HD_INTERNAL_AUTH_MODE",
    )

    internal_auth_client_credentials: ServiceCredentials | Json[ServiceCredentials] | None = Field(
        None,
        description=(
            "Client credentials as json encoded string."
            " For details confer the ServiceCredentials model class in the auth_outgoing.py"
            " file."
        ),
        examples=[
            (
                '{"realm": "my-realm", "auth_url": "https://test.com", "audience": "account",'
                ' "grant_credentials": {"grant_type": "client_credentials",'
                ' "client_id": "my-client",'
                ' "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false},'
                ' "post_kwargs": {}}'
            )
        ],
        validation_alias="HD_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS",
    )

    scheduling_internal_auth_mode: SchedulingInternalAuthMode = Field(
        SchedulingInternalAuthMode.OFF,
        description=(
            "How outgoing requests to internal services should be handled if part of a"
            " scheduled execution."
            " For example from backend to runtime if both are run as separate services."
            " One of "
            ", ".join(['"' + x.value + '"' for x in list(SchedulingInternalAuthMode)])
        ),
        validation_alias="HD_SCHEDULING_INTERNAL_AUTH_MODE",
    )

    scheduling_internal_auth_client_credentials: (
        ServiceCredentials | Json[ServiceCredentials] | None
    ) = Field(
        None,
        description=(
            "Client credentials as json encoded string."
            " For details confer the ServiceCredentials model class in the auth_outgoing.py"
            " file."
        ),
        examples=[
            (
                '{"realm": "my-realm", "auth_url": "https://test.com", "audience": "account",'
                ' "grant_credentials": {"grant_type": "client_credentials",'
                ' "client_id": "my-scheduled-job-client",'
                ' "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false},'
                ' "post_kwargs": {}}'
            )
        ],
        validation_alias="HD_SCHEDULING_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS",
    )

    external_auth_mode: ExternalAuthMode = Field(
        ExternalAuthMode.FORWARD_OR_FIXED,
        description=(
            "How outgoing requests to external services should be handled."
            " For example from runtime to adapters or during export/import."
            " One of "
            ", ".join(['"' + x.value + '"' for x in list(ExternalAuthMode)])
        ),
        validation_alias="HD_EXTERNAL_AUTH_MODE",
    )
    external_auth_client_credentials: ServiceCredentials | Json[ServiceCredentials] | None = Field(
        None,
        description="Client credentials as json encoded string.",
        examples=[
            (
                '{"realm": "my-realm", "auth_url": "https://test.com", "audience": "account",'
                ' "grant_credentials": {"grant_type": "client_credentials", "client_id":'
                ' "my-client",'
                ' "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false},'
                ' "post_kwargs": {}}'
            )
        ],
        validation_alias="HD_EXTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS",
    )

    maintenance_secret: SecretStr | None = Field(
        None,
        description="Secret necessary to access maintenance endpoints of the backend."
        " If this is set, the maintenance endpoints are activated."
        " To use them this secret is required as part of the payload."
        " Only alphanumeric characters are allowed",
        validation_alias="HD_MAINTENANCE_SECRET",
    )

    autoimport_directory: str = Field(
        "",
        description="Path to directory where to look for import sources during autoimport",
        validation_alias="HD_BACKEND_AUTOIMPORT_DIRECTORY",
    )

    otel_via_logfire_active: bool = Field(
        False,
        validation_alias="HD_OTEL_VIA_LOGFIRE_ACTIVE",
        description="Activate opentelemtry support via pydantic logfire",
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
        "|http://localhost:8080/adapters/virtual_structure"
        "|http://localhost:8090/adapters/virtual_structure,"
        "external-sources|External Sources"
        "|http://localhost:8090/adapters/external_sources"
        "|http://localhost:8090/adapters/external_sources,"
        "component-adapter|Component Adapter"
        "|http://localhost:8080/adapters/component"
        "|http://localhost:8080/adapters/component",
        validation_alias="HETIDA_DESIGNER_ADAPTERS",
        description=(
            "Information on installed / registered adapters in format"
            " key|Name|externalUrl|internalUrl,key2|Name2|externalUrl2|internalUrl2 ."
            " Must be configured for backend!"
            " If backend and runtime are separated this also can be used to tell"
            " the runtime the internal urls explicitely, so that the runtime does"
            " not have to query the backend's adapters endpoint. To enforce only"
            " using this fallback set HETIDA_DESIGNER_BACKEND_API_URL to an empty"
            " string for the runtime."
        ),
    )

    uri_wiring_shortcuts: dict[str, tuple[str, str]] = Field(
        {},
        validation_alias="HETIDA_DESIGNER_URI_WIRING_SHORTCUTS",
        description=(
            "Uri Wiring shortcuts: If the host part of the uri matches a key in this "
            "dictionary, the first entry of the value pair will be used as host "
            "(i.e. adapter_key) instead and the second part will be used as path (ref_id) "
            "instead. E.g. you might configure this to \n"
            '    {"pegel": ["component-adapter", "/230dfa9a-0efe-4418-a5b4-2ac3954ebd8f"]}\n'
            "and a user can then use a uri wiring of the form\n"
            "    hd://pegel?station=BONN&measurement=W\n"
            "instead of the much longer\n"
            "    hd://component-adapter/230dfa9a-0efe-4418-a5b4-2ac3954ebd8f?station=BONN&measurement=W\n"
            "Furthermore this allows to configuratively switch to another version of a component"
            " adapter source while keeping uri wirings as they are."
        ),
    )

    hd_runtime_engine_url: str = Field(
        "http://hetida-designer-runtime:8090/engine/",
        validation_alias="HETIDA_DESIGNER_RUNTIME_ENGINE_URL",
        description=(
            "URL to runtime engine. Note that if auth_runtime_engine_url_by_role is set"
            " this usually should point to the least privileged runtime service instance, as"
            " it is the fallback."
        ),
    )

    hd_runtime_verify_certs: bool = Field(
        True, validation_alias="HETIDA_DESIGNER_RUNTIME_VERIFY_CERTS"
    )

    # For scripts (e.g. transformation deployment)
    hd_backend_api_url: str = Field(
        "http://hetida-designer-backend:8090/api/",
        validation_alias="HETIDA_DESIGNER_BACKEND_API_URL",
        description=(
            "URL to backend. Necessary for transformation deployment "
            "and to allow runtime to access adapters endpoint."
            " The runtime can fallback to HETIDA_DESIGNER_ADAPTERS, i.e. the"
            " registered adapters. To enforce this and decouple runtime from designer"
            " you can set this configuration here to an empty string."
        ),
    )
    hd_backend_use_basic_auth: bool = Field(
        False,
        validation_alias="HETIDA_DESIGNER_BACKEND_USE_BASIC_AUTH",
        description=(
            "Whether Backend is protected via Basic Auth."
            " Only necessary for component deployment."
            " If Backend is protected via OpenIDConnect instead "
            " use the corresponding environment variables!"
        ),
    )
    hd_backend_basic_auth_user: str | None = Field(
        None,
        validation_alias="HETIDA_DESIGNER_BASIC_AUTH_USER",
        description="Basic Auth User",
    )
    hd_backend_basic_auth_password: SecretStr | None = Field(
        None,
        validation_alias="HETIDA_DESIGNER_BASIC_AUTH_PASSWORD",
        description="Basic Auth Password",
    )
    hd_backend_verify_certs: bool = Field(
        True, validation_alias="HETIDA_DESIGNER_BACKEND_VERIFY_CERTS"
    )
    hd_adapters_verify_certs: bool = Field(
        True, validation_alias="HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS"
    )

    hd_stream_mode: None | ExecByIdBase = Field(
        None,
        description=(
            "If this is set, all backend, runtime and adapter webservices are deactivated. "
            "Instead the provided execution input is run continuously: "
            "Generator-like adapters / adaper sources are invoked as such. "
            "Function-like adapters / adapter sources are invoked repeatedly "
            "The same applies to sinks for sending data: If they are generator-like "
            "data is send into the generator-like construct implying that the "
            "sink can have state."
        ),
        validation_alias="HETIDA_DESIGNER_STREAM_MODE",
    )

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
        validation_alias="HETIDA_DESIGNER_KAFKA_CONSUMPTION_MODE",
    )

    hd_kafka_consumer_enabled: bool = Field(
        False,
        description="Whether a Kafka consumer for executing workflows/components is enabled",
        validation_alias="HETIDA_DESIGNER_KAFKA_ENABLED",
    )

    hd_kafka_consumer_topic: str = Field(
        "hd-execution-topic",
        description="The topic to which the execution consumer will listen",
        validation_alias="HETIDA_DESIGNER_KAFKA_CONSUMER_TOPIC",
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
        examples=[
            {
                "bootstrap_servers": "kafka:19092",
                "group_id": "hd_kafka_consumer_group",
                "auto_commit_interval_ms": 1000,
                "auto_offset_reset": "earliest",
            }
        ],
        validation_alias="HETIDA_DESIGNER_KAFKA_CONSUMER_OPTIONS",
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
        examples=[{"bootstrap_servers": "kafka:19092"}],
        validation_alias="HETIDA_DESIGNER_KAFKA_PRODUCER_OPTIONS",
    )

    hd_kafka_response_topic: str = Field(
        "hd-execution-response-topic",
        description="The topic to which the execution consumer send execution results",
        validation_alias="HETIDA_DESIGNER_KAFKA_RESPONSE_TOPIC",
    )

    scheduling_active: bool = Field(
        True,
        description=(
            "Whether scheduling is activated for this service. "
            "Requires is_backend_service to be true!"
        ),
        validation_alias="HETIDA_DESIGNER_SCHEDULING_ACTIVE",
    )

    scheduling_sync_interval_seconds: int = Field(
        30,
        description=(
            "The scheduler syncs active jobs periodically from the database."
            "This defines the sync interval in seconds."
        ),
        validation_alias="HETIDA_DESIGNER_SCHEDULING_SYNC_INTERVAL_SECONDS",
    )

    scheduling_executions_retention_deletion_job_interval_seconds: int = Field(
        300,
        description="Time in seconds between two runs of the schedule executions"
        " table cleanup r Retention job.",
        alias="HETIDA_DESIGNER_SCHEDULING_RETENTION_JOB_TRIGGER_INTERVAL_SECONDS",
    )

    scheduling_executions_retention: datetime.timedelta = Field(
        datetime.timedelta(days=2),
        description="When the retention / cleanup job for schedule execution entries"
        " is run, this determines which entries are deleted: Everything older than now"
        " minus the specified timedelta. Accepts an ISO 8601 timedelta, see"
        " https://en.wikipedia.org/wiki/ISO_8601#Durations. E.G. P14D for fourteen days.",
        alias="HETIDA_DESIGNER_SCHEDULING_RETENTION_TIMEDELTA",
    )

    target_alembic_revision: str = Field(
        "head",
        description="alembic revision towards which migrations are run.",
        alias="HD_TARGET_ALEMBIC_REVISION",
    )

    @field_validator("internal_auth_client_credentials")
    @classmethod
    def internal_auth_client_credentials_set_if_internal_auth_mode_is_client(
        cls,
        v: Json[ServiceCredentials] | None,
        info: ValidationInfo,
    ) -> Json[ServiceCredentials] | None:
        internal_auth_mode = info.data["internal_auth_mode"]

        if internal_auth_mode == InternalAuthMode.CLIENT and v is None:
            msg = (
                "If internal auth mode is set to CLIENT, "
                "internal auth client credentials must be configured"
            )
            raise ValueError(msg)
        return v

    @field_validator("external_auth_client_credentials")
    @classmethod
    def external_auth_client_credentials_set_if_external_auth_mode_is_client(
        cls,
        v: Json[ServiceCredentials] | None,
        info: ValidationInfo,
    ) -> Json[ServiceCredentials] | None:
        external_auth_mode = info.data["external_auth_mode"]

        if external_auth_mode == ExternalAuthMode.CLIENT and v is None:
            msg = (
                "If external auth mode is set to CLIENT, "
                "external auth client credentials must be configured"
            )
            raise ValueError(msg)
        return v

    @field_validator("maintenance_secret")
    @classmethod
    def maintenance_secret_allowed_characters(cls, v: SecretStr | None) -> SecretStr | None:
        if v is None:
            return v
        if not maintenance_secret_pattern.fullmatch(v.get_secret_value()):
            raise ValueError(
                "Only numbers and alphabet letters allowed for the maintenance secret"
                " and it must have non-zero length."
            )
        return v

    @field_validator("is_runtime_service")
    @classmethod
    def must_be_at_least_backend_or_runtime(cls, v: bool, info: ValidationInfo) -> bool:
        is_backend_service = info.data["is_backend_service"]

        if not (v or is_backend_service):
            msg = (
                "At least one of is_backend_service or is_runtime_service must be true. "
                "It does not make sense to start the service with no active endpoints."
            )
            raise ValueError(msg)
        return v

    @field_validator("hd_backend_api_url")
    @classmethod
    def backend_api_url_ends_with_slash(cls, v: str) -> str:
        """make it end with a slash"""
        if not v.endswith("/"):
            v += "/"
        return v

    @field_validator("sqlalchemy_connection_string")
    @classmethod
    def database_url(
        cls, v: SecretStr | SQLAlchemy_DB_URL | None, info: ValidationInfo
    ) -> SecretStr | SQLAlchemy_DB_URL | None:
        if v is None:
            pw_secret = info.data["sqlalchemy_db_password"]
            return SQLAlchemy_DB_URL.create(
                drivername=info.data["sqlalchemy_db_drivername"],
                username=info.data["sqlalchemy_db_user"],
                password=(
                    pw_secret.get_secret_value() if isinstance(pw_secret, SecretStr) else pw_secret
                ),
                host=info.data["sqlalchemy_db_host"],
                port=info.data["sqlalchemy_db_port"],
                database=info.data["sqlalchemy_db_database"],
            )
        return v


environment_file = os.environ.get("HD_RUNTIME_ENVIRONMENT_FILE", None)

runtime_config = RuntimeConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_config() -> RuntimeConfig:
    return runtime_config
