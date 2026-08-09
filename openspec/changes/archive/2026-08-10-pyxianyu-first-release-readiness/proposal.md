## Why

`pyxianyu` 已具备基本的打包、CI 和 PyPI 发布骨架，但距离首个正式版本仍有几处会直接影响用户体验与发布可靠性的缺口：

- README 中声明的部分公开 API 与实际导出不一致
- Release workflow 在发布前缺少元数据和安装路径校验
- 仓库声明了 MIT，但缺少实际 `LICENSE` 文件，`pyproject.toml` 元数据也不完整
- `get_token()` 在特定返回下会无限重试，调用方缺少明确失败信号

这些问题不一定阻止构建成功，但会让首发版本在“能装、能调、能信任”这三个层面上打折扣。

## What

- 修复 `XianyuApis` facade 与 README 的公开 API 不一致问题
- 在 `release.yml` 中增加发布前校验，确保 tag 版本、分发元数据和 wheel 安装路径可用
- 新增 `LICENSE`，并补齐 `pyproject.toml` 的公开包元数据
- 给 `get_token()` 增加有限重试与明确异常
- 补充覆盖上述行为的最小测试

## Non-goals

- 本次不扩展新的业务 API
- 本次不重构历史根目录兼容文件
- 本次不引入完整的集成测试或真实网络回放测试

## Impact

- 修改 `src/pyxianyu/goofish_apis.py`
- 修改 `src/pyxianyu/apis/auth_api.py`
- 修改 `.github/workflows/release.yml`
- 修改 `pyproject.toml`
- 修改 `README.md`
- 新增 `LICENSE`
- 修改 `tests/`
