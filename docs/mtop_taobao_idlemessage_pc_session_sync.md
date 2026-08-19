# `mtop.taobao.idlemessage.pc.session.sync` 与相关 IM HTTP 接口记录

## 目的

梳理闲鱼 Web 端（goofish.com）私信/消息中心在页面加载阶段调用的 HTTP MTop 接口族。
这些接口用于：拉取会话摘要列表、按会话拉取历史消息、查询用户资料（用于消息发送者头像昵称）、
获取 IM 登录/ACCS token（为 WebSocket 连接做准备），以及未读红点查询。

其中"取消置顶"（`isTop=false`）与"会话置顶状态（`isTop`）"本身由 WebSocket 路由承载（见 `protocol_im_conversation_top.md`），
但会话列表的摘要同步（含置顶会话的出现顺序）走本文件的 `session.sync` HTTP 接口。

## 取证来源

### 浏览器验证页面

- 页面 URL：`https://www.goofish.com/im?spm=a21ybx.personal.sidebar.1.47136ac2o92NkB`
- 页面特征：左侧为"消息"会话列表（`rc-virtual-list` 虚拟化渲染）。
  - 置顶会话 CSS 类：`conversation-item-top--cQda1cba`（与普通会话 `conversation-item--JReyg97P` 组合）。
  - 普通会话 CSS 类：`conversation-item--JReyg97P`（无 `conversation-item-top--*`）。
  - 页面加载动作中，观察到总共 12 个会话条目，其中 8 条置顶、4 条非置顶。

### 前端源码定位

- 来源 bundle：`https://g.alicdn.com/idle-pc/xy-site/0.0.169/js/p_im-index.js`
- 关键片段（`session.sync` 请求类）：

```js
tz = function eu() {
  (0, eR._)(this, eu);
  this.api = "mtop.taobao.idlemessage.pc.session.sync";
  this.v = "3.0";
  this.needLogin = !0;
};
// ...
em.getListPushSessionReq = function () {
  var eu = new tz;
  eu.data = {
    sessionTypes: JSON.stringify(e$.F5),   // -> "[1,19,15,32,3,44,51,52,24]"
    fetchNum: 30,                           // 单次拉取数量
    sortIndex: void 0,                      // 翻页游标（首次不传）
    sessionId: void 0                       // 翻页游标（首次不传）
  };
  return eu;
};
em.listPushSession = function () {
  // ...
  // ep.data.sessions[Symbol.iterator]() 中读取 session.sessionId 传给 WS getConversations
  // 然后调用 convertSummaryToLiteSession 合并 summary + WS 详情
  return ep.data.sessions.length;
};
```

- 关键片段（`user.query` PC 端 4.0 调用）：

```js
// 单会话消息查询（type=0）
eC = {
  type: ep,                 // 0 = 历史消息
  sessionType: null != em ? em : 1, // 1 = 单聊
  sessionId: eg,            // "<sessionId>"
  isOwner: tH.h.getInstance().getUserId() === (0, tp.XC)(ef)
};
ew && (eC.messageId = ew);       // 可选：指定起始 messageId
eP({ api: "mtop.taobao.idlemessage.pc.user.query", v: "4.0", needLogin: !0, data: eC });
```

### 网络抓包（Network，脱敏）

从 `browser_network_requests` 观测到按顺序触发的 IM 相关 MTop 请求：

1. `POST mtop.taobao.idlemessage.pc.login.token/1.0/`
2. `POST mtop.taobao.idlemessage.face.emoji.load/1.0/`
3. `POST mtop.taobao.idlemessage.pc.accs.token/1.0/`
4. `POST mtop.taobao.idlemessage.pc.session.sync/3.0/`
5. 多个并发 `POST mtop.taobao.idlemessage.pc.user.query/4.0/`（参数不同）
   - 部分是 `type=0`：进入会话后拉取"该会话的历史消息"
   - 部分是 `type=1`：查询消息发送者的 `userInfo`（头像、昵称）
6. 轮询 `POST mtop.taobao.idlemessage.pc.redpoint.query/1.0/`（`sessionTypes=1,19,... fetch=50`）

另外在点击会话进入聊天后，额外触发：

7. `POST mtop.idle.trade.pc.message.headinfo/1.0/` — 交易消息卡片（商品标题、状态、收货等）
   - 参数：`itemId`, `sessionId`, `sessionType`
8. `POST mtop.taobao.idlemessage.pc.blacklist.query/1.0/` — 是否拉黑对方
   - 参数：`sessionId`

---

## 请求信息总览

所有请求均走 MTop 网关：

```text
POST https://h5api.m.goofish.com/h5/<api>/<v>/
Content-Type: application/x-www-form-urlencoded
body: data=<json-string>   # 需与 URL 中 sign/t 一致
```

Query 公共参数（所有 idlemessage.* 接口一致，敏感值已用 `<masked>` 占位）：

```text
jsv=2.7.2
appKey=34839810
t=<timestamp_ms>
sign=<masked>
v=<具体版本，见下表>
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=<具体 api 名，见下表>
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.im.0.0
spm_pre=a21ybx.personal.sidebar.1.47136ac2o92NkB
log_id=47136ac2o92NkB
```

| API | v | body `data` 关键字段 | 用途 |
|---|---|---|---|
| `mtop.taobao.idlemessage.pc.login.token` | `1.0` | 无 data（空） | 拿 IM 登录 token（给后续 WebSocket `/reg` 用） |
| `mtop.taobao.idlemessage.pc.accs.token` | `1.0` | 无 data（空） | 拿 ACCS token（长连接通道） |
| `mtop.taobao.idlemessage.pc.session.sync` | `3.0` | 见下 | **会话摘要列表同步（含置顶会话顺序）** |
| `mtop.taobao.idlemessage.pc.user.query` | `4.0` | `type=0` 见下 | 按会话拉取"历史消息列表"（取消置顶提醒等系统消息也混在其中） |
| `mtop.taobao.idlemessage.pc.user.query` | `4.0` | `type=1` 见下 | 查询某条消息发送者的 `userInfo` |
| `mtop.taobao.idlemessage.pc.redpoint.query` | `1.0` | `sessionTypes`, `fetch` | 未读红点批量查询 |

---

## 接口一：`mtop.taobao.idlemessage.pc.session.sync/3.0/`

### URL

```text
POST https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.session.sync/3.0/
```

### Body `data` 字段（JSON 字符串）

```json
{
  "sessionTypes": "[1,19,15,32,3,44,51,52,24]",
  "fetchNum": 30,
  "sortIndex": null,
  "sessionId": null
}
```

字段说明（由 bundle `getListPushSessionReq` 反推）：

- `sessionTypes`（string，JSON 数组字符串）：要同步哪些"会话类型"的摘要。
  页面默认 `e$.F5 = [1,19,15,32,3,44,51,52,24]`，其中：
  - `1`：单聊（普通用户对话）
  - 其余数字为群聊、系统消息、交易消息、服务号等"Tab 类型"（具体枚举待补）。
- `fetchNum`（number）：一页条数，默认 30。
- `sortIndex` / `sessionId`（string | null）：翻页游标。首次同步传 `undefined`/`null`；
  有下一页时根据响应的同名字段回传（字段名待实测验证）。

### 响应结构（基于 bundle 消费端归纳）

```json
{
  "ret": ["SUCCESS::接口调用成功"],
  "data": {
    "sessions": [
      {
        "session": {
          "sessionId": "<string, number 会话 id>",
          "sessionType": 1,
          "lastMsgTime": "<long, 毫秒时间戳，用于前端排序（置顶+时间）>"
        },
        "unreadCount": 0,
        "lastMsg": {
          "summary": "等待买家收货 [你已发货]"
        }
      }
    ],
    "hasMore": true,
    "nextSortIndex": "<string>",
    "nextSessionId": "<string>"
  }
}
```

**注意**：`session.sync` 响应中**暂未观测到显式的 `isTop/top` 字段**。置顶状态（是否置顶）由
WebSocket 路由 `/r/Conversation/listTop` + `/r/Conversation/listNewestPagination` 的返回决定，
前端再据此给会话条目附加 `conversation-item-top--*` CSS 类。换言之：**"会话列表"是 HTTP summary + WS 详情合并产物**。

### 已验证行为

- 首次进入 `/im` 页面即调用，仅传 `sessionTypes` + `fetchNum`。
- 会话摘要只含很少字段（`sessionId` 为核心）。具体头像、是否置顶、扩展信息、
  最新内容解析等，需要后续用 `sessionId` 调 WebSocket `/r/Conversation/getByCids` 或
  `/r/Conversation/listNewestPagination` 拿到（见 `protocol_ws_im.md` 与 `protocol_im_conversation_top.md`）。

---

## 接口二：`mtop.taobao.idlemessage.pc.user.query/4.0/`（type=0：单会话历史消息）

### URL

```text
POST https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.user.query/4.0/
```

### Body `data` 字段（进入会话后首次拉取 + 翻页）

```json
{
  "type": 0,
  "sessionType": 1,
  "sessionId": "<会话 id，字符串化的数字>",
  "isOwner": true,
  "messageId": "<可选，翻页时传最早一条的 messageId>"
}
```

字段说明：

- `type=0`：表示"拉取某会话的历史消息"。
- `sessionType=1`：单聊（枚举待补全群聊等其他值）。
- `sessionId`：会话 ID，值来源为 `session.sync` 返回的 `session.sessionId`。
- `isOwner`：布尔，`true` 表示"当前用户就是这个会话的店主/卖家视角"，由前端判断
  `当前登录 userId === 会话中卖家 userId`。买家视角一般传 `false`。
- `messageId`（可选 string）：翻页游标。首次进入不传；当返回有 `hasMore` 时，
  把本页中"最早一条"消息的 `messageId` 回传作为下一页起点（类似 `before_id`）。

### 响应结构（摘要）

```json
{
  "ret": ["SUCCESS::接口调用成功"],
  "data": {
    "messages": [
      {
        "messageId": "<message_id>.PNM",
        "senderUserId": "<对方 uid>",
        "sessionId": "<会话 id>",
        "contentType": 1,
        "createTime": "<long ms>",
        "content": {
          "custom": {
            "type": 1,
            "data": "<base64(JSON string) — 见 protocol_ws_im.md 的 content.custom.data 编码>"
          }
        },
        "extension": {
          "reminderTitle": "<如果是系统通知（例如取消置顶、退款等）会有这里的标题>"
        }
      }
    ],
    "hasMore": true,
    "userInfo": {
      "<对方 uid>": { "nick": "<脱敏>", "avatar": "<url>" },
      "<我方 uid>": { "nick": "<脱敏>", "avatar": "<url>" }
    }
  }
}
```

**取消置顶相关字段说明**：闲鱼 Web 端中，"你已取消置顶"、"商品因违规下架，系统自动取消置顶"、
"置顶到期自动取消"等都是作为**会话内的系统消息**下发的，并不会走独立的"取消置顶列表"接口。
因此要列出"取消置顶"这一类事件，需要按会话拉取 `user.query` 的 `type=0` 历史消息，
然后按 `extension.reminderTitle` 或 `content.custom.data` 解码后的关键词过滤。

---

## 接口三：`mtop.taobao.idlemessage.pc.user.query/4.0/`（type=1：用户资料）

### Body `data`

```json
{
  "type": 1,
  "sessionType": 1,
  "sessionId": "<会话 id>",
  "isOwner": true,
  "messageId": "<某条消息 id，用于定位那条消息的发送者>"
}
```

### 响应结构

```json
{
  "ret": ["SUCCESS::接口调用成功"],
  "data": {
    "userInfo": {
      "userId": "<uid>",
      "nick": "<昵称>",
      "avatarUrl": "<头像 url>"
    }
  }
}
```

用途：渲染消息气泡上的头像与昵称（当之前的会话列表里没有缓存头像时补齐）。

---

## 接口四：`mtop.taobao.idlemessage.pc.redpoint.query/1.0/`

### Body `data`

```json
{
  "sessionTypes": "1,19,15,32,3,44,51,52,24",
  "fetch": 50
}
```

### 响应结构（摘要）

```json
{
  "ret": ["SUCCESS::接口调用成功"],
  "data": {
    "points": [
      { "sessionId": "<id>", "unread": 3, "sessionType": 1 }
    ]
  }
}
```

用途：首页消息徽标（红点）的后台轮询。与"取消置顶"没有直接关联，用于和 `session.sync` 一起
构建"未读数 + 会话列表"。

---

## 当前验证状态

| 项 | 状态 | 说明 |
|---|---|---|
| `session.sync` URL + 版本 | ✅ 已在 Network 面板中验证 | `api=mtop.taobao.idlemessage.pc.session.sync/v=3.0`，与 bundle 一致 |
| `session.sync` body 字段 | ⚠️ 由 bundle 反推 | `sessionTypes/fetchNum/sortIndex/sessionId`，实际响应里游标字段名需一次真实请求验证 |
| `session.sync` 响应含 `data.sessions` | ✅ 由 bundle `listPushSession` 消费端证实 | `ep.data.sessions` 被迭代 + 读取 `session.sessionId` |
| `user.query type=0` URL + 字段 | ✅ 浏览器拦截到实际调用 | `{type, sessionType, sessionId, isOwner, messageId}`，并在 Network 中命中 |
| `user.query type=0` 响应 | ⚠️ 结构推导 | 结合 `xianyu_live.py` 中已有 `/r/MessageManager/listUserMessages` 字段命名推断；字段名应基本一致（PC HTTP 版与 WS 版同源） |
| `user.query type=1` 用户资料查询 | ✅ bundle 中证实 | `eS.data.userInfo` 用于构造头像/昵称对象 |
| `redpoint.query` | ✅ Network 中命中多次 | 轮询参数稳定 |
| 置顶字段在 `session.sync` 中 | ❌ 未发现 | 置顶状态由 WebSocket `/r/Conversation/*` 系列承载（见下一份文档） |
| 取消置顶独立 API | ❌ 不存在（结论） | 无论是"取消/设置置顶"还是"置顶取消"的提醒消息，均为：WS 路由 `setTop` + 会话内系统消息 |

---

## 当前在仓库中的用途（建议）

- 建议在 `third_party/pyxianyu/apis/` 下新增 `message_api.py`（或扩展现有 `user_api.py`），封装：
  - `session_list_sync(session_types, fetch_num, sort_index, session_id)` → 调 `mtop.taobao.idlemessage.pc.session.sync/3.0`
  - `list_conversation_messages(session_id, session_type=1, is_owner=True, message_id=None)` → 调 `type=0`
  - `get_im_token()` → 调 `pc.login.token/1.0`（与 `xianyu_live.init` 的 access token 获取配合）
- 作为后续：
  - `XianyuLive`（WebSocket 版）与新增 HTTP 版 `MessageApi` 组合使用：
    HTTP 拿 sessionIds → WS 拿详细会话（含 `isTop`）→ HTTP 拿历史消息过滤"取消置顶"关键词。
- 代码参考位置：
  - `third_party/pyxianyu/src/pyxianyu/core/client.py`：Mtop `build_mtop_params` / `post_json` / `ensure_api_success`
  - `third_party/pyxianyu/src/pyxianyu/xianyu_live.py`：WS `listUserMessages` 返回结构与消息解码 `base64 → JSON` 逻辑
