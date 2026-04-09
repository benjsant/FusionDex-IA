"""Database connection utilities shared across ETL scripts."""

from __future__ import annotations

import os

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_pg_connection():
    """Raw psycopg2 connection — for bulk inserts."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "fusiondex_db"),
        user=os.getenv("POSTGRES_USER", "fusiondex_user"),
        password=os.getenv("POSTGRES_PASSWORD", "fusiondex_password"),
    )


def get_engine():
    url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'fusiondex_user')}"
        f":{os.getenv('POSTGRES_PASSWORD', 'fusiondex_password')}"
        f"@{os.getenv('POSTGRES_HOST', 'db')}"
        f":{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DB', 'fusiondex_db')}"
    )
    return create_engine(url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
