from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import SQLALCHEMY_DATABASE_URI

SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency для FastAPI

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
