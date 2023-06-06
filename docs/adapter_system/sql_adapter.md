# SQL Adapter
The built-in sql adapter allows to access data from and write data to arbitrary sql databases.

More specifically, it enables
* Reading tables / arbitrary queries from sql databases thereby retrieving results as dataframes
* Writing dataframes to tables, either replacing the complete target table or appending to it. Tables are created in both cases if necessary.

Multiple sql databases can be configured at the same time. For configuration of each database a [sqlalchemy compatible connection uri](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) is required and the necessary sql driver Python libraries must [be installed](../custom_python_dependencies.md). Sqlite support as well as postgres support via [psycopg2](https://pypi.org/project/psycopg2/) are preinstalled.

**Note**: Under the hood this adapter simply invokes Pandas' built-in [read_sql_table](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_table.html), [read_sql_query](https://pandas.pydata.org/docs/reference/api/pandas.read_sql_query.html) and [to_sql](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html) methods. In particular access is sequential and configurability of typically relevant aspects like connection management is limited. This may lead to suboptimal performance for your concrete use case. Nevertheless the sql adapter can provide a good starting point / template for development of more individual sql adapters fitting project specific needs.

## Security hint

This adapter allows execution of arbitrary SQL queries on the configured databases via the SQL Query data source. It runs user-provided queries without any escaping or validation. Moreover user-provided Python component code can directly access any configured database — there is no built-in hurdle in accordance with the default "completely trust all component code" security model mentioned in the main [Readme.md](../../README.md#security-hints).

Typically it is a good idea to restrict the configured database user's permissions to what is strictly necessary. E.g. if this adapter should only read from certain tables and not write, we highly recommend to restrict the configured database user to have read only access to exactly these required tables.

Furthermore communication between frontend, runtime and backend should be properly secured and encrypted (https...), since queries are exchanged between them using http requests.

Again, you should take the security hints of the main [Readme.md](../../README.md#security-hints) seriously and seek assistance from professional security consultants when feeling uncomfortable configuring hetida designer yourself.

## Configuration

### Configuring the runtime

As a [general custom adapter](general_custom_adapter/instructions.md) the sql adapter is built into the runtime and needs to know to which databases it should
connect to. For each database an internal key, a human readable name and a sqlalchemy compatible database connection url must be provided.

Furthermore the tables to be used as sinks can be configured:

* "append_tables" generate sinks that allow to append tabular data to them.
* "replace_tables" replace the complete table with the provided dataframe on each write!

Example configuration for a sqlite database:

```yaml
  hetida-designer-runtime:
    ...
    environment:
      SQL_ADAPTER_SQL_DATABASES: '[{"name": "sqlite example db", "key": "example_sqlite_db", "connection_url": "sqlite+pysqlite:////example_data/example_sqlite.db", "append_tables": ["append_alert_table", "model_run_stats"], "replace_tables" : ["model_config_params"]}]'  
```

### Configuring the backend

Additionally the sql adapter itself needs to be [registered](./adapter_registration.md) in the designer backend. In the default docker-compose setup the sql adapter's part of the environment variable looks like this:

```
sql-adapter|SQL Adapter|http://localhost:8090/adapters/sql|http://localhost:8090/adapters/sql
```

If you have not changed anything else in your setup you may just leave this as is.


## Usage

### Basic Usage

After having made adaptions to the configuration described above you need to (re)start with

```bash
docker-compose stop
docker-compose up
```

In the execution dialog you should now be able to select "SQL Adapter" for inputs and outputs.

As sources the selction dialog offers
* All available tables. Choosing one will load the complete unfiltered table!
* A special "SQL Query" which when selected allows to enter an arbitrary SQL query.

As sinks it offers only the explicitely configured append and replace tables.

