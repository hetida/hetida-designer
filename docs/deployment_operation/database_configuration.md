# Database Configuration

The hetida designer backend stores components, workflows and further data like schedules in a database. PostgreSQL is recommended. A runtime service without backend (`HD_IS_BACKEND_SERVICE=false`) does not need a database.

## Database connection

The database connection is configured on the backend service either as a complete [SQLAlchemy database URL](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)

* `HD_DATABASE_URL`, e.g. `postgresql+psycopg://hetida_designer_dbuser:hetida_designer_dbpasswd@hetida-designer-db:5432/hetida_designer_db`

or via its parts

* `HD_DB_HOST` (default `hetida-designer-db`)
* `HD_DB_PORT` (default `5432`; its older name `HD_DATABASE_PORT` still works, `HD_DB_PORT` takes precedence over it if both are environment variables or both are in the environment file)
* `HD_DB_DATABASE` (default `hetida_designer_db`)
* `HD_DB_USER` (default `hetida_designer_dbuser`)
* `HD_DB_PASSWORD` (default `hetida_designer_dbpasswd`)
* `HD_DB_DRIVERNAME` (default `postgresql+psycopg`)

!!! warning
    If `HD_DATABASE_URL` is set, the parts `HD_DB_HOST`, `HD_DB_PORT`, `HD_DB_DATABASE`, `HD_DB_USER`, `HD_DB_PASSWORD` and `HD_DB_DRIVERNAME` are ignored completely, also if `HD_DATABASE_URL` is set in the environment file (see below) and the parts as environment variables. The backend logs a warning in this case.

The backend logs the database it uses at start and when running the migrations, e.g. `postgresql+psycopg://hetida_designer_dbuser:***@hetida-designer-db:5432/hetida_designer_db`, without password.

A SQLite database file in the container, e.g. `HD_DATABASE_URL="sqlite+pysqlite:////data/hd.db"`, is kept only as long as the container exists, unless its directory is a volume.

## Environment file

Backend and runtime additionally read their settings, e.g. the database connection described above, from an environment (.env) file if its path is set via `HD_RUNTIME_ENVIRONMENT_FILE`. Environment variables take precedence over values from the environment file.

The docker images do not contain an environment file. They use one only if `HD_RUNTIME_ENVIRONMENT_FILE` is set. If the file set via `HD_RUNTIME_ENVIRONMENT_FILE` does not exist, backend and runtime log a warning and use only the environment variables and defaults.

!!! warning
    The environment file may only contain these settings. Backend and runtime refuse to start if it contains other variables, like `HD_BACKEND_AUTOIMPORT_DIRECTORY_*`, `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP`, `WEB_CONCURRENCY`, `HOST`, `PORT` or `HETIDA_DESIGNER_PURE_UVICORN`. Set them as environment variables (adapter settings like `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` alternatively in the environment file of the adapter, see its documentation).

## Database preparation at backend start

At its start, the backend prepares the database before its web server starts, in this order:

1. Migrations of the database schema to the revision `HD_TARGET_ALEMBIC_REVISION` (default `head`, i.e. the latest revision)
2. [Deployment of base components and workflows](./trafo_import_export/base_trafo_deployment.md)
3. Prepopulation of the [virtual structure adapter](../integration_guide/adapter_system/builtin_adapters/virtual_structure_adapter.md) if `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` is `true`
4. [Autoimport](./trafo_import_export/autoimport.md) if `HD_BACKEND_AUTOIMPORT_DIRECTORY` is set

Each step runs once per start of the backend, also with several web server processes (`WEB_CONCURRENCY`).

Every container running as backend service (i.e. `HD_IS_BACKEND_SERVICE` not `false`) runs these steps at each of its starts, e.g. also replicas of the backend, [restricted execution services](../integration_guide/trafo_exec_guide/restricted_webservice.md) or containers in kafka consumption mode using the same database. In particular, a container of a newer version migrates the database for all of them. If a container of an older version starts later, it fails at the migrations if the newer version changed the database schema, and otherwise overwrites the base components and workflows with its older versions by default, see [Deployment of base components and workflows](./trafo_import_export/base_trafo_deployment.md). Therefore use the same version for all these containers, and consider to deactivate deployment, prepopulation and autoimport for all but one of them via `HD_BACKEND_AUTODEPLOY_BASE_TRANSFORMATIONS=false` and not setting `PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP` and `HD_BACKEND_AUTOIMPORT_DIRECTORY`. In particular, the prepopulation deletes and recreates an existing virtual structure at each start by default.

## In-memory database

An in-memory SQLite database, e.g. `HD_DATABASE_URL="sqlite+pysqlite:///:memory:"`, is meant for local development, see [Development Setup](../development/development-setup.md). All components, workflows and further data stored in it are lost when the backend stops, and scheduling is not available.

Since this is usually not wanted, the backend container refuses to start with an in-memory database unless it is allowed explicitly by setting

* `HD_ALLOW_IN_MEMORY_DB=true` (default `false`)

An in-memory database exists only in the process using it. Therefore it additionally requires

* a single web server process, i.e. `WEB_CONCURRENCY` unset or `1` (also outside the docker image, e.g. for local development), and
* the pure uvicorn mode, i.e. not the deprecated gunicorn mode.

The steps of the database preparation described above then run in the web server process when it starts, instead of before.
