# SQL Adapter
The built-in sql adapter allows to access data from and write data to arbitrary sql databases.

More specifically, it enables
* Reading tables / arbitrary queries from sql databases thereby retrieving results as dataframes
* Writing dataframes to tables, either replacing the complete target table or appending to it. Tables are created in both cases if necessary.
* Reading and writing timeseries data from sql databases (e.g. timescale db).

Multiple sql databases can be configured at the same time. For configuration of each database a [sqlalchemy compatible connection uri](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) is required and the necessary sql driver Python libraries must [be installed](../custom_python_dependencies.md). Sqlite support as well as postgres support via [psycopg2](https://pypi.org/project/psycopg2/) are preinstalled.

## Limitations
Under the hood this adapter simply invokes Pandas' built-in [read_sql_table](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_table.html), [read_sql_query](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_query.html) and [to_sql](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html) methods. In particular access is sequential and configurability of some possibly relevant aspects like connection management is limited. Additionally, parsing of data types is handled by Pandas automatically and cannot be configured in detail.

While providing robust, basic sql connectivity, the sql adapter can be regarded as a good starting point / template for development of more individual sql adapters fitting project specific needs.

## Security hints

This adapter allows execution of arbitrary SQL queries on the configured databases via the SQL Query data source. It runs user-provided queries without any escaping or validation. Moreover user-provided Python component code can directly access any configured database — there is no built-in hurdle in accordance with the default "completely trust all component code" security model mentioned in the main [Readme.md](../../README.md#security-hints).

Typically it is a good idea to restrict the configured database user's permissions to what is strictly necessary. E.g. if this adapter should only read from certain tables and not write, we highly recommend to restrict the configured database user to have read only access to exactly these required tables.

Furthermore communication between frontend, runtime and backend should be properly secured and encrypted (https...), since queries are exchanged between them using http requests.

Again, you should take the security hints of the main [Readme.md](../../README.md#security-hints) seriously and seek assistance from professional security consultants when feeling uncomfortable configuring hetida designer yourself.

## Configuration

As an example we configure two sqlite databases mounted on the runtime container and access to hetida designer's own postgres database.

This is based on the default docker-compose.yml setup — to start, make a copy of `docker-compose.yml` naming it `docker-compose-sql-example.yml` and edit the sections as follows.

### Configuring the runtime

As a [general custom adapter](general_custom_adapters/instructions.md) the sql adapter is built into the runtime and needs to know to which databases it should
connect to. For each database an internal key, a human readable name and a sqlalchemy compatible database connection url must be provided.

Furthermore the tables to be used as sinks can be configured:

* "append_tables" generate sinks that allow to append tabular data to them.
* "replace_tables" replace the complete table with the provided dataframe on each write!

Note that tables will be created and columns added automatically dependending on the data sent to these sinks.

Here we give an example configuration for mounting and accessing two sqlite databases and additionally access to hetida designer's own postgres db (only for demonstration, do not do this in a real setup!):

```yaml
  ...

  hetida-designer-runtime:
    
    ...

    volumes:
      ...
      - ./runtime/tests/data/sql_adapter:/mnt/sql_adapter_data

    ...

    environment:
      SQL_ADAPTER_ACTIVE: "true"
      SQL_ADAPTER_SQL_DATABASES: |
        [
          {
            "name": "sqlite example db (read only)",
            "key": "example_sqlite_db",
            "connection_url": "sqlite+pysqlite:////mnt/sql_adapter_data/example_sqlite.db",
            "append_tables": [],
            "replace_tables" : []
          },
          {
            "name": "writable sqlite db",
            "key": "temp_sqlite_db",
            "connection_url": "sqlite+pysqlite:////mnt/sql_adapter_data/writable_sqlite.db",
            "append_tables": ["append_alert_table", "model_run_stats"],
            "replace_tables" : ["model_config_params"]
          },
          {
            "name": "timeseries sqlite db",
            "key": "timeseries_sqlite_db",
            "connection_url": "sqlite+pysqlite:////mnt/sql_adapter_data/sqlite_with_tstables.db",
            "append_tables": [],
            "replace_tables" : [],
            "timeseries_tables": {
              "ro_ts_table": {
                "appendable": false,
                "metric_col_name": "metric",
                "timestamp_col_name": "timestamp",
                "fetchable_value_cols": ["value"],
                "writable_value_cols": [],
                "column_mapping_hd_to_db": {}
              },
              "ts_table": {
                "appendable": true,
                "metric_col_name": "metric",
                "timestamp_col_name": "timestamp",
                "fetchable_value_cols": ["value"],
                "writable_value_cols": ["value"],
                "column_mapping_hd_to_db": {}                
              }              
            }
          },
          {
            "name": "hd postgres",
            "key": "hd_postgres_db",
            "connection_url": "postgresql+psycopg2://hetida_designer_dbuser:hetida_designer_dbpasswd@hetida-designer-db:5432/hetida_designer_db",
            "append_tables": [],
            "replace_tables" : []            
          }
        ]
  ...
```

**Hint**: It is not possible to configure a postgres schema in a sqlalchemy connection url directly. We recommend to add all relevant schemas to the db user's search_path. E.g. if in the example above the timeseries table ts_table is in schema "timeseries", you can add that schema to the user's search path besides "public" by running the following SQL (with a sufficiently privileged user):
```sql
alter role hetida_designer_dbuser set search_path = timeseries, public
```

### Configuring the backend

Additionally, the sql adapter itself needs to be [registered](./adapter_registration.md) in the designer backend. In the default docker-compose setup the sql adapter is already configured. It's part of the environment variable `HETIDA_DESIGNER_ADAPTERS` is:

```
sql-adapter|SQL Adapter|http://localhost:8090/adapters/sql|http://localhost:8090/adapters/sql
```

If you have not changed anything else in your setup you may just leave this as is. Or set

```yaml
  ...

  hetida-designer-backend:

    ...

    environment:
      ...
      - HETIDA_DESIGNER_ADAPTERS="sql-adapter|SQL Adapter|http://localhost:8090/adapters/sql|http://localhost:8090/adapters/sql"
    ...
```
to explicitely activate only the sql adapter and no other adapters.


## Usage

### Basic Usage

After having made adaptions to the configuration described above you need to (re)start with

```bash
docker-compose -f docker-compose-sql-example.yml stop
docker-compose -f docker-compose-sql-example.yml up
```

In the execution dialog you should now be able to select "SQL Adapter" for inputs and outputs of type DATAFRAME.

As sources the selection dialog offers for each database
* All available tables. Choosing one will load the complete unfiltered table!
* A special "SQL Query" source which when selected allows to enter an arbitrary SQL query.

As sinks it offers only the explicitely configured append and replace tables for each configured database.

Similarly, for MULTITSFRAMEs you should be able to use the sql adapter's provided sources and sink for the configured timeseries tables. The example tables contain timeseries data for metrics `a`, `b` and `c` in august 2023. You can query all metrics by entering `ALL` into the filter.

