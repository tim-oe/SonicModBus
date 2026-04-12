"""SEN0658 Modbus register addresses and protocol constants.

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
