# MTop 接口：验货宝下单渲染 — `mtop.alibaba.idle.pc.yhb.order.create.render` v1.0

> 取证日期：2026-08-23
> 取证来源：`common/services/xianyu_order_client.py::XianyuOrderClient.yhb_render()`
> 实现代码位置：[trade_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/trade_api.py#L115-L181)（`TradeApi.yhb_order_render`）
> 配套方法（组合封装）：[place_order_yhb](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/trade_api.py#L236-L357)

---

## 1. 目的

验货宝专用链路第 2 步：校验商品是否可走验货宝、解析 `yhbVersion`（验货宝协议版本号，供 `channelData.yhbVersion` 填充）、`yhbConfirmBuy.buyQuantity`（购买数量）、以及 `buttonDisable`（是否按钮被禁用）。

⚠️ **Best-effort 策略**：非账号失效类错误（例如「按钮禁用」「商品暂不可买」等）在本方法内部**不抛异常**，使用默认值 `yhb_version=3 / buy_quantity=1 / button_disable=True` 继续下游调用。账号失效类错误（TOKEN_EXPIRED 等）必须向上抛，由调用方标记「账号失效」。

---

## 2. 请求

- **API**：`mtop.alibaba.idle.pc.yhb.order.create.render`
- **版本**：`1.0`
- **URL**：`https://h5api.m.goofish.com/h5/mtop.alibaba.idle.pc.yhb.order.create.render/1.0/`
- **方法**：`POST`（application/x-www-form-urlencoded）
- **签名**：标准 MTop sign。

### 2.1 请求 data_val

```json
{"itemId":"7891234567"}
```

### 2.2 spm / log_id

| 字段 | 示例值 |
|---|---|
| `spm_cnt` | `a21ybx.order.0.0` |
| `spm_pre` | `a21ybx.order.yhbrender.1.f00bar` |
| `log_id` | `xianyu_yhb_render` |

---

## 3. 响应

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "data": {
      "buttonDisable": false,
      "yhbVersion": "4",
      "yhbConfirmBuy": {
        "buyQuantity": 1
      }
    }
  }
}
```

### 3.1 关键返回字段

| 字段 | 类型 | 默认值（非账号失效错误兜底） |
|---|---|---|
| `buttonDisable` | bool → Python `bool` | `True` |
| `yhbVersion` | str → Python `int` | `3` |
| `yhbConfirmBuy.buyQuantity` | int → Python `int` | `1` |

**兜底触发条件**：`post_json` 过程中抛 `XianyuApiError`，且错误消息不命中 `_ACCOUNT_INVALID_MARKERS`（SESSION_EXPIRED / TOKEN_EXPIRED / TOKEN_EXOIRED / 已掉线 / 请重新登录）。

---

## 4. 验证方法

- 单测：`YhbRenderTest`（3 条：正常解析 4/1；非账号错误默认值 3/1 + fallback_used=True；账号失效类抛 `XianyuApiError`，上层转 `status=account_invalid`）。
- 三件套同上。

---

## 5. 用途

- 作为验货宝下单三步的**中间渲染**：一般不单独调用，通常由 `place_order_yhb` 自动发起。
- 返回的 `yhb_version` / `buy_quantity` 直接作为 `yhb_order_create(...)` 的入参。
