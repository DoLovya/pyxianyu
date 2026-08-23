## ADDED Requirements

### Requirement: 收货地址查询返回列表 + 默认地址（status==1 优先）

The system SHALL expose `TradeApi.get_address_list()` (via `mtop.taobao.idle.logistic.address.list.query` v1.0, empty payload) returning a structured dict containing `address_list` and `default_address`.

#### Scenario: 账号有 2 个地址，其中一个 status==1
- **WHEN** 上游返回 `data.data.addressList = [{addressId:100, status:0, ...}, {addressId:200, status:1, fullName:"张三", ...}]`
- **THEN** 返回 `{success: true, address_list: [100 地址, 200 地址], default_address: {addressId:200, status:1, fullName:"张三"}}`

#### Scenario: 账号地址列表为空（未配置）
- **WHEN** `addressList` 缺失、为 `None` 或 `[]`
- **THEN** 返回 `{success: true, address_list: [], default_address: None}`
- **AND** `place_order_yhb` 必须返回 `status="no_address"` 或等价失败态（本 spec 只约束 get_address_list，具体由 yhb-order-create spec 约束）。

#### Scenario: Token 过期 / 账号失效
- **WHEN** 上游返回 ret 中含 `TOKEN_EXPIRED` 等账号失效关键字
- **THEN** 方法抛 `XianyuApiError`（与现有 order_render 行为一致）
