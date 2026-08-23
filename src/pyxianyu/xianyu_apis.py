from .apis import AuthApi, ItemApi, MediaApi, SearchApi, TradeApi, UserApi
from .core import XianyuClient


class XianyuApis:
    def __init__(self, cookies, device_id):
        self.client = XianyuClient(cookies, device_id)
        self.login_url = self.client.login_url
        self.upload_media_url = self.client.upload_media_url
        self.refresh_token_url = self.client.refresh_token_url
        self.item_detail_url = self.client.item_detail_url
        self.item_search_url = self.client.item_search_url
        self.user_items_url = self.client.user_items_url
        self.user_page_nav_url = self.client.user_page_nav_url
        self.item_downshelf_url = self.client.item_downshelf_url
        self.item_prepublish_check_url = self.client.item_prepublish_check_url
        self.item_preget_url = self.client.item_preget_url
        self.item_edit_detail_url = self.client.item_edit_detail_url
        self.item_edit_url = self.client.item_edit_url
        self.item_polish_url = self.client.item_polish_url
        self.order_render_url = self.client.order_render_url
        self.order_create_url = self.client.order_create_url
        self.address_list_url = self.client.address_list_url
        self.yhb_order_render_url = self.client.yhb_order_render_url
        self.yhb_order_create_url = self.client.yhb_order_create_url
        self.reset_login_info_url = self.client.reset_login_info_url
        self.session = self.client.session
        self.device_id = device_id
        self.cookies = {}
        self.auth_api = AuthApi(self.client)
        self.item_api = ItemApi(self.client)
        self.media_api = MediaApi(self.client)
        self.search_api = SearchApi(self.client)
        self.trade_api = TradeApi(self.client)
        self.user_api = UserApi(self.client)

    def get_token(self):
        return self.auth_api.get_token()

    def refresh_token(self):
        return self.auth_api.refresh_token()

    def upload_media(self, media_path):
        return self.media_api.upload_media(media_path)

    def get_item_info(self, item_id):
        return self.item_api.get_item_info(item_id)

    def search_items(self, keyword, *, page_number=1, rows_per_page=20, sort_field="", sort_value=""):
        return self.search_api.search_items(
            keyword,
            page_number=page_number,
            rows_per_page=rows_per_page,
            sort_field=sort_field,
            sort_value=sort_value,
        )

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
        return self.item_api.get_user_items(
            user_id=user_id,
            page_number=page_number,
            page_size=page_size,
            need_group_info=need_group_info,
            group_name=group_name,
            group_id=group_id,
            default_group=default_group,
            group_sort_id=group_sort_id,
            filter_panel_group_id=filter_panel_group_id,
            next_page_model=next_page_model,
            next_page_num=next_page_num,
        )

    def get_all_user_items(self, user_id, page_size=20):
        return self.item_api.get_all_user_items(user_id=user_id, page_size=page_size)

    def get_user_page_nav(self):
        return self.user_api.get_user_page_nav()

    def downshelf_item(self, item_id):
        return self.item_api.downshelf_item(item_id)

    def prepublish_check(self, item_id=None):
        return self.item_api.prepublish_check(item_id)

    def preget(self, item_id=None, source_id=None, publish_scene=None, bizcode=None):
        return self.item_api.preget(
            item_id=item_id,
            source_id=source_id,
            publish_scene=publish_scene,
            bizcode=bizcode,
        )

    def get_item_edit_detail(self, item_id):
        return self.item_api.get_item_edit_detail(item_id)

    def edit_item(self, payload):
        return self.item_api.edit_item(payload)

    def publish_item(self, payload):
        return self.item_api.publish_item(payload)

    def build_reshelf_payload(self, edit_detail_result, *, item_id=None, source_id=None):
        return self.item_api.build_reshelf_payload(
            edit_detail_result,
            item_id=item_id,
            source_id=source_id,
        )

    def reshelf_item(self, item_id, source_id=None):
        return self.item_api.reshelf_item(item_id, source_id=source_id)

    def polish_item(self, item_id):
        return self.item_api.polish_item(item_id)

    def get_address_list(self):
        return self.trade_api.get_address_list()

    def yhb_order_render(self, item_id):
        return self.trade_api.yhb_order_render(item_id)

    def yhb_order_create(self, item_id, buyer_address_id, *, buy_quantity=1, yhb_version=3):
        return self.trade_api.yhb_order_create(
            item_id,
            buyer_address_id,
            buy_quantity=buy_quantity,
            yhb_version=yhb_version,
        )

    def place_order_yhb(self, item_id, *, buyer_address_id=None):
        return self.trade_api.place_order_yhb(item_id, buyer_address_id=buyer_address_id)

    def order_render(self, item_id):
        return self.trade_api.order_render(item_id)

    def order_create(self, item_buy_info):
        return self.trade_api.order_create(item_buy_info)

    def place_order(self, item_id):
        return self.trade_api.place_order(item_id)
