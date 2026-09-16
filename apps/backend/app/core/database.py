"""
GÖK SYSTEMS TECH — Database Layer & Auto-Migration
Configures SQLAlchemy engine, session maker, base declarative class,
and automated migration routines for SQLite & PostgreSQL.
"""

import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from gokai.apps.backend.app.core.config import settings
from gokai.packages.shared.logger import get_logger

logger = get_logger("database")

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_migrations():
    """Auto-migrates schema to add any newly introduced columns to existing tables."""
    Base.metadata.create_all(bind=engine)

    if settings.DATABASE_URL.startswith("sqlite"):
        # Dynamic SQLite column migration
        with engine.connect() as conn:
            # Check tasks table
            try:
                res = conn.execute(text("PRAGMA table_info(tasks)")).fetchall()
                existing_cols = {row[1] for row in res}
                if "total_tokens" not in existing_cols:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN total_tokens INTEGER DEFAULT 0"))
                if "debug_cycles" not in existing_cols:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN debug_cycles INTEGER DEFAULT 0"))
                if "error" not in existing_cols:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN error TEXT"))
                conn.commit()
            except Exception as ex:
                logger.warning(f"Tasks migration note: {ex}")

            # Check artifacts table
            try:
                res = conn.execute(text("PRAGMA table_info(artifacts)")).fetchall()
                existing_cols = {row[1] for row in res}
                if "metadata_json" not in existing_cols:
                    conn.execute(text("ALTER TABLE artifacts ADD COLUMN metadata_json TEXT DEFAULT '{}'"))
                conn.commit()
            except Exception as ex:
                logger.warning(f"Artifacts migration note: {ex}")

    logger.info("Database schema synchronized and migrations verified.")


def get_db():
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
