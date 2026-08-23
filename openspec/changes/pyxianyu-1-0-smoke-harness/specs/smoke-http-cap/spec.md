## ADDED Requirements

### Requirement: 无凭证模式下 harness 自动 mock，保证 HTTP API 结构正确

The system SHALL provide a standalone smoke script `scripts/smoke_1_0.py` that can run WITHOUT any real credential env variables. When `XY_COOKIE_STR` is unset, it MUST run HTTP-domain cases (`get_token`, `search_items`, `get_user_items`) in **mock mode** by injecting mocked `build_mtop_params/sign/post_json/parse_json_response/ensure_api_success` and still validate input → structure → return-shape for each public method (not just an import check).

#### Scenario: 空环境运行 — 不崩且无 FAIL
- **WHEN** 用户不设置任何凭证 env，执行 `python scripts/smoke_1_0.py`
- **THEN** 进程退出码为 0（PASS 或 SKIP，不能有 FAIL）
- **AND** 报告摘要里 `HTTP 域的 case status ∈ {PASS, SKIP}`

#### Scenario: mock 模式下每个 HTTP case 覆盖 shape 校验
- **WHEN** 任一 HTTP case 在 mock 模式跑完
- **THEN** case 的 `payload` 至少记录：方法名、mock 调用命中次数（非 0）、返回对象的类型（dict/dataclass/list）、关键字段存在性（如 place_order 有 status 字段）

### Requirement: 有凭证模式下真实 HTTP 调用，并对 polish/place_order 做宽松判定

When `XY_COOKIE_STR` is provided, the harness SHALL perform real network calls for HTTP cases. For write-capable endpoints the pass criteria MUST be lenient so that local development does not accidentally create real orders.

#### Scenario: polish_item — real 模式幂等成功
- **WHEN** 设置 `XY_TEST_ITEM_ID` + 有效 `XY_COOKIE_STR`，`mode=real`
- **THEN** `polish_item` 结果 `success` 必须为 true
- **AND** `already_polished` 是 `True` 或 `False` 之一（两种都算 PASS）
- **AND** 不抛出任何未捕获异常

#### Scenario: place_order — 四态判定
- **WHEN** 设置 `XY_TEST_ORDER_ITEM_ID` + `XY_RUN_ORDER_TESTS=1`（两层 opt-in），`mode=real`
- **THEN** `place_order` 返回的对象满足：
  1. 存在 `status` 字段
  2. `status` ∈ `{success, yhb_required, account_invalid, failed}`
  3. 若 `status == success` → `order_id` 不是空字符串（None 或非空 str 均通过）
- **AND** 即使 `status == failed` / `yhb_required`，case 标记 **PASS**（只保证不抛异常且 shape 合法）
- **AND** 未设置任一层 opt-in 时，case 标记 **SKIP**

### Requirement: 摘要退出码与凭证安全遮蔽

The harness MUST report outcome clearly to humans and CI, and never leak secrets into logs or JSON reports.

#### Scenario: 任意 FAIL
- **WHEN** 任一 case 结果 `status==FAIL`
- **THEN** 退出码 == 2

#### Scenario: 参数错误
- **WHEN** `--case` 指定不存在的 case 名
- **THEN** 退出码 == 3

#### Scenario: `--json` 报告脱敏
- **WHEN** 用 `--json report.json` 运行
- **THEN** 报告中 `env.XY_COOKIE_STR` 等凭证类字段仅显示 `<set>` 或 `<unset>`，不能写入任何 cookie 明文
