## Context

- 底层请求管线完全复用 `XianyuClient` 的 `build_mtop_params` + `build_signed_form` + `post_json` → `parse_json_response` → `ensure_api_success` 三段式，风格与 `downshelf_item`、`prepublish_check` 一致。
- `xianyu-auto-reply` 中 polish 为 `v=2.0`、order.render 为 `v=7.0`、order.create 为 `v=5.0`，均使用 `appKey=34839810`、`_m_h5_tk` token 的 sign 签名机制。
- `order.render` 返回的 `commonData.itemBuyInfo` 是黑盒数组结构，调用链路**不得修改或重排**，必须 JSON 紧凑序列化后原样传给 `order.create`；本设计仅提供取回和透传，不做字段解析。
- 普通链路与验货宝链路的切换判定：`ret[0]` 或 `error` 中出现 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT`、`必走验货宝`、`ONLY_YHB` 任一关键词时，表示商品是验货宝专属；当前变更集**不实现验货宝**，仅抛出结构化异常供上层（或后续 change）处理。
- create 接口会生成真实订单，需在 docstring 与接口文档中醒目提示风险。

## Goals / Non-Goals

**Goals：**

1. 在 `ItemApi` 中补齐 `polish_item`，幂等处理 `POLISH_AGAIN` / `宝贝已经擦亮过了`。
2. 新建 `TradeApi`，实现 `order_render` 与 `order_create`，并通过 `place_order` 封装为一条完整的普通下单链路；命中验货宝回退条件时抛出 `XianyuYhbRequiredError`。
3. 每个新增 API 在 `xianyu_apis.py` 门面中暴露，并在 `docs/` 生成对应 mtop_*.md 文档（脱敏）。

**Non-Goals：**

1. 不实现验货宝链路（address.list / yhb.render / yhb.create），留作后续独立 change（对应 `api_gap_analysis.md` 第二批）。
2. 不引入任何真实付款操作（不调用 `mtop.order.dopay` 等）。
3. 不修改 `send_msg` / `xianyu_live`（WebSocket 域，独立 change）。
4. 不引入异步改造：现有 `XianyuClient` 基于 `requests`（同步），新接口保持同步，异步由调用方通过 `asyncio.to_thread` 或 `run_in_executor` 自行包装。

## Decisions

- **决策 1（模块归属）**：polish 归 `apis/item_api.py`（与 downshelf/reshelf 同属商品管理）；render/create 归新建 `apis/trade_api.py`（与下单域独立，未来追加验货宝时同文件扩展）。
- **决策 2（幂等成功处理）**：`polish_item` 不抛 `XianyuPolishDuplicateError`，而是将「今天已擦亮过」视为**成功返回**并在返回 dict 中额外带 `already_polished: true` 标记，降低调用方的判断成本（`xianyu-auto-reply` 同样采用「视为成功」策略）。如需区分，可判断该布尔字段。
- **决策 3（验货宝回退处理）**：在 `ensure_api_success` 抛出 `XianyuApiError` 后，`order_render` / `order_create` / `place_order` 捕获并判定 `ret/msg` 是否匹配 `_YHB_ONLY_MARKERS`，匹配时重抛 `XianyuYhbRequiredError`（携带原始 error 文案），否则原样抛出。
- **决策 4（place_order 返回结构）**：`{status: "success" | "yhb_required" | "failed" | "account_invalid", order_id: str | None, pay_url: str | None, item_buy_info: list | None, error: str}`；与 `xianyu-auto-reply` 对齐，但保留结构中的 `item_buy_info` 便于调用方调试。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| `order_create` 生成真实未付款订单，滥用会占用卖家库存 | 业务侧信誉损失 | docstring + docs/ 顶部红色警告；默认建议先在测试账号跑通再投产 |
| Token 过期时 create/ polish 失败 | 调用方误判为接口异常 | 复用底层 `FAIL_SYS_TOKEN_EXOIRED` 判定，确保抛出 `XianyuApiError` 时含原始 ret，调用方可用 refresh_token 重试 |
| 今日已擦亮被误判为失败（批量时） | 运营侧定时任务统计失真 | `polish_item` 识别 `IDLEITEM_POLISH_AGAIN` / `宝贝已经擦亮过了`，返回 `{success: true, already_polished: true}` |
| 版本号/接口变更（MTop 协议升级）| 接口后续失效 | docs 中 `验证状态` 标记为 `待验证`；建议每 2 周对核心 API 做一次冒烟 |
