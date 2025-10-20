from sqlalchemy import create_engine, MetaData, text as sa_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from fastapi import Depends
from app.config import SQLALCHEMY_DATABASE_URI

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Налаштування підключення до бази даних
metadata = MetaData(naming_convention=convention)
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_size=10,
    poolclass=QueuePool,
    pool_pre_ping=True,
    connect_args={'ssl': {'fake_flag_to_enable_tls': True}}
)

# Створення сесій - використовуємо autoflush=True для автоматичного flush перед commit
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

# SQLAlchemy база для моделей
Base = declarative_base(metadata=metadata)

# OLD: scoped_session approach (replaced by fastapi-sqlalchemy middleware)
# db_session = scoped_session(SessionLocal)
# Base.query = db_session.query_property()

# Simple wrapper class for backward compatibility with legacy code
class DBWrapper:
    """Minimal wrapper for backward compatibility - use fastapi_sqlalchemy.db instead"""
    def __init__(self):
        self.Model = Base
        self.metadata = metadata
        self.engine = engine  # Keep engine accessible for lifespan and migrations

    def create_all(self):
        """Create all tables"""
        Base.metadata.create_all(bind=engine)

    def init_app(self, app):
        """Compatibility stub"""
        pass

# For backward compatibility with legacy code
# NOTE: For new code, use: from fastapi_sqlalchemy import db
db = DBWrapper()
text = sa_text

# Dependency function for routes that use Depends(get_db)
def get_db():
    """Get database session - for routes using Depends(get_db)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = [
    "db",
    "text",
    "get_db",
    "Base",
    "engine",
    "metadata"
]
