## Why

`pyxianyu` 当前已经具备标准打包与发布流程，但仓库尚未把 PyPy 纳入持续验证，也没有对外明确说明 PyPy 的支持级别。直接宣称支持 PyPy 会带来两个问题：

- 兼容性没有自动化证据，后续依赖升级可能悄悄破坏 PyPy
- README / PyPI 元数据没有统一口径，下游很难判断支持边界

因此需要建立一套“先验证，再声明”的流程：只有当 PyPy smoke 校验稳定通过时，才在对外文档和包元数据中声明支持。

## What

- 新增一条面向 PyPy 的 CI smoke 验证路径，覆盖安装、导入、编译与最小测试
- 在 `pyproject.toml` 中补充 Python implementation classifiers，明确 PyPy 属于受验证实现
- 在 README 中增加兼容性与支持声明，区分 CPython 正式支持与 PyPy 当前验证级别

## Non-goals

- 本次不为 PyPy 单独构建或发布专用 wheel
- 本次不承诺所有未来 PyPy 版本自动受支持
- 本次不扩展业务接口功能，也不引入更重的集成测试

## Impact

- 修改 `.github/workflows/ci.yml`
- 修改 `pyproject.toml`
- 修改 `README.md`
- 新增一条 OpenSpec 变更，用于沉淀 PyPy 支持策略
