class XianyuError(Exception):
    """闲鱼 SDK 基础异常。"""


class XianyuConfigError(XianyuError):
    """本地配置或运行环境异常，例如缺少必要 cookie。"""


class XianyuRequestError(XianyuError):
    """HTTP 请求阶段异常。"""

    def __init__(self, message, *, api_name=None, url=None):
        super().__init__(message)
        self.api_name = api_name
        self.url = url


class XianyuResponseError(XianyuError):
    """响应格式异常，例如返回了非 JSON 数据。"""

    def __init__(self, message, *, api_name=None, status_code=None):
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code


class XianyuApiError(XianyuError):
    """接口返回了业务失败结果。"""

    def __init__(self, message, *, api_name=None, ret=None, payload=None):
        super().__init__(message)
        self.api_name = api_name
        self.ret = ret or []
        self.payload = payload or {}
