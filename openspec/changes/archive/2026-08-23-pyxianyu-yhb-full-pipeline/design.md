## Context

### 当前状态
- 普通下单链路（render v7.0 + create v5.0）已在 `apis/trade_api.py` 就位，并提供了 `place_order(item_id)` 组合封装，遇到验货宝专属商品时在两处（render / create）任一处抛 `XianyuYhbRequiredError`，由 `place_order` 捕获为返回值 `status="yhb_required"`。
- 但验货宝三件套（地址查询 / yhb_render / yhb_create）目前完全未实现，调用方拿到 `yhb_required` 后无计可施，导致「想下单但走不完完整流程」。
- 现有 `core/client.py`、`xianyu_apis.py` 已具备「URL 常量 + 门面转发 → 实际 Api 类」的稳定模式，可零成本复用。

### 约束
1. `yhb_order_create` 与普通 create 一样，会生成**真实未付款订单**。
2. **不引入新三方依赖**（保持仅 `requests / websockets / loguru / typing_extensions` 的现有依赖集合）。
3. 返回值继续使用 `dict` 结构（与 1.x 其他 API 一致，避免提前跳到 2.0 Result dataclass），并提供 `success`、`raw`、业务字段三段。
4. 不修改既有 `place_order` 的前半段行为；**仅在普通链路返回 yhb_required 时追加自动回退**（最小侵入）。

## Goals / Non-Goals

### Goals
1. **补齐验货宝三件套**（address.list.query → yhb.render → yhb.create），调用方能独立调用每一步，也能走封装好的组合。
2. **自动回退**：`place_order(item_id)` 在普通链路返回 yhb_required 时，自动再次调用 `place_order_yhb(item_id)`，最终返回 `status` 反映「最终结果」而不只是「中间拦截信号」。
3. **Best-effort 兜底**：yhb_render 非账号失效类错误，用默认值（yhb_version=3 / buy_quantity=1）继续向下，提升成功率（对齐 xianyu-auto-reply 的实现）。
4. **零破变最大化**：既有 `place_order` 返回的 status 所有旧枚举值语义尽量不变；新增值放后面。

### Non-Goals
1. **不**实现 `Conversation/listNewestPagination`（WS 会话列表分页，P1 另一个 change 单独做）。
2. **不**同步做 `Result dataclass` 替换裸 dict 改造（留待 2.0）。
3. **不**提供 `XianyuApis` 层的「收货地址新增/编辑/删除」管理（只做只读查询，足够下单用）。

## Decisions

### Decision 1: place_order 回退模式 — 单步两阶段，中间态 yhb_required 保留为兜底

**选择**：
```python
def place_order(self, item_id):
    # 阶段 1：普通
    normal_result = self._place_order_normal(item_id)
    if normal_result["status"] != "yhb_required":
        return normal_result
    # 阶段 2：回退验货宝（若 address 为空或账号失效则不进入）
    try:
        yhb_result = self.place_order_yhb(item_id)
    except Exception as exc:
        return normal_result  # 回退完全失败，保留原始 yhb_required
    match yhb_result["status"]:
        case "success":
            return {**yhb_result, "status": "yhb_success"}
        case other:
            return {**yhb_result, "status": "yhb_failed"}
```

**Rationale**：
- 「yhb_required」语义从「最终状态」变成「中间信号」，但仍保留为最底层兜底（当验货宝完全无法启动时，给调用方最原始的信号）。
- 新增 `yhb_success` / `yhb_failed` 两个枚举值，便于 `match case` 做分支；旧代码的 `case _: pass` 不会崩。

**替代方案（否决）**：把普通 yhb_required 直接合并成 failed。问题：调用方会失去「这个商品必须验货宝但现在不可用」的精细化判断（尤其是自动下单机器人需要区分「商品不能买」vs「商品专属但下单过程失败」）。

### Decision 2: yhb_render best-effort — 只在「账号失效类」时抛错，其余兜底默认值

**选择**：yhb_render 返回 `{success: bool, yhb_version, buy_quantity, button_disable, raw}`；当上游抛 `XianyuApiError` 时：
- 若错误信息命中 `_ACCOUNT_INVALID_MARKERS`（Token 过期/已掉线/请重登）→ 直接抛 `XianyuYhbRequiredError`（上层 `place_order_yhb` 转成 `status="account_invalid"`）；
- 其他错误（如「按钮禁用」/「商品不可买」/「404」）→ 返回默认值 `yhb_version=3, buy_quantity=1`，并把 `button_disable=True` 写入，交给 yhb_create 真正判空。

**Rationale**：xianyu-auto-reply 实测显示 yhb_render 经常在版本号、按钮状态上「非关键失败」，直接放弃会导致整体下单成功率大幅下降；用默认值继续，真正的「商品不可买」会在 yhb_create 阶段被明确拦截（错误信息更完整）。

### Decision 3: address.list.query 默认地址选择 — `status == 1` 优先，否则第一个

**选择**：`get_address_list()` 返回：
```python
{
  "success": True,
  "address_list": [
      {"addressId": int, "status": int, "fullName": str, "mobile": str, "province": str, "city": str, "area": str, "detailAddress": str},
      ...
  ],
  "default_address": dict | None,  # status == 1 的地址，若没有则取第一个，若列表为空则 None
}
```

**替代方案（否决）**：只给 address_list 不给 default_address，调用方自己选。问题：每一处下游都会重写一次「选默认地址」的 5 行判断代码，易出错。

### Decision 4: yhb_create 所有参数都支持「紧凑 JSON 字符串」vs 原始类型 — 统一在内部做序列化

**选择**：
- `yhb_order_create(item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3)` 的：
  - `buyerAddressId`: 直接接收 int 或 str，内部按原样传；
  - `optionalPromotionIdValueList`: 固定值 `"[]"`（空数组 JSON 字符串）；
  - `channel`: 固定值 `"web"`；
  - `channelData`: 由 `yhb_version` 生成 `'{"yhbVersion":<int>}'`，`separators=(",", ":")` 紧凑序列化。

**Rationale**：避免把 JSON 序列化细节泄露给调用方（普通 create 的 params 就是前车之鉴，调用方常传 list 而不是字符串导致 400）。

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| `place_order` status 新增枚举值可能让严格校验调用方误判 | 在 `api_gap_analysis.md` 和 `trade-order` spec 的 scenario 中明确列出所有 status 合法集合；单测覆盖。 |
| yhb_render 默认值兜底可能掩盖「按钮真实禁用」 | 把 `button_disable` 字段写进 `place_order_yhb` 返回的 `yhb_render_result` 子结构，调用方可以事后审计。 |
| 自动回退导致「一次 place_order 产生两个请求」（普通失败 + 验货宝尝试），增加 TPS 压力 | 回退只在 `normal.status == yhb_required` 时触发（不是所有 failed），且普通链路不抛错；与 xianyu-auto-reply 的「客户端先判断 yhb flag 再选链路」一致，属业务刚需。 |
| yhb_create 生成真实未付款订单 ⚠️ | 文档顶部红色风险提示；smoke harness 中 place_order case 继续用两层 opt-in（`XY_TEST_ORDER_ITEM_ID + XY_RUN_ORDER_TESTS=1`）。 |
