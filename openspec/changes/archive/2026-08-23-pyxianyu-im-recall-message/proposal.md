## Why

当前 pyxianyu 的 IM 长连接客户端（`XianyuLive`）存在两个配套缺口：

1. `send_msg(ws, cid, toid, message)` 只执行 `await ws.send(...)` 后直接 `return`（原始响应 **body/messageId** 没有被收集），调用方无法拿到闲鱼服务端签发的 `messageId`。
2. 缺少 `/r/MessageManager/recallMessage` 路由实现：撤回一条 2 分钟内自己发送的消息。

两者是做 IM 自动化（客服、自动回复、机器人）的刚需组合：机器人难免发错消息，需要"发→校验→撤回/修正"的闭环。之前 `api_gap_analysis.md §4.2` 已取证该路由并给出了完整 body 结构与 messageId 解析顺序，但代码未实现。

## What Changes

### 修改文件

1. `src/pyxianyu/xianyu_live.py`
   - 为 `send_msg` 提供 **lwp 请求-响应匹配**（目前 `send_msg` 只发不收）：新的 `_send_lwp_and_wait(ws, lwp, body, *, timeout)` 辅助方法，按请求 `mid` 匹配响应消息；
   - `send_msg` 返回值从 `None` 改为结构化 `SentMessageReceipt` dataclass，字段包含 `messageId`、`uuid`、`cid`、`body`（原始响应）、`parse_path`（实际从哪一层解析出 messageId 的位置）；
   - 新增 `recall_message(ws, message_id)`：发送 `/r/MessageManager/recallMessage` lwp，body=`[message_id]`，返回 `RecallResult{success, code, reason, raw}`。

2. `src/pyxianyu/message/types.py`
   - 新增 dataclass：`SentMessageReceipt`、`RecallResult`、`LwpResponseError`（分类 400600001 等）。

3. `tests/test_live_recall.py`（新增）
   - 纯 mock：伪造 websocket 流（注册成功 → sendByReceiverScope 成功响应 → recallMessage 成功响应），验证 `messageId` 解析顺序、`400600001` 归类、超过时间撤回 reason 透传。
   - 不建立真实网络连接。

4. `docs/protocol_ws_im_recall.md`（新增）
   - 按工程规范：目的、取证来源、请求 body（数组位置敏感）、响应结构、验证状态、仓库用途建议。
   - 对真实 `<mid>` / `<message_id>` 脱敏。

5. `docs/api_gap_analysis.md §4.2` 行：新增 `✅ 已实现` + doc 链接。

## Capabilities

### New Capabilities

- `im-send-receipt-cap`：`XianyuLive.send_msg()` 不再是"发后即忘，调用方一定能拿到**结构化回执**（messageId、uuid、解析顺序：body.messageId → body.1.messageId → body.1.1 → raw UUID），并在响应完全缺字段时抛出明确的 `LwpResponseError`。
- `im-recall-cap`：新增 `XianyuLive.recall_message(ws, message_id)`，返回 code=200 判成功；超过撤回时间/不是本人消息/流控 400600001 分别映射到 `RecallResult.status` 枚举，不抛异常给业务方做分支判定。

### Modified Capabilities

- **`send_msg` 从 `None` 改为返回 `SentMessageReceipt`**：这是一个**潜在破坏变更**（如果调用方把返回值当 None 判断过）。为降低破坏，提供向后兼容：`SentMessageReceipt` 实现 `__bool__()` 和 `__getitem__`（兼容 `receipt["messageId"]` 调用面），并在调用方写 `if not send_msg(...)` 时仍然得到 False（`receipt.messageId 非空 → True）。

## Impact

- 修改：`xianyu_live.py`（3 处大改：引入 mid 等待匹配 + 新返回结构 + recall 方法），`message/types.py`（新增 3 个 dataclass）
- 新增：`protocol_ws_im_recall.md`、`tests/test_live_recall.py`
- 文档更新：`api_gap_analysis.md` §4.2 标注已实现
- 依赖：不新增第三方依赖（只用 asyncio.wait_for、unittest.mock）
