"""Python library for reading DFRobot SEN0658 sonic weather sensor via Modbus."""

__version__ = "0.1.0"

from sonic_modbus.baud_rate import BaudRate
from sonic_modbus.sensor import SonicSensor
from sonic_modbus.sensor_reading import SensorReading
from sonic_modbus.wind_direction import WindDirection

__all__ = [
    "BaudRate",
    "SensorReading",
    "SonicSensor",
    "WindDirection",
]
