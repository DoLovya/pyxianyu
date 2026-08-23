## 1. 基础扩展（core 层）

- [ ] 1.1 `core/client.py` 新增 3 个 URL 常量：`item_polish_url`（/2.0/ 后缀）、`order_render_url`（/7.0/ 后缀）、`order_create_url`（/5.0/ 后缀），并在 `xianyu_apis.py` 中作为 `self.*_url` 暴露。
- [ ] 1.2 `core/exceptions.py` 新增 `XianyuYhbRequiredError`（继承 `XianyuApiError`，含原始 error 与 `item_id` 属性），并在模块 `__init__.py` / `core/__init__.py` 导出。

## 2. ItemApi 擦亮接口

- [ ] 2.1 `apis/item_api.py::ItemApi.polish_item(item_id)` 实现：api=`mtop.taobao.idle.item.polish`，`v="2.0"`，`data={"itemId": ...}`；在调用 `ensure_api_success` 后，如 `ret[0]` 含 `IDLEITEM_POLISH_AGAIN` / `宝贝已经擦亮过了`，额外置返回 `already_polished: true`，不抛异常。
- [ ] 2.2 在 `xianyu_apis.py` 新增 `polish_item(item_id)` 门面方法。

## 3. TradeApi 新建模块（render + create）

- [ ] 3.1 新建 `apis/trade_api.py`，定义 `_YHB_ONLY_MARKERS = ("FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT", "必走验货宝", "ONLY_YHB")`，以及内部 `_is_yhb_only_error(err)` 判定函数。
- [ ] 3.2 `TradeApi.order_render(item_id)`：api=`mtop.taobao.idle.trade.order.render` v=7.0；取 `data.commonData.itemBuyInfo` 返回 `{success, item_buy_info, raw}`；命中验货宝则抛 `XianyuYhbRequiredError`。
- [ ] 3.3 `TradeApi.order_create(item_buy_info)`：api=`mtop.taobao.idle.trade.order.create` v=5.0；`params` 字段传 `json.dumps(item_buy_info, separators=(",", ":"))`；取 `bizOrderIdStr/bizOrderId`、`payUrl`，返回 `{success, biz_order_id, pay_url, raw}`；命中验货宝同样抛 `XianyuYhbRequiredError`。
- [ ] 3.4 `TradeApi.place_order(item_id)`：render → create 串行；两处任一处命中验货宝即返回 `{status: "yhb_required", ...}`；其他异常映射 `status: "failed"` / `"account_invalid"`（如异常信息包含 SESSION_EXPIRED/TOKEN 关键字则 account_invalid）。
- [ ] 3.5 `apis/__init__.py` 导出 `TradeApi`；`xianyu_apis.py` 新增 `self.trade_api` 初始化与 `order_render` / `order_create` / `place_order` 门面。

## 4. 文档

- [ ] 4.1 新建 `docs/mtop_taobao_idle_item_polish.md`：按既有模板，含接口名/版本、取证来源、请求、响应、验证状态。
- [ ] 4.2 新建 `docs/mtop_taobao_idle_trade_order_render.md`：同上，标注 YHB 回退条件。
- [ ] 4.3 新建 `docs/mtop_taobao_idle_trade_order_create.md`：顶部红色风险提示（会生成真实订单），并提供 `item_buy_info` 透传说明。
- [ ] 4.4 更新 `docs/api_gap_analysis.md`：将第一批的 polish / render / create 三项状态由「未实现」标为「已实现」并写入实现位置。

## 5. 验证

- [ ] 5.1 `python -m compileall third_party/pyxianyu/src/pyxianyu` 语法检查通过。
- [ ] 5.2 运行项目 lint（若配置了 ruff/pyright）：读取 `pyproject.toml` 选择正确命令；无配置时至少保证 `import pyxianyu; x = pyxianyu.XianyuApis({...}, device_id="..."); hasattr(x, "polish_item") and hasattr(x, "place_order")` 不报错（需在隔离环境手动冒烟）。
