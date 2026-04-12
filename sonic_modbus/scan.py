"""Scan Modbus RTU bus to discover the SEN0658 sensor and print readings."""

from pymodbus import ModbusException
from pymodbus.client import ModbusSerialClient

from sonic_modbus.constants import DEFAULT_BAUDRATE, DEFAULT_PORT, REG_WIND_SPEED
from sonic_modbus.sensor import SonicSensor


def scan() -> int | None:
    """Scan addresses 1-247 and return the first responding address."""
    client = ModbusSerialClient(
        port=DEFAULT_PORT,
        baudrate=DEFAULT_BAUDRATE,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=0.5,
    )
    client.connect()
    try:
        for addr in range(1, 248):
            try:
                result = client.read_holding_registers(
                    address=REG_WIND_SPEED, count=1, device_id=addr
                )
                if result.isError():
                    print(f"  {addr}: {result}")
                    continue
                print(f"✓ Found sensor at address {addr}")
                return addr
            except ModbusException as e:
                print(f"  {addr}: {e}")
    finally:
        client.close()
    return None


def main() -> None:
    """Scan for sensor and print all readings if found."""
    found = scan()
    if found is None:
        print("No sensor found on addresses 1-247.")
        return

    with SonicSensor(device_id=found) as sensor:
        reading = sensor.read()
        print(f"  Temperature:  {reading.temperature_c}°C")
        print(f"  Humidity:     {reading.humidity_pct}%RH")
        print(f"  Wind Speed:   {reading.wind_speed_ms} m/s")
        print(
            f"  Wind Dir:     {reading.wind_direction.name}"
            f" ({reading.wind_angle_deg}°)"
        )
        print(f"  Noise:        {reading.noise_db} dB")
        print(f"  PM2.5:        {reading.pm25_ugm3} µg/m³")
        print(f"  PM10:         {reading.pm10_ugm3} µg/m³")
        print(f"  Pressure:     {reading.atm_pressure_kpa} kPa")
        print(f"  Light:        {reading.light_lux} lux")
        print(f"  Rainfall:     {reading.rainfall_mm} mm")


if __name__ == "__main__":
    main()
