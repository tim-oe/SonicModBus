# {py:mod}`sonic_modbus.sensor_reading`

```{py:module} sonic_modbus.sensor_reading
```

```{autodoc2-docstring} sonic_modbus.sensor_reading
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`SensorReading <sonic_modbus.sensor_reading.SensorReading>`
  - ```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading
    :summary:
    ```
````

### API

`````{py:class} SensorReading(/, **data: typing.Any)
:canonical: sonic_modbus.sensor_reading.SensorReading

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading
```

```{rubric} Initialization
```

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.__init__
```

````{py:attribute} wind_speed_ms
:canonical: sonic_modbus.sensor_reading.SensorReading.wind_speed_ms
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.wind_speed_ms
```

````

````{py:attribute} wind_direction
:canonical: sonic_modbus.sensor_reading.SensorReading.wind_direction
:type: sonic_modbus.wind_direction.WindDirection
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.wind_direction
```

````

````{py:attribute} wind_angle_deg
:canonical: sonic_modbus.sensor_reading.SensorReading.wind_angle_deg
:type: int
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.wind_angle_deg
```

````

````{py:attribute} humidity_pct
:canonical: sonic_modbus.sensor_reading.SensorReading.humidity_pct
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.humidity_pct
```

````

````{py:attribute} temperature_c
:canonical: sonic_modbus.sensor_reading.SensorReading.temperature_c
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.temperature_c
```

````

````{py:attribute} noise_db
:canonical: sonic_modbus.sensor_reading.SensorReading.noise_db
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.noise_db
```

````

````{py:attribute} pm25_ugm3
:canonical: sonic_modbus.sensor_reading.SensorReading.pm25_ugm3
:type: int
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.pm25_ugm3
```

````

````{py:attribute} pm10_ugm3
:canonical: sonic_modbus.sensor_reading.SensorReading.pm10_ugm3
:type: int
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.pm10_ugm3
```

````

````{py:attribute} atm_pressure_kpa
:canonical: sonic_modbus.sensor_reading.SensorReading.atm_pressure_kpa
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.atm_pressure_kpa
```

````

````{py:attribute} light_lux
:canonical: sonic_modbus.sensor_reading.SensorReading.light_lux
:type: int
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.light_lux
```

````

````{py:attribute} rainfall_mm
:canonical: sonic_modbus.sensor_reading.SensorReading.rainfall_mm
:type: float
:value: >
   None

```{autodoc2-docstring} sonic_modbus.sensor_reading.SensorReading.rainfall_mm
```

````

`````
