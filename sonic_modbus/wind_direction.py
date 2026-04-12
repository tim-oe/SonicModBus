"""Wind direction enum for the SEN0658 sensor."""

from enum import IntEnum


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
