import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic config
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add backend folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import Base
from app.models import User, Property, PropertyUsers

target_metadata = Base.metadata


def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": settings.DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
