## Tasks

- [x] 新增 GitHub Actions CI 工作流
  - [x] 创建 `.github/workflows/ci.yml`
  - [x] 配置 push/PR 触发
  - [x] Python matrix 3.9~3.13
  - [x] 安装依赖并运行 `compileall + unittest`

- [x] （可选）补齐缺失运行依赖
  - [x] 若 CI 发现缺失依赖（例如 `websockets`），补齐到 `requirements.txt`
  - [x] README 的依赖说明同步更新

- [x] 自检
  - [x] 本地运行一次 workflow 等价命令（至少 `python -m compileall`）
