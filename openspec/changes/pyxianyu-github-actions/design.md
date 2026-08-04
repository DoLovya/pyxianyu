## Workflow Design

### Triggers

- `push`
- `pull_request`

（后续如需降低噪音，可进一步限定 branches/path）

### Jobs

#### `ci`

- Runs-on: `ubuntu-latest`
- Strategy: Python matrix `3.9` → `3.13`
- Steps:
  - checkout
  - setup-python（带 pip cache）
  - `pip install -r requirements.txt`
  - `python -m compileall -q .`
  - `python -m unittest discover -v`

### Dependency Policy

原则：CI 只安装仓库声明的运行依赖。

若发现仓库代码引用了未声明依赖（例如 `goofish_live.py` 依赖 `websockets`），应补齐到 `requirements.txt`，避免“本地能跑、CI 跑不动”的分叉。
