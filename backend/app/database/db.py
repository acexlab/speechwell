"""
File Logic Summary: Database connection and SQLAlchemy session factory setup used by backend services and routes.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..paths import SQLITE_DB_PATH

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

