from sqlalchemy import create_engine, MetaData, text as sa_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
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

# Створення сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# SQLAlchemy база для моделей
Base = declarative_base(metadata=metadata)
Base.query = db_session.query_property()

# Клас для сумісності з попередньою версією на Flask-SQLAlchemy
class SQLAlchemyWrapper:
    def __init__(self):
        self.session = db_session
        self.Model = Base
        self.metadata = metadata
        self.engine = engine
    
    def create_all(self):
        Base.metadata.create_all(bind=engine)
    
    def init_app(self, app):
        # Заглушка для сумісності
        pass

# Для зворотної сумісності з Flask-SQLAlchemy
db = SQLAlchemyWrapper()
text = sa_text

# Функція для отримання залежності бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

__all__ = [
    "db",
    "text",
    "get_db",
    "db_session",
    "Base"
]
