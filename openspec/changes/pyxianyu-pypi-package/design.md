## Context

当前仓库代码以“顶层目录模块”组织（`apis/`, `core/`, `utils/`, `message/` 等在仓库根目录下）。这对源码引用方便，但对打包分发不友好：安装到 site-packages 后会污染顶层模块名空间，并且下游项目难以声明稳定依赖。

目标是把 `pyxianyu` 作为独立可安装包发布到 PyPI，并通过 GitHub Actions 完成 CI 与发布流水线（Trusted Publishing）。

## Goals / Non-Goals

**Goals:**
- 提供 `pip install pyxianyu` 后可用的 `pyxianyu.*` 命名空间
- 用 `pyproject.toml` 管理依赖与构建（PEP 621），生成 sdist/wheel
- CI 覆盖 Python 3.9~3.13，验证依赖、编译、最小 import
- Release 在 tag `vX.Y.Z` 时构建并发布到 PyPI（OIDC Trusted Publishing）

**Non-Goals:**
- 不保证继续支持 `import apis/core/utils/message` 这种“顶层包名”用法
- 不在本次变更中引入完整单测体系与接口仿真（仅做 smoke-level 自检）
- 不在本次变更中调整闲鱼接口协议本身（仅调整工程组织与发布）

## Decisions

### 1) 采用 `src/` 布局，避免顶层包名污染

**Decision**：将核心代码迁移到 `src/pyxianyu/` 下，形成单一顶层包 `pyxianyu`，内部子模块包括：
- `pyxianyu.apis`
- `pyxianyu.core`
- `pyxianyu.utils`
- `pyxianyu.message`
- `pyxianyu.goofish_apis`
- `pyxianyu.goofish_live`

**Rationale**：`src/` 布局是 Python 打包的常见最佳实践，能够避免“仓库根目录可 import，但安装后不可 import”的问题，并避免把 `apis/core` 等通用名字暴露为顶层包。

**Alternative**：保持当前布局并直接打包 `apis/core/...` 为顶层包。该方案实现简单，但会污染依赖方的全局模块名空间且存在冲突风险，因此不采用。

### 2) 构建后端使用 `hatchling`

**Decision**：使用 `hatchling` 作为构建后端，统一 `pyproject.toml` 管理依赖与构建产物。

**Rationale**：上层项目 `xianyu-mcp` 已使用 `hatchling`，可保持一致的工程体验；同时它对 `src/` 布局与 wheel 构建支持良好。

### 3) Release 使用 GitHub OIDC Trusted Publishing

**Decision**：使用 `pypa/gh-action-pypi-publish` 并启用 OIDC trusted publishing，不在仓库保存 PyPI token。

**Rationale**：减少密钥管理成本与泄露风险，符合最小权限原则。

## Risks / Trade-offs

- [Import 路径大范围调整] → 通过一次性机械化替换（absolute→relative 或 `pyxianyu.*`）并在 CI 增加 `import pyxianyu` smoke，尽早暴露断链
- [下游仍依赖旧顶层包名] → 明确作为 Non-Goals；在 README 说明迁移路径（从 `apis.*` 迁移到 `pyxianyu.apis.*`）
- [PyPI 包名冲突] → 预期使用 `pyxianyu`；若冲突则在发布阶段改名（本次按 `pyxianyu` 设计）

## Migration Plan

1. 引入 `pyproject.toml` 与 `src/pyxianyu/` 目录
2. 迁移现有代码到 `src/pyxianyu/`，调整内部 import
3. 添加最小 smoke 测试（import + compile）
4. 更新 CI：使用 `pip install -e .` 安装并运行 smoke
5. 添加 Release workflow：tag `vX.Y.Z` 时 build + publish
6. 更新 README：安装与导入示例

回滚策略：
- 若发布后出现破坏性问题，可撤回最新 release，并在下一个 patch 版本修复（PyPI 不支持删除已下载版本，避免破坏依赖方缓存）
