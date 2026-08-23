## Why

当前 pyxianyu 1.x 的测试体系仅包含两个静态单测：

* `tests/test_smoke.py`：仅校验 import 与子模块存在；

* `tests/test_release_readiness.py`：仅 mock `user_page_nav` / `get_token`（无真实 HTTP/WS 调用）。

两者均无法保障「1.0 小改 → 后续 2.0 架构重构」过程中业务行为不回归。没有基线，任何重构都属于盲飞。

根据探索结果：

* `scripts/` 目录不存在；

* `.env.dev` 仅一行 `repo=...`，无真实账号凭证约定；

* `.gitignore` 已忽略 `test*.py`、`venv/`、`docs/drafts/`，但未忽略 `.env.local` / `.env` 类文件。

本 change 的目标：为 1.0 增加一套**真实行为的端到端冒烟基线（Smoke Harness）**，作为后续所有 1.x 小改（A1\~A4）和 2.0 迁移（v1-compat 验证）的统一回归入口。

## What Changes

### 新增文件

1. `scripts/smoke_1_0.py`

   * 独立可运行脚本（`python scripts/smoke_1_0.py`），无需 pytest/unittest 框架。

   * 采用环境变量驱动的「可选真实账号 + 可选 mock」策略，无账号时自动跳过需要凭证的用例。

   * 输出三色汇总（`✅ PASS / ⏭ SKIP / ❌ FAIL`）+ 非零退出码代表有失败，方便 CI 接入。

   * 支持 `--case NAME[,NAME]` 单独跑指定用例；支持 `--only-http / --only-ws` 分层运行；支持 `--json` 输出机器可读报告。

2. `scripts/smoke_env.example`（纯示例，不含任何真实凭证）

   * 约定环境变量：`XY_COOKIE_STR`、`XY_DEVICE_ID`、`XY_TEST_ITEM_ID`、`XY_TEST_ORDER_ITEM_ID`、`XY_WS_TIMEOUT`、`XY_RUN_LIVE_TESTS`、`XY_RUN_ORDER_TESTS`。

   * 文件末尾附 `.env`/`.env.local` 模式说明，同时建议将 `.env`、`.env.local` 加入 `.gitignore`。

3. `tests/` 不变（保持现有单测）；harness 放 `scripts/`，明确"这是端到端，不是单元测试"。

### 修改文件

1. `.gitignore`：追加忽略 `.env`、`.env.local`、`.env.*.local`（保留 `.env.dev` / `.env.*.example` 不忽略）。
2. `README.md`：追加「Smoke Harness 用法」一节（指向 `scripts/smoke_env.example`，并附命令示例）。
3. `docs/troubleshooting.md`：追加「Harness 用例常见失败」条目（如 `XY_COOKIE_STR 缺失自动 skip`、`400600001 流控`、`FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT` 视为 place\_order 合法结果等）。

## Capabilities

### New Capabilities

* `smoke-http-cap`：无网络、无凭证时自动 mock `build_mtop_params/sign/post_json/parse_json_response/ensure_api_success`，跑通"输入→结构→返回 shape"三层校验（不是纯 import）；有凭证时执行真实 HTTP 调用。

* `smoke-live-cap`：有 `XY_RUN_LIVE_TESTS=1` + 凭证时，真实 WS 连接 → 注册 → `list_all_conversations`（或 `Conversation/listNewestPagination` 后续补齐时加入）；无凭证或开关关闭时 skip。

* `smoke-order-guard`：`place_order` 用例允许 `status ∈ {success, yhb_required, account_invalid, failed}` 四态，任一均算 PASS（只保证不抛异常且 shape 合法，不保证真实下单成功 — 避免 harness 误生成大量订单）。

* `smoke-report`：终端三色 + 可选 `--json` 机器报告（用例名、耗时、status、环境变量命中情况），便于本地 shell 消费或 CI 存档。

### Modified Capabilities

无

## Impact

* 新增：`scripts/smoke_1_0.py`、`scripts/smoke_env.example`

* 修改：`.gitignore`、`README.md`、`docs/troubleshooting.md`

* 行为：不影响任何运行时代码，1.0 `XianyuApis` / `xianyu_live` 零改动；仅增加一个回归入口脚本和文档说明。

