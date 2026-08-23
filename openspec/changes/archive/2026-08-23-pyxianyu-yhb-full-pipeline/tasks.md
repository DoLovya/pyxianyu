## 1. Core 层 URL 常量与门面 URL 暴露

- [x] 1.1 `core/client.py` 追加 3 个 URL 常量：
  - [x] `self.address_list_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.logistic.address.list.query/1.0/"`
  - [x] `self.yhb_order_render_url = "https://h5api.m.goofish.com/h5/mtop.alibaba.idle.pc.yhb.order.create.render/1.0/"`
  - [x] `self.yhb_order_create_url = "https://h5api.m.goofish.com/h5/mtop.alibaba.idle.pc.yhb.order.create/1.0/"`
- [x] 1.2 `xianyu_apis.py` 顶部追加 3 个 URL 门面属性：`self.address_list_url = self.client.address_list_url` 等 3 行。

## 2. TradeApi 验货宝三件套（独立方法）

- [x] 2.1 新增 `get_address_list()`：
  - [x] api=`mtop.taobao.idle.logistic.address.list.query` v=1.0，data_val=`"{}"`（空对象）
  - [x] 取 `data.data.addressList`；按 status==1 选出默认地址；空 → `default_address=None`
  - [x] 返回 `{success, address_list, default_address, raw}`
- [x] 2.2 新增 `yhb_order_render(item_id)`：
  - [x] api=`mtop.alibaba.idle.pc.yhb.order.create.render` v=1.0，data_val=`json.dumps({"itemId": str(item_id)}, compact)`
  - [x] 正常：`{success=True, yhb_version=int(data.yhbVersion), buy_quantity=int(data.yhbConfirmBuy.buyQuantity or 1), button_disable=bool(data.buttonDisable), raw}`
  - [x] 非账号失效错误捕获 → `{success=False, yhb_version=3, buy_quantity=1, button_disable=True, error=str(exc), raw=exc.payload or {}}`（不抛）
  - [x] 账号失效错误 → 继续抛 `XianyuApiError`
- [x] 2.3 新增 `yhb_order_create(item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3)`：
  - [x] api=`mtop.alibaba.idle.pc.yhb.order.create` v=1.0；data_val 6 字段：itemId/optionalPromotionIdValueList="[]"/buyerAddressId/buyQuantity/channel="web"/channelData=json.dumps({"yhbVersion": <int>}, compact)
  - [x] 取 `bizOrderIdStr/bizOrderId` + payUrl；返回 `{success, biz_order_id, pay_url, raw}`
  - [x] 验货宝专属错误照常抛 `XianyuApiError`（不要在此处吞）

## 3. TradeApi 组合封装 + place_order 扩展回退

- [x] 3.1 新增 `place_order_yhb(item_id, *, buyer_address_id=None)`：
  - [x] 步骤 1：`addr = get_address_list()`；若 buyer_address_id 为空且 addr.default_address 空 → 直接返回 `{status: "no_address", order_id: None, pay_url: None, error: "账号未配置收货地址", address_result: addr}`（不再发 render/create 网络请求）
  - [x] 步骤 2：`render = yhb_order_render(item_id)`，取 render.yhb_version/buy_quantity；账号失效类异常 → 返回 `{status: "account_invalid", error=..., ...}`
  - [x] 步骤 3：`create = yhb_order_create(..., buyer_address_id = buyer_address_id or addr.default_address.addressId)`
  - [x] 最终成功 → `{status: "yhb_success", order_id: create.biz_order_id, pay_url: create.pay_url, address_result: addr, yhb_render_result: render, raw: create.raw, error: ""}`
  - [x] 最终失败（非账号失效）→ `{status: "yhb_failed", error=..., address_result: addr, yhb_render_result: render, ...}`
- [x] 3.2 扩展现有 `place_order(item_id)`：
  - [x] 保留原有 render → create 逻辑（不重写），仅在其返回结果为 `normal["status"] == "yhb_required"` 时追加：
    - [x] 包裹 try/except 调 `place_order_yhb(item_id)`
    - [x] 若 yhb.status == "yhb_success" → `return {status: "yhb_success", order_id: yhb.order_id, pay_url: yhb.pay_url, item_buy_info: normal.get("item_buy_info"), normal_result: normal, yhb_result: yhb, error: ""}`
    - [x] 若 yhb.status == "yhb_failed" → 同上 status="yhb_failed"，error 用 yhb.error
    - [x] 若 yhb.status == "no_address" / 任何未预料异常 → 退回原始 normal（保留 `status="yhb_required"`），便于调用方识别「二次回退根本没跑」
    - [x] 若 yhb.status == "account_invalid" → `status="account_invalid"`（优先级高；覆盖 normal）
  - [x] 其余 status 原封不动返回

## 4. XianyuApis 门面暴露

- [x] 4.1 在 `xianyu_apis.py` 追加 5 个方法：`get_address_list / yhb_order_render / yhb_order_create / place_order_yhb` + 保持现有 `place_order`（行为已在 TradeApi 层扩展，门面只转发）。
  - [x] 每个方法 = `return self.trade_api.<method>(...)`，参数原样透传

## 5. 文档

- [x] 5.1 新建 `docs/mtop_taobao_idle_logistic_address_list_query.md`（§3.4 对应）：6 节（目的/取证/请求/响应/验证/用途），脱敏占位符。
- [x] 5.2 新建 `docs/mtop_alibaba_idle_pc_yhb_order_create_render.md`（§3.5 对应）：标注 best-effort 与默认值兜底。
- [x] 5.3 新建 `docs/mtop_alibaba_idle_pc_yhb_order_create.md`（§3.6 对应）：顶部**红色风险提示**（生成真实未付款订单）+ `channelData` 紧凑 JSON 字段说明。
- [x] 5.4 `docs/api_gap_analysis.md` §3.4/§3.5/§3.6 三项：
  - [x] 把「建议实现位置」字段右边插入「实现状态」 ✅ 已实现（2026-08-23）+ 链接对应 5.1/5.2/5.3 三个文档。
  - [x] 「验证状态」⏳ 待验证 → 全部改为 ✅ 已验证（单测三件套 + mock 验证）

## 6. 单测 + 三件套验证

- [x] 6.1 新建 `tests/test_trade_yhb.py`（unittest，mock `self.client.post_json`，不发起真实网络）：
  - [x] `GetAddressListTest`：地址 status==1 默认；空列表 default=None；Token 过期抛异常（3 条）
  - [x] `YhbRenderTest`：正常解析 yhb_version=4/qty=1；非账号类错误 → 默认值 3/1/button_disable=True；账号失效抛异常（3 条）
  - [x] `YhbCreateTest`：6 字段 data_val 断言；成功返回 biz_order_id；业务错误抛 XianyuApiError（3 条）
  - [x] `PlaceOrderYhbTest`：地址空 → status="no_address"（不发 render/create）；地址有 → render 默认值兜底 → create 成功 → status="yhb_success"；create 业务错误 → status="yhb_failed"（3 条）
  - [x] `PlaceOrderFallbackTest`：普通 status="yhb_required" + yhb_success → 最终 status="yhb_success"；yhb_failed → 最终 yhb_failed；yhb_result.status == no_address → 保留原 yhb_required（4 条）
- [x] 6.2 三件套验证：
  - [x] `python -m compileall -q src scripts tests` → 0 错误
  - [x] `PYTHONPATH=src python -m unittest discover -s tests -v` → 新增 16 条 + 原有 17 条 = 33 条 100% OK
  - [x] `PYTHONPATH=src python scripts/smoke_1_0.py` → 退出码 0，place_order case shape 校验新增 `yhb_success/yhb_failed` 合法值（避免 status 新枚举值误判 FAIL）

## 7. OpenSpec 同步 + 归档

- [x] 7.1 sync-specs：4 个 capabilities（3 新建 + 1 修改 trade-order）同步到 `openspec/specs/`（3 新建目录 + trade-order spec 追加 MODIFIED scenario）。
- [x] 7.2 tasks.md 全勾后 `archive pyxianyu-yhb-full-pipeline` 到 `archive/2026-08-23-pyxianyu-yhb-full-pipeline/`。
