import time

import requests

from .exceptions import XianyuApiError, XianyuConfigError, XianyuRequestError, XianyuResponseError
from ..utils.xianyu_utils import generate_sign


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)


class XianyuClient:
    def __init__(self, cookies, device_id):
        self.login_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/"
        self.upload_media_url = "https://stream-upload.goofish.com/api/upload.api"
        self.refresh_token_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.loginuser.get/1.0/"
        self.item_detail_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/"
        self.item_search_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/"
        self.user_items_url = "https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/"
        self.user_page_nav_url = "https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/"
        self.item_downshelf_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.downshelf/2.0/"
        self.item_prepublish_check_url = (
            "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.prepublish.check/1.0/"
        )
        self.item_preget_url = "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.preget/1.0/"
        self.item_edit_detail_url = (
            "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.editDetail/1.0/"
        )
        self.item_edit_url = "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.edit/1.0/"
        self.item_publish_url = "https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.publish/1.0/"
        self.item_polish_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.polish/2.0/"
        self.order_render_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.render/7.0/"
        self.order_create_url = "https://h5api.m.goofish.com/h5/mtop.taobao.idle.trade.order.create/5.0/"
        self.reset_login_info_url = "https://passport.goofish.com/newlogin/hasLogin.do"
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.device_id = device_id

    def build_json_headers(self, include_host=False):
        headers = {
            "accept": "application/json",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7,ja;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.goofish.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.goofish.com/",
            "sec-ch-ua": "\"Chromium\";v=\"146\", \"Not-A.Brand\";v=\"24\", \"Google Chrome\";v=\"146\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": DEFAULT_USER_AGENT,
        }
        if include_host:
            headers["Host"] = "h5api.m.goofish.com"
        return headers

    def build_mtop_params(self, api, spm_cnt, spm_pre, log_id, v="1.0"):
        return {
            "jsv": "2.7.2",
            "appKey": "34839810",
            "t": str(int(time.time() * 1000)),
            "sign": "",
            "v": v,
            "type": "originaljson",
            "accountSite": "xianyu",
            "dataType": "json",
            "timeout": "20000",
            "api": api,
            "sessionOption": "AutoLoginOnly",
            "spm_cnt": spm_cnt,
            "spm_pre": spm_pre,
            "log_id": log_id,
        }

    def get_cookie_value(self, cookie_name):
        matching_cookies = [
            cookie for cookie in self.session.cookies if cookie.name == cookie_name and cookie.value
        ]
        if not matching_cookies:
            return ""

        def _cookie_score(cookie):
            domain = cookie.domain or ""
            path = cookie.path or ""
            return (
                2 if "goofish.com" in domain else 1 if domain else 0,
                len(path),
                len(domain),
            )

        return max(matching_cookies, key=_cookie_score).value

    def build_signed_form(self, params, data_val):
        token = self.get_cookie_value("_m_h5_tk").split("_")[0]
        if not token:
            raise XianyuConfigError("缺少 _m_h5_tk cookie，无法生成签名")
        params["sign"] = generate_sign(params["t"], token, data_val)
        return {"data": data_val}

    def post_json(self, url, params, data_val, headers=None, verify=None):
        request_headers = headers or self.build_json_headers()
        data = self.build_signed_form(params, data_val)
        api_name = params.get("api")
        try:
            response = self.session.post(
                url,
                params=params,
                headers=request_headers,
                data=data,
                verify=verify,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise XianyuRequestError(
                f"请求闲鱼接口失败: {api_name or url}",
                api_name=api_name,
                url=url,
            ) from exc

    def parse_json_response(self, response, *, api_name=None):
        try:
            return response.json()
        except ValueError as exc:
            raise XianyuResponseError(
                f"闲鱼接口返回了无法解析的 JSON: {api_name or response.url}",
                api_name=api_name,
                status_code=response.status_code,
            ) from exc

    def ensure_api_success(self, payload, *, api_name=None):
        ret = payload.get("ret")
        if not ret:
            return payload
        first_ret = ret[0]
        if first_ret.startswith("SUCCESS") or "调用成功" in first_ret:
            return payload
        raise XianyuApiError(
            f"闲鱼接口返回失败: {first_ret}",
            api_name=api_name,
            ret=ret,
            payload=payload,
        )

    def clear_conflicting_cookies(self, response):
        response_cookie_names = set(response.cookies.get_dict().keys())
        session_cookie_names = self.session.cookies.get_dict()
        for cookie_name in response_cookie_names:
            if cookie_name not in session_cookie_names:
                continue
            for cookie in list(self.session.cookies):
                if cookie.name == cookie_name and cookie.domain == "" and cookie.path == "/":
                    self.session.cookies.clear(
                        domain=cookie.domain,
                        path=cookie.path,
                        name=cookie.name,
                    )
                    break
