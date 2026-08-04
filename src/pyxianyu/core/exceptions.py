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

