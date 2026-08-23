## Why

普通下单链路已就绪，但真实环境中大量商品为验货宝专属（`FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT` 拦截）。当前 `place_order` 捕获该标志仅返回 `status="yhb_required"`，上层没有可直接调用的验货宝全链路方法，导致「想下单但走不完完整流程」。同时验货宝下单强依赖 `buyerAddressId`，而目前**完全没有地址查询 API**，即便手动拼接参数也无从下手。本变更补齐验货宝三件套：地址查询 → yhb_render（best-effort）→ yhb_create，并在 `TradeApi` 层面提供「普通→验货宝」自动回退的高层封装。

## What Changes

- `core/client.py` 新增 3 个 URL 常量：`address_list_url`（v1.0）、`yhb_order_render_url`（v1.0）、`yhb_order_create_url`（v1.0）。
- `TradeApi` 新增 5 个方法：
  1. `get_address_list()` → 返回 `{success, address_list, default_address}`。
  2. `yhb_order_render(item_id)` → 返回 `{success, yhb_version, buy_quantity, button_disable, raw}`；非账号失效类错误时用默认值（yhb=3, qty=1）兜底（best-effort）。
  3. `yhb_order_create(item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3)` → 创建真实验货宝订单。
  4. `place_order_yhb(item_id, *, buyer_address_id=None)` → yhb 链路组合封装（自动 address → yhb.render best-effort → yhb.create）。
  5. `place_order(item_id)` 扩展：**当普通链路返回 `yhb_required` 时，自动调用 `place_order_yhb` 做二次尝试**，最终返回一个新 `status` 字段（新增 `yhb_success` / `yhb_failed` 两态），保持向后兼容（`yhb_required` 仍然作为回退链路失败后的兜底返回值）。
- `XianyuApis` 门面新增对应 5 个转发方法，并暴露 3 个 URL 常量。
- 文档新增 3 份 `mtop_*` 协议说明，`api_gap_analysis.md` §3.4/3.5/3.6 三项更新为「✅ 已实现」。
- 单测覆盖：地址为空 → 验货宝失败、yhb_render 非致命错误默认值兜底、place_order 扩展普通→验货宝回退；三件套（compileall/unittest/smoke_1_0.py）全绿。

### BREAKING

- `place_order()` 返回值在 `status` 枚举上**新增**两个值 `"yhb_success"` / `"yhb_failed"`（属于非破变，新增枚举值不破坏 `match case _` 的默认分支）。
- `place_order()` 返回的 `status` 历史值 `"yhb_required"` 含义变化：仅在「普通链路标记验货宝 + 验货宝链路因致命错误（如 address 为空或账号失效）无法启动」时才返回。原先所有 yhb 命中都返回的调用方只需加两行 case。

## Capabilities

### New Capabilities

- `logistic-address-list`: 收货地址查询（`mtop.taobao.idle.logistic.address.list.query v1.0`）；`status==1` 优先作为默认地址，地址空时验货宝链路失败。
- `yhb-order-render`: 验货宝下单渲染（`mtop.alibaba.idle.pc.yhb.order.create.render v1.0`）；best-effort 策略：非账号失效类错误 → 默认 `yhb_version=3 / buy_quantity=1` 继续向下。
- `yhb-order-create`: 验货宝订单创建（`mtop.alibaba.idle.pc.yhb.order.create v1.0`）；与普通 create 同等风险，会生成真实未付款订单。
- (隐含在 `trade-order` 上的 Modified Capability) `place_order` 回退行为：普通→验货宝自动二次尝试，最终 `status` 反映最终结果。

### Modified Capabilities

- `trade-order`: 新增「普通链路 yhb_required 自动二次回退验货宝」；`status` 枚举增加 `"yhb_success"` / `"yhb_failed"`；`"yhb_required"` 仅在验货宝二次链路根本未启动时返回。

## Impact

- 受影响文件：
  - `src/pyxianyu/core/client.py`（3 URL）
  - `src/pyxianyu/apis/trade_api.py`（5 方法 + `place_order` 扩展）
  - `src/pyxianyu/xianyu_apis.py`（3 URL 属性 + 5 个门面）
  - `docs/mtop_taobao_idle_logistic_address_list_query.md`（新建）
  - `docs/mtop_alibaba_idle_pc_yhb_order_create_render.md`（新建）
  - `docs/mtop_alibaba_idle_pc_yhb_order_create.md`（新建，顶部红色风险提示）
  - `docs/api_gap_analysis.md` §3.4/3.5/3.6 三项打勾
  - `tests/test_trade_yhb.py`（新建，mock `post_json` 不跑真实网络）
- 依赖：复用现有 `core/exceptions.py::XianyuYhbRequiredError` / `XianyuApiError`，不引入新三方包。
- 风险：yhb_order_create 会生成真实未付款订单；与 trade-order spec 一致，harness 中 place_order 采用两层 opt-in。
