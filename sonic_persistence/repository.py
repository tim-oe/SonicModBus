"""Repository for persisting and querying :class:`SensorReadingEntity` records."""

from datetime import datetime

from sonic_modbus.sensor_reading import SensorReading
from sqlalchemy.orm import Session

from sonic_persistence.models import SensorReadingEntity


class SensorReadingRepository:
    """Provides save and query operations for :class:`SensorReadingEntity`.

    The repository accepts a :class:`sqlalchemy.orm.Session` at construction
    time so callers control transaction boundaries (e.g. via
    :func:`sonic_persistence.database.get_session`).

    Args:
        session: An open SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, reading: SensorReading) -> SensorReadingEntity:
        """Persist a :class:`SensorReading` and return the stored entity.

        The entity is flushed to the database so its auto-generated *id* and
        *recorded_at* fields are populated before this method returns.

        Args:
            reading: The sensor reading to persist.

        Returns:
            The newly created :class:`SensorReadingEntity` with its database
            identity set.
        """
        entity = SensorReadingEntity(
            read_time=datetime.now(),
            wind_speed_ms=reading.wind_speed_ms,
            wind_direction=int(reading.wind_direction),
            wind_angle_deg=reading.wind_angle_deg,
            humidity_pct=reading.humidity_pct,
            temperature_c=reading.temperature_c,
            noise_db=reading.noise_db,
            pm25_ugm3=reading.pm25_ugm3,
            pm10_ugm3=reading.pm10_ugm3,
            atm_pressure_kpa=reading.atm_pressure_kpa,
            light_lux=reading.light_lux,
            rainfall_mm=reading.rainfall_mm,
        )
        self._session.add(entity)
        self._session.flush()
        return entity

    def find_by_id(self, reading_id: int) -> SensorReadingEntity | None:
        """Look up a single entity by primary key.

        Args:
            reading_id: The integer primary key to look up.

        Returns:
            The matching :class:`SensorReadingEntity`, or ``None`` if not found.
        """
        return self._session.get(SensorReadingEntity, reading_id)

    def find_all(self) -> list[SensorReadingEntity]:
        """Return all stored sensor readings ordered by *recorded_at* ascending.

        Returns:
            A list of :class:`SensorReadingEntity` objects, oldest first.
        """
        return (
            self._session.query(SensorReadingEntity)
            .order_by(SensorReadingEntity.read_time)
            .all()
        )

    def delete(self, reading_id: int) -> bool:
        """Remove a stored sensor reading by primary key.

        Args:
            reading_id: The primary key of the record to remove.

        Returns:
            ``True`` if a record was deleted, ``False`` if it did not exist.
        """
        entity = self.find_by_id(reading_id)
        if entity is None:
            return False
        self._session.delete(entity)
        self._session.flush()
        return True
