## Context

`pyxianyu` 是纯 Python 包，发布产物不依赖 CPython 专属二进制扩展，因此 PyPy 支持的关键不在“单独发布机制”，而在“依赖与导入链是否能在 PyPy 下稳定通过”。这意味着最有价值的工程动作是建立自动化验证，并把支持声明绑定到这条验证链上。

## Goals / Non-Goals

**Goals**

- 用 CI 持续验证至少一个受支持的 PyPy 版本
- 让包元数据与 README 对支持范围使用同一口径
- 保持改动集中在工程质量层，不影响现有 API

**Non-Goals**

- 不新增 PyPy 专属代码分支
- 不调整 release workflow 触发方式
- 不把 PyPy 提升为高于现有证据等级的承诺

## Decisions

### 1) 使用独立的 PyPy smoke job

**Decision**：在现有 CPython 矩阵之外，增加单独的 `pypy-smoke` job。

**Rationale**：

- 让 CPython 正常回归与 PyPy 兼容性验证彼此独立，失败归因更清楚
- 便于后续单独扩展更多 PyPy 版本，而不影响主矩阵可读性

### 2) 以“构建后安装”方式验证 PyPy 可安装性

**Decision**：PyPy job 先执行 `python -m build`，再安装构建出的 wheel 进行 smoke 校验。

**Rationale**：

- 比 `pip install -e .` 更接近真实用户安装路径
- 能同时覆盖构建配置与安装后导入路径

### 3) 对外声明采用“正式支持 + 实验支持”分层

**Decision**：

- CPython 3.9~3.13 继续作为正式支持矩阵
- PyPy 当前声明为“实验性支持”，前提是 CI smoke 持续通过

**Rationale**：

- 现有测试深度仍以 smoke 为主，直接宣称 PyPy 全量正式支持会超过证据范围
- 分层声明既能给下游预期，也保留后续升级空间

## Risks / Trade-offs

- `actions/setup-python` 对 PyPy 版本标签的支持可能随平台变化：先固定一个稳定版本，避免矩阵过宽
- 某些未来依赖版本可能回退 PyPy 兼容性：通过独立 job 尽早暴露
- classifier 一旦声明支持，下游会据此建立预期：因此 README 明确其为实验支持级别

## Migration Plan

1. 新建 OpenSpec 变更并定义支持策略
2. 为 CI 增加 PyPy 构建后安装的 smoke job
3. 在包元数据中增加 PyPy implementation classifier
4. 在 README 增加兼容性与支持声明
5. 运行本地可执行的构建与单测验证
