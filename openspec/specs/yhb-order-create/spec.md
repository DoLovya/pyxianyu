## ADDED Requirements

### Requirement: yhb 创建订单，参数紧凑序列化 + 真实订单风险提示

The system SHALL provide `yhb_order_create(item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3)` invoking `mtop.alibaba.idle.pc.yhb.order.create` v1.0. All JSON string parameters (`optionalPromotionIdValueList`, `channelData`) SHALL be serialized with `separators=(",", ":")`. On success it SHALL expose `biz_order_id` and `pay_url`.

#### Scenario: create 成功
- **WHEN** `buyerAddressId=200, yhb_version=4, buy_quantity=1, item_id="7891234567"`
- **THEN** data_val 内的 6 个字段正确对应：itemId=`"7891234567"`, optionalPromotionIdValueList=`"[]"`, buyerAddressId=`200`, buyQuantity=`1`, channel=`"web"`, channelData=`'{"yhbVersion":4}'`
- **AND** 返回 `{success: true, biz_order_id: "<非空字符串>", pay_url: "<url或None>", raw: {...}}`

#### Scenario: create 验货宝专属原因失败（如地址非法）
- **WHEN** 上游返回非 200 类业务错误（不含账号失效关键字）
- **THEN** 抛出与普通 create 一致的 `XianyuApiError`（由上层 place_order_yhb 转 `status="yhb_failed"`）。

#### Scenario: place_order_yhb 组合封装（自动取默认地址）
- **WHEN** 调用方传入 `place_order_yhb(item_id, buyer_address_id=None)`
- **THEN** 自动完成：`1) get_address_list` → 2) 取 default_address.addressId；若 default_address 为 None → 直接返回 `{status: "no_address", error: "账号未配置收货地址", ...}`，不发起 yhb_render 与 yhb_create 请求。
- **AND** yhb_render 非致命错误使用默认值 yhb_version=3 buy_quantity=1 继续 yhb_create；最终成功 → `status="yhb_success"`（与 `trade-order` delta spec 的 place_order 回退语义一致），失败 → `status="yhb_failed"`，账号失效 → `status="account_invalid"`。
