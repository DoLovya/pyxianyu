class XianyuError(Exception):
    pass


class XianyuConfigError(XianyuError):
    pass


class XianyuRequestError(XianyuError):
    def __init__(self, message, *, api_name=None, url=None):
        super().__init__(message)
        self.api_name = api_name
        self.url = url


class XianyuResponseError(XianyuError):
    def __init__(self, message, *, api_name=None, status_code=None):
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code


class XianyuApiError(XianyuError):
    def __init__(self, message, *, api_name=None, ret=None, payload=None):
        super().__init__(message)
        self.api_name = api_name
        self.ret = ret or []
        self.payload = payload or {}


class XianyuYhbRequiredError(XianyuApiError):
    """
    普通下单链路返回「必走验货宝商品」时抛出，用于在 place_order 中识别回退信号。
    后续验货宝链路实现后，调用方捕获此异常可切换至 address.list.query -> yhb.render -> yhb.create。
    """

    def __init__(self, message, *, api_name=None, ret=None, payload=None, item_id=None):
        super().__init__(message, api_name=api_name, ret=ret, payload=payload)
        self.item_id = item_id

