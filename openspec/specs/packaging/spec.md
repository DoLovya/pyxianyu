## Purpose

定义 `pyxianyu` 作为可安装 Python 包的分发、命名空间与发布要求。

## Requirements

### Requirement: Package can be installed from PyPI
`pyxianyu` MUST be installable via standard Python packaging tools (pip/uv/uvx) and function without requiring a source checkout or git submodule.

#### Scenario: Install and import
- **WHEN** a user runs `pip install pyxianyu`
- **THEN** `python -c "import pyxianyu"` MUST succeed

### Requirement: Package namespace is `pyxianyu`
The distribution MUST expose its public modules under the `pyxianyu.*` namespace and MUST NOT require importing top-level module names such as `apis`, `core`, `utils`, or `message`.

#### Scenario: Import via package namespace
- **WHEN** a user imports `pyxianyu.apis`, `pyxianyu.core`, `pyxianyu.utils`, `pyxianyu.message`
- **THEN** the imports MUST succeed

### Requirement: Minimal public API is stable
The package MUST provide a stable minimal public API for downstream projects:
- `pyxianyu.core.XianyuClient`
- `pyxianyu.apis.AuthApi`
- `pyxianyu.apis.ItemApi`
- `pyxianyu.apis.MediaApi`
- `pyxianyu.apis.SearchApi`（如存在）
- `pyxianyu.apis.UserApi`（如存在）

#### Scenario: Downstream imports succeed
- **WHEN** a downstream project imports the symbols listed above
- **THEN** the imports MUST succeed on all supported Python versions

### Requirement: CI validates installability
The repository MUST run CI on pushes and pull requests that validates at minimum:
- dependency installation
- `python -m compileall`
- smoke import of `pyxianyu`

#### Scenario: CI smoke check
- **WHEN** CI runs on a pull request
- **THEN** the job MUST fail if `import pyxianyu` fails

### Requirement: Release publishes to PyPI via Trusted Publishing
The repository MUST provide a release workflow that publishes sdist/wheel to PyPI using GitHub OIDC Trusted Publishing when a semver tag is pushed.

#### Scenario: Tag release
- **WHEN** a tag `vX.Y.Z` is pushed
- **THEN** CI MUST build sdist and wheel and publish them to PyPI
