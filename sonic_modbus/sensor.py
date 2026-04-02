"""DFRobot SEN0658 sonic weather sensor Modbus RTU client.

Register map per official DFRobot wiki:
https://wiki.dfrobot.com/sen0658/docs/21684

Sensor defaults: 4800 baud, 8N1, Modbus RTU, device address 1.

Holding registers (function code 0x03):
    0x01F4 (500): wind speed            (raw / 10.0 = m/s)
    0x01F6 (502): wind direction        (0-7, 8-point compass, 0=N, 2=E)
    0x01F7 (503): wind direction angle  (0-360°)
    0x01F8 (504): humidity              (raw / 10.0 = %RH)
    0x01F9 (505): temperature           (raw / 10.0 = °C, two's complement)
    0x01FA (506): noise                 (raw / 10.0 = dB)
    0x01FB (507): PM2.5                 (µg/m³)
    0x01FC (508): PM10                  (µg/m³)
    0x01FD (509): atmospheric pressure  (raw / 10.0 = kPa)
    0x01FE (510): illumination high 16  (combined 32-bit = lux)
    0x01FF (511): illumination low 16
    0x0200 (512): illumination          (single register lux)
    0x0201 (513): rainfall              (raw / 10.0 = mm)

Configuration registers (function codes 0x03/0x06):
    0x07D0 (2000): device address       (1-254, default 1)
    0x07D1 (2001): baud rate            (0=2400 .. 7=1200)

Calibration registers (function code 0x06):
    0x6000 (24576): wind direction offset (0=normal, 1=180° offset)
    0x6001 (24577): wind speed zeroing    (write 0xAA, wait 10s)
    0x6002 (24578): rainfall zeroing      (write 0x5A)
"""

from enum import IntEnum

from pydantic import BaseModel
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 4800
DEFAULT_DEVICE_ID = 1

# --- Sensor data registers (0x03 read) ---
REG_WIND_SPEED = 0x01F4  # 500
REG_WIND_DIRECTION = 0x01F6  # 502
REG_WIND_ANGLE = 0x01F7  # 503
REG_HUMIDITY = 0x01F8  # 504
REG_TEMPERATURE = 0x01F9  # 505
REG_NOISE = 0x01FA  # 506
REG_PM25 = 0x01FB  # 507
REG_PM10 = 0x01FC  # 508
REG_ATM_PRESSURE = 0x01FD  # 509
REG_LIGHT_HIGH = 0x01FE  # 510
REG_LIGHT_LOW = 0x01FF  # 511
REG_LIGHT = 0x0200  # 512
REG_RAINFALL = 0x0201  # 513

# Contiguous block 500-513 (14 registers)
REG_DATA_START = 0x01F4  # 500
REG_DATA_COUNT = 14

# --- Configuration registers (0x03 read / 0x06 write) ---
REG_DEVICE_ADDRESS = 0x07D0  # 2000
REG_BAUD_RATE = 0x07D1  # 2001

# --- Calibration registers (0x06 write only) ---
REG_WIND_DIR_OFFSET = 0x6000  # 24576
REG_WIND_SPEED_ZERO = 0x6001  # 24577
REG_RAINFALL_ZERO = 0x6002  # 24578

WIND_SPEED_ZERO_CMD = 0xAA
RAINFALL_ZERO_CMD = 0x5A


class BaudRate(IntEnum):
    """Sensor baud rate configuration values."""

    BAUD_2400 = 0
    BAUD_4800 = 1
    BAUD_9600 = 2
    BAUD_19200 = 3
    BAUD_38400 = 4
    BAUD_57600 = 5
    BAUD_115200 = 6
    BAUD_1200 = 7

    def to_int(self) -> int:
        """Return the actual baud rate as an integer."""
        return _BAUD_MAP[self]


_BAUD_MAP = {
    BaudRate.BAUD_1200: 1200,
    BaudRate.BAUD_2400: 2400,
    BaudRate.BAUD_4800: 4800,
    BaudRate.BAUD_9600: 9600,
    BaudRate.BAUD_19200: 19200,
    BaudRate.BAUD_38400: 38400,
    BaudRate.BAUD_57600: 57600,
    BaudRate.BAUD_115200: 115200,
}


class WindDirection(IntEnum):
    """8-point compass wind direction.

    Per spec: 0=N increasing clockwise, 2=E.
    """

    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7


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


def _signed16(value: int) -> int:
    """Convert unsigned 16-bit Modbus register to signed integer.

    The sensor uses two's complement for negative temperatures.
    """
    if value >= 0x8000:
        return value - 0x10000
    return value


class SonicSensor:
    """Modbus RTU client for the DFRobot SEN0658 sonic weather sensor."""

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        device_id: int = DEFAULT_DEVICE_ID,
        timeout: float = 1.0,
    ):
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
            temperature_c=_signed16(self._reg(regs, REG_TEMPERATURE)) / 10.0,
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
