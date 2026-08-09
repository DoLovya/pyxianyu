## Purpose

定义 `pyxianyu` 首个公开版本在 facade 一致性、发布前校验与元数据完整性方面的要求。

## Requirements

### Requirement: Public facade MUST match documented API
`XianyuApis` MUST 暴露 README 中承诺的 facade API，避免文档声明与实际可调用方法不一致。

#### Scenario: User profile facade method is available
- **WHEN** 下游用户实例化 `XianyuApis`
- **THEN** 其 MUST 提供 `get_user_page_nav()` 方法
- **AND** 该方法 MUST 委托给 `UserApi`

### Requirement: Release workflow MUST validate distributable artifacts before publishing
仓库在发布到 PyPI 前 MUST 验证版本标记、分发元数据以及 wheel 安装后的最小可用性。

#### Scenario: Release workflow validates package before publish
- **WHEN** 仓库触发 tag 发布 workflow
- **THEN** workflow MUST 校验 git tag 与 `pyproject.toml` 版本一致
- **AND** workflow MUST 运行 `twine check dist/*`
- **AND** workflow MUST 安装构建出的 wheel 并执行 smoke import

### Requirement: Package metadata MUST include license and project URLs
首个公开版本的分发包 MUST 包含可识别的许可证与项目元数据。

#### Scenario: Metadata is visible on PyPI
- **WHEN** 构建或发布分发包
- **THEN** `pyproject.toml` MUST 声明 license、repository 相关 URL 与基础关键词
- **AND** 仓库 MUST 包含 `LICENSE` 文件

### Requirement: Token acquisition MUST fail predictably after bounded retries
当登录态无法恢复时，`get_token()` MUST 在有限次重试后抛出明确异常，而不是无限循环。

#### Scenario: Token remains expired after retries
- **WHEN** `get_token()` 连续收到“令牌过期”类响应
- **THEN** 它 MUST 在达到上限后抛出 `XianyuApiError`
- **AND** 错误信息 MUST 表明已达到重试上限
