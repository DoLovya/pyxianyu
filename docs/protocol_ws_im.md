# WebSocket 私信协议说明（闲鱼 Web 端）

## 目的

整理 `pyxianyu/goofish_live.py` 所实现的闲鱼 WebSocket 私信协议形态，便于：

- 理解消息实时收发的整体流程
- 快速扩展更多 lwp 路由（例如更多会话能力、已读回执等）
- 在协议/字段变化时快速定位受影响点

## 取证来源

- 闲鱼 Web 端私信页面抓包与行为观察
- 本仓库实现：`third_party/pyxianyu/goofish_live.py`

## 连接信息

### WebSocket 地址

```text
wss://wss-goofish.dingtalk.com/
```

### 关键 Header

连接时需要带上已登录态 Cookie（来源于 HTTP session/cookies）并模拟浏览器 Origin：

- `Cookie`: Web 登录态 Cookie（建议复用 `XianyuApis.session`）
- `Origin`: `https://www.goofish.com`
- `User-Agent`: 浏览器 UA

参考实现见：`XianyuLive.list_all_conversations`。

## 消息封装总览

WebSocket 消息均为 JSON 文本，常见字段：

- `lwp`: 路由（形如 `/r/...` 或 `/s/...`）
- `headers`: 包含 `mid`（消息 id）等
- `body`: 请求体/响应体（list/obj，依路由而定）

示例（发送）：

```json
{
  "lwp": "/r/MessageManager/listUserMessages",
  "headers": { "mid": "xxxxx" },
  "body": ["<cid>@goofish", false, 9007199254740991, 20, false]
}
```

## ACK 机制

客户端收到任意消息后，需要回一个 ACK（否则可能被服务器认为未正确消费）：

```json
{
  "code": 200,
  "headers": {
    "mid": "<server message mid>",
    "sid": "<server sid>"
  }
}
```

实现中会“尽力带回”服务端 headers 的一些字段：

- `app-key`
- `ua`
- `dt`

参考实现见：`XianyuLive.list_all_conversations` 内对每条消息的 `await websocket.send(json.dumps(ack))`。

## 初始化与心跳（/s/vulcan）

服务端会发送 `lwp == "/s/vulcan"` 的消息，通常可视为会话初始化/心跳通道。

本仓库实现策略：

- 收到 `/s/vulcan` 后再发送真正的业务请求（例如拉取历史消息的 `listUserMessages`）

对应逻辑见：`XianyuLive.list_all_conversations`：

- 如果收到 `/s/vulcan` → `await websocket.send(json.dumps(msg))`

## 典型路由（lwp）

### 拉取某会话历史消息

- 路由：`/r/MessageManager/listUserMessages`
- body（示例）：
  - `<cid>@goofish`
  - 是否只拉未读
  - cursor（首次用极大值）
  - pageSize（默认 20）

响应中：

- `body.hasMore`
- `body.nextCursor`
- `body.userMessageModels[]`

### 创建会话

- 路由：`/r/SingleChatConversation/create`
- body：包含 `pairFirst/pairSecond` 与 `itemId` 等 extension

### 发送消息

- 路由：`/r/MessageSend/sendByReceiverScope`
- body：数组，包含：
  - 消息主体（uuid/cid/content/...）
  - receivers 信息（actualReceivers）

## content.custom.data 编码规则

消息内容通过 `content.custom.data` 承载：

- data 是 base64 编码的 JSON 字符串
- JSON 内 `contentType` 决定消息类型

### 文本消息

```json
{
  "contentType": 1,
  "text": { "text": "hello" }
}
```

### 图片消息

```json
{
  "contentType": 2,
  "image": {
    "pics": [
      { "type": 0, "url": "https://...", "width": 800, "height": 600 }
    ]
  }
}
```

发送时：

- `json.dumps(payload)` → `base64.b64encode` → 写入 `custom.data`

接收时：

- `base64.b64decode(custom.data)` → `json.loads` 得到 payload

参考实现见：`XianyuLive.send_msg` 与 `XianyuLive.list_all_conversations`。

## 常见问题

### 为什么需要先拿 token（accessToken）

`XianyuLive.init` 内部会调用 `XianyuApis.get_token()` 获取 `accessToken`，用于后续与 WebSocket 侧的会话联动（以及保持登录态的可用性）。

### 解密/Protobuf

README 中提到“base64 + Protobuf”，但当前实现中对私信内容主要是 base64 的 JSON payload。若后续出现 Protobuf 帧/加密 payload，可优先在：

- `utils/goofish_utils.py`
- `message/types.py`

补齐更底层的帧结构与解析逻辑。
