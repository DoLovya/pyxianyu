## 1. 脚本与环境约定

- [ ] 1.1 新建 `scripts/` 目录。
- [ ] 1.2 新建 `scripts/smoke_env.example`：列出所有 env 名称、默认值（安全占位符，不含真实值）、说明、opt-in 开关说明（如 `XY_RUN_ORDER_TESTS`、`XY_RUN_LIVE_TESTS`）。
- [ ] 1.3 更新 `.gitignore`：追加忽略 `.env`、`.env.local`、`.env.*.local`，但不忽略 `.env.dev`、`*.example`。
- [ ] 1.4 追加 `docs/troubleshooting.md`：Harness 常见 FAQ（4 条：缺凭证自动 skip；WS 需要 opt-in flag；place_order 为什么 failed 也记 PASS；400600001 的重试建议）。

## 2. 核心 harness 结构

- [ ] 2.1 `scripts/smoke_1_0.py` 实现基础类：
  - `SmokeStatus = Literal["PASS", "SKIP", "FAIL"]`
  - `@dataclass SmokeResult(case_name, status, duration_ms, mode: Literal["mock","real"], payload, reason, env_hits: list[str])`
  - `Case` 基类：`name`/`requires: list[str]`（env 依赖）/`run(ctx: RunContext) -> SmokeResult`
  - `RunContext`：持有 `mode`、`cookies`、`device_id`、`apis: XianyuApis`、`live: XianyuLive | None`、`http_retry: int`。
- [ ] 2.2 主入口：加载 env（若存在 `.env.local`，以 python-dotenv 可选加载 — 若未安装 dotenv 则 print warning 后仍工作，避免强依赖）→ 构造 ctx → 实例化 6 个 Case → 顺序执行 → 汇总打印 + 写 JSON（`--json`） + `exit(0 if fail_count==0 else 2)`。
- [ ] 2.3 ANSI 颜色：仅在 `isatty` 时启用；非 tty（CI）自动关闭颜色。

## 3. 6 个用例实现（按 A1 定义顺序）

- [ ] 3.1 Case `get_token`：依赖 `XY_COOKIE_STR`。real 模式下调用 `XianyuApis.get_token()`，要求 `data.accessToken` 非空；mock 模式下 patch `auth_api.get_token` 返回一个合法 shape。
- [ ] 3.2 Case `search_items`：无 env 强依赖。调用 `search_items("耳机")`，要求结果是 `list` 或 `dict`（兼容当前返回结构）。real 模式走网络，mock 模式返回 2 条假结构。
- [ ] 3.3 Case `get_user_items`：同 search_items。real 模式需要凭证；mock 模式返回一页假数据。
- [ ] 3.4 Case `polish_item`：依赖 `XY_TEST_ITEM_ID`。缺 env → SKIP。断言 `success==true` 且 `already_polished ∈ {True, False}`。
- [ ] 3.5 Case `place_order`：依赖 `XY_TEST_ORDER_ITEM_ID` 与 `XY_RUN_ORDER_TESTS=1`（两层 opt-in，防止误下订单）。缺任一 → SKIP。只断言 shape 合法（§决策 3），不要求 status==success。
- [ ] 3.6 Case `ws_list_all_conversations`：依赖 `XY_COOKIE_STR + XY_RUN_LIVE_TESTS=1`，否则 SKIP。真实模式：`xianyu_live.init(timeout=12)` 成功 → `list_all_conversations()` 返回 list；超 15s 未完成 → 记 SKIP + reason。

## 4. Mock Transport / Mock XianyuApis 模式

- [ ] 4.1 实现 `_MockMtopContext`：对 `build_mtop_params/sign/post_json/parse_json_response/ensure_api_success` 进行标准 mock 注入，按 case 名返回最简合法 data（如 polish 返回 `data={}`，place_order 返回 `status=failed` 以避免假阳性；断言只看结构）。
- [ ] 4.2 保证 mock 模式的每个 case 至少命中"输入→结构→返回 shape"三层校验，避免 mock 模式变成"只测 import"。
- [ ] 4.3 实现 `_MockLive`：对 WS 链路（init、register、heartbeat、list_all_conversations）返回空 list，保证 shape。

## 5. 文档与 CI 友好性

- [ ] 5.1 `README.md` 追加「Smoke Harness 用法」小节：2 条命令示例（`cp scripts/smoke_env.example .env.local` + `python scripts/smoke_1_0.py`；可选 `--case polish_item,place_order`、`--only-http`、`--json > report.json`）。
- [ ] 5.2 `--json` 输出字段：`summary`（pass/skip/fail 计数）、`total_duration_ms`、`cases: list[SmokeResult]`、`env: {key: "<redacted if secret>"}`（cookie 类仅显示 `XY_COOKIE_STR=<set>` 或 `<unset>`）。
- [ ] 5.3 退出码：`0` 全 pass/skip；`2` 有任一 fail；`3` 非法参数。

## 6. 验证

- [ ] 6.1 空环境（不设任何 env）执行 `python scripts/smoke_1_0.py` → 6 个 case 中至少 4 个 PASS（mock 模式），2 个因缺 env SKIP；退出码为 0。
- [ ] 6.2 `python scripts/smoke_1_0.py --case this_case_not_exist` → 退出码 3。
- [ ] 6.3 （可选，有凭证时）手动设 env 后执行 `place_order`，确认即使 `status=yhb_required` 仍然记 PASS。
