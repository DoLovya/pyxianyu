import os

from requests import RequestException

from ..core.exceptions import XianyuRequestError


class MediaApi:
    def __init__(self, client):
        self.client = client

    def upload_media(self, media_path):
        api_name = "stream-upload.goofish.com/api/upload.api"
        headers = {
            "accept": "*/*",
            "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-TW;q=0.7,ja;q=0.6",
            "cache-control": "no-cache",
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
            "user-agent": self.client.build_json_headers()["user-agent"],
        }
        params = {
            "floderId": "0",
            "appkey": "xy_chat",
            "_input_charset": "utf-8",
        }
        with open(media_path, "rb") as file_obj:
            media_name = os.path.basename(media_path)
            ext = os.path.splitext(media_name)[1].lower().lstrip(".")
            mime = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
                "gif": "image/gif",
                "mp4": "video/mp4",
                "mov": "video/quicktime",
                "mkv": "video/x-matroska",
                "mp3": "audio/mpeg",
                "m4a": "audio/mp4",
                "wav": "audio/wav",
                "aac": "audio/aac",
                "amr": "audio/amr",
            }.get(ext, "application/octet-stream")
            files = {
                "file": (media_name, file_obj, mime),
            }
            try:
                response = self.client.session.post(
                    self.client.upload_media_url,
                    headers=headers,
                    params=params,
                    files=files,
                    verify=False,
                )
                response.raise_for_status()
            except RequestException as exc:
                raise XianyuRequestError(
                    f"请求闲鱼媒体上传接口失败: {api_name}",
                    api_name=api_name,
                    url=self.client.upload_media_url,
                ) from exc
        return self.client.parse_json_response(response, api_name=api_name)

