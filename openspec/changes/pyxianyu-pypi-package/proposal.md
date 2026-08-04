## Why

当前 `pyxianyu` 以“源码目录 + submodule”的形式被上层项目引用，导致：

- 无法通过 `uvx` / `pip` 直接安装使用（用户需要 clone + init submodule）
- 上层项目构建时依赖本地目录结构（例如通过 `sys.path` 动态导入），发布 wheel 后无法运行
- 依赖与版本边界不清晰（升级/回滚困难）

将 `pyxianyu` 制作为独立可安装的 Python 包并发布到 PyPI，可显著降低接入成本，并为上层 MCP 服务提供稳定的依赖与版本管理能力。

## What Changes

- 将 `pyxianyu` 代码整理为标准 Python package（`import pyxianyu`），避免安装后暴露 `apis/core/utils` 等顶层包名
- 新增 `pyproject.toml`（PEP 621）作为打包与依赖的单一事实来源
- 新增 GitHub Actions：
  - CI：多版本 Python matrix 安装并做最小自检（import + compile）
  - Release：在打 tag 时构建并发布到 PyPI（Trusted Publishing / OIDC）
- 更新 README：提供 `pip/uv/uvx` 安装与最小使用示例

## Capabilities

### New Capabilities
- `packaging`: 将 pyxianyu 作为可安装 Python 包发布与分发（含 CI/Release 流水线）

### Modified Capabilities
- （无）

## Impact

- 代码结构将从“顶层模块”迁移到 `pyxianyu.*` 命名空间（涉及内部 import 路径调整）
- 上层项目（例如 `xianyu-mcp`）将改为依赖 PyPI 包并使用 `import pyxianyu`（不再依赖 submodule 目录结构）
