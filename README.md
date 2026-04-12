# SonicModbus

Python library for reading the DFRobot SEN0658 sonic weather sensor via Modbus.

- [Product page](https://www.dfrobot.com/product-2942.html)
- [Wiki](https://wiki.dfrobot.com/sen0658/docs/21684)

## Installation

```bash
pip install sonic-modbus
```

## Development

```bash
poetry install --with docs
poetry run pytest
```

## Documentation

Build HTML docs locally:

```bash
cd docs
poetry run make html
```

Sync docs to the [GitHub wiki](https://github.com/tim-oe/SonicModBus/wiki) (runs Sphinx with [sphinx-markdown-builder](https://pypi.org/project/sphinx-markdown-builder/), then copies `_build/markdown`):

```bash
./scripts/sync-wiki.sh
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
