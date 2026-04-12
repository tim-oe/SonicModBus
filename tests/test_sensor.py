"""Tests for SonicSensor with mock serial transport and raw Modbus RTU packets.

Every response fed to the sensor is a byte-level Modbus RTU frame built from
scratch (device-id + FC + payload + CRC-16), so the full pymodbus framing and
parsing stack is exercised on each assertion.
"""

import struct
from collections import deque
from unittest.mock import patch

import pytest

from sonic_modbus.baud_rate import BaudRate
from sonic_modbus.constants import (
    RAINFALL_ZERO_CMD,
    REG_BAUD_RATE,
    REG_DATA_COUNT,
    REG_DATA_START,
    REG_DEVICE_ADDRESS,
    REG_RAINFALL_ZERO,
    REG_WIND_DIR_OFFSET,
    REG_WIND_SPEED_ZERO,
    WIND_SPEED_ZERO_CMD,
)
from sonic_modbus.sensor import SonicSensor
from sonic_modbus.sensor_reading import SensorReading
from sonic_modbus.wind_direction import WindDirection

# ---------------------------------------------------------------------------
# Modbus RTU helpers
# ---------------------------------------------------------------------------


def modbus_crc(data: bytes) -> int:
    """CRC-16/Modbus (polynomial 0xA001, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def build_read_response(device_id: int, registers: list[int]) -> bytes:
    """Build a raw Modbus RTU response for FC 0x03 (read holding registers)."""
    byte_count = len(registers) * 2
    pdu = struct.pack(">BBB", device_id, 0x03, byte_count)
    for val in registers:
        pdu += struct.pack(">H", val)
    crc = modbus_crc(pdu)
    return pdu + struct.pack("<H", crc)


def build_write_response(device_id: int, address: int, value: int) -> bytes:
    """Build a raw Modbus RTU echo response for FC 0x06 (write single register)."""
    pdu = struct.pack(">BBHH", device_id, 0x06, address, value)
    crc = modbus_crc(pdu)
    return pdu + struct.pack("<H", crc)


def build_error_response(
    device_id: int, function_code: int, exception_code: int
) -> bytes:
    """Build a raw Modbus RTU exception response."""
    pdu = struct.pack(">BBB", device_id, function_code | 0x80, exception_code)
    crc = modbus_crc(pdu)
    return pdu + struct.pack("<H", crc)


# ---------------------------------------------------------------------------
# Mock serial port
# ---------------------------------------------------------------------------


class MockSerialPort:
    """Fake serial port that feeds pre-built Modbus RTU response frames.

    Responses are queued with :meth:`queue_response` and delivered to the
    read buffer when pymodbus writes a request via :meth:`write`.
    """

    def __init__(self, **kwargs):
        self.port = kwargs.get("port", "/dev/fake")
        self.baudrate = kwargs.get("baudrate", 4800)
        self.bytesize = kwargs.get("bytesize", 8)
        self.parity = kwargs.get("parity", "N")
        self.stopbits = kwargs.get("stopbits", 1)
        self.timeout = kwargs.get("timeout", 1.0)
        self.inter_byte_timeout: float | None = None
        self._is_open = True
        self._read_buf = bytearray()
        self._response_queue: deque[bytes] = deque()
        self.requests: list[bytes] = []

    def queue_response(self, frame: bytes) -> None:
        """Enqueue a raw RTU frame to be returned after the next write."""
        self._response_queue.append(frame)

    # -- serial.Serial interface used by pymodbus -------------------------

    @property
    def in_waiting(self) -> int:
        return len(self._read_buf)

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        self._is_open = False

    def read(self, size: int = 1) -> bytes:
        data = bytes(self._read_buf[:size])
        del self._read_buf[:size]
        return data

    def write(self, data: bytes) -> int:
        self.requests.append(bytes(data))
        if self._response_queue:
            self._read_buf.extend(self._response_queue.popleft())
        return len(data)

    def reset_input_buffer(self) -> None:
        self._read_buf.clear()

    def reset_output_buffer(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Register value sets — based on SEN0658 datasheet measurement ranges
# https://wiki.dfrobot.com/sen0658/#tech_specs
#
# Index-to-register mapping for the 14-register block (500 .. 513):
#   [0]  500  wind_speed         raw / 10 → m/s          spec: 0–40 m/s
#   [1]  501  (reserved)
#   [2]  502  wind_direction     0-7  (8-point compass)
#   [3]  503  wind_angle         0-359°                   spec: 0–359°
#   [4]  504  humidity           raw / 10 → %RH           spec: 0–99 %RH
#   [5]  505  temperature        signed16, raw / 10 → °C  spec: -40–80 °C
#   [6]  506  noise              raw / 10 → dB            spec: 30–120 dB
#   [7]  507  PM2.5              µg/m³                     spec: 0–1000
#   [8]  508  PM10               µg/m³                     spec: 0–1000
#   [9]  509  atm_pressure       raw / 10 → kPa           spec: 0–120 kPa
#   [10] 510  illumination_hi    combined 32-bit → lux    spec: 0–200000
#   [11] 511  illumination_lo
#   [12] 512  illumination       (single-reg, unused by read())
#   [13] 513  rainfall           raw / 10 → mm
# ---------------------------------------------------------------------------

MIN_REGISTERS: list[int] = [
    0,       # wind_speed      → 0.0 m/s
    0,       # (reserved)
    0,       # wind_direction  → N  (compass min)
    0,       # wind_angle      → 0°
    0,       # humidity        → 0.0 %RH
    0xFE70,  # temperature     → signed -400 → -40.0 °C
    300,     # noise           → 30.0 dB
    0,       # PM2.5           → 0 µg/m³
    0,       # PM10            → 0 µg/m³
    0,       # atm_pressure    → 0.0 kPa
    0,       # light_hi        → 0 lux
    0,       # light_lo
    0,       # light (unused)
    0,       # rainfall        → 0.0 mm
]

MAX_REGISTERS: list[int] = [
    400,     # wind_speed      → 40.0 m/s
    0,       # (reserved)
    7,       # wind_direction  → NW  (compass max)
    359,     # wind_angle      → 359°
    990,     # humidity        → 99.0 %RH
    800,     # temperature     → signed +800 → 80.0 °C
    1200,    # noise           → 120.0 dB
    1000,    # PM2.5           → 1000 µg/m³
    1000,    # PM10            → 1000 µg/m³
    1200,    # atm_pressure    → 120.0 kPa
    0x0003,  # light_hi        → 0x0003_0D40 = 200000 lux
    0x0D40,  # light_lo
    0,       # light (unused)
    0,       # rainfall        → 0.0 mm  (not spec'd by datasheet)
]

TYPICAL_REGISTERS: list[int] = [
    35,      # wind_speed      → 3.5 m/s
    0,       # (reserved)
    2,       # wind_direction  → E
    90,      # wind_angle      → 90°
    650,     # humidity        → 65.0 %RH
    223,     # temperature     → signed +223 → 22.3 °C
    452,     # noise           → 45.2 dB
    12,      # PM2.5           → 12 µg/m³
    28,      # PM10            → 28 µg/m³
    1013,    # atm_pressure    → 101.3 kPa
    0,       # light_hi        → 0x0000_C350 = 50000 lux
    0xC350,  # light_lo
    0xC350,  # light (unused)
    5,       # rainfall        → 0.5 mm
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_serial():
    """Patch ``serial.serial_for_url`` so pymodbus uses our MockSerialPort."""
    port = MockSerialPort()
    with patch("serial.serial_for_url", return_value=port):
        yield port


@pytest.fixture
def sensor(mock_serial):
    """Connected SonicSensor backed by the mock serial port."""
    s = SonicSensor(port="/dev/fake", baudrate=4800, device_id=1, timeout=0.1)
    s.connect()
    yield s
    s.close()


# ---------------------------------------------------------------------------
# Read — minimum values
# ---------------------------------------------------------------------------


class TestReadMinValues:
    """Sensor read with every register at its datasheet minimum."""

    def test_parsed_values(self, sensor, mock_serial):
        mock_serial.queue_response(build_read_response(1, MIN_REGISTERS))
        reading = sensor.read()

        assert reading.wind_speed_ms == 0.0
        assert reading.wind_direction == WindDirection.N
        assert reading.wind_angle_deg == 0
        assert reading.humidity_pct == 0.0
        assert reading.temperature_c == pytest.approx(-40.0)
        assert reading.noise_db == pytest.approx(30.0)
        assert reading.pm25_ugm3 == 0
        assert reading.pm10_ugm3 == 0
        assert reading.atm_pressure_kpa == 0.0
        assert reading.light_lux == 0
        assert reading.rainfall_mm == 0.0

    def test_returns_sensor_reading(self, sensor, mock_serial):
        mock_serial.queue_response(build_read_response(1, MIN_REGISTERS))
        assert isinstance(sensor.read(), SensorReading)


# ---------------------------------------------------------------------------
# Read — maximum values
# ---------------------------------------------------------------------------


class TestReadMaxValues:
    """Sensor read with every register at its datasheet maximum."""

    def test_parsed_values(self, sensor, mock_serial):
        mock_serial.queue_response(build_read_response(1, MAX_REGISTERS))
        reading = sensor.read()

        assert reading.wind_speed_ms == pytest.approx(40.0)
        assert reading.wind_direction == WindDirection.NW
        assert reading.wind_angle_deg == 359
        assert reading.humidity_pct == pytest.approx(99.0)
        assert reading.temperature_c == pytest.approx(80.0)
        assert reading.noise_db == pytest.approx(120.0)
        assert reading.pm25_ugm3 == 1000
        assert reading.pm10_ugm3 == 1000
        assert reading.atm_pressure_kpa == pytest.approx(120.0)
        assert reading.light_lux == 200_000
        assert reading.rainfall_mm == 0.0


# ---------------------------------------------------------------------------
# Read — typical mid-range values
# ---------------------------------------------------------------------------


class TestReadTypicalValues:
    """Sensor read with realistic mid-range data."""

    def test_parsed_values(self, sensor, mock_serial):
        mock_serial.queue_response(build_read_response(1, TYPICAL_REGISTERS))
        reading = sensor.read()

        assert reading.wind_speed_ms == pytest.approx(3.5)
        assert reading.wind_direction == WindDirection.E
        assert reading.wind_angle_deg == 90
        assert reading.humidity_pct == pytest.approx(65.0)
        assert reading.temperature_c == pytest.approx(22.3)
        assert reading.noise_db == pytest.approx(45.2)
        assert reading.pm25_ugm3 == 12
        assert reading.pm10_ugm3 == 28
        assert reading.atm_pressure_kpa == pytest.approx(101.3)
        assert reading.light_lux == 50000
        assert reading.rainfall_mm == pytest.approx(0.5)

    def test_full_read_negative_temp(self, sensor, mock_serial):
        """Negative temperature through the full Modbus pipeline."""
        regs = list(TYPICAL_REGISTERS)
        regs[5] = 0xFFCE  # -50 → -5.0 °C
        mock_serial.queue_response(build_read_response(1, regs))
        assert sensor.read().temperature_c == pytest.approx(-5.0)


# ---------------------------------------------------------------------------
# Wind direction edge case
# ---------------------------------------------------------------------------


class TestWindDirectionWrap:
    """Direction values ≥ 8 are wrapped mod 8 by the sensor driver."""

    def test_value_wraps(self, sensor, mock_serial):
        regs = list(TYPICAL_REGISTERS)
        regs[2] = 10  # 10 % 8 == 2 → E
        mock_serial.queue_response(build_read_response(1, regs))
        assert sensor.read().wind_direction == WindDirection.E


# ---------------------------------------------------------------------------
# Raw request frame verification
# ---------------------------------------------------------------------------


class TestRequestFrameStructure:
    """Verify the raw bytes pymodbus sends for each operation."""

    def test_read_holding_registers_request(self, sensor, mock_serial):
        mock_serial.queue_response(build_read_response(1, MIN_REGISTERS))
        sensor.read()

        req = mock_serial.requests[-1]
        assert req[0] == 1  # device id
        assert req[1] == 0x03  # FC read holding registers
        assert struct.unpack(">H", req[2:4])[0] == REG_DATA_START
        assert struct.unpack(">H", req[4:6])[0] == REG_DATA_COUNT
        assert modbus_crc(req[:-2]) == struct.unpack("<H", req[-2:])[0]

    def test_write_single_register_request(self, sensor, mock_serial):
        mock_serial.queue_response(build_write_response(1, REG_DEVICE_ADDRESS, 5))
        sensor.set_device_address(5)

        req = mock_serial.requests[-1]
        assert req[0] == 1
        assert req[1] == 0x06  # FC write single register
        assert struct.unpack(">H", req[2:4])[0] == REG_DEVICE_ADDRESS
        assert struct.unpack(">H", req[4:6])[0] == 5
        assert modbus_crc(req[:-2]) == struct.unpack("<H", req[-2:])[0]


# ---------------------------------------------------------------------------
# Raw response frame integrity
# ---------------------------------------------------------------------------


class TestResponseFrameIntegrity:
    """Sanity-check the helper-built frames before they reach pymodbus."""

    def test_read_response_length(self):
        frame = build_read_response(1, MIN_REGISTERS)
        expected = 1 + 1 + 1 + REG_DATA_COUNT * 2 + 2  # 33
        assert len(frame) == expected

    def test_read_response_byte_count_field(self):
        frame = build_read_response(1, MIN_REGISTERS)
        assert frame[2] == REG_DATA_COUNT * 2

    def test_read_response_crc_valid(self):
        frame = build_read_response(1, MAX_REGISTERS)
        assert modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]

    def test_write_response_crc_valid(self):
        frame = build_write_response(1, REG_DEVICE_ADDRESS, 42)
        assert modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]

    def test_error_response_crc_valid(self):
        frame = build_error_response(1, 0x03, 0x02)
        assert modbus_crc(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]


# ---------------------------------------------------------------------------
# Configuration read / write
# ---------------------------------------------------------------------------


class TestReadConfig:
    def test_read_config(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_read_response(1, [1, int(BaudRate.BAUD_4800)])
        )
        addr, baud = sensor.read_config()
        assert addr == 1
        assert baud == BaudRate.BAUD_4800

    def test_read_config_alternate(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_read_response(1, [42, int(BaudRate.BAUD_115200)])
        )
        addr, baud = sensor.read_config()
        assert addr == 42
        assert baud == BaudRate.BAUD_115200


class TestSetDeviceAddress:
    def test_valid_address(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_DEVICE_ADDRESS, 100)
        )
        sensor.set_device_address(100)

    def test_address_below_range(self, sensor):
        with pytest.raises(ValueError):
            sensor.set_device_address(0)

    def test_address_above_range(self, sensor):
        with pytest.raises(ValueError):
            sensor.set_device_address(255)


class TestSetBaudRate:
    def test_set_baud(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_BAUD_RATE, int(BaudRate.BAUD_9600))
        )
        sensor.set_baud_rate(BaudRate.BAUD_9600)

        req = mock_serial.requests[-1]
        assert struct.unpack(">H", req[2:4])[0] == REG_BAUD_RATE
        assert struct.unpack(">H", req[4:6])[0] == int(BaudRate.BAUD_9600)


# ---------------------------------------------------------------------------
# Calibration commands
# ---------------------------------------------------------------------------


class TestCalibration:
    def test_zero_wind_speed(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_WIND_SPEED_ZERO, WIND_SPEED_ZERO_CMD)
        )
        sensor.zero_wind_speed()

        req = mock_serial.requests[-1]
        assert struct.unpack(">H", req[2:4])[0] == REG_WIND_SPEED_ZERO
        assert struct.unpack(">H", req[4:6])[0] == WIND_SPEED_ZERO_CMD

    def test_zero_rainfall(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_RAINFALL_ZERO, RAINFALL_ZERO_CMD)
        )
        sensor.zero_rainfall()

        req = mock_serial.requests[-1]
        assert struct.unpack(">H", req[2:4])[0] == REG_RAINFALL_ZERO
        assert struct.unpack(">H", req[4:6])[0] == RAINFALL_ZERO_CMD

    def test_wind_direction_offset_on(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_WIND_DIR_OFFSET, 1)
        )
        sensor.set_wind_direction_offset(True)
        assert struct.unpack(">H", mock_serial.requests[-1][4:6])[0] == 1

    def test_wind_direction_offset_off(self, sensor, mock_serial):
        mock_serial.queue_response(
            build_write_response(1, REG_WIND_DIR_OFFSET, 0)
        )
        sensor.set_wind_direction_offset(False)
        assert struct.unpack(">H", mock_serial.requests[-1][4:6])[0] == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorResponses:
    def test_read_error_raises(self, sensor, mock_serial):
        mock_serial.queue_response(build_error_response(1, 0x03, 0x02))
        with pytest.raises(Exception):
            sensor.read()

    def test_write_error_raises(self, sensor, mock_serial):
        mock_serial.queue_response(build_error_response(1, 0x06, 0x01))
        with pytest.raises(Exception):
            sensor.set_device_address(5)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager(self, mock_serial):
        with SonicSensor(port="/dev/fake", timeout=0.1) as s:
            mock_serial.queue_response(build_read_response(1, TYPICAL_REGISTERS))
            reading = s.read()
            assert reading.temperature_c == pytest.approx(22.3)
