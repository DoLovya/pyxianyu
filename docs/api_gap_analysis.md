# pyxianyu vs xianyu-auto-reply API 差距分析文档

> 生成日期：2026-08-22
> 对比基准：本地 pyxianyu（`third_party/pyxianyu/`） vs 外部 `zhinianboke/xianyu-auto-reply`（main 分支）
> 文档用途：列出 xianyu-auto-reply 已实现但 pyxianyu 尚未实现的闲鱼 API，供后续逐步实现时参考。

---

## 1. 对比范围与结论总览

### 1.1 本地 pyxianyu 已实现 API 计数

| 类别 | 已实现（代码） | 仅文档无代码 | 合计 |
|---|---|---|---|
| MTop HTTP 接口 | 13 | 2 | 15 |
| WebSocket lwp 路由 | 6 | 1 | 7 |

### 1.2 xianyu-auto-reply 独有 API（未实现）

| 类别 | 数量 | 优先级分布 |
|---|---|---|
| MTop HTTP 接口 | 6 | 高 3、中 3 |
| WebSocket lwp 路由 | 2 | 高 1、中 1 |
| 合计 | **8** | — |

> 此外，xianyu-auto-reply README 提及「订单同步 / 自动评价 / 卡券发货」等功能，但源码中未取证到对应 MTop 接口名，详见第 7 节「待进一步确认的 API」。

---

## 2. pyxianyu 已实现 API 清单（对照基准）

### 2.1 MTop HTTP 接口（已实现代码）

| API 名称 | 版本 | 所在文件 | 方法名 |
|---|---|---|---|
| `mtop.taobao.idlemessage.pc.login.token` | 1.0 | [auth_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/auth_api.py#L8-L49) | `AuthApi.get_token()` |
| `mtop.taobao.idlemessage.pc.loginuser.get` | 1.0 | [auth_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/auth_api.py#L51-L67) | `AuthApi.refresh_token()` |
| `mtop.taobao.idle.pc.detail` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L9-L24) | `ItemApi.get_item_info()` |
| `mtop.idle.web.xyh.item.list` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L26-L136) | `ItemApi.get_user_items()` |
| `mtop.taobao.idle.item.downshelf` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L138-L154) | `ItemApi.downshelf_item()` |
| `mtop.idle.pc.idleitem.prepublish.check` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L156-L174) | `ItemApi.prepublish_check()` |
| `mtop.idle.pc.idleitem.preget` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L176-L200) | `ItemApi.preget()` |
| `mtop.idle.pc.idleitem.editDetail` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L202-L217) | `ItemApi.get_item_edit_detail()` |
| `mtop.idle.pc.idleitem.edit` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L219-L240) | `ItemApi.edit_item()` |
| `mtop.idle.pc.idleitem.publish` | 1.0 | [item_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/item_api.py#L242-L262) | `ItemApi.publish_item()` |
| `mtop.taobao.idlemtopsearch.pc.search` | 1.0 | [search_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/search_api.py#L9-L46) | `SearchApi.search_items()` |
| `mtop.idle.web.user.page.nav` | 1.0 | [user_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/user_api.py#L1-L19) | `UserApi.get_user_page_nav()` |
| `stream-upload.goofish.com/api/upload.api` | — | [media_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/media_api.py#L8-L71) | `MediaApi.upload_media()` |

### 2.2 WebSocket lwp 路由（已实现代码）

| 路由名称 | 所在文件 | 方法名 |
|---|---|---|
| `/reg`（注册） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L186-L228) | `init()` |
| `/r/SyncStatus/ackDiff`（ACK 同步） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L212-L228) | `init()` |
| `/r/MessageManager/listUserMessages`（聊天记录） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L47-L121) | `list_all_conversations()` |
| `/r/SingleChatConversation/create`（创建会话） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L123-L137) | `create_chat()` |
| `/r/MessageSend/sendByReceiverScope`（发消息） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L139-L184) | `send_msg()` |
| `/!`（心跳） | [xianyu_live.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/xianyu_live.py#L258-L262) | `heart_beat()` |

### 2.3 仅文档未实现代码（pyxianyu 内部欠账）

| API / 路由 | 文档路径 | 状态 |
|---|---|---|
| `mtop.taobao.idlemessage.pc.session.sync` | [mtop_taobao_idlemessage_pc_session_sync.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/mtop_taobao_idlemessage_pc_session_sync.md) | ⚠️ 仅文档 |
| `/r/Conversation/setTop` | [protocol_im_conversation_top.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/protocol_im_conversation_top.md) | ⚠️ 仅文档 |

---

## 3. 未实现 MTop HTTP API 详情（6 个）

---

### 3.1 商品擦亮：`mtop.taobao.idle.item.polish` v2.0

| 字段 | 值 |
|---|---|
| **优先级** | 🔴 高 |
| **功能用途** | 重新上架（擦亮）在售商品，提升曝光排名；每个商品每天限擦亮 1 次。 |
| **取证来源** | `scheduler/app/services/scheduler/polish_task.py::_polish_item()` |
| **建议实现位置** | `apis/item_api.py::ItemApi.polish_item()`（与 `downshelf_item` 并列） |
| **实现状态** | ✅ 已实现（`apis/item_api.py` + `xianyu_apis.py` 门面，2026-08-23）。实现细节参见 [mtop_taobao_idle_item_polish.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/mtop_taobao_idle_item_polish.md)。 |
| **验证状态** | ⏳ 待验证（xianyu-auto-reply 生产环境使用，接口名与版本确认有效） |

#### 请求参数

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `itemId` | string | 是 | `"7891234567"` | 商品 ID |

> 请求通过 `application/x-www-form-urlencoded` 以 `data={"itemId":"..."}` 形式提交，需附带标准 MTop sign 签名（`appKey=34839810`，token 取 `_m_h5_tk` 按下划线分割第一段）。

#### 响应要点

```
ret[0] == "SUCCESS::调用成功"                    → 擦亮成功
ret[0] 含 "IDLEITEM_POLISH_AGAIN" 或 "宝贝已经擦亮过了"  → 幂等视为成功（当日已擦亮）
ret[0] 含 "UNSUPPORTED_ITEM_STATUS" 或 "已下架商品不支持该操作" → 商品已下架，跳过
ret[0] 含 "TOKEN_EXOIRED" / "TOKEN_EXPIRED"      → 需刷新 cookie 后重试
```

#### 注意事项

1. 每个商品每日仅可擦亮 1 次，`IDLEITEM_POLISH_AGAIN` 应作为幂等成功处理，不报错。
2. 请求间隔建议 ≥2 秒（xianyu-auto-reply 中 `asyncio.sleep(2)`），防止账号风控。
3. 擦亮接口若返回 Set-Cookie（令牌过期时服务端下发新 cookie），需回写实例供后续复用。

---

### 3.2 普通下单-渲染：`mtop.taobao.idle.trade.order.render` v7.0

| 字段 | 值 |
|---|---|
| **优先级** | 🔴 高 |
| **功能用途** | 渲染下单页面信息，拿到 `commonData.itemBuyInfo`（含收货地址、价格、运费等），作为下一步 create 的输入。 |
| **取证来源** | `common/services/xianyu_order_client.py::XianyuOrderClient.render()` |
| **建议实现位置** | 新建 `apis/trade_api.py::TradeApi.order_render()` |
| **实现状态** | ✅ 已实现（`apis/trade_api.py` + 门面 XianyuApis.order_render()/place_order()，2026-08-23）。实现细节参见 [mtop_taobao_idle_trade_order_render.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/mtop_taobao_idle_trade_order_render.md)。 |
| **验证状态** | ⏳ 待验证 |

#### 请求参数

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `itemId` | string | 是 | `"7891234567"` | 商品 ID |

#### 响应要点

```
data.commonData.itemBuyInfo  →  List[dict]，直接原样传给 order.create 的 params
                              （内部结构为闲鱼黑盒，请勿修改字段）
data.commonData.priceInfo    →  价格详情
data.commonData.addressInfo  →  收货地址列表（render 会预选默认地址）
ret[0] 含 "FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT" / "必走验货宝" / "ONLY_YHB"
                              →  该商品必须走验货宝链路，调用方应回退至 §3.5/§3.6
```

#### 注意事项

1. **链路依赖**：render 返回的 `itemBuyInfo` 必须完整透传给 create，不能丢失或修改，否则 create 报参数错误。
2. **账号前置条件**：账号需配置至少一个有效收货地址，否则 render 成功但 itemBuyInfo 为空。
3. **风控提醒**：高频调用 render 会触发账号验证，生产环境需加调用频率限制。

---

### 3.3 普通下单-创建：`mtop.taobao.idle.trade.order.create` v5.0

| 字段 | 值 |
|---|---|
| **优先级** | 🔴 高 |
| **功能用途** | 创建真实订单（拍下）。**警告：该接口会生成真实未付款订单，请确认业务风险。** |
| **取证来源** | `common/services/xianyu_order_client.py::XianyuOrderClient.create()` |
| **建议实现位置** | 新建 `apis/trade_api.py::TradeApi.order_create()` |
| **实现状态** | ✅ 已实现（`apis/trade_api.py` + 门面 XianyuApis.order_create()/place_order()，2026-08-23）。注意：会生成真实未付款订单，仅用于测试/明确授权场景。实现细节参见 [mtop_taobao_idle_trade_order_create.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/mtop_taobao_idle_trade_order_create.md)。 |
| **验证状态** | ⏳ 待验证 |

#### 请求参数

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `params` | string (JSON) | 是 | `'[{"...": "..."}]'` | `order_render()` 返回的 `itemBuyInfo` 列表 **JSON 字符串化**后的值，注意 `separators=(",", ":")` 无空格紧凑序列化 |

#### 响应要点

```
data.bizOrderIdStr 或 data.bizOrderId  →  订单号（bizOrderId，字符串格式用于后续链路）
data.payUrl                           →  付款链接（HTTPS 开头，调用方不应自动访问）
ret[0] 同 §3.2 的 YHB 标志            →  若 create 阶段才返回验货宝限制，同样回退
```

#### 注意事项

1. ⚠️ **风险提示**：该接口会在闲鱼生成真实的未付款订单，占用卖家的商品库存额度。仅用于自动化测试或经过用户明确授权的场景。
2. render → create 必须使用**同一个 cookie 实例**，否则服务端会返回「下单参数已失效」。
3. 若返回 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT`，说明该商品是验货宝商品，普通链路 create 也可能在 create 阶段才拒绝（不一定在 render 阶段），调用方需实现**两处**回退判断。

---

### 3.4 收货地址列表：`mtop.taobao.idle.logistic.address.list.query` v1.0

| 字段 | 值 |
|---|---|
| **优先级** | 🟡 中 |
| **功能用途** | 查询账号已配置的所有收货地址，用于验货宝下单时确定 `buyerAddressId`。 |
| **取证来源** | `common/services/xianyu_order_client.py::XianyuOrderClient._get_default_address_id()` |
| **建议实现位置** | 新建 `apis/trade_api.py::TradeApi.get_address_list()`（验货宝链路前置） |
| **验证状态** | ⏳ 待验证 |

#### 请求参数

无（空对象 `{}` 即可）。

#### 响应要点

```
data.data.addressList: [
  {
    "addressId": 123456789,      // 地址ID，验货宝下单时作为 buyerAddressId 传入
    "status": 1,                  // 1 = 默认地址 / 正常；其他值可能是历史地址
    "fullName": "张三",           // 收货人姓名
    "mobile": "138****1234",      // 脱敏手机号
    "province"/"city"/"area"/"detailAddress"  // 省市区详细地址
  },
  ...
]
```

#### 注意事项

1. 选择逻辑：优先取 `status == 1` 的地址作为默认，否则取列表第一个。
2. 如果 `addressList` 为空，验货宝链路直接失败，返回「账号未配置收货地址」。

---

### 3.5 验货宝下单-渲染：`mtop.alibaba.idle.pc.yhb.order.create.render` v1.0

| 字段 | 值 |
|---|---|
| **优先级** | 🟡 中 |
| **功能用途** | 验货宝专用链路第 2 步：校验商品可买并拿到 `yhbVersion`（验货宝协议版本）和 `buyQuantity`（购买数量）。失败时可用默认值（`yhbVersion=3, buyQuantity=1`）兜底。 |
| **取证来源** | `common/services/xianyu_order_client.py::XianyuOrderClient.yhb_render()` |
| **建议实现位置** | 新建 `apis/trade_api.py::TradeApi.yhb_order_render()` |
| **验证状态** | ⏳ 待验证 |

#### 请求参数

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `itemId` | string | 是 | `"7891234567"` | 商品 ID |

#### 响应要点

```
data.buttonDisable == true          →  验货宝下单按钮被禁用（商品不可买/已下架），直接失败
data.yhbVersion          →  "3" 等字符串，转 int 后填入 channelData
data.yhbConfirmBuy.buyQuantity      →  1，购买数量（闲鱼一般为 1 件制）
```

#### 注意事项

1. **best-effort 策略**：xianyu-auto-reply 中即使该接口失败（非账号失效类错误），依然使用默认值继续走 yhb_create，提高成功率。
2. 账号失效类错误（Token 过期等）应及时中断链路，避免无意义重试。

---

### 3.6 验货宝下单-创建：`mtop.alibaba.idle.pc.yhb.order.create` v1.0

| 字段 | 值 |
|---|---|
| **优先级** | 🟡 中 |
| **功能用途** | 验货宝专用链路第 3 步：创建真实订单（拍下）。与普通链路相同，**会生成真实订单**。 |
| **取证来源** | `common/services/xianyu_order_client.py::XianyuOrderClient.yhb_create()` |
| **建议实现位置** | 新建 `apis/trade_api.py::TradeApi.yhb_order_create()` |
| **验证状态** | ⏳ 待验证 |

#### 请求参数

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `itemId` | string | 是 | `"7891234567"` | 商品 ID |
| `optionalPromotionIdValueList` | string | 是 | `"[]"` | 空数组 JSON 字符串 |
| `buyerAddressId` | int/string | 是 | `123456789` | §3.4 返回的 `addressId` |
| `buyQuantity` | int | 是 | `1` | 购买数量（一般 1） |
| `channel` | string | 是 | `"web"` | 渠道固定 web |
| `channelData` | string (JSON) | 是 | `'{"yhbVersion":3}'` | §3.5 返回的 yhbVersion，紧凑 JSON 字符串 |

#### 响应要点

与普通 create 一致：`data.bizOrderIdStr` / `data.bizOrderId` 为订单号，验货宝订单后续需要在 yhb 专属页面付款。

#### 注意事项

1. ⚠️ **风险提示**：同 §3.3，会生成真实未付款订单。
2. 完整验货宝链路顺序（推荐在 TradeApi 层面提供一个 `place_order_yhb` 组合方法封装）：
   ```
   address.list.query → (yhb.render 可选) → yhb.create
   ```
3. 推荐再提供一个更高层 `place_order(item_id)` 方法，自动处理「普通链路 → 验货宝回退」判断逻辑，标志位：`FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT`、`必走验货宝`、`ONLY_YHB`，任一命中即回退。

---

## 4. 未实现 WebSocket lwp 路由详情（2 个）

以下路由均需在已注册的 WS 连接上发送，遵循 pyxianyu 现有模式：
```python
{"lwp": "/r/...", "headers": {"mid": <唯一请求ID>, ...}, "body": [...]}
```
并通过 `mid` 匹配响应。

---

### 4.1 会话列表分页：`/r/Conversation/listNewestPagination`

| 字段 | 值 |
|---|---|
| **优先级** | 🔴 高 |
| **功能用途** | 按时间倒序获取账号的会话（聊天窗口）列表，支持分页。是当前 pyxianyu 缺失的核心 IM 入口方法（现有的 `list_all_conversations` 实际拿的是消息记录，命名有误）。 |
| **取证来源** | `backend-web/app/services/chat_new/im_client.py::GoofishImClient.get_conversations()` |
| **建议实现位置** | `xianyu_live.py::XianyuLive.list_conversations()`（新增方法，与现有 `list_all_conversations` 并列，后续建议重命名后者为 `list_messages`） |
| **验证状态** | ⏳ 待验证 |

#### 请求 body 结构（数组，位置敏感）

| 索引 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `body[0]` | int | 是 | `9007199254740991` | 起始时间戳；**首页传 `Number.MAX_SAFE_INTEGER` (≈9e15)**；翻页传上一页返回的 `nextCursor` |
| `body[1]` | int | 是 | `20` | 每页数量，建议 20 |

```json
{
  "lwp": "/r/Conversation/listNewestPagination",
  "headers": { "mid": "<mid>" },
  "body": [9007199254740991, 20]
}
```

#### 响应 body 结构

```json
{
  "hasMore": true,
  "nextCursor": 1724500000000,
  "userConvs": [
    {
      "cid": "<cid>@goofish",
      "lastMessage": {
        "msgType": 1,
        "contentSummary": "你好，在吗？",
        "createdAt": 1724500000000
      },
      "unreadCount": 2,
      "receiverId": "<对方uid>@goofish",
      "receiverNick": "卖家昵称",
      "avatarUrl": "https://...",
      "itemId": "7891234567",       // 若会话关联商品
      "title": "商品标题",           // 若会话关联商品
      "price": "100.00"             // 若会话关联商品
    }
  ]
}
```

#### 注意事项（重要）

1. **IM 流控**：xianyu-auto-reply 实测会返回 `body.code == "400600001"`（IM 服务限流），需**指数退避重试**：`wait_sec = (attempt + 1) * 2`，最多重试 3 次。
2. **注册后冷却**：WS 注册成功后建议 `asyncio.sleep(3)` 再首次调用，防止第一笔请求直接被限流。
3. `body[0]` 首页必须传**极大值**（不是 0 也不是当前时间），否则返回的是从该时间点起「旧→新」的少量记录，拿不到最新会话。
4. 翻页结束条件：`hasMore == false` 或 `nextCursor` 缺失。

---

### 4.2 消息撤回：`/r/MessageManager/recallMessage`

| 字段 | 值 |
|---|---|
| **优先级** | 🟡 中 |
| **功能用途** | 撤回一条自己在 2 分钟内发送的消息。 |
| **取证来源** | `backend-web/app/services/chat_new/im_client.py::GoofishImClient.recall_message()` + `send_text_message()` 返回 `messageId` 的解析逻辑 |
| **建议实现位置** | `xianyu_live.py::XianyuLive.recall_message(message_id)`（新增）。同时需修改 `send_msg()` 的返回值，额外返回 `messageId` 和 `uuid`（当前只返回原始响应）。 |
| **实现状态** | ✅ 已实现（`xianyu_live.py::XianyuLive.recall_message` + `send_msg` 返回 `SentMessageReceipt`，2026-08-23）。实现细节参见 [protocol_ws_im_recall.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/protocol_ws_im_recall.md)。 |
| **验证状态** | ✅ 已验证（单测 12 条全绿 + mock smoke shape 校验；4 条 messageId 解析顺序、5 种 recall 状态、400600001 指数退避）。 |

#### 请求 body 结构

| 索引 | 类型 | 必填 | 示例值 | 说明 |
|---|---|---|---|---|
| `body[0]` | string | 是 | `"<message_id>"` | 通过 `sendByReceiverScope` 返回体中解析出的服务端 `messageId` |

```json
{
  "lwp": "/r/MessageManager/recallMessage",
  "headers": { "mid": "<mid>" },
  "body": ["<message_id>"]
}
```

#### 响应要点

```
response.code == 200                →  撤回成功
response.code != 200                →  撤回失败
    body.reason 字段                 →  失败原因文案（如"超过可撤回时间"、"非本人消息"）
```

#### `messageId` 获取方法（配套改造 `send_msg`）

`/r/MessageSend/sendByReceiverScope` 成功返回时，`messageId` 可能嵌套在多个位置（xianyu-auto-reply 实测发现不同版本返回位置不同），解析顺序：

```python
body = response.get("body", {})
message_id = ""
if isinstance(body, dict):
    raw = body.get("messageId") or body.get("1")
    if isinstance(raw, dict):
        raw = raw.get("messageId") or raw.get("1")
    if isinstance(raw, str):
        message_id = raw
```

调用方需在 `send_msg()` 返回值中同时返回 `messageId`，否则无法支持撤回。

#### 注意事项

1. 撤回时限由闲鱼服务端控制（通常为发送后 2 分钟），超期会返回明确 reason，无需客户端计时。
2. 只有**自己发送**的消息能撤回；已被对方「已读」后的消息在部分场景下仍可撤回（闲鱼策略）。
3. 撤回成功后，对方会话中原消息会被替换为「你撤回了一条消息」占位卡片。

---

## 5. pyxianyu 内部已有文档但未代码实现（2 项）

这两个属于 pyxianyu 自己的技术债，不来自 xianyu-auto-reply 对比，但一并列出方便排期。

### 5.1 `mtop.taobao.idlemessage.pc.session.sync`（HTTP）

- 文档：[mtop_taobao_idlemessage_pc_session_sync.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/mtop_taobao_idlemessage_pc_session_sync.md)
- 用途：HTTP 拉取会话列表与最新消息（WS 长连接外的兜底/补全方案），与 `Conversation/listNewestPagination` 功能有重叠但粒度不同。
- 优先级：🟡 中（已有文档，实现成本低；可以作为 WS 不可用时的备用方案）

### 5.2 `/r/Conversation/setTop`（WS）+ 配套 `listTop`

- 文档：[protocol_im_conversation_top.md](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/docs/protocol_im_conversation_top.md)
- 用途：会话置顶 / 取消置顶；`listTop` 可独立获取置顶会话。
- 优先级：🟡 中（已有完整文档，实现时参照 §4 的 WS body 构造模式即可；注意 `isTop=true/false` 的 body 位置）

---

## 6. 实现排期建议（按优先级分批次）

### 第一批（高优先级，高频刚需）

| # | API / 路由 | 放哪里 | 依赖关系 |
|---|---|---|---|
| 1 | `item.polish` | `apis/item_api.py` | 无（独立可用） |
| 2 | `Conversation/listNewestPagination` | `xianyu_live.py` | 需先修复现有 `list_all_conversations` 命名混淆 |
| 3 | `trade.order.render` + `trade.order.create` | 新建 `apis/trade_api.py` | render → create 强依赖；实现时先提供独立方法再提供 `place_order` 封装 |

### 第二批（中优先级，特定业务）

| # | API / 路由 | 放哪里 | 依赖关系 |
|---|---|---|---|
| 4 | `logistic.address.list.query` + `yhb.*` | `apis/trade_api.py`（同文件） | 在第一批 render/create 的基础上扩展回退逻辑 |
| 5 | `MessageManager/recallMessage` | `xianyu_live.py` | 需先改造 `send_msg()` 返回 `messageId` |
| 6 | 补齐 §5 两个内部欠账 | `apis/session_api.py`（新建） + `xianyu_live.py` | 参考已有文档直接实现 |

---

## 7. 待进一步确认的 API（xianyu-auto-reply README 提及，源码未取证到）

以下功能在 xianyu-auto-reply 项目 README / 模块名中有提及，但本次 `search_code("mtop.")` + 核心文件读取未定位到实际 MTop 接口名，需后续浏览器取证后补充：

| 功能模块 | 可能的接口命名模式 | 当前状态 |
|---|---|---|
| 自动评价（订单完成后自动给卖家好评） | `mtop.*.rate.*` / `mtop.*.comment.*` 系列 | ❓ 未确认接口名 |
| 订单同步（自动发货前置：获取待发货订单列表） | `mtop.*.trade.*.list` / `mtop.*.order.list` 系列 | ❓ 未确认接口名 |
| 卡券 / 虚拟物品发货 | `mtop.*.virtual.*` 系列 | ❓ 未确认接口名 |
| 自动回复关键词触发 & 延迟策略 | 非 API，纯业务逻辑 | — |

> 建议在实现完 §6 的 8 + 2 个已确认 API 后，通过浏览器自动化对上述功能进行取证补全。

---

## 8. 通用实现规范（对齐 pyxianyu 现有代码风格）

所有新增 API 在代码实现时请遵守以下约定（与现有 apis 模块保持一致）：

1. **文件归属**：新增方法优先放入语义对应的 `apis/*_api.py`（如擦亮放 `item_api.py`，下单系列放 `trade_api.py`），并在 `xianyu_apis.py` 门面类中转发对外暴露。
2. **签名机制**：所有 MTop HTTP 请求复用现有 sign 逻辑（`_m_h5_tk` → token；`timestamp + token + data_val` 拼接后 MD5），与 `item_api.py` 中 `downshelf_item` 等保持一致。
3. **Token 过期处理**：请求返回 `ret[]` 中任一元素含 `TOKEN_EXOIRED` 或 `TOKEN_EXPIRED` 时，自动触发 `refresh_token()` 并重试一次；多次失败抛异常。
4. **返回结构**：方法返回值统一为 `dict` 格式，含 `success: bool` + 业务字段，错误信息放 `error: str`，避免直接裸抛 `ret[]` 原始数组。
5. **文档同步**：每个 API 代码实现后，同步在 `docs/` 下生成对应接口文档，命名规范：
   - MTop 接口 → `mtop_<下划线分隔的接口名后半段>.md`（例：`mtop_taobao_idle_item_polish.md`）
   - WS 路由 → `protocol_<语义名>.md`（例：`protocol_im_conversation_list.md`）
   - 文档必须脱敏：真实 `sessionId` → `<sid>`，`messageId` → `<message_id>`，`cid` → `<cid>`，UID → `<uid>`。
