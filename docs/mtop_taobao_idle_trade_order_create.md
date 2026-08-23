# `mtop.taobao.idle.trade.order.create` 接口记录

> # ⚠️ 高风险：会生成真实订单
>
> 调用本接口会在闲鱼账号下生成一笔**真实的未付款订单**，占用卖家库存和买家下单额度。请先在非关键的测试账号、测试商品上完成冒烟，再用于生产自动化。
>
> 本仓库只做到「创建订单（拍下）」，**不实现任何付款逻辑**（不调用 `mtop.order.dopay` 等接口）。

## 目的

在 `order.render` 成功后，用其返回的 `itemBuyInfo` 作为 `params` 紧凑序列化，发起真正的下单（拍下）。

本实现取证来源：
- 外部仓库 `zhinianboke/xianyu-auto-reply`，文件 `common/services/xianyu_order_client.py::XianyuOrderClient.create()`

## 取证来源

### 外部源码定位

参考调用：
- `CREATE_API = "mtop.taobao.idle.trade.order.create"`
- `CREATE_VERSION = "5.0"`
- 调用方式：`POST .../h5/mtop.taobao.idle.trade.order.create/5.0/`
- 关键 data 构造：

```python
params_str = json.dumps(item_buy_info, ensure_ascii=False, separators=(",", ":"))
data = {"params": params_str}
```

> 注意 `params` 本身是字符串（不是嵌套对象），是 `itemBuyInfo` 数组经过 **紧凑 JSON 序列化**（无空格）后的值。

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.create/5.0/
```

### Query 参数

```text
jsv=2.7.2
appKey=34839810
v=5.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=mtop.taobao.idle.trade.order.create
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.order.0.0
spm_pre=a21ybx.order.create.1.f00bar
log_id=xianyu_order_create
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

```json
{
  "params": "[{\"...\":\"...\"}]"
}
```

> `params` 的**字符串内容**，即 `order_render()` 返回的 `item_buy_info` 紧凑序列化结果。任何对 `item_buy_info` 字段的修改、重排、添加空白键（非紧凑序列化）都可能导致 create 失败。

## 响应结构

### 成功（拍下，待付款）

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "bizOrderIdStr": "4123456789012345678",
    "bizOrderId": 4123456789012345678,
    "payUrl": "https://h5.m.taobao.com/awp/core/detail.htm?id=..."
  }
}
```

- `bizOrderIdStr`：后续链路（如查看订单、取消订单、付款）应优先使用字符串形式。
- `payUrl`：付款页面 URL，调用方**不得自动访问**，返回给人工操作即可。

### 验货宝专属（create 阶段才拒绝）

与 render 阶段相同，出现 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT` / `必走验货宝` / `ONLY_YHB` 任一关键词时，本仓库抛出 `XianyuYhbRequiredError`。

### 常见失败

- 「同一时间下单人数过多」- 建议指数退避重试。
- 「下单参数已失效」- render 与 create 使用了不同 cookie 或间隔太久。
- 「该宝贝已被拍下」- 商品库存不足（二手商品常见）。

## 注意事项

1. **Token 过期**：若 ret 含 `TOKEN_EXOIRED`/`TOKEN_EXPIRED`，调用方应先 `refresh_token()`，再**从头重跑** render → create 链路（不是只重跑 create）。
2. **幂等**：若调用超时未拿到响应，不要盲重试；否则可能生成多笔未付款订单。如果外部仓库有「同一 itemId + uniqueCode 幂等键」可后续引入。
3. **风险提醒**：每次成功调用都会生成真实订单，请做好定时清理（取消超时未付款），避免账号信用受损。

## 验证状态

⏳ 待验证（外部仓库生产环境调用，尚未在本项目做浏览器自动化抓包交叉验证）

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/trade_api.py::TradeApi.order_create(item_buy_info)`
- `third_party/pyxianyu/src/pyxianyu/apis/trade_api.py::TradeApi.place_order(item_id)`（组合封装，自动 render→create，并将验货宝/账户失效映射为状态码）
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py::XianyuApis.order_create(item_buy_info)`、`XianyuApis.place_order(item_id)`
