## ADDED Requirements

### Requirement: 渲染下单页并返回可透传的 itemBuyInfo

The system SHALL provide `order_render(item_id)` that calls `mtop.taobao.idle.trade.order.render` v=7.0 and returns the `commonData.itemBuyInfo` list (opaque, unparsed). Callers MUST be able to pass the returned list to `order_create` without modification.

#### Scenario: 普通商品 render 成功
- **WHEN** 调用方传入可在普通链路下单的 `item_id`，且账号已配置至少一个收货地址
- **THEN** 返回 `{success: true, item_buy_info: list[dict], raw: ...}`，且 `item_buy_info` 非空

#### Scenario: 必走验货宝商品 render 拒绝
- **WHEN** 传入的 `item_id` 是验货宝专属（上游返回 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT` / `必走验货宝` / `ONLY_YHB`）
- **THEN** 抛出 `XianyuYhbRequiredError`，并在异常属性中携带原始 `item_id` 与错误文案

### Requirement: 基于 itemBuyInfo 创建真实订单（拍下）

The system SHALL provide `order_create(item_buy_info)` that calls `mtop.taobao.idle.trade.order.create` v=5.0 with `params = json.dumps(item_buy_info, compact)`. On success it MUST expose the server-provided `bizOrderIdStr`/`bizOrderId` and `payUrl`.

#### Scenario: create 成功
- **WHEN** `item_buy_info` 由同一 cookie 的 render 返回且未修改
- **THEN** 返回 `{success: true, biz_order_id: str, pay_url: str, raw: ...}`，其中 `biz_order_id` 非空

#### Scenario: create 阶段才命中验货宝
- **WHEN** render 阶段未拦截但 create 上游返回验货宝专属标志
- **THEN** 抛出 `XianyuYhbRequiredError`（与 render 一致的异常类型）

### Requirement: 组合 place_order 封装并标注账户失效

The system SHALL provide `place_order(item_id)` that runs render → create sequentially, and maps outcomes to a unified `status` enum: `success` / `yhb_required` / `failed` / `account_invalid`.

#### Scenario: 完整链路成功
- **WHEN** render + create 均成功
- **THEN** 返回 `{status: "success", order_id: <non-empty>, pay_url: <url>, item_buy_info: [...], error: ""}`

#### Scenario: 任一阶段验货宝
- **WHEN** render 或 create 抛出 `XianyuYhbRequiredError`
- **THEN** 返回 `{status: "yhb_required", order_id: null, ..., error: <原始错误文案>}`，不抛异常

#### Scenario: 账号登录态失效
- **WHEN** 异常信息包含 `SESSION_EXPIRED` / `TOKEN_EXPIRED` / `已掉线` / `请重新登录` 任一关键词
- **THEN** 返回 `{status: "account_invalid", ...}`，不抛异常

#### Scenario: 其他失败
- **WHEN** 其他网络或业务错误
- **THEN** 返回 `{status: "failed", error: <错误信息>}`，不抛异常
