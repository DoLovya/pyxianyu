## 1. OpenSpec 变更

- [x] 1.1 新建 `pyxianyu-first-release-readiness` 变更并补齐 proposal / design / tasks / spec

## 2. 公开 API 与运行时行为

- [x] 2.1 为 `XianyuApis` 接入 `UserApi` 并暴露 `get_user_page_nav()`
- [x] 2.2 给 `get_token()` 增加有限重试与明确异常

## 3. 发布与元数据

- [x] 3.1 为 `release.yml` 增加 tag/version、twine、wheel 安装校验
- [x] 3.2 新增 `LICENSE` 并补齐 `pyproject.toml` 元数据

## 4. 测试与文档

- [x] 4.1 补充覆盖 facade 与有限重试行为的最小测试
- [x] 4.2 运行本地验证并回填任务状态
