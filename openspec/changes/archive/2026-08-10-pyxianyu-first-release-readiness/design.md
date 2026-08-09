## Context

首个正式版本最怕的不是“功能少”，而是“文档、分发包和真实安装路径彼此不一致”。当前 `pyxianyu` 的主要问题都集中在这类发布收尾层面，因此这次变更应聚焦于缩小文档、代码与发布行为之间的偏差。

## Goals / Non-Goals

**Goals**

- 让 README 中列出的 facade API 与代码实现一致
- 让 release workflow 在真正发布前先完成版本、构建产物与安装校验
- 让 PyPI 页面具备基本完整的合规与项目信息
- 让 `get_token()` 在异常登录态下可预测地失败，而不是无限重试

**Non-Goals**

- 不改动已有业务协议实现
- 不调整 CI 主矩阵结构
- 不为根目录历史兼容代码补额外保证

## Decisions

### 1) 以代码对齐 README，而不是删减 README 声明

**Decision**：为 `XianyuApis` 接入 `UserApi`，补上 `get_user_page_nav()` facade 方法。

**Rationale**：

- 该能力已经存在于 `src/pyxianyu/apis/user_api.py`
- README 已经对外承诺，补齐 facade 的成本低于撤回文档描述

### 2) Release workflow 采用“构建后验证再发布”

**Decision**：在 `release.yml` 中增加三个发布前校验：

- tag 与 `pyproject.toml` 版本一致
- `twine check dist/*`
- 安装构建出的 wheel 后执行 smoke import 与 unittest

**Rationale**：

- 能拦住最常见的首发问题：版本错位、README 元数据异常、wheel 安装后不可用

### 3) `get_token()` 使用有限次重试

**Decision**：`get_token()` 对“令牌过期”类返回进行有限次重试，超过阈值后抛出 `XianyuApiError`，错误信息中明确说明已达到重试上限。

**Rationale**：

- 保留一定的自恢复能力
- 避免调用方在异常 cookie 状态下被无限阻塞

### 4) 元数据以“首发够用”为目标补齐

**Decision**：新增 MIT `LICENSE`，并在 `pyproject.toml` 中补齐：

- `license`
- `keywords`
- `urls`
- 许可证 classifier

**Rationale**：

- 这几项对首个公开版本的可识别性和可信度帮助最大，且改动成本低

## Risks / Trade-offs

- Release job 新增校验后，首次 tag 失败概率会高于现在，但这是希望尽早暴露的问题
- facade 补齐后，后续就需要把 `get_user_page_nav()` 视作稳定公开接口
- `get_token()` 改为有限次重试后，少数极慢恢复场景会更早失败，但整体可控性更高

## Migration Plan

1. 新建 OpenSpec 变更并补齐 proposal / design / tasks / spec
2. 修复 `XianyuApis` 公开 API 缺口
3. 更新 `get_token()` 重试逻辑并补测试
4. 更新 `release.yml`、`pyproject.toml` 与 `LICENSE`
5. 运行本地单测与构建级验证
