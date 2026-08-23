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
    普通下单链路 + 验货宝链路。普通链路遇到验货宝专属商品会返回 yhb_required，
    此时 place_order 会自动二次调用 place_order_yhb 回退，最终返回 yhb_success / yhb_failed。
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

    def _is_account_invalid(self, exc_or_msg):
        if isinstance(exc_or_msg, BaseException):
            text = str(exc_or_msg)
            ret = getattr(exc_or_msg, "ret", None)
            if ret:
                text += " " + " ".join(ret)
        else:
            text = str(exc_or_msg)
        return _contains_any(text, _ACCOUNT_INVALID_MARKERS)

    # ------------------------------------------------------------------
    # 收货地址
    # ------------------------------------------------------------------
    def get_address_list(self):
        """
        查询收货地址列表（验货宝下单必填 buyerAddressId）。

        返回：
        {
            "success": bool,
            "address_list": list[dict],
            "default_address": dict | None,  # status == 1，没有则取第一个
            "raw": dict,
        }
        """
        api_name = "mtop.taobao.idle.logistic.address.list.query"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.order.0.0",
            spm_pre="a21ybx.order.address.1.f00bar",
            log_id="xianyu_address_list",
            v="1.0",
        )
        data_val = "{}"
        response = self.client.post_json(
            self.client.address_list_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        ensured = self.client.ensure_api_success(result, api_name=api_name)

        inner = (ensured.get("data") or {}).get("data") or ensured.get("data") or {}
        address_list = inner.get("addressList") or []
        default_address = None
        if address_list:
            for addr in address_list:
                if int(addr.get("status") or 0) == 1:
                    default_address = addr
                    break
            if default_address is None:
                default_address = address_list[0]
        return {
            "success": True,
            "address_list": address_list,
            "default_address": default_address,
            "raw": ensured,
        }

    # ------------------------------------------------------------------
    # 验货宝三件套
    # ------------------------------------------------------------------
    def yhb_order_render(self, item_id):
        """
        验货宝下单渲染（best-effort：非账号失效类错误不抛，用默认值兜底）。

        返回：
        {
            "success": bool,
            "yhb_version": int,
            "buy_quantity": int,
            "button_disable": bool,
            "raw": dict,
            "error": str,
            "fallback_used": bool,
        }
        """
        api_name = "mtop.alibaba.idle.pc.yhb.order.create.render"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.order.0.0",
            spm_pre="a21ybx.order.yhbrender.1.f00bar",
            log_id="xianyu_yhb_render",
            v="1.0",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))
        try:
            response = self.client.post_json(
                self.client.yhb_order_render_url,
                params=params,
                data_val=data_val,
            )
            result = self.client.parse_json_response(response, api_name=api_name)
            ensured = self.client.ensure_api_success(result, api_name=api_name)
        except XianyuApiError as exc:
            # 账号失效类继续抛（place_order_yhb 会转 account_invalid）
            if self._is_account_invalid(exc):
                raise
            # 其余非致命错误 → 默认值
            return {
                "success": False,
                "yhb_version": 3,
                "buy_quantity": 1,
                "button_disable": True,
                "raw": exc.payload or {},
                "error": str(exc),
                "fallback_used": True,
            }

        data = (ensured.get("data") or {}).get("data") or ensured.get("data") or {}
        try:
            yhb_version = int(data.get("yhbVersion") or 3)
        except (TypeError, ValueError):
            yhb_version = 3
        confirm = data.get("yhbConfirmBuy") or {}
        try:
            buy_quantity = int(confirm.get("buyQuantity") or 1)
        except (TypeError, ValueError):
            buy_quantity = 1
        button_disable = bool(data.get("buttonDisable"))
        return {
            "success": True,
            "yhb_version": yhb_version,
            "buy_quantity": buy_quantity,
            "button_disable": button_disable,
            "raw": ensured,
            "error": "",
            "fallback_used": False,
        }

    def yhb_order_create(self, item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3):
        """
        创建验货宝订单。⚠️ 生成真实未付款订单。

        返回：
        {
            "success": bool,
            "biz_order_id": str | None,
            "pay_url": str | None,
            "raw": dict,
        }
        """
        api_name = "mtop.alibaba.idle.pc.yhb.order.create"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.order.0.0",
            spm_pre="a21ybx.order.yhbcreate.1.f00bar",
            log_id="xianyu_yhb_create",
            v="1.0",
        )
        channel_data = json.dumps(
            {"yhbVersion": int(yhb_version)},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        payload = {
            "itemId": str(item_id),
            "optionalPromotionIdValueList": "[]",
            "buyerAddressId": buyer_address_id,
            "buyQuantity": int(buy_quantity),
            "channel": "web",
            "channelData": channel_data,
        }
        data_val = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.yhb_order_create_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        ensured = self.client.ensure_api_success(result, api_name=api_name)

        data = (ensured.get("data") or {}).get("data") or ensured.get("data") or {}
        biz_order_id = data.get("bizOrderIdStr") or data.get("bizOrderId")
        if biz_order_id is not None:
            biz_order_id = str(biz_order_id)
        return {
            "success": True,
            "biz_order_id": biz_order_id,
            "pay_url": data.get("payUrl"),
            "raw": ensured,
        }

    def place_order_yhb(self, item_id, *, buyer_address_id=None):
        """
        验货宝组合封装：自动 address → yhb_render(best-effort) → yhb_create。

        ⚠️ 风险：会产生真实未付款订单，请在测试账号或明确授权的场景下使用。

        返回结构：
        {
            "status": "yhb_success" | "yhb_failed" | "no_address" | "account_invalid" | "failed",
            "order_id": str | None,
            "pay_url": str | None,
            "error": str,
            "address_result": dict | None,
            "yhb_render_result": dict | None,
            "raw": dict | None,
        }
        """
        address_result = None
        yhb_render_result = None
        try:
            # 1) address
            try:
                address_result = self.get_address_list()
            except XianyuApiError as exc:
                if self._is_account_invalid(exc):
                    return {
                        "status": "account_invalid",
                        "order_id": None,
                        "pay_url": None,
                        "error": str(exc),
                        "address_result": None,
                        "yhb_render_result": None,
                        "raw": exc.payload or {},
                    }
                raise

            chosen_address_id = buyer_address_id
            if chosen_address_id is None:
                if not address_result.get("default_address"):
                    return {
                        "status": "no_address",
                        "order_id": None,
                        "pay_url": None,
                        "error": "账号未配置收货地址",
                        "address_result": address_result,
                        "yhb_render_result": None,
                        "raw": address_result["raw"],
                    }
                chosen_address_id = address_result["default_address"]["addressId"]

            # 2) render (best-effort)
            try:
                yhb_render_result = self.yhb_order_render(item_id)
            except XianyuApiError as exc:
                if self._is_account_invalid(exc):
                    return {
                        "status": "account_invalid",
                        "order_id": None,
                        "pay_url": None,
                        "error": str(exc),
                        "address_result": address_result,
                        "yhb_render_result": None,
                        "raw": exc.payload or {},
                    }
                # yhb_order_render 内部已经对非账号失效做了 fallback；这里若抛是其他不可预期异常
                raise
            yhb_version = yhb_render_result["yhb_version"]
            buy_quantity = yhb_render_result["buy_quantity"]

            # 3) create
            try:
                create_result = self.yhb_order_create(
                    item_id,
                    chosen_address_id,
                    buy_quantity=buy_quantity,
                    yhb_version=yhb_version,
                )
            except XianyuApiError as exc:
                if self._is_account_invalid(exc):
                    return {
                        "status": "account_invalid",
                        "order_id": None,
                        "pay_url": None,
                        "error": str(exc),
                        "address_result": address_result,
                        "yhb_render_result": yhb_render_result,
                        "raw": exc.payload or {},
                    }
                return {
                    "status": "yhb_failed",
                    "order_id": None,
                    "pay_url": None,
                    "error": str(exc),
                    "address_result": address_result,
                    "yhb_render_result": yhb_render_result,
                    "raw": exc.payload or {},
                }

            return {
                "status": "yhb_success",
                "order_id": create_result["biz_order_id"],
                "pay_url": create_result["pay_url"],
                "error": "",
                "address_result": address_result,
                "yhb_render_result": yhb_render_result,
                "raw": create_result["raw"],
            }
        except Exception as exc:
            msg = str(exc)
            if self._is_account_invalid(exc):
                status = "account_invalid"
            else:
                status = "yhb_failed"
            return {
                "status": status,
                "order_id": None,
                "pay_url": None,
                "error": msg,
                "address_result": address_result,
                "yhb_render_result": yhb_render_result,
                "raw": getattr(exc, "payload", None) or {},
            }

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
        先跑普通下单链路（render → create），命中验货宝后自动二次回退到验货宝链路。

        ⚠️ 风险：会产生真实未付款订单，请在测试账号或明确授权的场景下使用。

        返回结构：
        {
            "status": "success"
                    | "yhb_required"
                    | "failed"
                    | "account_invalid"
                    | "yhb_success"
                    | "yhb_failed",
            "order_id": str | None,
            "pay_url": str | None,
            "item_buy_info": list | None,
            "error": str,
            "normal_result": dict | None,
            "yhb_result": dict | None,
        }
        """
        item_buy_info = None
        normal_result = None

        # 1) render
        try:
            render = self.order_render(item_id)
            item_buy_info = render["item_buy_info"]
        except XianyuYhbRequiredError as exc:
            normal_result = {
                "status": "yhb_required",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": None,
                "error": str(exc),
            }
        except Exception as exc:
            msg = str(exc)
            status = "account_invalid" if _contains_any(msg, _ACCOUNT_INVALID_MARKERS) else "failed"
            normal_result = {
                "status": status,
                "order_id": None,
                "pay_url": None,
                "item_buy_info": None,
                "error": msg,
            }
            normal_result.setdefault("normal_result", None)
            normal_result.setdefault("yhb_result", None)
            return normal_result

        # 2) create
        if normal_result is None:
            try:
                create = self.order_create(item_buy_info)
                normal_result = {
                    "status": "success",
                    "order_id": create["biz_order_id"],
                    "pay_url": create["pay_url"],
                    "item_buy_info": item_buy_info,
                    "error": "",
                }
            except XianyuYhbRequiredError as exc:
                normal_result = {
                    "status": "yhb_required",
                    "order_id": None,
                    "pay_url": None,
                    "item_buy_info": item_buy_info,
                    "error": str(exc),
                }
            except Exception as exc:
                msg = str(exc)
                status = "account_invalid" if _contains_any(msg, _ACCOUNT_INVALID_MARKERS) else "failed"
                normal_result = {
                    "status": status,
                    "order_id": None,
                    "pay_url": None,
                    "item_buy_info": item_buy_info,
                    "error": msg,
                }

        # 3) 回退验货宝（仅在普通阶段返回 yhb_required 时启动）
        if normal_result.get("status") != "yhb_required":
            normal_result.setdefault("normal_result", normal_result)
            normal_result.setdefault("yhb_result", None)
            return normal_result

        try:
            yhb_result = self.place_order_yhb(item_id)
        except Exception as exc:
            normal_result.setdefault("normal_result", normal_result)
            normal_result.setdefault("yhb_result", None)
            return normal_result

        yhb_status = yhb_result.get("status")
        if yhb_status == "yhb_success":
            return {
                "status": "yhb_success",
                "order_id": yhb_result.get("order_id"),
                "pay_url": yhb_result.get("pay_url"),
                "item_buy_info": normal_result.get("item_buy_info"),
                "error": "",
                "normal_result": normal_result,
                "yhb_result": yhb_result,
            }
        if yhb_status == "yhb_failed":
            return {
                "status": "yhb_failed",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": normal_result.get("item_buy_info"),
                "error": yhb_result.get("error") or "",
                "normal_result": normal_result,
                "yhb_result": yhb_result,
            }
        if yhb_status == "no_address":
            err = normal_result.get("error") or ""
            if yhb_result.get("error"):
                err = "yhb fallback skipped: {}; normal reason: {}".format(yhb_result["error"], err)
            return {
                "status": "yhb_required",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": normal_result.get("item_buy_info"),
                "error": err,
                "normal_result": normal_result,
                "yhb_result": yhb_result,
            }
        if yhb_status == "account_invalid":
            return {
                "status": "account_invalid",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": normal_result.get("item_buy_info"),
                "error": yhb_result.get("error") or normal_result.get("error") or "",
                "normal_result": normal_result,
                "yhb_result": yhb_result,
            }
        return {
            "status": "yhb_failed",
            "order_id": None,
            "pay_url": None,
            "item_buy_info": normal_result.get("item_buy_info"),
            "error": yhb_result.get("error") or "unexpected yhb status: {}".format(yhb_status),
            "normal_result": normal_result,
            "yhb_result": yhb_result,
        }
