# Getting Started

## Installation

```bash
pip install sonic-modbus
```

## Hardware

- [DFRobot SEN0658 product page](https://www.dfrobot.com/product-2942.html)
- [SEN0658 wiki](https://wiki.dfrobot.com/sen0658/docs/21684)

## Quick Example

Connect over Modbus RTU (default **4800** baud, 8N1, device address **1** — see the [hardware wiki](https://wiki.dfrobot.com/sen0658/docs/21684)). Adjust `port` for your system (`/dev/ttyUSB0`, `/dev/ttyAMA0`, `COM3`, …).

```python
from sonic_modbus import SonicSensor

with SonicSensor(port="/dev/ttyUSB0") as sensor:
    r = sensor.read()
    print(f"Wind: {r.wind_speed_ms} m/s {r.wind_direction.name} ({r.wind_angle_deg}°)")
    print(f"Temp: {r.temperature_c} °C, humidity: {r.humidity_pct} %RH")
    print(f"Pressure: {r.atm_pressure_kpa} kPa, light: {r.light_lux} lux")
    print(f"PM2.5: {r.pm25_ugm3} µg/m³, PM10: {r.pm10_ugm3} µg/m³, rain: {r.rainfall_mm} mm")
```

`read()` raises `pymodbus.ModbusException` if the bus read fails; ensure the sensor is wired and the port/baud/device id match the module.
