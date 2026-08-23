# MTop 接口：验货宝订单创建 — `mtop.alibaba.idle.pc.yhb.order.create` v1.0

> ⚠️ **红色风险提示**：调用本接口会在闲鱼平台生成**真实的未付款订单**，占用卖家库存，测试账号 + 明确授权两层 opt-in 后才可调用（XY_TEST_ORDER_ITEM_ID + XY_RUN_ORDER_TESTS=1）。
>
> 取证日期：2026-08-23
> 取证来源：`common/services/xianyu_order_client.py::XianyuOrderClient.yhb_create()`
> 实现代码位置：[trade_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/trade_api.py#L183-L234)（`TradeApi.yhb_order_create`）
> 组合封装：[place_order_yhb](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/trade_api.py#L236-L357)（自动 address→render→create，成功返回 `status=yhb_success`，失败返回 `status=yhb_failed`，地址空返回 `status=no_address`，账号失效返回 `status=account_invalid`）

---

## 1. 目的

验货宝专用链路第 3 步：用前面两步拿到的默认地址 `buyerAddressId`、渲染默认值 `yhbVersion` 与 `buyQuantity`，生成**真实验货宝订单**，返回订单号 `bizOrderId` 与付款链接 `payUrl`。

---

## 2. 请求

- **API**：`mtop.alibaba.idle.pc.yhb.order.create`
- **版本**：`1.0`
- **URL**：`https://h5api.m.goofish.com/h5/mtop.alibaba.idle.pc.yhb.order.create/1.0/`
- **方法**：`POST`（application/x-www-form-urlencoded）
- **签名**：标准 MTop sign。

### 2.1 请求 data_val（6 字段，紧凑无空格 JSON 序列化）

```json
{
  "itemId": "7891234567",
  "optionalPromotionIdValueList": "[]",
  "buyerAddressId": 123456789,
  "buyQuantity": 1,
  "channel": "web",
  "channelData": "{\"yhbVersion\":3}"
}
```

**注意事项（非常关键）**：

1. `optionalPromotionIdValueList` 必须是**空数组 JSON 字符串** `"[]"`，而不是 Python `list` 类型。
2. `channelData` 必须是 `'{"yhbVersion":<int>}'` 的**紧凑 JSON 字符串**，必须使用 `json.dumps(obj, ensure_ascii=False, separators=(",", ":"))`；不要带空格，不要 `pretty` 格式，否则 sign 签名校验失败。
3. `buyQuantity` 为 int，`channel` 固定为 `"web"`。
4. `buyerAddressId` 类型可 int 或 str，闲鱼两侧兼容；推荐取 §3.4 返回的 int 原样传。

### 2.2 spm / log_id

| 字段 | 示例值 |
|---|---|
| `spm_cnt` | `a21ybx.order.0.0` |
| `spm_pre` | `a21ybx.order.yhbcreate.1.f00bar` |
| `log_id` | `xianyu_yhb_create` |

---

## 3. 响应

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "data": {
      "bizOrderId": 3006100000000000001,
      "bizOrderIdStr": "3006100000000000001",
      "payUrl": "https://h5.m.goofish.com/app/...",
      "waitForPay": true
    }
  }
}
```

### 3.1 关键字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `bizOrderId` / `bizOrderIdStr` | int / str | 验货宝订单 ID，上层统一转 str 返回（`biz_order_id`） |
| `payUrl` | str 或 None | 付款页面 HTTPS 链接，调用方**不应主动发起访问**（避免误付款） |

---

## 4. 验证方法

- 单测：`YhbCreateTest`（3 条：6 字段 data_val 断言（含 `channelData` 紧凑 JSON）；成功返回 bizOrderId；业务错误抛 `XianyuApiError`）；`PlaceOrderYhbTest`（地址空→ `status=no_address` 不发 render/create；render 兜底 + create 成功 → `status=yhb_success`；create 业务错 → `yhb_failed`）。
- 三件套：compileall 0 错误，unittest ≥19 条全绿，smoke_1_0.py 退出码 0。

---

## 5. 风险与合规

1. 🔴 **必生成真实未付款订单**：验货宝 create 与普通 create 同级风险。
2. 🔴 **两层 opt-in**：smoke harness 及任何自动化测试，在 `XY_TEST_ORDER_ITEM_ID` 且 `XY_RUN_ORDER_TESTS=1` 同时满足时才调用。
3. **频率限制**：高频调用会触发风控，建议 1 单/分钟以上。

---

## 6. 完整三步组合封装

`place_order_yhb(item_id, buyer_address_id=None)`：
1. `get_address_list()` → 选默认 address；若空 → `status=no_address`（不发后续两步请求）；
2. `yhb_order_render(item_id)` → 非账号错误默认值兜底；账号错误 → `status=account_invalid`；
3. `yhb_order_create(item_id, chosen_address_id, yhb_version=render.yhb_version, buy_quantity=render.buy_quantity)` → 成功 `status=yhb_success`；业务错 `status=yhb_failed`；账号错 `account_invalid`。

现有 `place_order(item_id)` 已内置回退：普通 render/create 任一步返回 `yhb_required` 时自动再次 `place_order_yhb(item_id)`，最终返回六态枚举（success / yhb_success / yhb_failed / yhb_required / account_invalid / failed）。
