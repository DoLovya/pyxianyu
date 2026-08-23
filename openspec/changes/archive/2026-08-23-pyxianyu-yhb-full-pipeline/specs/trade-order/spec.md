## MODIFIED Requirements

### Requirement: 组合 place_order 封装并标注账户失效

The system SHALL provide `place_order(item_id)` that runs render → create sequentially, then automatically falls back to `place_order_yhb(item_id)` when the normal path returns `status="yhb_required"`. Final outcome SHALL map to a unified `status` enum that includes new states: `success` / `yhb_required` / `failed` / `account_invalid` / `yhb_success` / `yhb_failed`.

#### Scenario: 完整链路成功
- **WHEN** render + create 均成功
- **THEN** 返回 `{status: "success", order_id: <non-empty>, pay_url: <url>, item_buy_info: [...], error: ""}`

#### Scenario: 任一阶段验货宝 → 自动回退验货宝 → 验货宝也成功
- **WHEN** render 或 create 抛出 `XianyuYhbRequiredError` → normal 返回 yhb_required → place_order_yhb 最终成功
- **THEN** 返回 `{status: "yhb_success", order_id: <non-empty>, pay_url: <url>, error: "", yhb_result: {...}, normal_result: {原来 yhb_required 的那一份}}`

#### Scenario: 任一阶段验货宝 → 验货宝失败（比如 create 失败）
- **WHEN** normal 返回 yhb_required → place_order_yhb 最终失败（非 account_invalid）
- **THEN** 返回 `{status: "yhb_failed", error: <yhb 的错误信息>, yhb_result: {...}, normal_result: {...}}`

#### Scenario: 任一阶段验货宝 → 验货宝因「地址为空」根本未启动
- **WHEN** normal 返回 yhb_required → place_order_yhb 首次取 get_address_list 返回 default_address=None
- **THEN** 返回 `{status: "yhb_required", error: "yhb fallback skipped: no address; normal fallback reason: <原 info>", normal_result: {...}}`

#### Scenario: 账号登录态失效（普通阶段直接）
- **WHEN** 异常信息包含 `SESSION_EXPIRED` / `TOKEN_EXPIRED` / `已掉线` / `请重新登录` 任一关键词
- **THEN** 返回 `{status: "account_invalid", ...}`，不抛异常

#### Scenario: 其他失败
- **WHEN** 其他网络或业务错误
- **THEN** 返回 `{status: "failed", error: <错误信息>}`，不抛异常
