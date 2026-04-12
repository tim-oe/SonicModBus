"""Database configuration for sonic_persistence."""

from dataclasses import dataclass, field
from pathlib import Path


_DEFAULT_MIGRATION_DIR = str(
    Path(__file__).parent / "db" / "migrations"
)


@dataclass
class DatabaseConfig:
    """Configuration for the persistence layer.

    Attributes:
        db_url: SQLAlchemy connection URL.  Defaults to a local MariaDB database.
            Examples:

            * ``mysql+mysqlconnector://user:pass@host:3306/dbname`` (MariaDB/MySQL)
            * ``postgresql+psycopg2://user:pass@host:5432/dbname`` (PostgreSQL)
            * ``sqlite:///sonic.db`` (SQLite – useful for local testing)
        migration_dir: Absolute or CWD-relative path to pyway SQL migration files.
        pyway_table: Name of the pyway schema-history table.
    """

    db_url: str = "mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather"
    migration_dir: str = field(default_factory=lambda: _DEFAULT_MIGRATION_DIR)
    pyway_table: str = "pyway_history"
