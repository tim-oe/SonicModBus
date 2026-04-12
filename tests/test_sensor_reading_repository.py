"""Tests for SensorReadingRepository using an in-memory SQLite database."""

import pytest
from sqlalchemy.orm import sessionmaker

from sonic_modbus.sensor_reading import SensorReading
from sonic_modbus.wind_direction import WindDirection
from sonic_persistence import DatabaseConfig, SensorReadingRepository
from sonic_persistence.database import create_db_engine, get_session, init_db
from sonic_persistence.models import Base


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def in_memory_config() -> DatabaseConfig:
    """DatabaseConfig pointing at a transient in-memory SQLite database."""
    return DatabaseConfig(db_url="sqlite:///:memory:")


@pytest.fixture
def session(in_memory_config: DatabaseConfig):
    """Provide a fresh SQLAlchemy session backed by an in-memory SQLite database.

    Tables are created via SQLAlchemy's ``create_all`` (bypassing pyway) so
    unit tests have no external dependencies.
    """
    engine = create_db_engine(in_memory_config)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    db_session = factory()
    yield db_session
    db_session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def repo(session) -> SensorReadingRepository:
    return SensorReadingRepository(session)


@pytest.fixture
def sample_reading() -> SensorReading:
    return SensorReading(
        wind_speed_ms=3.5,
        wind_direction=WindDirection.N,
        wind_angle_deg=0,
        humidity_pct=55.0,
        temperature_c=21.3,
        noise_db=42.1,
        pm25_ugm3=12,
        pm10_ugm3=18,
        atm_pressure_kpa=101.3,
        light_lux=500,
        rainfall_mm=0.0,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSensorReadingRepositorySave:
    def test_save_returns_entity_with_id(self, repo, sample_reading):
        entity = repo.save(sample_reading)
        assert entity.id is not None
        assert entity.id > 0

    def test_save_persists_all_fields(self, repo, sample_reading):
        entity = repo.save(sample_reading)
        assert entity.wind_speed_ms == pytest.approx(sample_reading.wind_speed_ms)
        assert entity.wind_direction == int(sample_reading.wind_direction)
        assert entity.wind_angle_deg == sample_reading.wind_angle_deg
        assert entity.humidity_pct == pytest.approx(sample_reading.humidity_pct)
        assert entity.temperature_c == pytest.approx(sample_reading.temperature_c)
        assert entity.noise_db == pytest.approx(sample_reading.noise_db)
        assert entity.pm25_ugm3 == sample_reading.pm25_ugm3
        assert entity.pm10_ugm3 == sample_reading.pm10_ugm3
        assert entity.atm_pressure_kpa == pytest.approx(sample_reading.atm_pressure_kpa)
        assert entity.light_lux == sample_reading.light_lux
        assert entity.rainfall_mm == pytest.approx(sample_reading.rainfall_mm)

    def test_save_multiple_readings_get_unique_ids(self, repo, sample_reading):
        e1 = repo.save(sample_reading)
        e2 = repo.save(sample_reading)
        assert e1.id != e2.id


class TestSensorReadingRepositoryFindById:
    def test_find_by_id_returns_saved_entity(self, repo, sample_reading):
        saved = repo.save(sample_reading)
        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.id == saved.id

    def test_find_by_id_returns_none_for_missing(self, repo):
        assert repo.find_by_id(9999) is None


class TestSensorReadingRepositoryFindAll:
    def test_find_all_empty_initially(self, repo):
        assert repo.find_all() == []

    def test_find_all_returns_all_saved(self, repo, sample_reading):
        repo.save(sample_reading)
        repo.save(sample_reading)
        assert len(repo.find_all()) == 2


class TestSensorReadingRepositoryDelete:
    def test_delete_existing_returns_true(self, repo, sample_reading):
        entity = repo.save(sample_reading)
        assert repo.delete(entity.id) is True

    def test_delete_removes_record(self, repo, sample_reading):
        entity = repo.save(sample_reading)
        repo.delete(entity.id)
        assert repo.find_by_id(entity.id) is None

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete(9999) is False


class TestSensorReadingRepositoryNegativeTemperature:
    def test_save_negative_temperature(self, repo):
        reading = SensorReading(
            wind_speed_ms=0.0,
            wind_direction=WindDirection.S,
            wind_angle_deg=180,
            humidity_pct=80.0,
            temperature_c=-15.2,
            noise_db=30.0,
            pm25_ugm3=5,
            pm10_ugm3=7,
            atm_pressure_kpa=99.8,
            light_lux=0,
            rainfall_mm=2.5,
        )
        entity = repo.save(reading)
        assert entity.temperature_c == pytest.approx(-15.2)


class TestSensorReadingRepositoryGetSession:
    """Verify that entity attributes are accessible inside the get_session block.

    This replicates the production usage pattern in collect_reading.py where
    entity.id is read while the session is still open (before commit+close).
    The detached-instance bug (bhk3) occurs when attributes are accessed after
    the session closes; keeping the access inside the ``with`` block is the fix.
    """

    @pytest.fixture
    def session_factory(self, in_memory_config: DatabaseConfig):
        engine = create_db_engine(in_memory_config)
        Base.metadata.create_all(engine)
        return sessionmaker(bind=engine)

    def test_entity_id_accessible_inside_get_session(
        self, session_factory, sample_reading
    ):
        """entity.id must be readable inside the with-block (session still open)."""
        captured_id = None
        with get_session(session_factory) as session:
            entity = SensorReadingRepository(session).save(sample_reading)
            captured_id = entity.id  # access while session is open — must not raise

        assert captured_id is not None
        assert captured_id > 0

    def test_entity_id_detaches_after_session_closes(
        self, session_factory, sample_reading
    ):
        """Accessing entity.id outside the with-block raises DetachedInstanceError.

        This documents the incorrect pattern that caused the production bug and
        ensures we never regress to calling log/print on the entity after close.
        """
        from sqlalchemy.orm.exc import DetachedInstanceError

        with get_session(session_factory) as session:
            entity = SensorReadingRepository(session).save(sample_reading)

        # session is now closed and entity is expired — any attribute access
        # that requires a DB round-trip must raise DetachedInstanceError
        with pytest.raises(DetachedInstanceError):
            _ = entity.wind_speed_ms  # non-PK attribute triggers lazy refresh
