## 1. 包结构调整

- [x] 1.1 新增 `src/pyxianyu/` 包结构，并迁移现有代码到 `pyxianyu.*` 命名空间
- [x] 1.2 批量修正内部 import（确保 `import pyxianyu` 及子模块可用）
- [x] 1.3 增加最小 smoke 测试（至少覆盖：import + compile）

## 2. 打包与依赖

- [x] 2.1 新增 `pyproject.toml`（PEP 621）并声明 dependencies / requires-python（>=3.9）
- [x] 2.2 统一依赖来源：保留 `requirements.txt`（开发用）并与 `pyproject.toml` 对齐
- [x] 2.3 本地构建自检：`python -m build` 生成 sdist/wheel 并验证安装可 import

## 3. GitHub Actions

- [x] 3.1 调整 CI：使用 `pip install -e .`（或安装 wheel）后运行 smoke import/compile（Python 3.9\~3.13）
- [x] 3.2 新增 Release workflow：tag `vX.Y.Z` 时 build 并通过 Trusted Publishing 发布到 PyPI
- [x] 3.3 在 README 增加发布前置配置说明（PyPI Trusted Publisher 配置步骤）

## 4. 文档与对外用法

- [x] 4.1 README 增加安装方式：pip/uv/uvx
- [x] 4.2 README 明确新导入路径示例（`pyxianyu.apis.*` 等）
