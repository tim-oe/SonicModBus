"""Tests for scripts/wiki_postprocess.py."""

from scripts.wiki_postprocess import fix_google_style_fields


def test_args_expands_to_bullets():
    line = (
        "Args: port: Serial device path (e.g. `/dev/ttyUSB0`, `COM3` on Windows). "
        "baudrate: Line speed in baud; must match the sensor. "
        "device_id: Modbus unit / slave address (1–254). "
        "timeout: Socket timeout in seconds passed to pymodbus for I/O."
    )
    out = fix_google_style_fields(line)
    assert "Args:" in out
    assert "- **port**:" in out
    assert "- **baudrate**:" in out
    assert "- **device_id**:" in out
    assert "- **timeout**:" in out
    assert "`/dev/ttyUSB0`" in out


def test_raises_expands_to_bullets():
    line = (
        "Raises: ModbusException: on communication error. "
        "ValueError: on unexpected response data."
    )
    out = fix_google_style_fields(line)
    assert "- **ModbusException**:" in out
    assert "- **ValueError**:" in out


def test_single_arg_still_listed():
    line = "Args: offset_180: True to offset wind direction by 180°, False for normal direction."
    out = fix_google_style_fields(line)
    assert "- **offset_180**:" in out


def test_skips_fenced_code():
    text = "```\nArgs: foo: bar. baz: qux.\n```\n"
    assert fix_google_style_fields(text) == text


def test_does_not_touch_unrelated_lines():
    assert fix_google_style_fields("Some Args: in prose.\n") == "Some Args: in prose.\n"
