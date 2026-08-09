import unittest
from unittest.mock import Mock

from pyxianyu.apis.auth_api import AuthApi
from pyxianyu.core.exceptions import XianyuApiError
from pyxianyu.goofish_apis import XianyuApis


class ReleaseReadinessTest(unittest.TestCase):
    def test_xianyu_apis_exposes_user_page_nav(self):
        api = XianyuApis({"_m_h5_tk": "token_value_123"}, "device-id")
        api.user_api.get_user_page_nav = Mock(return_value={"data": {"userId": "123"}})

        result = api.get_user_page_nav()

        api.user_api.get_user_page_nav.assert_called_once_with()
        self.assertEqual(result["data"]["userId"], "123")

    def test_get_token_retries_then_succeeds(self):
        client = _FakeAuthClient(
            [
                {"ret": ["FAIL_SYS_TOKEN_EXPIRED::令牌过期"]},
                {"ret": ["SUCCESS::调用成功"], "data": {"accessToken": "token-123"}},
            ]
        )
        api = AuthApi(client)

        result = api.get_token(max_attempts=2)

        self.assertEqual(client.post_json.call_count, 2)
        self.assertEqual(result["data"]["accessToken"], "token-123")

    def test_get_token_raises_after_retry_limit(self):
        client = _FakeAuthClient(
            [
                {"ret": ["FAIL_SYS_TOKEN_EXPIRED::令牌过期"]},
                {"ret": ["FAIL_SYS_TOKEN_EXPIRED::令牌过期"]},
            ]
        )
        api = AuthApi(client)

        with self.assertRaises(XianyuApiError) as ctx:
            api.get_token(max_attempts=2)

        self.assertEqual(client.post_json.call_count, 2)
        self.assertIn("达到重试上限 2 次后仍提示令牌过期", str(ctx.exception))


class _FakeAuthClient:
    def __init__(self, responses):
        self.device_id = "device-id"
        self.login_url = "https://example.com/login"
        self._responses = list(responses)
        self.post_json = Mock(return_value=object())

    def build_mtop_params(self, **kwargs):
        return kwargs

    def build_json_headers(self, include_host=False):
        return {"Host": "h5api.m.goofish.com"} if include_host else {}

    def clear_conflicting_cookies(self, response):
        return None

    def parse_json_response(self, response, *, api_name=None):
        return self._responses.pop(0)

    def ensure_api_success(self, payload, *, api_name=None):
        return payload


if __name__ == "__main__":
    unittest.main()
