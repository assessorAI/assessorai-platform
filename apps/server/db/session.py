import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = None
engine = None
SessionLocal = None

def init_db() -> None:
    """Create all tables. Call once at startup."""
    global DATABASE_URL, engine, SessionLocal
    print(f"init_db: os.environ DATABASE_URL = {os.environ.get('DATABASE_URL')}")
    if DATABASE_URL is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"init_db: DATABASE_URL set to {DATABASE_URL}")
        if not DATABASE_URL:
            db_user = os.getenv("DATABASE_USER", "postgres")
            db_password = os.getenv("DATABASE_PASSWORD", "postgres")
            db_hostname = os.getenv("DATABASE_HOSTNAME", "localhost")
            db_port = os.getenv("DATABASE_PORT", "5432")
            db_name = os.getenv("DATABASE_NAME", "assessorai")
            DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}"
            print(f"init_db: DATABASE_URL built to {DATABASE_URL}")
    if engine is None:
        print(f"Creating engine with {DATABASE_URL}")
        engine = create_engine(
            DATABASE_URL,
            echo=os.getenv("SQL_ECHO", "False") == "True",
            pool_pre_ping=True,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"Engine created: {engine}")
    # Ensure models are imported so metadata is aware of them
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
