"""Cron script: read one sample from the SEN0658 sensor and persist it to the DB.

Configuration is entirely via environment variables so no config file needs to
be present on the target machine:

    SONIC_PORT        Serial device path         (default: /dev/ttyUSB0)
    SONIC_BAUDRATE    Line speed in baud          (default: 4800)
    SONIC_DEVICE_ID   Modbus slave address 1-254  (default: 1)
    SONIC_DB_URL      SQLAlchemy connection URL
                      (default: mysql+mysqlconnector://sonic:sonic@localhost:3306/weather)

Exit codes
----------
0  Reading was taken and persisted successfully.
1  Sensor communication failed.
2  Database write failed.

Suggested crontab entry (every 5 minutes, log to file):

    */5 * * * * /path/to/.venv/bin/collect-reading >> /var/log/sonic_reading.log 2>&1
"""

import logging
import os
import sys

from sonic_modbus.constants import DEFAULT_BAUDRATE, DEFAULT_DEVICE_ID, DEFAULT_PORT
from sonic_modbus.sensor import SonicSensor
from sonic_persistence.config import DatabaseConfig
from sonic_persistence.database import create_session_factory, get_session
from sonic_persistence.repository import SensorReadingRepository

_LOG_FORMAT = "%(asctime)s %(levelname)-8s [collect_reading] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

logging.basicConfig(format=_LOG_FORMAT, datefmt=_DATE_FORMAT, level=logging.INFO)
log = logging.getLogger(__name__)


def _config_from_env() -> tuple[str, int, int, DatabaseConfig]:
    """Read runtime parameters from environment variables.

    Returns:
        Tuple of ``(port, baudrate, device_id, db_config)``.
    """
    port = os.environ.get("SONIC_PORT", DEFAULT_PORT)
    baudrate = int(os.environ.get("SONIC_BAUDRATE", str(DEFAULT_BAUDRATE)))
    device_id = int(os.environ.get("SONIC_DEVICE_ID", str(DEFAULT_DEVICE_ID)))
    db_url = os.environ.get(
        "SONIC_DB_URL",
        "mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather",
    )
    return port, baudrate, device_id, DatabaseConfig(db_url=db_url)


def main() -> int:
    """Read one sensor sample and write it to the database.

    Returns:
        0 on success, 1 on sensor error, 2 on database error.
    """
    port, baudrate, device_id, db_config = _config_from_env()

    log.info(
        "Connecting to sensor: port=%s baudrate=%d device_id=%d",
        port,
        baudrate,
        device_id,
    )

    try:
        with SonicSensor(port=port, baudrate=baudrate, device_id=device_id) as sensor:
            reading = sensor.read()
    except Exception as exc:
        log.error("Sensor read failed: %s", exc)
        return 1

    log.info(
        "Read OK — temp=%.1f°C wind=%.1fm/s %s(%d°) "
        "humidity=%.1f%% pressure=%.1fkPa noise=%.1fdB "
        "pm25=%dµg/m³ pm10=%dµg/m³ light=%dlux rain=%.1fmm",
        reading.temperature_c,
        reading.wind_speed_ms,
        reading.wind_direction.name,
        reading.wind_angle_deg,
        reading.humidity_pct,
        reading.atm_pressure_kpa,
        reading.noise_db,
        reading.pm25_ugm3,
        reading.pm10_ugm3,
        reading.light_lux,
        reading.rainfall_mm,
    )

    log.info("Persisting to %s", db_config.db_url)

    try:
        factory = create_session_factory(db_config)
        with get_session(factory) as session:
            entity = SensorReadingRepository(session).save(reading)
            log.info("Persisted: id=%d", entity.id)
    except Exception as exc:
        log.error("Database write failed: %s", exc)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
