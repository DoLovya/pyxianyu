import asyncio
import base64
import inspect
import json
import threading
import time

import websockets
from loguru import logger

from .xianyu_apis import XianyuApis
from .message import LwpResponseError, LwpTimeout, Message, RecallResult, SentMessageReceipt, make_image, make_text
from .utils.xianyu_utils import (
    decrypt,
    generate_device_id,
    generate_mid,
    generate_uuid,
    get_session_cookies_str,
    trans_cookies,
)


RATE_LIMIT_CODE = "400600001"
_RATE_LIMIT_MARK = str(RATE_LIMIT_CODE)


def _ws_connect(url, headers):
    kwargs = {}
    parameters = inspect.signature(websockets.connect).parameters
    if "additional_headers" in parameters:
        kwargs["additional_headers"] = headers
    elif "extra_headers" in parameters:
        kwargs["extra_headers"] = headers
    else:
        kwargs["headers"] = headers
    if "proxy" in parameters:
        kwargs["proxy"] = None
    return websockets.connect(url, **kwargs)


def _parse_message_id(body, *, sent_uuid=None):
    """按决策 2 的四条解析顺序提取 messageId。"""
    # 1. body.messageId
    if isinstance(body, dict) and isinstance(body.get("messageId"), str) and body["messageId"]:
        return body["messageId"], "body.messageId"
    # 2. body["1"].messageId
    if isinstance(body, dict) and isinstance(body.get("1"), dict):
        nested = body["1"]
        if isinstance(nested.get("messageId"), str) and nested["messageId"]:
            return nested["messageId"], "body.1.messageId"
    # 3. body["1"]["1"] （字符串型）
    if isinstance(body, dict) and isinstance(body.get("1"), dict):
        inner = body["1"].get("1")
        if isinstance(inner, str) and inner:
            return inner, "body.1.1"
    if isinstance(sent_uuid, str) and sent_uuid:
        return sent_uuid, "sent_uuid_fallback"
    raise LwpResponseError(
        "无法从响应 body 中解析 messageId（解析顺序：body.messageId / body.1.messageId / body.1.1 / sent_uuid）",
        body=body,
        raw_response=body,
        status="parse_error",
    )


async def _ack_message(ws, message):
    """ACK 回传：code=200, headers.mid/sid/app-key/ua/dt 回传（与 list_all_conversations 模式一致）。"""
    try:
        ack = {
            "code": 200,
            "headers": {
                "mid": message.get("headers", {}).get("mid") or generate_mid(),
                "sid": message.get("headers", {}).get("sid", ""),
            },
        }
        headers = message.get("headers", {})
        for k in ("app-key", "ua", "dt"):
            if k in headers:
                ack["headers"][k] = headers[k]
        await ws.send(json.dumps(ack))
    except Exception:
        pass


class XianyuLive:
    def __init__(self, cookies_str):
        self.base_url = "wss://wss-goofish.dingtalk.com/"
        self.cookies_str = cookies_str
        self.cookies = trans_cookies(cookies_str)
        self.myid = self.cookies["unb"]
        self.device_id = generate_device_id(self.myid)
        self.xianyu = XianyuApis(self.cookies, self.device_id)
        self.ws = None

    async def list_all_conversations(self, cid):
        headers = {
            "Cookie": get_session_cookies_str(self.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/133.0.0.0 Safari/537.36"
            ),
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        async with _ws_connect(self.base_url, headers) as websocket:
            asyncio.create_task(self.init(websocket))
            send_mid = generate_mid()
            msg = {
                "lwp": "/r/MessageManager/listUserMessages",
                "headers": {"mid": send_mid},
                "body": [f"{cid}@goofish", False, 9007199254740991, 20, False],
            }
            user_message_models = []
            async for message in websocket:
                try:
                    message = json.loads(message)
                    await _ack_message(websocket, message)
                except Exception:
                    pass
                try:
                    if "lwp" in message and message["lwp"] == "/s/vulcan":
                        await websocket.send(json.dumps(msg))
                    recv_mid = message.get("headers", {}).get("mid", "") if isinstance(message, dict) else ""
                    if recv_mid == send_mid:
                        body = message.get("body", {}) if isinstance(message, dict) else {}
                        has_more = body.get("hasMore") == 1
                        next_cursor = body.get("nextCursor")
                        for user_message in body.get("userMessageModels", []):
                            send_user_name = user_message["message"]["extension"]["reminderTitle"]
                            send_user_id = user_message["message"]["extension"]["senderUserId"]
                            send_message_base64 = user_message["message"]["content"]["custom"]["data"]
                            send_message_json = json.loads(
                                base64.b64decode(send_message_base64).decode("utf-8")
                            )
                            user_message_models.insert(
                                0,
                                {
                                    "send_user_id": send_user_id,
                                    "send_user_name": send_user_name,
                                    "message": send_message_json,
                                },
                            )
                        if has_more:
                            send_mid = generate_mid()
                            msg["headers"]["mid"] = send_mid
                            msg["body"][2] = next_cursor
                            await websocket.send(json.dumps(msg))
                        else:
                            return user_message_models
                except Exception:
                    return user_message_models

    async def create_chat(self, ws, toid, item_id="891198795482"):
        msg = {
            "lwp": "/r/SingleChatConversation/create",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "pairFirst": f"{toid}@goofish",
                    "pairSecond": f"{self.myid}@goofish",
                    "bizType": "1",
                    "extension": {"itemId": item_id},
                    "ctx": {"appVersion": "1.0", "platform": "web"},
                }
            ],
        }
        await ws.send(json.dumps(msg))

    # ------------------------------------------------------------------
    # lwp 请求-响应匹配通用工具
    # ------------------------------------------------------------------
    async def _send_lwp_and_wait(self, ws, lwp: str, body, *, timeout_sec: int = 15, rate_limit_retries: int = 3):
        """发送 lwp 消息，按 mid 匹配响应，并处理 400600001 指数退避重试。

        返回 (body, full_msg, send_mid)。
        """
        attempts_total = max(1, rate_limit_retries + 1)
        last_body: Any = None
        last_full: Any = None
        last_mid: str = ""
        for attempt in range(attempts_total):
            mid = generate_mid()
            last_mid = mid
            msg = {"lwp": lwp, "headers": {"mid": mid}, "body": body}
            try:
                full, matched_body = await asyncio.wait_for(
                    self._wait_for_mid(ws, msg, mid, timeout_sec=timeout_sec),
                    timeout=timeout_sec + 1,
                )
            except (LwpTimeout, asyncio.TimeoutError) as exc:
                if attempt + 1 < attempts_total:
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                raise LwpTimeout(
                    f"lwp={lwp} mid={mid} 等待响应超时 {timeout_sec}s（{attempts_total} 次尝试）",
                    body=last_body,
                    raw_response=last_full,
                    status="timeout",
                ) from None
            last_full, last_body = full, matched_body
            if isinstance(last_body, dict):
                code = last_body.get("code")
                if str(code) == _RATE_LIMIT_MARK or _RATE_LIMIT_MARK in json.dumps(last_body, ensure_ascii=False):
                    if attempt + 1 < attempts_total:
                        await asyncio.sleep((attempt + 1) * 2)
                        continue
                    raise LwpResponseError(
                        f"lwp={lwp} 连续 {attempts_total} 次命中 IM 流控 {_RATE_LIMIT_MARK}",
                        code=_RATE_LIMIT_MARK,
                        body=last_body,
                        raw_response=last_full,
                        status="rate_limit",
                    )
            return last_body, last_full, last_mid
        return last_body, last_full, last_mid

    async def _wait_for_mid(self, ws, msg, mid, *, timeout_sec):
        deadline = time.monotonic() + timeout_sec
        sent = False
        async for raw in ws:
            try:
                recv = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                continue
            await _ack_message(ws, recv)
            if not sent and isinstance(recv, dict) and recv.get("lwp") == "/s/vulcan":
                await ws.send(json.dumps(msg))
                sent = True
            if isinstance(recv, dict) and recv.get("headers", {}).get("mid") == mid:
                matched_body = recv.get("body", {}) if isinstance(recv, dict) else {}
                return recv, matched_body
            if time.monotonic() > deadline:
                raise LwpTimeout(f"mid={mid} 未匹配到响应")
        raise LwpTimeout(f"mid={mid} websocket 提前结束")

    async def send_msg(self, ws, cid, toid, message: Message) -> SentMessageReceipt:
        msg_type = message["type"]
        msg_uuid = generate_uuid()
        send_body_item: dict = {
            "uuid": msg_uuid,
            "cid": f"{cid}@goofish",
            "conversationType": 1,
            "content": {"contentType": 101, "custom": {"type": None, "data": None}},
            "redPointPolicy": 0,
            "extension": {"extJson": "{}"},
            "ctx": {"appVersion": "1.0", "platform": "web"},
            "mtags": {},
            "msgReadStatusSetting": 1,
        }
        send_body: list = [send_body_item, {"actualReceivers": [f"{toid}@goofish", f"{self.myid}@goofish"]}]
        if msg_type == "text":
            payload = {"contentType": 1, "text": {"text": message["text"]}}
            text_base64 = str(base64.b64encode(json.dumps(payload).encode("utf-8")), "utf-8")
            send_body_item["content"]["custom"]["type"] = 1
            send_body_item["content"]["custom"]["data"] = text_base64
        elif msg_type == "image":
            payload = {
                "contentType": 2,
                "image": {
                    "pics": [
                        {
                            "type": 0,
                            "url": message["image_url"],
                            "width": message["width"],
                            "height": message["height"],
                        }
                    ]
                },
            }
            image_base64 = str(base64.b64encode(json.dumps(payload).encode("utf-8")), "utf-8")
            send_body_item["content"]["custom"]["type"] = 2
            send_body_item["content"]["custom"]["data"] = image_base64
        else:
            logger.error(f"不支持的消息类型: {msg_type}")
            raise ValueError(f"不支持的消息类型: {msg_type}")
        body, full_msg, used_mid = await self._send_lwp_and_wait(ws, "/r/MessageSend/sendByReceiverScope", send_body)
        message_id, parse_path = _parse_message_id(body, sent_uuid=msg_uuid)
        code = body.get("code") if isinstance(body, dict) else None
        return SentMessageReceipt(
            cid=f"{cid}@goofish",
            messageId=message_id,
            uuid=msg_uuid,
            status_code=code if isinstance(code, int) else None,
            raw={"body": body, "full": full_msg},
            parse_path=parse_path,
            mid=used_mid,
        )

    async def recall_message(self, ws, message_id: str) -> RecallResult:
        if not isinstance(message_id, str) or not message_id.strip():
            raise ValueError("message_id 不能为空")
        try:
            body, _full, _mid = await self._send_lwp_and_wait(ws, "/r/MessageManager/recallMessage", [message_id])
        except LwpResponseError as exc:
            if exc.status == "rate_limit":
                return RecallResult(
                    success=False,
                    status="rate_limit",
                    code=_RATE_LIMIT_MARK,
                    reason=str(exc),
                    raw=exc.raw_response,
                )
            if exc.status == "timeout":
                return RecallResult(success=False, status="timeout", code=exc.code, reason=str(exc), raw=exc.raw_response)
            return RecallResult(success=False, status="unknown_error", code=exc.code, reason=str(exc), raw=exc.raw_response)

        code = None
        reason = None
        if isinstance(body, dict):
            code = body.get("code")
            reason = body.get("reason") or None
            for k in ("msg", "message", "errorMsg", "errMsg", "errmsg"):
                if reason is None and body.get(k):
                    reason = body[k]
        success = code == 200
        status: Any = "unknown_error"
        if success:
            status = "success"
        elif isinstance(reason, str):
            if "超过" in reason and ("可撤回时间" in reason or "分钟" in reason):
                status = "timeout"
            elif "非本人" in reason or "不属于自己" in reason or "不属于本人" in reason:
                status = "not_mine"
            elif _RATE_LIMIT_MARK in reason:
                status = "rate_limit"
            else:
                if any(_RATE_LIMIT_MARK in str(x) for x in [code, body]):
                    status = "rate_limit"
        else:
            if str(code) == _RATE_LIMIT_MARK:
                status = "rate_limit"
        return RecallResult(success=success, status=status, code=code, reason=reason, raw=body)

    async def init(self, ws):
        data = self.xianyu.get_token()
        token = data.get("data", {}).get("accessToken", "")
        if not token:
            raise RuntimeError("获取 token 失败")
        msg = {
            "lwp": "/reg",
            "headers": {
                "cache-header": "app-key token ua wv",
                "app-key": "444e9908a51d1cb236a27862abc769c9",
                "token": token,
                "ua": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) "
                    "Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5"
                ),
                "dt": "j",
                "wv": "im:3,au:3,sy:6",
                "sync": "0,0;0;0;",
                "did": self.device_id,
                "mid": generate_mid(),
            },
        }
        await ws.send(json.dumps(msg))
        current_time = int(time.time() * 1000)
        msg = {
            "lwp": "/r/SyncStatus/ackDiff",
            "headers": {"mid": generate_mid()},
            "body": [
                {
                    "pipeline": "sync",
                    "tooLong2Tag": "PNM,1",
                    "channel": "sync",
                    "topic": "sync",
                    "highPts": 0,
                    "pts": current_time * 1000,
                    "seq": 0,
                    "timestamp": current_time,
                }
            ],
        }
        await ws.send(json.dumps(msg))

    async def send_msg_once(self, toid, item_id, send_message: Message):
        headers = {
            "Cookie": get_session_cookies_str(self.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/133.0.0.0 Safari/537.36"
            ),
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        async with _ws_connect(self.base_url, headers) as websocket:
            await self.init(websocket)
            await self.create_chat(websocket, toid, item_id)
            async for message in websocket:
                try:
                    message = json.loads(message)
                    cid = message["body"]["singleChatConversation"]["cid"].split("@")[0]
                    receipt: SentMessageReceipt = await self.send_msg(websocket, cid, toid, send_message)
                    return receipt
                except Exception:
                    pass

    async def heart_beat(self, ws):
        while True:
            msg = {"lwp": "/!", "headers": {"mid": generate_mid()}}
            await ws.send(json.dumps(msg))
            await asyncio.sleep(15)

    def user_alive(self):
        while True:
            time.sleep(600)
            self.xianyu.refresh_token()

    async def main(self):
        headers = {
            "Cookie": get_session_cookies_str(self.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/133.0.0.0 Safari/537.36"
            ),
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        threading.Thread(target=self.user_alive, daemon=True).start()
        async with _ws_connect(self.base_url, headers) as websocket:
            asyncio.create_task(self.init(websocket))
            asyncio.create_task(self.heart_beat(websocket))
            async for message in websocket:
                message = json.loads(message)
                ack = {
                    "code": 200,
                    "headers": {
                        "mid": message["headers"]["mid"] if "mid" in message["headers"] else generate_mid(),
                        "sid": message["headers"]["sid"] if "sid" in message["headers"] else "",
                    },
                }
                if "app-key" in message["headers"]:
                    ack["headers"]["app-key"] = message["headers"]["app-key"]
                if "ua" in message["headers"]:
                    ack["headers"]["ua"] = message["headers"]["ua"]
                if "dt" in message["headers"]:
                    ack["headers"]["dt"] = message["headers"]["dt"]
                await websocket.send(json.dumps(ack))
                await self.handle_message(message, websocket)

    async def handle_message(self, message, websocket):
        try:
            data = message["body"]["syncPushPackage"]["data"][0]["data"]
            data = json.loads(data)
        except Exception:
            try:
                data = decrypt(data)
                message = json.loads(data)
                send_user_name = message["1"]["10"]["reminderTitle"]
                send_user_id = message["1"]["10"]["senderUserId"]
                send_message = message["1"]["10"]["reminderContent"]
                cid = message["1"]["2"].split("@")[0]
                reply = f"{send_user_name} 说了: {send_message}"
                await self.send_msg(websocket, cid, send_user_id, make_text(reply))
            except Exception:
                pass
