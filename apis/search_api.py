import json


class SearchApi:
    def __init__(self, client):
        self.client = client

    def search_items(
        self,
        keyword: str,
        *,
        page_number: int = 1,
        rows_per_page: int = 20,
        sort_field: str = "",
        sort_value: str = "",
        prop_value_str: dict | None = None,
        extra_filter_value: str = "{}",
        from_filter: bool = False,
    ):
        api_name = "mtop.taobao.idlemtopsearch.pc.search"
        params = self.client.build_mtop_params(
            api=api_name,
            spm_cnt="a21ybx.search.0.0",
            spm_pre="a21ybx.search.searchInput.0",
            log_id="xianyu_item_search",
        )
        data_payload = {
            "keyword": str(keyword),
            "pageNumber": int(page_number),
            "rowsPerPage": int(rows_per_page),
            "sortField": str(sort_field or ""),
            "sortValue": str(sort_value or ""),
            "propValueStr": prop_value_str or {},
            "extraFilterValue": str(extra_filter_value or "{}"),
            "fromFilter": bool(from_filter),
            "searchReqFromPage": "pcSearch",
        }
        data_val = json.dumps(data_payload, ensure_ascii=False, separators=(",", ":"))
        response = self.client.post_json(
            self.client.item_search_url,
            params=params,
            data_val=data_val,
        )
        result = self.client.parse_json_response(response, api_name=api_name)
        return self.client.ensure_api_success(result, api_name=api_name)

