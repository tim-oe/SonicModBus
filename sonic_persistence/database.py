"""Database engine, session factory, and pyway migration helpers."""

import subprocess
from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from sonic_persistence.config import DatabaseConfig
from sonic_persistence.models import Base


def create_db_engine(config: DatabaseConfig) -> Engine:
    """Return a configured SQLAlchemy :class:`Engine`.

    Args:
        config: Database configuration.

    Returns:
        A ready-to-use SQLAlchemy engine.
    """
    return create_engine(config.db_url)


def create_session_factory(config: DatabaseConfig) -> sessionmaker[Session]:
    """Return a :class:`sessionmaker` bound to the engine described by *config*.

    Args:
        config: Database configuration.

    Returns:
        A session factory.
    """
    engine = create_db_engine(config)
    return sessionmaker(bind=engine)


@contextmanager
def get_session(
    session_factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    """Context manager that yields a session with automatic commit/rollback.

    Args:
        session_factory: Factory produced by :func:`create_session_factory`.

    Yields:
        An open :class:`Session`.

    Raises:
        Exception: Re-raises any exception after rolling back the transaction.
    """
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _sqlite_path_from_url(db_url: str) -> str:
    """Extract the file-system path from a SQLite connection URL.

    Args:
        db_url: SQLAlchemy SQLite URL, e.g. ``sqlite:///foo.db``.

    Returns:
        The path portion of the URL (relative or absolute).
    """
    return db_url[len("sqlite:///"):]


def _mysql_pyway_args(db_url: str) -> list[str]:
    """Build pyway CLI connection arguments for a MySQL/MariaDB URL.

    Strips the scheme and optional driver suffix (e.g. ``mariadb+mysqlconnector``
    or ``mysql+mysqlconnector``) before parsing so that
    :func:`urllib.parse.urlparse` resolves the components correctly.

    Args:
        db_url: SQLAlchemy MySQL/MariaDB connection URL.

    Returns:
        A flat list of ``--flag value`` pairs ready to extend a pyway command.
    """
    scheme = db_url.split("://", 1)[0]
    if "+" in scheme or not scheme.startswith("mysql"):
        db_url = "mysql://" + db_url.split("://", 1)[1]
    parsed = urlparse(db_url)
    return [
        "--database-host", parsed.hostname or "localhost",
        "--database-port", str(parsed.port or 3306),
        "--database-name", parsed.path.lstrip("/"),
        "--database-username", parsed.username or "",
        "--database-password", parsed.password or "",
    ]


def run_migrations(config: DatabaseConfig) -> None:
    """Apply pending pyway migrations to the target database.

    Constructs the appropriate pyway CLI arguments from *config* and invokes
    ``pyway migrate`` as a subprocess.

    Args:
        config: Database configuration.

    Raises:
        subprocess.CalledProcessError: If pyway exits with a non-zero status.
        ValueError: If the database type cannot be inferred from *db_url*.
    """
    url = config.db_url
    if url.startswith("sqlite"):
        db_type = "sqlite"
        db_args = ["--database-name", _sqlite_path_from_url(url)]
    elif url.startswith("mysql") or url.startswith("mariadb"):
        db_type = "mysql"
        db_args = _mysql_pyway_args(url)
    elif url.startswith("postgresql") or url.startswith("postgres"):
        db_type = "postgres"
        db_args = _mysql_pyway_args(url.replace("postgresql", "mysql", 1))
    else:
        raise ValueError(f"Cannot infer pyway database type from URL: {url!r}")

    cmd = [
        "pyway",
        "migrate",
        "--database-type", db_type,
        "--database-migration-dir", config.migration_dir,
        "--database-table", config.pyway_table,
        *db_args,
    ]
    subprocess.run(cmd, check=True)


def init_db(config: DatabaseConfig) -> None:
    """Create all tables that are not yet present (development / testing helper).

    Uses SQLAlchemy's ``create_all`` rather than pyway migrations.  This is
    intended for unit tests and local experimentation; prefer
    :func:`run_migrations` for production deployments.

    Args:
        config: Database configuration.
    """
    engine = create_db_engine(config)
    Base.metadata.create_all(engine)
