# Data Collection

`sonic_persistence` is the companion persistence layer for `sonic_modbus`.
It stores every `SensorReading` to a MariaDB database via SQLAlchemy and manages
the schema with [pyway](https://github.com/jasondcamp/pyway).

## Prerequisites

- MariaDB 10+ running and reachable
- `sonic-modbus` installed with persistence extras (`pip install sonic-modbus`)
- The `sonic` database user created with the [required privileges](#database-setup)

---

## Database Setup

### Start MariaDB with Docker Compose

A ready-made compose file is included in the repository:

```bash
docker compose -f mariadb-docker-compose.yml up -d
```

This starts MariaDB 12 on port **3306** with:

| Setting | Value |
|---|---|
| Root password | `root` |
| Database | `weather` |
| Application user | `sonic` / `sonic` |

### Grant user privileges

Connect as root and run:

```sql
GRANT SELECT, INSERT ON weather.sonic_reading TO 'sonic'@'%';
GRANT LOCK TABLES, CREATE, ALTER ON weather.* TO 'sonic'@'%';
FLUSH PRIVILEGES;
```

### Apply the schema migration

Run pyway once from the project root to create the `sonic_reading` table:

```bash
pyway migrate
```

The default `.pyway.conf` in the repository root points at `localhost:3306/weather`
with the `sonic` user.  Override any setting with environment variables:

```bash
PYWAY_DATABASE_HOST=192.168.1.10 pyway migrate
```

---

## Configuration

All runtime parameters are read from environment variables.
Every variable has a sensible default so only the values that differ from the
defaults need to be set.

| Variable | Default | Description |
|---|---|---|
| `SONIC_PORT` | `/dev/ttyUSB0` | Serial device path to the sensor |
| `SONIC_BAUDRATE` | `4800` | Modbus line speed (must match sensor) |
| `SONIC_DEVICE_ID` | `1` | Modbus slave address (1–254) |
| `SONIC_DB_URL` | `mariadb+mysqlconnector://sonic:sonic`<br>`@localhost:3306/weather` | SQLAlchemy connection URL |

---

## Sample Reference Code

The script at `scripts/collect_reading.py` reads one sample from the sensor
and writes it to the database.  The same logic can be embedded in any
application:

```python
import os
import sys
import logging

from sonic_modbus import SonicSensor
from sonic_persistence import DatabaseConfig, SensorReadingRepository
from sonic_persistence.database import create_session_factory, get_session

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def collect_and_store() -> int:
    """Read one sensor sample and persist it. Returns 0 on success."""

    # --- sensor read ---
    try:
        with SonicSensor(
            port=os.environ.get("SONIC_PORT", "/dev/ttyUSB0"),
            baudrate=int(os.environ.get("SONIC_BAUDRATE", "4800")),
            device_id=int(os.environ.get("SONIC_DEVICE_ID", "1")),
        ) as sensor:
            reading = sensor.read()
    except Exception as exc:
        log.error("Sensor read failed: %s", exc)
        return 1

    log.info(
        "Read OK — temp=%.1f°C wind=%.1fm/s %s(%d°) humidity=%.1f%%",
        reading.temperature_c,
        reading.wind_speed_ms,
        reading.wind_direction.name,
        reading.wind_angle_deg,
        reading.humidity_pct,
    )

    # --- persist ---
    config = DatabaseConfig(
        db_url=os.environ.get(
            "SONIC_DB_URL",
            "mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather",
        )
    )
    try:
        factory = create_session_factory(config)
        with get_session(factory) as session:
            entity = SensorReadingRepository(session).save(reading)
            log.info("Persisted reading id=%d", entity.id)
    except Exception as exc:
        log.error("Database write failed: %s", exc)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(collect_and_store())
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Reading taken and persisted successfully |
| `1` | Sensor communication error |
| `2` | Database write error |

---

## Cron Job Setup

### 1. Locate the virtualenv interpreter

```bash
which collect-reading
# /home/pi/src/SonicModBus/.venv/bin/collect-reading
```

### 2. Create a log file

```bash
sudo touch /var/log/sonic_reading.log
sudo chown $USER /var/log/sonic_reading.log
```

### 3. Edit the crontab

```bash
crontab -e
```

Paste the following block, adjusting any values that differ from the defaults:

```cron
# --- SonicModBus data collection ---
SONIC_PORT=/dev/ttyUSB0
SONIC_BAUDRATE=4800
SONIC_DEVICE_ID=1
SONIC_DB_URL=mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather

# Run every 5 minutes; append timestamped output to log
*/5 * * * * /home/pi/src/SonicModBus/.venv/bin/collect-reading >> /var/log/sonic_reading.log 2>&1
```

> **Tip — different interval examples**
>
> | Cron expression | Frequency |
> |---|---|
> | `*/1 * * * *` | Every minute |
> | `*/5 * * * *` | Every 5 minutes |
> | `*/15 * * * *` | Every 15 minutes |
> | `0 * * * *` | Top of every hour |

### 4. Verify the crontab

```bash
crontab -l
```

### 5. Test the script manually first

```bash
SONIC_PORT=/dev/ttyUSB0 \
SONIC_DB_URL=mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather \
/home/pi/src/SonicModBus/.venv/bin/collect-reading
```

Expected output (exit 0):

```
2026-04-11T09:00:01 INFO     [collect_reading] Connecting to sensor: port=/dev/ttyUSB0 baudrate=4800 device_id=1
2026-04-11T09:00:01 INFO     [collect_reading] Read OK — temp=21.3°C wind=3.5m/s N(0°) humidity=55.0% pressure=101.3kPa noise=42.1dB pm25=12µg/m³ pm10=18µg/m³ light=500lux rain=0.0mm
2026-04-11T09:00:01 INFO     [collect_reading] Persisting to mariadb+mysqlconnector://sonic:sonic@localhost:3306/weather
2026-04-11T09:00:01 INFO     [collect_reading] Persisted: id=1
```

### 6. Monitor the log

```bash
tail -f /var/log/sonic_reading.log
```

---

## Troubleshooting

**`ModbusException` / exit code 1** — Check the serial port is correct and the
sensor is powered.  Run `ls /dev/ttyUSB*` to confirm the device node exists.
The user running the cron job must be in the `dialout` group:

```bash
sudo usermod -aG dialout $USER   # log out and back in to take effect
```

**`Database write failed` / exit code 2** — Confirm MariaDB is running and the
`SONIC_DB_URL` credentials match.  Test the connection directly:

```bash
mysql -u sonic -psonic -h 127.0.0.1 weather -e "SELECT 1;"
```

**Cron job never runs** — Make sure the cron service is active:

```bash
sudo systemctl status cron      # Debian / Raspberry Pi OS
sudo systemctl status crond     # RHEL / Fedora
```
