"""Database engine/session/bootstrap."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base class for SQLAlchemy models."""


def _ensure_sqlite_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    db_file = Path(url.replace("sqlite:///", "", 1)).expanduser()
    db_file.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine_kwargs = {}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context-managed DB session for background workers."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create tables and ensure bootstrap records exist."""
    from app.models.entities import ModelVersion, User  # Imported lazily to avoid circular imports
    from app.services.auth_service import AuthService
    from ml.inference import MODEL_PATH

    Base.metadata.create_all(bind=engine)

    with db_session() as db:
        # Seed active model version if missing.
        version_name = Path(MODEL_PATH).stem
        existing_model = db.scalar(select(ModelVersion).where(ModelVersion.version == version_name))
        if existing_model is None:
            db.add(
                ModelVersion(
                    version=version_name,
                    path=str(MODEL_PATH),
                    accuracy=None,
                    status="active",
                    created_at=datetime.utcnow(),
                )
            )

        # Bootstrap admin account when no users exist.
        has_users = db.scalar(select(User.id).limit(1))
        if has_users is None and settings.bootstrap_admin_username and settings.bootstrap_admin_password:
            auth_service = AuthService()
            admin = auth_service.create_user(
                db=db,
                username=settings.bootstrap_admin_username,
                password=settings.bootstrap_admin_password,
                role=settings.bootstrap_admin_role,
            )
            db.add(admin)

