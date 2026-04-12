# {py:mod}`sonic_modbus.sensor`

```{py:module} sonic_modbus.sensor
```

```{autodoc2-docstring} sonic_modbus.sensor
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SonicSensor <sonic_modbus.sensor.SonicSensor>`
  - ```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor
    :summary:
    ```
````

### API

`````{py:class} SonicSensor(port: str = DEFAULT_PORT, baudrate: int = DEFAULT_BAUDRATE, device_id: int = DEFAULT_DEVICE_ID, timeout: float = 1.0)
:canonical: sonic_modbus.sensor.SonicSensor

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor
```

```{rubric} Initialization
```

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.__init__
```

````{py:method} connect() -> bool
:canonical: sonic_modbus.sensor.SonicSensor.connect

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.connect
```

````

````{py:method} close() -> None
:canonical: sonic_modbus.sensor.SonicSensor.close

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.close
```

````

````{py:method} __enter__()
:canonical: sonic_modbus.sensor.SonicSensor.__enter__

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.__enter__
```

````

````{py:method} __exit__(exc_type, exc_val, exc_tb)
:canonical: sonic_modbus.sensor.SonicSensor.__exit__

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.__exit__
```

````

````{py:method} _reg(regs: list[int], address: int) -> int
:canonical: sonic_modbus.sensor.SonicSensor._reg

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor._reg
```

````

````{py:method} read() -> sonic_modbus.sensor_reading.SensorReading
:canonical: sonic_modbus.sensor.SonicSensor.read

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.read
```

````

````{py:method} read_config() -> tuple[int, sonic_modbus.baud_rate.BaudRate]
:canonical: sonic_modbus.sensor.SonicSensor.read_config

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.read_config
```

````

````{py:method} set_device_address(new_address: int) -> None
:canonical: sonic_modbus.sensor.SonicSensor.set_device_address

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.set_device_address
```

````

````{py:method} set_baud_rate(baud: sonic_modbus.baud_rate.BaudRate) -> None
:canonical: sonic_modbus.sensor.SonicSensor.set_baud_rate

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.set_baud_rate
```

````

````{py:method} zero_wind_speed() -> None
:canonical: sonic_modbus.sensor.SonicSensor.zero_wind_speed

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.zero_wind_speed
```

````

````{py:method} zero_rainfall() -> None
:canonical: sonic_modbus.sensor.SonicSensor.zero_rainfall

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.zero_rainfall
```

````

````{py:method} set_wind_direction_offset(offset_180: bool) -> None
:canonical: sonic_modbus.sensor.SonicSensor.set_wind_direction_offset

```{autodoc2-docstring} sonic_modbus.sensor.SonicSensor.set_wind_direction_offset
```

````

`````
