## Purpose

定义 `pyxianyu` 在不同 Python 运行时下的持续验证与支持声明规则。

## Requirements

### Requirement: CI MUST validate at least one PyPy runtime
仓库 MUST 在持续集成中验证至少一个受支持的 PyPy 运行时，且验证流程至少覆盖构建后安装、包导入、源码编译与最小测试。

#### Scenario: PyPy smoke validation runs on pull requests
- **WHEN** 仓库触发 `pull_request` 或 `push` CI
- **THEN** CI MUST 运行独立的 PyPy smoke job
- **AND** 该 job MUST 在安装构建产物后执行 `import pyxianyu`
- **AND** 该 job MUST 在导入失败、编译失败或最小测试失败时失败

### Requirement: Support claims MUST match automated evidence
仓库对 PyPy 的支持声明 MUST 与自动化验证证据保持一致，不得在缺少持续验证的情况下宣称受支持。

#### Scenario: README documents PyPy support tier
- **WHEN** README 描述 Python 兼容性
- **THEN** README MUST 区分 CPython 正式支持矩阵与 PyPy 当前支持级别
- **AND** README MUST 说明 PyPy 支持基于 CI smoke 验证

### Requirement: Package metadata MUST declare supported implementation
当仓库已经建立持续的 PyPy 验证链时，包元数据 MUST 声明对应的 Python implementation classifier。

#### Scenario: PyPI metadata includes PyPy classifier
- **WHEN** 项目生成或发布分发包
- **THEN** `pyproject.toml` MUST 包含 `Programming Language :: Python :: Implementation :: PyPy`
