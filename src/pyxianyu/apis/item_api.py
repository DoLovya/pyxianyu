import json
import uuid

from ..core import XianyuApiError


_POLISH_DUPLICATE_MARKERS = ("IDLEITEM_POLISH_AGAIN", "宝贝已经擦亮过了", "一天只能擦亮一次")


class ItemApi:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def _contains_any(text, markers):
        if not text:
            return False
        return any(marker in text for marker in markers)

    def polish_item(self, item_id):
        """
        擦亮单个商品，每日多次调用幂等（视为成功）。

        返回结构：
        {
            "success": bool,
            "already_polished": bool,  # True 表示今日已擦亮过（幂等成功）
            "api": "mtop.taobao.idle.item.polish",
            "itemId": str,
            "ret": list,
            "data": dict,
        }
        """
        api_name = "mtop.taobao.idle.item.polish"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.item.0.0",
            spm_pre="a21ybx.personal.feeds.1.42f86ac21eZ9zd",
            log_id="42f86ac21eZ9zd",
            v="2.0",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))

        try:
            response = self.client.post_json(
                self.client.item_polish_url,
                params=params,
                data_val=data_val,
            )
            result = self.client.parse_json_response(response, api_name=api_name)
            ensured = self.client.ensure_api_success(result, api_name=api_name)
            already_polished = False
            ret_list = ensured.get("ret") or []
            for entry in ret_list:
                if self._contains_any(entry, _POLISH_DUPLICATE_MARKERS):
                    already_polished = True
                    break
            return {
                "success": True,
                "already_polished": already_polished,
                "api": api_name,
                "itemId": str(item_id),
                "ret": ret_list,
                "data": ensured.get("data") or {},
            }
        except XianyuApiError as exc:
            ret_list = exc.ret or []
            first_ret = ret_list[0] if ret_list else str(exc)
            if self._contains_any(first_ret, _POLISH_DUPLICATE_MARKERS):
                return {
                    "success": True,
                    "already_polished": True,
                    "api": api_name,
                    "itemId": str(item_id),
                    "ret": ret_list,
                    "data": (exc.payload or {}).get("data") or {},
                }
            raise

    def get_item_info(self, item_id):
        api_name = "mtop.taobao.idle.pc.detail"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.im.0.0",
            spm_pre="a21ybx.item.want.1.12523da6waCtUp",
            log_id="12523da6waCtUp",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_detail_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def get_user_items(
        self,
        user_id,
        page_number=1,
        page_size=20,
        need_group_info=False,
        group_name=None,
        group_id=None,
        default_group=None,
        group_sort_id=None,
        filter_panel_group_id=None,
        next_page_model=None,
        next_page_num=None,
    ):
        api_name = "mtop.idle.web.xyh.item.list"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.personal.0.0",
            spm_pre="a21ybx.personal.0.0",
            log_id="xianyu_my_items",
        )
        data_payload = {
            "pageNumber": page_number,
            "userId": str(user_id),
            "pageSize": page_size,
        }
        if need_group_info:
            data_payload["needGroupInfo"] = True
        if group_name is not None:
            data_payload["groupName"] = group_name
        if group_id is not None:
            data_payload["groupId"] = group_id
        if default_group is not None:
            data_payload["defaultGroup"] = default_group
        if group_sort_id is not None:
            data_payload["groupSortId"] = group_sort_id
        if filter_panel_group_id is not None:
            data_payload["filterPanelGroupId"] = filter_panel_group_id
        if next_page_model is not None:
            data_payload["nextPageModel"] = next_page_model
        if next_page_num is not None:
            data_payload["nextPageNum"] = next_page_num

        data_val = json.dumps(data_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.user_items_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def get_all_user_items(self, user_id, page_size=20):
        first_page = self.get_user_items(
            user_id=user_id,
            page_number=1,
            page_size=page_size,
            need_group_info=True,
        )
        first_data = first_page.get("data", {})
        card_list = list(first_data.get("cardList") or [])
        item_group_list = first_data.get("itemGroupList") or []
        page_summaries = [
            {
                "pageNumber": 1,
                "count": len(first_data.get("cardList") or []),
            }
        ]

        selected_group = item_group_list[0] if item_group_list else {}
        next_page = first_data.get("nextPage", False)
        next_page_num = first_data.get("nextPageNum")
        next_page_model = first_data.get("nextPageModel")
        current_page = 2

        while next_page:
            page_result = self.get_user_items(
                user_id=user_id,
                page_number=current_page,
                page_size=page_size,
                group_name=selected_group.get("groupName"),
                group_id=selected_group.get("groupId"),
                default_group=selected_group.get("defaultGroup"),
                next_page_model=next_page_model,
                next_page_num=next_page_num,
            )
            page_data = page_result.get("data", {})
            page_cards = page_data.get("cardList") or []
            card_list.extend(page_cards)
            page_summaries.append(
                {
                    "pageNumber": current_page,
                    "count": len(page_cards),
                }
            )
            next_page = page_data.get("nextPage", False)
            next_page_num = page_data.get("nextPageNum")
            next_page_model = page_data.get("nextPageModel")
            current_page += 1

        return {
            "api": "mtop.idle.web.xyh.item.list",
            "userId": str(user_id),
            "pageSize": page_size,
            "pageCount": len(page_summaries),
            "pages": page_summaries,
            "itemGroupList": item_group_list,
            "cardList": card_list,
            "topItem": first_data.get("topItem"),
            "totalCount": first_data.get("totalCount", len(card_list)),
        }

    def downshelf_item(self, item_id):
        api_name = "mtop.taobao.idle.item.downshelf"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.item.0.0",
            spm_pre="a21ybx.item.0.0",
            log_id="xianyu_item_downshelf",
            v="2.0",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_downshelf_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def prepublish_check(self, item_id=None):
        api_name = "mtop.idle.pc.idleitem.prepublish.check"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.publish.0.0",
            spm_pre="a21ybx.publish.0.0",
            log_id="xianyu_item_prepublish_check",
        )
        data_payload = {}
        if item_id is not None and str(item_id).strip():
            data_payload["itemId"] = str(item_id).strip()
        data_val = json.dumps(data_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_prepublish_check_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def preget(self, item_id=None, source_id=None, publish_scene=None, bizcode=None):
        api_name = "mtop.idle.pc.idleitem.preget"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.publish.0.0",
            spm_pre="a21ybx.publish.0.0",
            log_id="xianyu_item_preget",
        )
        data_payload = {}
        if item_id is not None and str(item_id).strip():
            data_payload["itemId"] = str(item_id).strip()
        if source_id is not None and str(source_id).strip():
            data_payload["sourceId"] = str(source_id).strip()
        if publish_scene is not None and str(publish_scene).strip():
            data_payload["publishScene"] = str(publish_scene).strip()
        if bizcode is not None and str(bizcode).strip():
            data_payload["bizcode"] = str(bizcode).strip()
        data_val = json.dumps(data_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_preget_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def get_item_edit_detail(self, item_id):
        api_name = "mtop.idle.pc.idleitem.editDetail"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.publish.0.0",
            spm_pre="a21ybx.publish.0.0",
            log_id="xianyu_item_edit_detail",
        )
        data_val = json.dumps({"itemId": str(item_id)}, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_edit_detail_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def edit_item(self, payload):
        api_name = "mtop.idle.pc.idleitem.edit"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.publish.0.0",
            spm_pre="a21ybx.publish.0.0",
            log_id="xianyu_item_edit",
        )
        request_payload = dict(payload or {})
        request_payload.setdefault("uniqueCode", uuid.uuid4().hex)
        request_payload.setdefault("bizcode", "pcMainPublish")
        request_payload.setdefault("publishScene", "pcMainPublish")
        if "sourceId" not in request_payload:
            request_payload["sourceId"] = request_payload.get("itemId", "")
        data_val = json.dumps(request_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_edit_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def publish_item(self, payload):
        api_name = "mtop.idle.pc.idleitem.publish"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.publish.0.0",
            spm_pre="a21ybx.publish.0.0",
            log_id="xianyu_item_publish",
        )
        request_payload = dict(payload or {})
        request_payload.setdefault("uniqueCode", uuid.uuid4().hex)
        request_payload.setdefault("bizcode", "pcMainPublish")
        request_payload.setdefault("publishScene", "pcMainPublish")
        request_payload.setdefault("sourceId", "publish")
        data_val = json.dumps(request_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_publish_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

    def build_reshelf_payload(self, edit_detail_result, *, item_id=None, source_id=None):
        detail_data = edit_detail_result.get("data", edit_detail_result or {})
        payload = {}

        scalar_keys = (
            "attribute_biz_line",
            "bizcode",
            "bucketId",
            "canBargain",
            "defaultPrice",
            "errorTipsMsg",
            "freebies",
            "itemStatus",
            "itemTypeStr",
            "quantity",
            "scene",
            "simpleItem",
            "supportBargainPrice",
            "topics",
        )
        object_keys = (
            "asyncSecurityInfo",
            "baseParams",
            "itemAddrDTO",
            "itemCatDTO",
            "itemGroupDTO",
            "itemPostFeeDTO",
            "itemPriceDTO",
            "itemTextDTO",
            "itemTopicParams",
            "yhbItemInfoDTO",
        )
        list_keys = (
            "imageInfoDOList",
            "itemLabelExtList",
            "itemProperties",
            "itemSkuList",
            "userRightsProtocols",
        )

        for key in scalar_keys:
            if key in detail_data:
                payload[key] = detail_data[key]
        for key in object_keys:
            if key in detail_data:
                payload[key] = detail_data[key]
        for key in list_keys:
            if key in detail_data:
                payload[key] = detail_data[key]

        resolved_item_id = str(item_id or detail_data.get("itemId") or detail_data.get("id") or "").strip()
        if resolved_item_id:
            payload["itemId"] = resolved_item_id

        if source_id is not None and str(source_id).strip():
            payload["sourceId"] = str(source_id).strip()
        elif detail_data.get("sourceId"):
            payload["sourceId"] = str(detail_data["sourceId"]).strip()
        elif resolved_item_id:
            payload["sourceId"] = resolved_item_id
        else:
            payload["sourceId"] = "editDetail"

        payload["uniqueCode"] = uuid.uuid4().hex
        payload["bizcode"] = str(payload.get("bizcode") or "pcMainPublish")
        payload["publishScene"] = str(detail_data.get("publishScene") or "pcMainPublish")
        payload.setdefault("quantity", "1")
        payload.setdefault("scene", "")
        payload.setdefault("itemTypeStr", "b")
        payload.setdefault("itemGroupDTO", {"groupId": ""})
        payload.setdefault("topics", [])
        payload.setdefault("asyncSecurityInfo", {"securityStrategyHitResult": {"FORBIDDEN": [], "WARN": []}})

        item_text = dict(payload.get("itemTextDTO") or {})
        if item_text.get("desc") and not item_text.get("title"):
            item_text["title"] = str(item_text["desc"]).strip().splitlines()[0][:60]
        if item_text:
            payload["itemTextDTO"] = item_text

        post_fee = dict(payload.get("itemPostFeeDTO") or {})
        for key in ("canFreeShipping", "supportFreight", "onlyTakeSelf"):
            if key in post_fee:
                post_fee[key] = self._normalize_bool(post_fee[key])
        if post_fee:
            payload["itemPostFeeDTO"] = post_fee

        protocols = []
        for protocol in payload.get("userRightsProtocols") or []:
            if not isinstance(protocol, dict):
                continue
            normalized_protocol = dict(protocol)
            if "enable" in normalized_protocol:
                normalized_protocol["enable"] = self._normalize_bool(normalized_protocol["enable"])
            protocols.append(normalized_protocol)
        if protocols or "userRightsProtocols" in payload:
            payload["userRightsProtocols"] = protocols

        return payload

    def reshelf_item(self, item_id, source_id=None):
        edit_detail_result = self.get_item_edit_detail(item_id)
        payload = self.build_reshelf_payload(
            edit_detail_result,
            item_id=item_id,
            source_id=source_id,
        )
        edit_result = self.edit_item(payload)
        return {
            "itemId": str(item_id),
            "editDetail": edit_detail_result,
            "editPayload": payload,
            "editResult": edit_result,
        }

    @staticmethod
    def _normalize_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == "true"
        return bool(value)

