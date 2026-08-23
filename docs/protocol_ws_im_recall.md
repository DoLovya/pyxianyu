# WebSocket 消息撤回协议说明（`/r/MessageManager/recallMessage`）

## 1. 目的

整理闲鱼 Web 端「撤回一条 2 分钟内自己发送的消息」配套协议，以及 `send_msg()` 返回 `messageId` 的解析规则，用于：

- IM 自动化机器人发错消息时自动撤回（刚需）
- 与 `SentMessageReceipt` / `RecallResult` 结构化返回的使用
- 配合 `send_msg` 的 4 条 `messageId` 解析路径的文档化

配套代码：`src/pyxianyu/xianyu_live.py::XianyuLive.recall_message`、`src/pyxianyu/xianyu_live.py::XianyuLive.send_msg`。

---

## 2. 取证来源

- 外部对比仓库 `zhinianboke/xianyu-auto-reply`：`backend-web/app/services/chat_new/im_client.py` 中的 `GoofishImClient.recall_message()` + `send_text_message()` 的 `messageId` 解析逻辑
- 闲鱼 Web 端私信页面抓包：`/r/MessageSend/sendByReceiverScope` 响应体 + `/r/MessageManager/recallMessage` 请求/响应

---

## 3. 请求 body 结构（位置敏感数组）

### 3.1 撤回请求：`lwp = /r/MessageManager/recallMessage`

`body` 是**单元素字符串数组**（位置敏感，长度=1）：

| 索引 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `body[0]` | `string` | 是 | `"<message_id>"` | 从 `sendByReceiverScope` 返回体中解析出的**服务端** `messageId`（不是本地 uuid） |

完整请求示例：

```json
{
  "lwp": "/r/MessageManager/recallMessage",
  "headers": {
    "mid": "<mid>",
    "sid": "<sid>",
    "app-key": "444e9908a51d1cb236a27862abc769c9",
    "ua": "Mozilla/5.0 ... DingTalk(...)",
    "dt": "j"
  },
  "body": ["<message_id>"]
}
```

> ⚠️ **重要：`body` 必须是 `[message_id]` 的**单元素列表**，不能传 dict，也不能是长度 >1 的数组，否则闲鱼会直接返回 `code != 200` 的非本人/参数错误响应。

### 3.2 配套发送请求（`messageId` 获取前置）：`lwp = /r/MessageSend/sendByReceiverScope

这是 `send_msg()` 走的发送路由（已在 `pyxianyu` 实现；此处仅列 messageId 解析规则）。成功响应里 `messageId` 可能出现在 4 个位置（xianyu-auto-reply 实测不同版本返回位置有差异），**解析顺序固定**（详见 §5。

---

## 4. 响应结构

### 4.1 撤回响应 `recallMessage`

典型响应：

```json
{
  "lwp": "/r/MessageManager/recallMessage",
  "headers": { "mid": "<mid>", "sid": "<sid>" },
  "body": {
    "code": 200,
    "reason": null
  }
}
```

判定规则：

| 情况 | `body.code` | `body.reason`（样例） | `RecallResult.status` |
|---|---|---|---|
| 撤回成功 | `200` | `null` / `""` | `"success"` |
| 超过可撤回时间（通常 2 分钟） | 非 200 | `"超过可撤回时间（仅支持发送后2分钟内撤回）` / 含「超过 + 分钟/可撤回」 | `"timeout"` |
| 非本人消息 | 非 200 | `"非本人消息，无法撤回"` / 含「非本人 / 不属于自己 / 不属于本人」 | `"not_mine"` |
| 流控 | `"400600001"` 或 reason 含该字符串 | `"...400600001..."` | `"rate_limit"`（`_send_lwp_and_wait` 3 次退避失败后统一映射） |
| 其他业务错误 | 其他 | 任意 | `"unknown_error"` |

> 注意：除 `message_id` 为空串/非字符串这种**调用方参数错误**时，`recall_message()` 会**直接 `raise ValueError`**（不包装成 RecallResult）。其他 LwpResponseError / LwpTimeout 在方法都不会向外抛（只在内部翻译成 RecallResult）。

---

## 5. `messageId` 解析规则（4 条路径 + uuid fallback）

`send_msg() 解析顺序（`_parse_message_id`，按顺序命中即返回，全部不命中 → **抛 `LwpResponseError(status="parse_error")：

| # | 位置 | 伪代码 | `parse_path` 标签 |
|---|---|---|---|
| 1 | `body.messageId`（顶层字符串） | `body.get("messageId") 非空字符串 | `"body.messageId"` |
| 2 | `body["1"].messageId` | `body["1"]["messageId"]` 非空字符串 | `"body.1.messageId"` |
| 3 | `body["1"]["1"]`（字符串型） | `body["1"]["1"] 非空字符串 | `"body.1.1"` |
| 4 | fallback 本地 `uuid fallback | 调用 `send_msg()` 生成的 `msg_uuid`（第 4 条仅在前 3 条都不命中时兜底，且调用方确实发消息实际发送，但不保证「服务端实际 messageId 已生效但在本地） | `"sent_uuid_fallback"` |
| 全不命中 | 抛 `LwpResponseError(status="parse_error")`。

对应 `SentMessageReceipt.parse_path`。

- 如果调用 `send_msg` 返回 `SentMessageReceipt` 三个关键字段：

```python
@dataclass
class SentMessageReceipt:
    cid: str               # "xxx@goofish
    messageId: str            # 解析出的 messageId（上面 4 条之一
    uuid: str              # 本地生成的 uuid（用于 body.uuid 字段，通常）
    status_code: int | None # body.code（int 时）
    raw: dict             # {"body": <原始 body 响应, "full": <完整 WS 响应>}
    parse_path: str        # "body.messageId" / "body.1.messageId" / "body.1.1" / "sent_uuid_fallback"
    mid: str               # 本次 /s/vulcan发送时 generate_mid() 的 mid
    created_at_ms: int
```

> 向后兼容：`SentMessageReceipt` 实现了：

- `__bool__`：`messageId` 非空 → True；否则 False（原 `if not send_msg(...)` 的语义保持一致）
- `__getitem__`：`receipt["messageId"]` / `receipt["mid"]` / `receipt["cid"]` 等 dict-like 访问（原调用方把返回 dict 的写法无需改动）

---

## 6. 验证状态

- ✅ **单测全绿**：`tests/test_live_recall.py` 12 条用例覆盖：
  - `_parse_message_id` 4 条解析顺序 + parse_error 抛异常（共 5 条
  - `send_msg` 成功 → `SentMessageReceipt` 的 bool/dict-like/messageId/parse_path/cid/mid
  - `recall_message` success/timeout/超过 2 分钟/not_mine/空串 ValueError
  - `_send_lwp_and_wait` 连续 4 次 400600001 → 3 次指数退避 sleep → 最终抛 `LwpResponseError(status="rate_limit")`
- ✅ **compileall 0 报错：`src scripts tests` 全量编译 无语法错误
- ✅ **冒烟 harness 空环境：6 Case 退出码 0（`PASS=1 SKIP=5 FAIL=0`
- ⏳ **真实环境（手动可选）：真实账号 XY_RUN_LIVE_TESTS=1 发送 → 立刻 recall → success=True。

---

## 7. 用途与使用建议

```python
from pyxianyu import XianyuLive
from pyxianyu.message import make_text, RecallResult, SentMessageReceipt

live = XianyuLive(cookies_str)

async with websockets.connect(...) as ws:
    await live.init(ws)
    receipt: SentMessageReceipt = await live.send_msg(ws, cid, toid, make_text("发错了😭"))
    
    # 立刻撤回（2 分钟内有效：
    if receipt:
        result: RecallResult = await live.recall_message(ws, receipt.messageId)
        match result.status:
            case "success": print("ok")
            case "timeout": print("超时", result.reason)
            case "not_mine": print("不是自己的消息")
            case "rate_limit": print("被限流", result.code)
            case _: print("未知错误",  # unknown_error")
```

- 注意：
  1. 撤回时限由闲鱼服务端计时，调用方不要本地计时不可靠（以 reason 文本匹配「超过 + 分钟」统一映射 `status="timeout"
  2. 调用 `recall_message` 永远不向外抛 `LwpResponseError`（除 ValueError 外），方便上层只做分支判断不用 try/except；只有在参数错误才会向外抛 ValueError 错误（调用方自己的错例如 message_id 为空串）时才 ValueError。
  3. `400600001 指数退避 2s/4s/6s（最多 3 次重试），仍失败才映射为 `rate_limit`，建议上层再排队等待更长时间（例如退避）。"
