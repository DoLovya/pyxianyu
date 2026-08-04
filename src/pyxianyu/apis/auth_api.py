class AuthApi:
    def __init__(self, client):
        self.client = client

    def get_token(self):
        api_name = "mtop.taobao.idlemessage.pc.login.token"
        while True:
            params = self.client.build_mtop_params(
                api=api_name,
                spm_cnt="a21ybx.im.0.0",
                spm_pre="a21ybx.item.want.1.14ad3da6ALVq3n",
                log_id="14ad3da6ALVq3n",
            )
            data_val = (
                '{"appKey":"444e9908a51d1cb236a27862abc769c9",'
                f'"deviceId":"{self.client.device_id}"'
                "}"
            )
            response = self.client.post_json(
                self.client.login_url,
                params=params,
                data_val=data_val,
                headers=self.client.build_json_headers(include_host=True),
                verify=False,
            )
            self.client.clear_conflicting_cookies(response)
            result = self.client.parse_json_response(response, api_name=api_name)
            if "ret" in result and result["ret"] and "令牌过期" in result["ret"][0]:
                continue
            return self.client.ensure_api_success(result, api_name=api_name)

    def refresh_token(self):
        api_name = "mtop.taobao.idlemessage.pc.loginuser.get"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.im.0.0",
            spm_pre="a21ybx.item.want.1.12523da6waCtUp",
            log_id="12523da6waCtUp",
        )
        response = self.client.post_json(
            self.client.refresh_token_url,
            params=params,
            data_val="{}",
            headers=self.client.build_json_headers(),
        )
        self.client.clear_conflicting_cookies(response)
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

