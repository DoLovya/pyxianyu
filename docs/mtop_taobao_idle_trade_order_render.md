# `mtop.taobao.idle.trade.order.render` 接口记录

> ⚠️ 本接口为**写操作链路前置**：它本身不生成订单，但返回的 `itemBuyInfo` 将被 `order.create` 用于创建真实订单。请在实现 create 时注意风险。

## 目的

渲染某个商品的下单页面信息，核心产出是 `commonData.itemBuyInfo`（黑盒数组）。调用方**不得修改或重排**该数组，需紧凑 JSON 序列化后透传给 `mtop.taobao.idle.trade.order.create`。

本实现取证来源：
- 外部仓库 `zhinianboke/xianyu-auto-reply`，文件 `common/services/xianyu_order_client.py::XianyuOrderClient.render()`

## 取证来源

### 外部源码定位

参考调用：
- `RENDER_API = "mtop.taobao.idle.trade.order.render"`
- `RENDER_VERSION = "7.0"`
- 调用方式：`POST .../h5/mtop.taobao.idle.trade.order.render/7.0/`，data：`{"itemId": "<item_id>"}`
- 回退条件：当 ret[0] 或错误信息中包含 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT` / `必走验货宝` / `ONLY_YHB` 任一关键词 → 商品是验货宝专属，普通链路无法下单，调用方应切到验货宝链路（另独立 change 实现）。

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.render/7.0/
```

### Query 参数（标准 MTop，与 downshelf/polish 相同 appKey/sign 机制）

```text
jsv=2.7.2
appKey=34839810
v=7.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=mtop.taobao.idle.trade.order.render
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.order.0.0
spm_pre=a21ybx.order.render.1.f00bar
log_id=xianyu_order_render
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

```json
{
  "itemId": "7891234567"
}
```

## 响应结构

### 普通商品渲染成功

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "commonData": {
      "itemBuyInfo": [
        {
          "__raw__": "...黑盒字段，禁止修改..."
        }
      ],
      "priceInfo": { "priceStr": "￥100.00" },
      "addressInfo": [
        { "addressId": 123456789, "fullName": "张三" }
      ]
    }
  }
}
```

### 验货宝专属（普通链路 render 阶段拒绝）

```json
{
  "ret": [
    "FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT::本宝贝为必走验货宝商品，不支持普通链路下单"
  ]
}
```

### 账号未配置收货地址（itemBuyInfo 为空）

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": { "commonData": {} }
}
```

本仓库在 `itemBuyInfo` 为空时会抛出 `XianyuApiError`，便于调用方定位。

## 注意事项

1. **链路前置**：普通下单 create 调用前必须调过本接口，且用同一 cookie 实例返回的 `itemBuyInfo`，否则「下单参数已失效」。
2. **itemBuyInfo 黑盒**：项目只做透传，不对字段做解析；若闲鱼侧升级导致 create 报错，优先排查是不是 render 版本不对。
3. **验货宝回退**：命中 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT`/`必走验货宝`/`ONLY_YHB` 时，本仓库抛出 `XianyuYhbRequiredError(item_id=...)`，供上层或后续 change 切换至 address.list -> yhb.render -> yhb.create。

## 验证状态

⏳ 待验证（外部仓库生产环境调用，尚未在本项目做浏览器自动化抓包交叉验证）

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/trade_api.py::TradeApi.order_render(item_id)`
- `third_party/pyxianyu/src/pyxianyu/apis/trade_api.py::TradeApi.place_order(item_id)`（组合封装）
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py::XianyuApis.order_render(item_id)`、`XianyuApis.place_order(item_id)`
