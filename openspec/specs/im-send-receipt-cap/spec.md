# Capability: IM Send Receipt (im-send-receipt-cap)

## Purpose

`XianyuLive.send_msg()` 从「发后即忘（只 `await ws.send`，返回 None）」改为「发送 + 等待服务端响应 + 解析 messageId + 返回结构化回执（`SentMessageReceipt`）」，以便调用方进行「发错即撤」闭环。所有返回值通过 `__bool__` + `__getitem__` 做向后兼容，最小化对旧代码的破坏。

## Requirements

### Requirement: send_msg 返回结构化回执，且至少保证 messageId 解析顺序可回溯解析路径

The system SHALL return a `SentMessageReceipt` from `XianyuLive.send_msg(ws, cid, toid, message)` containing at least `messageId`、`uuid`、`cid`、`parse_path`、`mid`、`status_code`。When the IM service returns success response body, at four possible nesting positions. the messageId 解析 4 个优先顺序 (决策 2）并记录在 `parse_path`，而 which path 以调用方进行调试。

#### Scenario: send_msg 成功响应包含 body.messageId
- **WHEN** 成功 IM send_msg 的成功响应为 `{"body": {"messageId": "<mid>", ...}`
- **THEN** receipt.messageId == "<mid>"
- **AND** receipt.parse_path == "body.messageId"
- **AND** `bool(receipt) == True

#### Scenario: messageId 在 body["1"]["1]
- **WHEN** `body={"1": {"messageId": "id1"}}
- **THEN** receipt.messageId == "id1"
- **AND** receipt.parse_path == "body.1.messageId"

#### Scenario: 无任何一种位置都未命中
- **WHEN** 响应 body 中找不到 messageId
- **THEN** send_msg 抛 `LwpResponseError`
- **AND** exc.raw_response 存原响应

#### Scenario: 400600001 流控
- **WHEN** send_msg 连续 3 次收到 400600001
- **THEN** 前 3 次每次退避 2s/4s/6s
- **THEN** 第 4 次失败后抛 LwpResponseError（status=rate_limit）

### Requirement: 发送后的旧代码仍然兼容
- **WHEN** `res = await send_msg(...)
- **THEN** `if not res: ...` 在成功时 res 非空时进入 else（原返回 None，所以以前一定进入 if 现在成 if False，但调用方基本都不判断返回值；需要兼容：`receipt.__bool__()`仅当 messageId 非空时 True，也就是"发成功时 receipt`才 True，跟 `receipt`以前返回 None 不判断 `receipt["messageId"]` 还能取到 messageId。

#### Scenario: 兼容 dict-like access
- **WHEN** receipt.messageId = "abc"
- **THEN** `receipt["messageId"] == "abc"

### Requirement: recall_message 返回 RecallResult 四分类决策分类正确映射

The system SHALL expose method `recall_message(ws, message_id)` returning a RecallResult and mapping failure reasons to the 4 status variants.

#### Scenario: code==200
- **WHEN** 服务端返回 code=200
- **THEN** RecallResult.success=True，status="success"

#### Scenario:超过2分钟
- **WHEN** 响应体 reason 含 "超过可撤回时间/2 分钟"
- **THEN** RecallResult.success=False，status="timeout"，status，reason 原文

#### Scenario: 非 200 非本人/非自己消息
- **WHEN** reason 含 "非本人消息" / "不属于自己"
- **THEN** RecallResult.success=False，status="not_mine"

#### Scenario: 400600001
- **WHEN** _send_lwp 连续 3 次 400600001
- **THEN** RecallResult.success=False，status="rate_limit"，code=="400600001"
