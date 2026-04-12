"""Pydantic model for a single SEN0658 weather sensor reading."""

from pydantic import BaseModel

from sonic_modbus.wind_direction import WindDirection


class SensorReading(BaseModel):
    """Weather sensor reading from the SEN0658."""

    wind_speed_ms: float
    wind_direction: WindDirection
    wind_angle_deg: int
    humidity_pct: float
    temperature_c: float
    noise_db: float
    pm25_ugm3: int
    pm10_ugm3: int
    atm_pressure_kpa: float
    light_lux: int
    rainfall_mm: float
