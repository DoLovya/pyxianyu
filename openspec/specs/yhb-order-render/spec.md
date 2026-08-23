## ADDED Requirements

### Requirement: yhb 渲染 best-effort — 非账号失效错误默认值不抛异常

The system SHALL call `mtop.alibaba.idle.pc.yhb.order.create.render` v1.0 with `{itemId: <string>}`. When the API call succeeds, the returned yhbVersion SHALL be parsed as integer and buyQuantity as integer. When the call fails with a **non-account-invalid error** (anything not matching `_ACCOUNT_INVALID_MARKERS`), the method SHALL NOT throw and SHALL instead return default values `yhb_version=3, buy_quantity=1` plus `button_disable=True` as a warning.

#### Scenario: render 完全成功，buttonDisable=false
- **WHEN** 上游返回 `data = {buttonDisable: false, yhbVersion: "4", yhbConfirmBuy: {buyQuantity: 1}}`
- **THEN** 返回 `{success: true, yhb_version: 4, buy_quantity: 1, button_disable: false, raw: {...}}`

#### Scenario: render 非账号失效错误（如「商品已下架」网络错误）
- **WHEN** 抛出 `XianyuApiError`，错误信息不含 TOKEN/SESSION
- **THEN** 返回 `{success: false, yhb_version: 3, buy_quantity: 1, button_disable: true, raw: exc.payload, error: exc.message}`
- **AND** 方法不抛异常，调用方可继续向下走 yhb_create（best-effort）。

#### Scenario: render 账号失效
- **WHEN** 抛出 `XianyuApiError`，信息含 `TOKEN_EXPIRED` / `已掉线` 任一
- **THEN** 方法继续抛（由上层 place_order_yhb 转 `status="account_invalid"`）。
