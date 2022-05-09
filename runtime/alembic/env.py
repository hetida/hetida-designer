import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support

# target_metadata = mymodel.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_target_metadata():
    from hetdesrun.persistence.dbmodels import Base

    return Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    from hetdesrun.webservice.config import runtime_config

    url = (
        runtime_config.sqlalchemy_connection_string
    )  # config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_target_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from hetdesrun import configure_logging

    logger = logging.getLogger("hetdesrun")

    alembic_logger = logging.getLogger("alembic")
    configure_logging(alembic_logger)

    from hetdesrun.persistence import get_db_engine

    connectable = get_db_engine()

    logger.info(
        "Running online migrations with driver %s", connectable.url.get_driver_name()
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=get_target_metadata())
        logger.info("Connected to db for migrations")
        with context.begin_transaction():
            logger.info(
                "Beginning transaction. Dialect name is %s", connection.dialect.name
            )
            if connection.dialect.name == "postgresql":
                logger.info("Detected postgresql driver. Ensuring versioning table")
                # Make sure no two processed can migrate at the same time
                context.get_context()._ensure_version_table()  # pylint: disable=protected-access
                logger.info(
                    "Ensured versioning table. Now locking alembic version table"
                )
                connection.execute(
                    text("LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE")
                )
                # Postgres lock is released when transaction ends
            logger.info("actually starting to run migrations")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
