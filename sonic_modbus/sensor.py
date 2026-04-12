"""Modbus RTU client for the DFRobot SEN0658 sonic weather sensor."""

import struct

from pymodbus import ModbusException
from pymodbus.client import ModbusSerialClient

from sonic_modbus.baud_rate import BaudRate
from sonic_modbus.constants import (
    DEFAULT_BAUDRATE,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    RAINFALL_ZERO_CMD,
    REG_ATM_PRESSURE,
    REG_BAUD_RATE,
    REG_DATA_COUNT,
    REG_DATA_START,
    REG_DEVICE_ADDRESS,
    REG_HUMIDITY,
    REG_LIGHT_HIGH,
    REG_LIGHT_LOW,
    REG_NOISE,
    REG_PM10,
    REG_PM25,
    REG_RAINFALL,
    REG_RAINFALL_ZERO,
    REG_TEMPERATURE,
    REG_WIND_ANGLE,
    REG_WIND_DIR_OFFSET,
    REG_WIND_DIRECTION,
    REG_WIND_SPEED,
    REG_WIND_SPEED_ZERO,
    WIND_SPEED_ZERO_CMD,
)
from sonic_modbus.sensor_reading import SensorReading
from sonic_modbus.wind_direction import WindDirection


class SonicSensor:
    """Modbus RTU client for the DFRobot SEN0658 sonic weather sensor.

    Typical flow: construct → :meth:`connect` (or use as a context manager) →
    :meth:`read` → :meth:`close`.

    Construction does not open the serial port; see parameters on
    :meth:`__init__`.
    """

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: float = 1.0,
    ):
        """Configure the Modbus serial client; the port is opened by :meth:`connect`.

        Args:
            port: Serial device path (e.g. ``/dev/ttyUSB0``, ``COM3`` on Windows).
            baudrate: Line speed in baud; must match the sensor (library default
                matches the SEN0658 factory setting).
            device_id: Modbus unit / slave address (1–254).
            timeout: Socket timeout in seconds passed to pymodbus for I/O.
        """
        self._device_id = device_id
        self._client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout,
        )

    def connect(self) -> bool:
        """Open the serial connection. Returns True on success."""
        return self._client.connect()

    def close(self) -> None:
        """Close the serial connection."""
        self._client.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _reg(self, regs: list[int], address: int) -> int:
        """Extract a register value by absolute address from a block read."""
        return regs[address - REG_DATA_START]

    def read(self) -> SensorReading:
        """Read all sensor values in a single Modbus transaction.

        Reads registers 0x01F4-0x0201 and parses into a SensorReading.

        Raises:
            ModbusException: on communication error.
            ValueError: on unexpected response data.
        """
        result = self._client.read_holding_registers(
            address=REG_DATA_START,
            count=REG_DATA_COUNT,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus read error: {result}")

        regs = result.registers
        if len(regs) < REG_DATA_COUNT:
            raise ValueError(f"Expected {REG_DATA_COUNT} registers, got {len(regs)}")

        wind_dir_raw = self._reg(regs, REG_WIND_DIRECTION)
        try:
            wind_dir = WindDirection(wind_dir_raw)
        except ValueError:
            wind_dir = WindDirection(wind_dir_raw % 8)

        light = self._reg(regs, REG_LIGHT_HIGH) << 16 | self._reg(regs, REG_LIGHT_LOW)

        return SensorReading(
            wind_speed_ms=self._reg(regs, REG_WIND_SPEED) / 10.0,
            wind_direction=wind_dir,
            wind_angle_deg=self._reg(regs, REG_WIND_ANGLE),
            humidity_pct=self._reg(regs, REG_HUMIDITY) / 10.0,
            temperature_c=(
                struct.unpack(
                    ">h", struct.pack(">H", self._reg(regs, REG_TEMPERATURE) & 0xFFFF)
                )[0]
                / 10.0
            ),
            noise_db=self._reg(regs, REG_NOISE) / 10.0,
            pm25_ugm3=self._reg(regs, REG_PM25),
            pm10_ugm3=self._reg(regs, REG_PM10),
            atm_pressure_kpa=self._reg(regs, REG_ATM_PRESSURE) / 10.0,
            light_lux=light,
            rainfall_mm=self._reg(regs, REG_RAINFALL) / 10.0,
        )

    def read_config(self) -> tuple[int, BaudRate]:
        """Read device address and baud rate.

        Returns:
            Tuple of (device_address, baud_rate).
        """
        result = self._client.read_holding_registers(
            address=REG_DEVICE_ADDRESS,
            count=2,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus read error: {result}")
        return result.registers[0], BaudRate(result.registers[1])

    def set_device_address(self, new_address: int) -> None:
        """Change the sensor's Modbus device address (1-254).

        The sensor will respond at the new address after this call.
        """
        if not 1 <= new_address <= 254:
            raise ValueError(f"Address must be 1-254, got {new_address}")
        result = self._client.write_register(
            address=REG_DEVICE_ADDRESS,
            value=new_address,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus write error: {result}")
        self._device_id = new_address

    def set_baud_rate(self, baud: BaudRate) -> None:
        """Change the sensor's baud rate.

        Reconnect with the new baud rate after calling this.
        """
        result = self._client.write_register(
            address=REG_BAUD_RATE,
            value=int(baud),
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus write error: {result}")

    def zero_wind_speed(self) -> None:
        """Zero the wind speed sensor. Wait 10 seconds after calling."""
        result = self._client.write_register(
            address=REG_WIND_SPEED_ZERO,
            value=WIND_SPEED_ZERO_CMD,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus write error: {result}")

    def zero_rainfall(self) -> None:
        """Reset the rainfall counter to zero."""
        result = self._client.write_register(
            address=REG_RAINFALL_ZERO,
            value=RAINFALL_ZERO_CMD,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus write error: {result}")

    def set_wind_direction_offset(self, offset_180: bool) -> None:
        """Set wind direction offset.

        Args:
            offset_180: True to offset wind direction by 180°,
                        False for normal direction.
        """
        result = self._client.write_register(
            address=REG_WIND_DIR_OFFSET,
            value=1 if offset_180 else 0,
            device_id=self._device_id,
        )
        if result.isError():
            raise ModbusException(f"Modbus write error: {result}")
