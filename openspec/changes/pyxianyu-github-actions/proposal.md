## Why

pyxianyu 作为独立仓库（submodule 指向 `DoLovya/pyxianyu`），需要自己的 GitHub Actions 来保证：

- 每次提交/PR 都能自动做基础质量校验（至少语法检查、基本用例检查）
- Python 版本兼容性可见（README 声明 3.9+）
- 未来扩展（lint、打包发布）有稳定的 CI 基线

## What

- 新增 GitHub Actions 工作流 `CI`：
  - 触发：push、pull_request（默认分支）
  - Python matrix：3.9 / 3.10 / 3.11 / 3.12 / 3.13
  - 安装依赖：`pip install -r requirements.txt`
  - 校验：
    - `python -m compileall`（语法/可编译检查）
    - `python -m unittest discover -v`（若仓库后续补 tests，可自然接入；无 tests 时也不失败）

## Non-goals

- 本次不做 PyPI 发布（release workflow）
- 本次不引入强制 lint（避免历史代码一次性全红）

## Impact

- 新增 `.github/workflows/ci.yml`
- （可选）补齐 `requirements.txt` 里缺失但运行时必需的依赖（例如 `websockets`）
