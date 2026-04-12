"""Baud rate configuration for the SEN0658 sensor."""

from enum import IntEnum


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
