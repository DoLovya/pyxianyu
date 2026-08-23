# Capability: Item Polish (item-polish)

## Purpose

暴露 `ItemApi.polish_item(item_id)` + 门面 `XianyuApis.polish_item(item_id)`：每日一擦亮（v2.0 `mtop.taobao.idle.item.polish`）。幂等：多次调用不报错，以 `already_polished` 区分。

## Requirements

### Requirement: 单个商品擦亮，每日多次调用幂等

The system SHALL provide `polish_item(item_id)` that invokes `mtop.taobao.idle.item.polish` v=2.0 and returns a structured dict indicating success. When the upstream returns `IDLEITEM_POLISH_AGAIN` or its Chinese equivalent `宝贝已经擦亮过了` (item polished again today), the method MUST still return `success=True` and mark `already_polished=True`, instead of raising an error.

#### Scenario: 首次擦亮成功
- **WHEN** 调用方传入一个在售且今日未擦亮的 `item_id`
- **THEN** 返回 `{success: true, already_polished: false, ret: [...], data: {...}}`

#### Scenario: 今日已再次擦亮（幂等）
- **WHEN** 调用方对同一天内已擦亮过的商品再次调用 `polish_item`
- **THEN** 上游 `ret[]` 包含 `IDLEITEM_POLISH_AGAIN` 或 `宝贝已经擦亮过了`
- **AND** 方法返回 `{success: true, already_polished: true}` 且不抛出 `XianyuApiError`

#### Scenario: Token 过期
- **WHEN** `_m_h5_tk` 过期或缺失
- **THEN** 抛出与 `downshelf_item` 一致的 `XianyuApiError`（携带 ret），调用方可以通过 `refresh_token()` 刷新后重试
