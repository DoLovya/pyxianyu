## Why

根据 `docs/api_gap_analysis.md` 的第一批高优先级清单，当前 pyxianyu 缺失三类高价值 HTTP 接口：

1. **商品擦亮（polish）**：自动化日常运营的高频需求，每日可执行一次，与 downshelf/reshelf 同属于商品管理域。
2. **普通下单渲染（order.render）**：下单链路的前置校验，获取 `itemBuyInfo` 黑盒参数。
3. **普通下单创建（order.create）**：在渲染成功的基础上，生成真实的未付款订单。

当前项目已具备 sign 签名、`build_mtop_params`/`post_json`/`ensure_api_success` 等底层公共能力，新增接口仅需按现有 `ItemApi` 的调用模板补齐，实现成本低但收益显著（可覆盖自动擦亮、监控下单场景）。

## What Changes

- `apis/item_api.py` 新增 `polish_item(item_id)` 方法，并扩展幂等判定：`IDLEITEM_POLISH_AGAIN` / `宝贝已经擦亮过了` 视为成功。
- 新增 `apis/trade_api.py` 模块，包含：
  - `order_render(item_id)`：返回 `item_buy_info` 列表（原样透传给 create 不做解析）。
  - `order_create(item_buy_info)`：传入 render 返回值，返回 `biz_order_id` / `pay_url`。
  - `place_order(item_id)`：组合方法，render → create 自动串行执行，并在两处均检测 `FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT`/`必走验货宝`/`ONLY_YHB` 标志，命中时抛出 `XianyuYhbRequiredError`（验货宝需后续变更单独引入）。
- `apis/__init__.py` 导出 `TradeApi`。
- `xianyu_apis.py` 新增 `item_polish` / `order_render` / `order_create` / `place_order` 门面方法，并在 `__init__` 中初始化 `trade_api`。
- `core/client.py` 新增 `item_polish_url`、`order_render_url`、`order_create_url` 三个 URL 常量，并由门面层透传。
- `core/exceptions.py` 新增 `XianyuPolishDuplicateError`（可选，便于调用方区分幂等成功）与 `XianyuYhbRequiredError`（验货宝回退信号）。
- `docs/` 下新增三份接口文档：`mtop_taobao_idle_item_polish.md`、`mtop_taobao_idle_trade_order_render.md`、`mtop_taobao_idle_trade_order_create.md`。

## Capabilities

### New Capabilities

- `item-polish`：单个商品擦亮；每日多次调用幂等（POLISH_AGAIN/宝贝已擦亮过 → success=true，不抛异常）。
- `trade-order-render`：渲染商品下单页，获取必须透传的 `itemBuyInfo`；检测「必走验货宝」错误并向上抛出特定异常。
- `trade-order-create`：根据 render 返回的 `itemBuyInfo` 生成真实订单（拍下，未付款），返回订单号与付款链接。

### Modified Capabilities

无

## Impact

- 代码：`third_party/pyxianyu/src/pyxianyu/core/client.py`、`core/exceptions.py`、`apis/item_api.py`、`apis/trade_api.py`（新建）、`apis/__init__.py`、`xianyu_apis.py`、`docs/*.md`（3 份）
- 行为：`order_create` 为**写操作且产生真实业务单据**，在调用方需接受明确风险提示；不影响现有任何读/写接口。
