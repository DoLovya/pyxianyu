## Context

现状：
- `XianyuLive.send_msg(...)` 只做 `await ws.send(json)`，不等待响应，也不解析服务端返回的 messageId；返回 None。
- `XianyuLive` 现有 6 个 WS 路由中没有 `/r/MessageManager/recallMessage`，缺少撤回能力。

## Goals / Non-Goals

**Goals：**
1. `send_msg` 改为「请求-响应匹配」，返回结构化回执，至少包含 messageId、uuid、原始 body。
2. 新增 `recall_message(ws, message_id)`，提供明确的成功/失败判定。
3. IM 流控错误码 `400600001` 在两个方法中统一指数退避重试最多 3 次，重试耗尽才失败。
4. 新增一份标准化文档 docs/protocol_ws_im_recall.md（脱敏）。

**Non-Goals：**
1. 不修改现有 `create_chat / init / heart_beat` 行为。
2. 不扩展撤回旧消息的轮询/缓存（调用方自行记录 messageId）。
3. 不改变 WS 协议：不引入消息订阅/消息去重/消息已读回执（属于后续 2.4 能力单独实现）。

## Decisions

- **决策 1：WS mid 匹配机制**：
  新增 `_send_lwp_and_wait(ws, lwp, body, *, timeout, retries_on_400600001=3)`：
  - 生成 mid，把 mid 写入 headers；
  - `asyncio.create_task` 监听 `/s/vulcan` 回调时 send（按现有模式）；
  - 在 websocket 消息循环中匹配 `recv_mid == send_mid` 返回对应 body；
  - 若 body.code == "400600001" 或 body 含 `code` 等于该串 → 记录 attempt+1，`sleep((attempt+1)*2)` 后重发；>3 次报错。
  - 这个 helper 同时供 `send_msg`、`recall_message`、未来的 `list_conversations`（撤回配套）共用，避免重复模式。

- **决策 2：messageId 解析顺序**（与 api_gap_analysis.md §4.2 一致，按优先级）：
  1. `body.messageId`（普通成功返回）
  2. `body["1"].messageId`
  3. `body["1"]["1"]`（dict 内键）
  4. 作为「未命中」：抛出 `LwpResponseError`，不瞎猜（防止误撤回其他消息）。
  - 同时 `receipt.parse_path` 记录命中哪一条，用于后续调试。

- **决策 3：`send_msg` 向后兼容**：
  - `SentMessageReceipt` 实现：
    - `__bool__`：`bool(self.messageId)`
    - `__getitem__(k)`：`getattr(self, key, None)` 或从 dataclass fields（允许 `receipt["messageId"]` 字段；
    - 字段缺失，调用方仍可写 `if not send_msg(...)` 失败判断，语义保持一致。

- **决策 4：撤回结果语义**：
  - `RecallResult.success` 只在响应 `code == 200` 才 True；
  - `RecallResult.status` 枚举：`success / timeout / not_mine / rate_limit / unknown_error`，便于业务分支；
  - 原始响应体放 `raw`，调用方可再分析。

## Risks / Trade-offs

| 风险 | 影响 | 缓解 |
|---|---|---|
| `send_msg` 返回值变更为非 None，旧代码 `res = send_msg(...) if res is None: ...` 可能误判 | 低：破坏行为（原返回 None 语义是"调用方根本不使用返回值，或当作 True/False 判断） | 决策 3：实现 `__bool__` + `__getitem__`，不破坏典型写法；README + troubleshooting 加 CHANGELOG 一节。 |
| mid 匹配死等导致 send_msg 永久挂起 | 中：IM 长连接本来就长 | `asyncio.wait_for` 设 15 秒超时；超时抛出明确 `LwpTimeout`；记录异常原因，不阻塞调用方。 |
| 不同账号体系 messageId 返回位置与取证到的不一致 | 中：解析顺序漏掉 → 误撤回 | 解析顺序 4 条全部不命中就报错不瞎猜，抛出 `LwpResponseError`，日志记录原始 body keys，调用方可再扩展新位置。 |
| 撤回失败原因「超过可撤回时间」被当成 success | 低：用户以为撤回成功 | `RecallResult.success` 只有 code==200 才 True，reason 原文透传。 |
