import json

from ..core import XianyuApiError, XianyuYhbRequiredError


_YHB_ONLY_MARKERS = (
    "FAIL_BIZ_ITEM_ONLY_YHB_BUY_APP_LIMIT",
    "必走验货宝",
    "ONLY_YHB",
)

_ACCOUNT_INVALID_MARKERS = (
    "SESSION_EXPIRED",
    "TOKEN_EXPIRED",
    "TOKEN_EXOIRED",
    "已掉线",
    "请重新登录",
)


def _contains_any(text, markers):
    if not text:
        return False
    if isinstance(text, (list, tuple)):
        return any(_contains_any(item, markers) for item in text)
    return any(marker in str(text) for marker in markers)


class TradeApi:
    """
    普通下单链路（不含验货宝）。验货宝链路在后续 change 中实现，调用方捕获
    XianyuYhbRequiredError 后可自行切换。
    """

    def __init__(self, client):
        self.client = client

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------
    def _rethrow_if_yhb(self, exc, *, api_name, item_id):
        combined = " ".join(exc.ret or []) + " " + str(exc)
        if _contains_any(combined, _YHB_ONLY_MARKERS):
            raise XianyuYhbRequiredError(
                str(exc),
                api_name=api_name,
                ret=exc.ret,
                payload=exc.payload,
                item_id=item_id,
            ) from exc
        raise

    # ------------------------------------------------------------------
    # 普通下单链路
    # ------------------------------------------------------------------
    def order_render(self, item_id):
        """
        渲染下单信息，拿到 itemBuyInfo（黑盒列表，原样传给 order_create）。

        返回结构：
        {
            "success": bool,
            "item_buy_info": list[dict] | None,
            "raw": dict,
        }
        """
        api_name = "mtop.taobao.idle.trade.order.render"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.order.0.0",
            spm_pre="a21ybx.order.render.1.f00bar",
            log_id="xianyu_order_render",
            v="7.0",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))
        try:
            response = self.client.post_json(
                self.client.order_render_url,
                params=params,
                data_val=data_val,
            )
            result = self.client.parse_json_response(response, api_name=api_name)
            ensured = self.client.ensure_api_success(result, api_name=api_name)
        except XianyuApiError as exc:
            self._rethrow_if_yhb(exc, api_name=api_name, item_id=item_id)

        data = (ensured.get("data") or {}).get("data") or ensured.get("data") or {}
        common = data.get("commonData") or {}
        item_buy_info = common.get("itemBuyInfo")
        if not item_buy_info:
            raise XianyuApiError(
                "下单渲染缺少 itemBuyInfo（可能商品不可买或账号未配置收货地址）",
                api_name=api_name,
                ret=ensured.get("ret") or [],
                payload=ensured,
            )
        return {
            "success": True,
            "item_buy_info": item_buy_info,
            "raw": ensured,
        }

    def order_create(self, item_buy_info):
        """
        创建订单（拍下），生成真实的未付款订单。

        ⚠️ 风险：会产生真实未付款订单，请在测试账号或明确授权的场景下使用。

        参数：
            item_buy_info: order_render 返回的 item_buy_info 列表，必须原样传入，不要修改。

        返回结构：
        {
            "success": bool,
            "biz_order_id": str | None,
            "pay_url": str | None,
            "raw": dict,
        }
        """
        api_name = "mtop.taobao.idle.trade.order.create"
        if not item_buy_info:
            raise ValueError("item_buy_info 不能为空")
        params_str = json.dumps(item_buy_info, ensure_ascii=False, separators=(",", ":"))
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.order.0.0",
            spm_pre="a21ybx.order.create.1.f00bar",
            log_id="xianyu_order_create",
            v="5.0",
        )
        data_val = json.dumps({"params": params_str}, ensure_ascii=False, separators=(",", ":"))
        try:
            response = self.client.post_json(
                self.client.order_create_url,
                params=params,
                data_val=data_val,
            )
            result = self.client.parse_json_response(response, api_name=api_name)
            ensured = self.client.ensure_api_success(result, api_name=api_name)
        except XianyuApiError as exc:
            self._rethrow_if_yhb(exc, api_name=api_name, item_id=None)

        data = ensured.get("data") or {}
        biz_order_id = data.get("bizOrderIdStr") or data.get("bizOrderId")
        if biz_order_id is not None:
            biz_order_id = str(biz_order_id)
        return {
            "success": True,
            "biz_order_id": biz_order_id,
            "pay_url": data.get("payUrl"),
            "raw": ensured,
        }

    def place_order(self, item_id):
        """
        对单个商品执行普通下单链路（render → create）。

        ⚠️ 风险：会产生真实未付款订单，请在测试账号或明确授权的场景下使用。

        返回结构：
        {
            "status": "success" | "yhb_required" | "failed" | "account_invalid",
            "order_id": str | None,
            "pay_url": str | None,
            "item_buy_info": list | None,
            "error": str,
        }
        """
        item_buy_info = None

        # 1) render
        try:
            render = self.order_render(item_id)
            item_buy_info = render["item_buy_info"]
        except XianyuYhbRequiredError as exc:
            return {
                "status": "yhb_required",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": None,
                "error": str(exc),
            }
        except Exception as exc:
            msg = str(exc)
            status = "account_invalid" if _contains_any(msg, _ACCOUNT_INVALID_MARKERS) else "failed"
            return {
                "status": status,
                "order_id": None,
                "pay_url": None,
                "item_buy_info": None,
                "error": msg,
            }

        # 2) create
        try:
            create = self.order_create(item_buy_info)
            return {
                "status": "success",
                "order_id": create["biz_order_id"],
                "pay_url": create["pay_url"],
                "item_buy_info": item_buy_info,
                "error": "",
            }
        except XianyuYhbRequiredError as exc:
            return {
                "status": "yhb_required",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": item_buy_info,
                "error": str(exc),
            }
        except Exception as exc:
            msg = str(exc)
            status = "account_invalid" if _contains_any(msg, _ACCOUNT_INVALID_MARKERS) else "failed"
            return {
                "status": status,
                "order_id": None,
                "pay_url": None,
                "item_buy_info": item_buy_info,
                "error": msg,
            }
