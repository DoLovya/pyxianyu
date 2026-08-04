class UserApi:
    def __init__(self, client):
        self.client = client

    def get_user_page_nav(self):
        api_name = "mtop.idle.web.user.page.nav"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.personal.0.0",
            spm_pre="a21ybx.im.nav.1.4deb4f10uD9XhK",
            log_id="4deb4f10uD9XhK",
        )
        response = self.client.post_json(
            self.client.user_page_nav_url,
            params=params,
            data_val="{}",
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

