# Publishing

## Nexus Repository

The project uses a Sonatype Nexus Repository as a private PyPI registry for development and shakeout before publishing to PyPI.

### Nexus Setup

1. Create a **pypi (hosted)** repository in Nexus named `tec-pypi`.
2. Set the deployment policy to **Allow redeploy** during development.
3. Create a user with a role containing the following privileges:
   - `nx-component-upload`
   - `nx-repository-view-pypi-tec-pypi-add`
   - `nx-repository-view-pypi-tec-pypi-edit`
   - `nx-repository-view-pypi-tec-pypi-read`
   - `nx-repository-view-pypi-tec-pypi-browse`

## Poetry Configuration

### Register the Nexus repository

```bash
poetry config repositories.nexus <nexus-pypi-repo-url>
```

### Store credentials

With username/password:

```bash
poetry config http-basic.nexus <username> <password>
```

Or with a token:

```bash
poetry config pypi-token.nexus <token>
```

Credentials are stored in `~/.config/pypoetry/auth.toml` and are not committed to version control.

## Build and Publish

```bash
poetry build
poetry publish -r nexus
```

## Installing from Nexus

With pip:

```bash
pip install sonic-modbus --index-url <nexus-pypi-repo-url>
```

With Poetry (in a consuming project):

```bash
poetry source add nexus <nexus-pypi-repo-url>
poetry add sonic-modbus
```

## Publishing to PyPI

When the package is ready for public release, publish to PyPI with the default target:

```bash
poetry publish
```
