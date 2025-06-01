import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from mydb import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def include_object(object, name: str, type_, reflected, compare_to):
    """
    Should you include this table or not?
    """
    if type_ == 'table' and (name.startswith('_') or object.info.get("skip_autogenerate", False)):
        return False
    elif type_ == "column" and object.info.get("skip_autogenerate", False):
        return False
    return True

def get_engine_url():
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.getenv('DATABASE_URI')
        if db_url:
            return db_url.replace('%', '%%')
        else:
            # Фолбек на mydb
            from mydb import db
            return str(db.engine.url).replace('%', '%%')
    except Exception as e:
        raise e


# add your model's MetaData object here
# for 'autogenerate' support
from models import *  # Імпортуємо всі моделі

config.set_main_option('sqlalchemy.url', get_engine_url())
target_metadata = db.Model.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    return target_metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_engine_url()
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

