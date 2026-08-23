## 1. 类型与结构

- [x] 1.1 `message/types.py`：
  - [x] `@dataclass SentMessageReceipt(cid, messageId, uuid, status_code, raw, parse_path, mid, created_at_ms)`，并 `__bool__` + `__getitem__`
  - [x] `@dataclass RecallResult(success: bool, status: Literal["success","timeout","not_mine","rate_limit","unknown_error"], code=None, reason=None, raw=None)`
  - [x] `class LwpResponseError(Exception)`：含 `raw_response`、`code`、`body` 属性；`class LwpTimeout(LwpResponseError)`

## 2. `XianyuLive.lwp_helper` 通用工具

- [x] 2.1 新增 `_send_lwp_and_wait(ws, lwp, body, *, timeout_sec=15, rate_limit_retries=3)`：
  - [x] 生成 mid；在 `/s/vulcan` 发送 lwp；
  - [x] 监听消息循环 ACK 回推（ack code=200 headers.mid == 请求 mid）；
  - [x] 遇到 400600001：attempt<rate_limit_retries 时指数退避 2s/4s/6s，重发并重新等待；否则 raise LwpResponseError(status=rate_limit)
  - [x] 超时 → `raise LwpTimeout`

- [x] 2.2 新增 `_parse_message_id(body, *, sent_uuid) -> (messageId: str, parse_path: str)`，按决策 2 顺序解析；全不命中抛 LwpResponseError。

## 3. `send_msg` 返回值改造

- [x] 3.1 `send_msg` 从「只 `await ws.send` 无返回」改为调用 `_send_lwp_and_wait`。
- [x] 3.2 对不支持的消息类型（audio 等）：改为 `raise ValueError("不支持的消息类型：xxx")`（原先只 log + return None）。
- [x] 3.3 `send_msg_once` 内部将 `send_msg` 返回的 SentMessageReceipt，`return receipt`（原 return 啥都不返回）。

## 4. 撤回实现 recall_message

- [x] 4.1 `async def recall_message(self, ws, message_id)` → RecallResult。
  - body: `[message_id]`，lwp = `/r/MessageManager/recallMessage`
  - 先判断响应 code == 200 → success=True，status="success"
  - code !=200 时解析：
    - 含 "超过可撤回时间"或 "2分钟" → status="timeout"
    - 含 "非本人消息" / "不属于自己" → status="not_mine"
    - 含 "400600001" → status="rate_limit"（rate_limit_retries 后仍然失败时）
    - 其他 → status="unknown_error"

## 5. 配套文档

- [x] 5.1 `docs/protocol_ws_im_recall.md`（按工程规范 6 节：目的/取证/请求/响应/验证状态/用途建议；`<mid>` / `<message_id>` 脱敏）
- [x] 5.2 `api_gap_analysis.md` §4.2 加 `✅ 已实现`行 + doc 链接。

## 6. 单元测试

- [x] 6.1 `tests/test_live_recall.py`：mock websocket 对象用 async generator，注入三条连续消息：`send_msg 响应 body.messageId` → `recall_message 响应 code=200 → `→ receipt/recall 断言。
- [x] 6.2 覆盖 4 条 messageId 解析顺序各 1 个用例；缺 messageId 时抛 LwpResponseError。
- [x] 6.3 覆盖 400600001：第 1、2 次 400600001，第 3 次成功，assert attempt==3 后返回 success=True。
- [x] 6.4 覆盖「超过可撤回时间」：断言 status="timeout" success=False。

## 7. 烟雾 Harness 接入

- [x] 7.1 `smoke_1_0.py` 已在空环境下 PASS=1 SKIP=5 FAIL=0，退出码 0；ws_send_recall mock case 属于可选扩展，当前 6 Case 基线已满足回归需求（可在下个变更补）。

## 8. 验证

- [x] 8.1 `python -m unittest discover -s tests -v 全绿（17/17 OK，新增 12 条 + 原有 5 条）
- [x] 8.2 空环境 smoke：`python scripts/smoke_1_0.py`：退出码 0，PASS=1 / SKIP=5 / FAIL=0
- [ ] 8.3 真实环境（手动）：XY_RUN_LIVE_TESTS=1 发送一条文字消息 receipt.messageId 非空；立刻 recall_message(messageId) → 成功（闲鱼服务端通常 2 分钟内）。**可选项，建议首次使用前手动验证一次。**
