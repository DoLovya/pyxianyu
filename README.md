# pyxianyu

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](./LICENSE)

闲鱼底层 HTTP / WebSocket 能力库，封装闲鱼 Web 端的登录态、商品、消息、媒体等接口，为上层应用提供统一调用抽象。

> **风险提示**：本项目仅供学习与技术研究使用。通过自动化手段操作闲鱼账号存在被平台风控、限制功能甚至封号的风险，使用者需自行承担一切后果。详见[免责声明](#免责声明)。

## 目录

- [项目概览](#项目概览)
- [项目结构](#项目结构)
- [功能特性](#功能特性)
- [已知限制](#已知限制)
- [环境要求](#环境要求)
- [兼容性与支持声明](#兼容性与支持声明)
- [快速开始](#快速开始)
- [相关文档](#相关文档)
- [鸣谢](#鸣谢)
- [许可](#许可)
- [免责声明](#免责声明)

## 项目概览

闲鱼官方未开放 IM 消息接口。要做 AI 客服、自动回复等场景，首先需要能稳定收发消息。pyxianyu 解决的正是这个前置问题：

- 逆向还原了闲鱼 WebSocket 私信协议（sign 签名 + base64 + Protobuf）
- 封装全部 HTTP 接口（sign 参数已解密）
- 提供统一的消息收发抽象层，开发者只需关注业务逻辑

pyxianyu 可通过 `pip/uv` 安装后直接使用，也可作为 git submodule 被上层项目（如 xianyu-mcp-server）集成用于开发调试。

## 项目结构

```text
pyxianyu/
├── src/
│   └── pyxianyu/
│       ├── __init__.py
│       ├── apis/
│       │   ├── __init__.py
│       │   ├── auth_api.py
│       │   ├── item_api.py
│       │   ├── search_api.py
│       │   ├── user_api.py
│       │   └── media_api.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── exceptions.py
│       ├── message/
│       │   ├── __init__.py
│       │   └── types.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── xianyu_utils.py
│       ├── xianyu_live.py
│       └── xianyu_apis.py
├── docs/                # API 接口分析文档
├── tests/
│   └── test_smoke.py
├── .env.dev
├── .gitignore
├── Dockerfile
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 功能特性

| 模块 | 功能 |
|------|------|
| HTTP API | 闲鱼所有 HTTP 接口（sign 签名已解密） |
| WebSocket | 私信实时收发（sign + base64 + Protobuf 协议） |
| 消息类型 | 文字、图片消息 |
| 会话管理 | 获取全部历史聊天记录 |
| 主动发送 | 主动向指定用户发消息 |
| Token 维持 | 自动刷新登录态，常驻进程不掉线 |
| 获取聊天记录 | 获取与指定用户的历史消息记录 |
| 商品信息 | 获取商品详情 |
| 商品管理 | 获取商品列表、商品下架、商品编辑详情、商品重新上架、全新发布 |
| 媒体上传 | 上传图片并发送 |

`pyxianyu.xianyu_apis.XianyuApis` 暴露的主要方法：

| 方法 | 说明 |
| --- | --- |
| `get_token()` | 校验登录态并换取 `accessToken` |
| `refresh_token()` | 刷新当前登录态 |
| `get_item_info(item_id)` | 获取商品详情 |
| `get_user_items(user_id, ...)` | 获取指定用户某一页商品 |
| `get_all_user_items(user_id, page_size=20)` | 自动翻页聚合当前用户全部商品 |
| `downshelf_item(item_id)` | 下架指定商品 |
| `prepublish_check(item_id=None)` | 调用发布前校验接口 |
| `preget(item_id=None, source_id=None, publish_scene=None, bizcode=None)` | 获取发布/编辑链路所需预置信息 |
| `get_item_edit_detail(item_id)` | 获取商品 PC 编辑页详情 |
| `edit_item(payload)` | 调用 PC 编辑接口提交商品 |
| `build_reshelf_payload(edit_detail_result, ...)` | 基于编辑详情构造重发布 payload |
| `reshelf_item(item_id, source_id=None)` | 一步完成"读取编辑详情 -> 重发布" |
| `publish_item(payload)` | 直接发布全新商品（PC 端发布链路） |
| `upload_media(media_path)` | 上传图片素材 |
| `get_user_page_nav()` | 获取当前登录用户的个人信息/个人页导航数据 |

对应接口分析文档已整理在 `docs/` 目录，方便继续扩展发布类能力。

## 已知限制

- `pyxianyu.xianyu_live` 是消息收发核心模块，需由上层服务调度，不宜直接嵌入阻塞主循环
- 未内置扫码登录能力，需依赖已登录态 Cookie
- `prepublish_check`、`preget` 等预置原语保留为底层调用，未做进一步封装，可按需组合
- `reshelf_item`、`edit_item`、`publish_item` 均走 PC 端发布/编辑链路；闲鱼对虚拟商品的 PC 端发布有管控，可能返回 `FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT`

## 环境要求

- Python 3.9+
- 依赖：`requests`、`loguru`、`websockets`、`msgpack`、`blackboxprotobuf`、`typing_extensions`

## 兼容性与支持声明

- CPython 3.9~3.13：正式支持；CI 持续执行安装、导入、编译与最小单测
- PyPy 3.10：实验性支持；CI 持续执行构建后安装的 smoke 校验（build + import + compile + unittest）
- 当前不提供 PyPy 专用发布流程；由于 `pyxianyu` 为纯 Python 包，继续沿用同一套 sdist / wheel 分发产物

只有当上述 CI 校验持续通过时，README 与包元数据才保留 PyPy 支持声明；若后续依赖升级导致 PyPy 校验失败，应先回退声明或修复兼容性，再继续发布。

## 快速开始

### 1. 安装

```bash
pip install pyxianyu
```

使用 uv：

```bash
uv pip install pyxianyu
```

使用 uvx（一次性环境）：

```bash
uvx --from pyxianyu python -c "import pyxianyu; print(pyxianyu.__version__)"
```

### 2. 配置 Cookie

作为库被上层项目（如 xianyu-mcp-server）集成时，Cookie 通过环境变量注入：

```env
# .env
XIANYU_COOKIE=完整_cookie_字符串
```

或者将 Cookie 保存到文件，通过文件路径引用：

```env
# .env
XIANYU_COOKIE_FILE=/path/to/cookie.txt
```

优先级：

- 配置了 `XIANYU_COOKIE` 时，`XIANYU_COOKIE_FILE` 会被忽略
- `XIANYU_COOKIE_FILE` 支持相对路径和绝对路径

> Cookie 必须是登录 [goofish.com](https://www.goofish.com) 后的状态，否则无法获取消息。

### 3. Docker 部署

```bash
# 构建镜像
docker build -t pyxianyu .

# 以环境变量方式运行（或 --env-file .env）
docker run -it pyxianyu
```

默认入口为 `python -m pyxianyu.xianyu_live`，启动后进入消息监听与收发模式。

### 4. 导入示例

```python
from pyxianyu.core import XianyuClient
from pyxianyu.apis import AuthApi, ItemApi
from pyxianyu.xianyu_apis import XianyuApis
from pyxianyu.utils.xianyu_utils import trans_cookies, generate_device_id
```

## 发布到 PyPI（Trusted Publishing）

1. 在 PyPI 创建项目 `pyxianyu`
2. 在 PyPI 的 Publishing 设置中新增 Trusted Publisher
   - Owner：本仓库所属 GitHub org/user
   - Repository：`pyxianyu`
   - Workflow：`.github/workflows/release.yml`
   - Environment：留空或按需配置
3. 推送 tag `vX.Y.Z` 触发 Release workflow 自动构建并发布

## 相关文档

- 协议说明：[`./docs/protocol_mtop.md`](./docs/protocol_mtop.md)
- 协议说明：[`./docs/protocol_ws_im.md`](./docs/protocol_ws_im.md)
- 排查手册：[`./docs/troubleshooting.md`](./docs/troubleshooting.md)
- 扩展指南：[`./docs/how_to_add_api.md`](./docs/how_to_add_api.md)
- 商品列表接口记录：[`./docs/mtop_idle_web_xyh_item_list.md`](./docs/mtop_idle_web_xyh_item_list.md)
- 商品下架接口记录：[`./docs/mtop_taobao_idle_item_downshelf.md`](./docs/mtop_taobao_idle_item_downshelf.md)
- 商品预发布检查接口记录：[`./docs/mtop_idle_pc_idleitem_prepublish_check.md`](./docs/mtop_idle_pc_idleitem_prepublish_check.md)
- 商品预取发布参数接口记录：[`./docs/mtop_idle_pc_idleitem_preget.md`](./docs/mtop_idle_pc_idleitem_preget.md)
- 商品编辑详情接口记录：[`./docs/mtop_idle_pc_idleitem_edit_detail.md`](./docs/mtop_idle_pc_idleitem_edit_detail.md)
- 商品编辑重发布接口记录：[`./docs/mtop_idle_pc_idleitem_edit.md`](./docs/mtop_idle_pc_idleitem_edit.md)
- 用户个人页接口记录：[`./docs/mtop_idle_web_user_page_nav.md`](./docs/mtop_idle_web_user_page_nav.md)

## 鸣谢

感谢 [cv-cat/XianYuApis](https://github.com/cv-cat/XianYuApis) 项目提供的研究思路与资料参考，对本项目的接口分析与能力整理有所帮助。

## 许可

本项目采用 MIT 协议开源。详细条款见 [`./LICENSE`](./LICENSE)。

## 免责声明

本项目仅供学习、技术研究与个人自动化实践使用，不用于任何商业用途。

闲鱼（Goofish）是阿里巴巴集团旗下的二手交易平台，本项目未获得阿里巴巴集团的任何授权或认可。本项目通过逆向分析闲鱼 Web 端接口实现自动化操作，可能违反闲鱼用户协议及相关平台规则。

使用本项目可能导致以下风险，包括但不限于：

- 账号被平台风控系统识别，触发功能限制、临时封禁或永久封号
- 账号内商品、资金、信用等资产受到冻结或扣减
- 因接口变更导致工具失效或数据异常

**项目开发者及贡献者不对任何人因使用本项目而产生的任何直接或间接损失承担责任，包括但不限于账号封禁、数据丢失、财产损失。**

使用本项目即表示你已阅读并理解上述风险，并同意自行承担一切后果。如果所在地区法律禁止此类使用，请立即停止使用并删除本项目。
