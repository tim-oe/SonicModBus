"""sonic_persistence – SQLAlchemy-backed persistence layer for SonicModBus.

Typical usage::

    from sonic_persistence import DatabaseConfig, SensorReadingRepository
    from sonic_persistence.database import init_db, get_session, create_session_factory

    config = DatabaseConfig()                    # MariaDB on localhost:3306/sonic
    init_db(config)                          # or run_migrations(config) for pyway
    factory = create_session_factory(config)

    with get_session(factory) as session:
        repo = SensorReadingRepository(session)
        repo.save(my_reading)
"""

from sonic_persistence.config import DatabaseConfig
from sonic_persistence.models import Base, SensorReadingEntity
from sonic_persistence.repository import SensorReadingRepository

__all__ = [
    "Base",
    "DatabaseConfig",
    "SensorReadingEntity",
    "SensorReadingRepository",
]
