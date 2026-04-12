"""SQLAlchemy ORM entity for a SEN0658 sensor reading."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ---------------------------------------------------------------------------
# Reusable column type aliases
#
# Each alias uses a portable SQLAlchemy generic type as its base so that
# SQLite (used in unit tests) renders standard DDL.  The ``with_variant``
# call attaches the MariaDB/MySQL-specific type so that production migrations
# receive the correct ``UNSIGNED`` constraints.
# ---------------------------------------------------------------------------

_UnsignedInt = Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql")
_UnsignedTinyInt = Integer().with_variant(mysql.TINYINT(unsigned=True), "mysql")
_UnsignedSmallInt = Integer().with_variant(mysql.SMALLINT(unsigned=True), "mysql")
_UnsignedDouble = Float().with_variant(mysql.DOUBLE(unsigned=True), "mysql")
_SignedDouble = Float().with_variant(mysql.DOUBLE(), "mysql")


class Base(DeclarativeBase):
    """Declarative base shared by all sonic_persistence models."""


class SensorReadingEntity(Base):
    """Persistent representation of a single SEN0658 weather sensor reading.

    Non-negative measurement columns are declared ``UNSIGNED`` for
    MariaDB/MySQL.  ``temperature_c`` remains signed as it can be below zero.
    Unit tests run against SQLite which uses the generic base types and
    ignores the ``unsigned`` flag.
    """

    __tablename__ = "sonic_reading"

    id: Mapped[int] = mapped_column(
        _UnsignedInt, primary_key=True, autoincrement=True
    )
    read_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    wind_speed_ms: Mapped[float] = mapped_column(_UnsignedDouble)
    wind_direction: Mapped[int] = mapped_column(_UnsignedTinyInt)
    wind_angle_deg: Mapped[int] = mapped_column(_UnsignedSmallInt)
    humidity_pct: Mapped[float] = mapped_column(_UnsignedDouble)
    temperature_c: Mapped[float] = mapped_column(_SignedDouble)
    noise_db: Mapped[float] = mapped_column(_UnsignedDouble)
    pm25_ugm3: Mapped[int] = mapped_column(_UnsignedInt)
    pm10_ugm3: Mapped[int] = mapped_column(_UnsignedInt)
    atm_pressure_kpa: Mapped[float] = mapped_column(_UnsignedDouble)
    light_lux: Mapped[int] = mapped_column(_UnsignedInt)
    rainfall_mm: Mapped[float] = mapped_column(_UnsignedDouble)

    def __repr__(self) -> str:
        return (
            f"SensorReadingEntity(id={self.id!r}, read_time={self.read_time!r}, "
            f"temperature_c={self.temperature_c!r}, wind_speed_ms={self.wind_speed_ms!r})"
        )
