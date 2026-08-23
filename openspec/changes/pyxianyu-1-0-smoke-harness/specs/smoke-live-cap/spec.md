## ADDED Requirements

### Requirement: WS 域测试必须显式 opt-in，超时不阻塞整体 harness

The system SHALL only run live WebSocket (IM) smoke cases when the user explicitly enables them. Otherwise, all IM cases are marked SKIP.

#### Scenario: WS 默认关闭（安全默认）
- **WHEN** 不设置 `XY_RUN_LIVE_TESTS`，即便设置了 `XY_COOKIE_STR`
- **THEN** `ws_list_all_conversations` case 结果是 SKIP
- **AND** 没有任何公网 WS 连接发起（不会建立 wss://wss-goofish.dingtalk.com 连接）

#### Scenario: 启用 WS — 成功路径
- **WHEN** `XY_RUN_LIVE_TESTS=1` + `XY_COOKIE_STR` 非空，且 `XY_WS_TIMEOUT >= 10`
- **THEN** Harness 依次完成：
  1. 创建 `XianyuLive(cookies, device_id, app_key=..., device_id=...)`
  2. 调用 `init(timeout=XY_WS_TIMEOUT or 12)` 注册成功
  3. 调用 `list_all_conversations()`
- **THEN** 若返回结果是 `list`，case 标记 PASS

#### Scenario: 启用 WS — 注册超时（或 IM 流控 400600001）
- **WHEN** 启用 WS 但 `init()` 在总 15 秒内未成功，或 `list_all_conversations()` 返回含 `code=400600001`
- **THEN** case 标记 SKIP（**不是 FAIL**，避免 CI 偶发抖动）
- **AND** reason 字段明确写出是 timeout 还是 rate limit

### Requirement: IM case 不会主动触发"发消息/撤回"等写操作

- **WHEN** WS case 执行期间
- **THEN** Harness 不得调用 `send_msg`、`recall_message`、`create_chat` 等任何写接口，保证运行一次 WS smoke 不产生 IM 副作用。
