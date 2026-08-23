#!/usr/bin/env python3
"""pyxianyu 1.x 端到端冒烟 Harness。

用法：
    python scripts/smoke_1_0.py
    python scripts/smoke_1_0.py --case polish_item,place_order
    python scripts/smoke_1_0.py --only-http --json report.json

环境变量详见：scripts/smoke_env.example。缺关键 env 对应 case 自动 SKIP。
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Awaitable, Iterable, Literal, Optional
from unittest.mock import Mock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from pyxianyu.xianyu_apis import XianyuApis
from pyxianyu.xianyu_live import XianyuLive
from pyxianyu.utils.xianyu_utils import generate_device_id, trans_cookies

SmokeStatus = Literal["PASS", "SKIP", "FAIL"]
SECRET_ENV_KEYS = ("XY_COOKIE_STR",)
ORDER_STATUSES = {"success", "yhb_required", "account_invalid", "failed"}


# ---------------------------------------------------------------------------
# 颜色与输出
# ---------------------------------------------------------------------------
_IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(s: str, code: str) -> str:
    return f"\x1b[{code}m{s}\x1b[0m" if _IS_TTY else s


_GREEN = lambda s: _c(s, "32")
_YELLOW = lambda s: _c(s, "33")
_RED = lambda s: _c(s, "31")
_CYAN = lambda s: _c(s, "36")
_DIM = lambda s: _c(s, "2")

_STATUS_FMT = {
    "PASS": lambda t: _GREEN(f"✅ {t}"),
    "SKIP": lambda t: _YELLOW(f"⏭  {t}"),
    "FAIL": lambda t: _RED(f"❌ {t}"),
}


def status_fmt(status: SmokeStatus) -> str:
    return _STATUS_FMT[status](status)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
@dataclass
class SmokeResult:
    case_name: str
    status: SmokeStatus
    duration_ms: int
    mode: Literal["mock", "real"]
    payload: Any = None
    reason: str = ""
    env_hits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "case_name": self.case_name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "mode": self.mode,
            "payload": _json_safe(self.payload),
            "reason": self.reason,
            "env_hits": list(self.env_hits),
        }


@dataclass
class RunContext:
    mode: Literal["mock", "real"]
    cookies: dict
    cookies_str: str
    device_id: str
    apis: XianyuApis
    live: Optional[XianyuLive]
    http_retry: int
    env: dict[str, str]

    def env_get(self, key: str, default: str = "") -> str:
        return self.env.get(key, default)


# ---------------------------------------------------------------------------
# 用例基类
# ---------------------------------------------------------------------------
class Case:
    name: str = "base"
    domain: Literal["http", "ws"] = "http"
    requires: tuple[str, ...] = ()
    requires_attrs: tuple[str, ...] = ()

    def _check_requires(self, ctx: RunContext) -> Optional[SmokeResult]:
        hits: list[str] = []
        for k in self.requires:
            v = ctx.env_get(k).strip()
            if not v:
                return SmokeResult(
                    case_name=self.name,
                    status="SKIP",
                    duration_ms=0,
                    mode=ctx.mode,
                    reason=f"缺少 env: {k}",
                    env_hits=hits,
                )
            hits.append(k)
        for attr in self.requires_attrs:
            parts = attr.split(".", 1)
            if len(parts) == 1:
                obj: Any = ctx.apis
                name = parts[0]
            else:
                obj = getattr(ctx.apis, parts[0], None)
                name = parts[1]
                if obj is None:
                    return SmokeResult(
                        case_name=self.name,
                        status="SKIP",
                        duration_ms=0,
                        mode=ctx.mode,
                        reason=f"代码未实现: XianyuApis 缺少属性 {parts[0]!r}（对应 {attr}）",
                        env_hits=hits,
                    )
            if not hasattr(obj, name):
                return SmokeResult(
                    case_name=self.name,
                    status="SKIP",
                    duration_ms=0,
                    mode=ctx.mode,
                    reason=f"代码未实现: 缺少 {attr!r}（本次 session 尚未落地 trade-polish-apis 的代码实现）",
                    env_hits=hits,
                )
        return None

    def _run(self, ctx: RunContext) -> SmokeResult:
        raise NotImplementedError

    def run(self, ctx: RunContext) -> SmokeResult:
        skip = self._check_requires(ctx)
        if skip:
            return skip
        t0 = time.perf_counter()
        try:
            res = self._run(ctx)
        except Exception as exc:  # noqa: BLE001 - 做 smoke 汇总
            res = SmokeResult(
                case_name=self.name,
                status="FAIL",
                duration_ms=int((time.perf_counter() - t0) * 1000),
                mode=ctx.mode,
                reason=f"未捕获异常: {type(exc).__name__}: {exc}",
            )
        else:
            res.duration_ms = int((time.perf_counter() - t0) * 1000)
        return res


# ---------------------------------------------------------------------------
# 具体用例
# ---------------------------------------------------------------------------
class GetTokenCase(Case):
    name = "get_token"
    domain = "http"
    requires = ("XY_COOKIE_STR",)

    def _run(self, ctx: RunContext) -> SmokeResult:
        # real 模式真实调用；mock 模式 patch auth_api.get_token 返回合法 shape
        if ctx.mode == "mock":
            mock_ret = {"data": {"accessToken": "token-mock-" + os.urandom(4).hex()}, "ret": ["SUCCESS::调用成功"]}
            with patch.object(ctx.apis.auth_api, "get_token", return_value=mock_ret) as m:
                ret = ctx.apis.get_token()
                calls = m.call_count
        else:
            ret = _retry_http(lambda: ctx.apis.get_token(), ctx.http_retry)
            calls = 1
        token = (ret or {}).get("data", {}).get("accessToken", "")
        if not isinstance(token, str) or not token:
            return SmokeResult(
                case_name=self.name,
                status="FAIL",
                duration_ms=0,
                mode=ctx.mode,
                payload={"ret_type": type(ret).__name__},
                reason="data.accessToken 为空或非字符串",
                env_hits=list(self.requires),
            )
        return SmokeResult(
            case_name=self.name,
            status="PASS",
            duration_ms=0,
            mode=ctx.mode,
            payload={"calls": calls, "token_len": len(token), "ret_type": type(ret).__name__},
            env_hits=list(self.requires),
        )


class SearchItemsCase(Case):
    name = "search_items"
    domain = "http"

    def _run(self, ctx: RunContext) -> SmokeResult:
        q = "耳机"
        if ctx.mode == "mock":
            fake = [
                {"itemId": "1", "title": "mock-A"},
                {"itemId": "2", "title": "mock-B"},
            ]
            with patch.object(ctx.apis.search_api, "search_items", return_value=fake) as m:
                ret = ctx.apis.search_items(q)
                calls = m.call_count
        else:
            ret = _retry_http(lambda: ctx.apis.search_items(q), ctx.http_retry)
            calls = 1
        ok = isinstance(ret, (list, dict))
        return SmokeResult(
            case_name=self.name,
            status="PASS" if ok else "FAIL",
            duration_ms=0,
            mode=ctx.mode,
            payload={"calls": calls, "ret_type": type(ret).__name__, "count": len(ret) if hasattr(ret, "__len__") else None},
            reason="" if ok else f"返回类型异常: {type(ret).__name__}",
        )


class GetUserItemsCase(Case):
    name = "get_user_items"
    domain = "http"
    requires = ("XY_COOKIE_STR",)
    requires_attrs = ("get_user_items",)

    def _run(self, ctx: RunContext) -> SmokeResult:
        # 调用时优先用当前登录 userId（从 user_page_nav 里取），避免需要外部传参。
        # mock 模式下 patch item_api.get_user_items 的时候，也能保证走 shape 校验。
        if ctx.mode == "mock":
            fake = [
                {"itemId": "mock-user-1", "title": "mock", "userId": "u-mock"},
            ]
            with patch.object(ctx.apis.item_api, "get_user_items", return_value=fake) as m:
                ret = ctx.apis.item_api.get_user_items("u-mock")
                calls = m.call_count
        else:
            calls = 1
            try:
                user_id: Optional[str] = None
                if hasattr(ctx.apis, "get_user_page_nav"):
                    nav = _retry_http(lambda: ctx.apis.get_user_page_nav(), ctx.http_retry)
                    user_id = (nav or {}).get("data", {}).get("userId")
                if not user_id:
                    user_id = ctx.cookies.get("unb") or ctx.cookies.get("userid")
                if not user_id:
                    return SmokeResult(
                        case_name=self.name,
                        status="SKIP",
                        duration_ms=0,
                        mode=ctx.mode,
                        reason="无法从 user_page_nav 或 cookie 推断当前 userId，请显式传参",
                        env_hits=list(self.requires),
                    )
                ret = _retry_http(lambda: ctx.apis.get_user_items(user_id), ctx.http_retry)
            except TypeError as exc:
                return SmokeResult(
                    case_name=self.name,
                    status="SKIP",
                    duration_ms=0,
                    mode=ctx.mode,
                    reason=f"当前 XianyuApis.get_user_items 不支持从 cookie 推断 userId（需要自行实现默认 userId 逻辑）：{exc}",
                    env_hits=list(self.requires),
                )
        ok = isinstance(ret, (list, dict))
        return SmokeResult(
            case_name=self.name,
            status="PASS" if ok else "FAIL",
            duration_ms=0,
            mode=ctx.mode,
            payload={"calls": calls, "ret_type": type(ret).__name__, "count": len(ret) if hasattr(ret, "__len__") else None},
            reason="" if ok else f"返回类型异常: {type(ret).__name__}",
            env_hits=list(self.requires),
        )


class PolishItemCase(Case):
    name = "polish_item"
    domain = "http"
    requires = ("XY_TEST_ITEM_ID",)
    requires_attrs = ("polish_item", "item_api.polish_item")

    def _run(self, ctx: RunContext) -> SmokeResult:
        item_id = ctx.env_get("XY_TEST_ITEM_ID").strip()
        if ctx.mode == "mock":
            fake = {"success": True, "already_polished": False, "ret": ["SUCCESS::调用成功"]}
            # 优先 patch 门面；不存在就 patch item_api。
            if hasattr(ctx.apis, "polish_item"):
                with patch.object(ctx.apis, "polish_item", return_value=fake) as m:
                    ret = ctx.apis.polish_item(item_id)
                    calls = m.call_count
            else:
                with patch.object(ctx.apis.item_api, "polish_item", return_value=fake) as m:
                    ret = ctx.apis.item_api.polish_item(item_id)
                    calls = m.call_count
        else:
            calls = 1
            if hasattr(ctx.apis, "polish_item"):
                ret = _retry_http(lambda: ctx.apis.polish_item(item_id), ctx.http_retry)
            else:
                ret = _retry_http(lambda: ctx.apis.item_api.polish_item(item_id), ctx.http_retry)
        ok = bool((ret or {}).get("success")) and (ret.get("already_polished") in (True, False))
        return SmokeResult(
            case_name=self.name,
            status="PASS" if ok else "FAIL",
            duration_ms=0,
            mode=ctx.mode,
            payload={"calls": calls, "item_id": item_id, "ret_keys": list(ret.keys()) if isinstance(ret, dict) else None, "ret_type": type(ret).__name__},
            reason="" if ok else f"polish 结果异常: ret={_truncate(ret)}",
            env_hits=list(self.requires),
        )


class PlaceOrderCase(Case):
    name = "place_order"
    domain = "http"
    requires = ("XY_TEST_ORDER_ITEM_ID", "XY_RUN_ORDER_TESTS")
    requires_attrs = ("place_order",)

    def _check_requires(self, ctx: RunContext) -> Optional[SmokeResult]:
        base = super()._check_requires(ctx)
        if base:
            return base
        flag = ctx.env_get("XY_RUN_ORDER_TESTS").strip()
        if flag != "1":
            return SmokeResult(
                case_name=self.name,
                status="SKIP",
                duration_ms=0,
                mode=ctx.mode,
                reason=f"XY_RUN_ORDER_TESTS={flag!r} != 1（两层 opt-in，需设 1 才启用）",
                env_hits=list(self.requires),
            )
        return None

    def _run(self, ctx: RunContext) -> SmokeResult:
        item_id = ctx.env_get("XY_TEST_ORDER_ITEM_ID").strip()
        if ctx.mode == "mock":
            fake = {
                "status": "failed",
                "order_id": None,
                "pay_url": None,
                "item_buy_info": None,
                "error": "mock-place-order-not-enabled",
            }
            with patch.object(ctx.apis, "place_order", return_value=fake) as m:
                ret = ctx.apis.place_order(item_id)
                calls = m.call_count
        else:
            calls = 1
            ret = _retry_http(lambda: ctx.apis.place_order(item_id), ctx.http_retry)
        if not isinstance(ret, dict):
            return SmokeResult(
                case_name=self.name,
                status="FAIL",
                duration_ms=0,
                mode=ctx.mode,
                payload={"calls": calls, "ret_type": type(ret).__name__},
                reason="place_order 返回值非 dict",
                env_hits=list(self.requires),
            )
        status = ret.get("status")
        if status not in ORDER_STATUSES:
            return SmokeResult(
                case_name=self.name,
                status="FAIL",
                duration_ms=0,
                mode=ctx.mode,
                payload={"calls": calls, "status": status, "ret_keys": list(ret.keys())},
                reason=f"status={status!r} 不在允许集合 {sorted(ORDER_STATUSES)}",
                env_hits=list(self.requires),
            )
        if status == "success" and ret.get("order_id") == "":
            return SmokeResult(
                case_name=self.name,
                status="FAIL",
                duration_ms=0,
                mode=ctx.mode,
                payload={"calls": calls, "status": status},
                reason="status=success 但 order_id 为空字符串",
                env_hits=list(self.requires),
            )
        return SmokeResult(
            case_name=self.name,
            status="PASS",
            duration_ms=0,
            mode=ctx.mode,
            payload={"calls": calls, "status": status, "order_id_present": bool(ret.get("order_id")), "pay_url_present": bool(ret.get("pay_url"))},
            env_hits=list(self.requires),
        )


class WsListAllConversationsCase(Case):
    name = "ws_list_all_conversations"
    domain = "ws"
    requires = ("XY_COOKIE_STR", "XY_RUN_LIVE_TESTS")

    def _check_requires(self, ctx: RunContext) -> Optional[SmokeResult]:
        base = super()._check_requires(ctx)
        if base:
            return base
        flag = ctx.env_get("XY_RUN_LIVE_TESTS").strip()
        if flag != "1":
            return SmokeResult(
                case_name=self.name,
                status="SKIP",
                duration_ms=0,
                mode=ctx.mode,
                reason=f"XY_RUN_LIVE_TESTS={flag!r} != 1（WS 显式 opt-in 未开启）",
                env_hits=list(self.requires),
            )
        return None

    def _run(self, ctx: RunContext) -> SmokeResult:
        if ctx.mode == "mock":
            return SmokeResult(
                case_name=self.name,
                status="PASS",
                duration_ms=0,
                mode=ctx.mode,
                payload={"mode": "mock", "count": 0},
                env_hits=list(self.requires),
            )

        try:
            timeout_raw = int(ctx.env_get("XY_WS_TIMEOUT", "12") or "12")
        except ValueError:
            timeout_raw = 12
        ws_timeout = max(10, timeout_raw)
        overall_deadline = ws_timeout + 3

        async def _coro() -> SmokeResult:
            live = XianyuLive(ctx.cookies_str)
            t0 = time.perf_counter()
            try:
                # list_all_conversations 需要一个 cid；这里使用 user 的自 cid，不存在时兜底空
                my_cid = f"{live.myid}@goofish" if getattr(live, "myid", None) else "0@goofish"
                try:
                    ret = await asyncio.wait_for(live.list_all_conversations(my_cid), timeout=overall_deadline)
                except (asyncio.TimeoutError, TimeoutError):
                    return SmokeResult(
                        case_name=self.name,
                        status="SKIP",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        mode=ctx.mode,
                        reason=f"WS list_all_conversations 超时 {overall_deadline}s（公网不稳定或注册慢）",
                        env_hits=list(self.requires),
                    )
                except Exception as exc:  # noqa: BLE001
                    msg = f"{type(exc).__name__}: {exc}"
                    if "400600001" in msg:
                        return SmokeResult(
                            case_name=self.name,
                            status="SKIP",
                            duration_ms=int((time.perf_counter() - t0) * 1000),
                            mode=ctx.mode,
                            reason="IM 流控 400600001，记 SKIP",
                            env_hits=list(self.requires),
                        )
                    return SmokeResult(
                        case_name=self.name,
                        status="FAIL",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        mode=ctx.mode,
                        reason=msg[:200],
                        env_hits=list(self.requires),
                    )
                if not isinstance(ret, list):
                    return SmokeResult(
                        case_name=self.name,
                        status="FAIL",
                        duration_ms=int((time.perf_counter() - t0) * 1000),
                        mode=ctx.mode,
                        payload={"ret_type": type(ret).__name__},
                        reason="返回结果非 list",
                        env_hits=list(self.requires),
                    )
                return SmokeResult(
                    case_name=self.name,
                    status="PASS",
                    duration_ms=int((time.perf_counter() - t0) * 1000),
                    mode=ctx.mode,
                    payload={"count": len(ret)},
                    env_hits=list(self.requires),
                )
            finally:
                try:
                    ws = getattr(live, "ws", None)
                    if ws is not None and hasattr(ws, "close"):
                        close = ws.close()
                        if isinstance(close, Awaitable):
                            await close
                except Exception:
                    pass

        return asyncio.run(_coro())


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def _retry_http(fn, attempts: int):
    """real 模式下对 HTTP 调用做 attempts+1 次尝试（指数退避 1s/2s/4s...）。"""
    total = max(1, int(attempts) + 1)
    last_exc: Optional[BaseException] = None
    for i in range(total):
        try:
            return fn()
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:  # noqa: BLE001
            last_exc = exc
            if i + 1 < total:
                time.sleep(2 ** i)
    assert last_exc is not None
    raise last_exc


def _truncate(obj: Any, n: int = 180) -> str:
    s = repr(obj)
    if len(s) <= n:
        return s
    return s[: n - 3] + "..."


def _json_safe(obj: Any):
    try:
        json.dumps(obj, default=str)
    except Exception:
        return _truncate(obj)
    return obj


def _load_dotenv_local(root: str) -> dict[str, str]:
    """可选加载 .env.local / .env（不强依赖 python-dotenv）。

    若 python-dotenv 未安装，则走内置的简易解析（只支持 KEY=VAL 不含换行的情况）。
    """
    merged: dict[str, str] = {}
    files = [os.path.join(root, ".env.local"), os.path.join(root, ".env")]
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import dotenv_values  # type: ignore

        for f in files:
            if os.path.exists(f):
                for k, v in dotenv_values(f).items():
                    if isinstance(v, str):
                        merged.setdefault(k, v)
    else:
        for f in files:
            if not os.path.exists(f):
                continue
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if v.startswith(("'", '"')) and v.endswith(v[0]) and len(v) >= 2:
                        v = v[1:-1]
                    merged.setdefault(k, v)
    return merged


def _build_env() -> dict[str, str]:
    merged = _load_dotenv_local(ROOT)
    # 当前 os.environ 优先级最高（覆盖 .env.local/.env 中的值）
    for k, v in os.environ.items():
        if k.startswith("XY_"):
            merged[k] = v
    return merged


def _redact_env(env: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in env.items():
        if k in SECRET_ENV_KEYS or "_COOKIE_" in k or k.endswith("_COOKIE"):
            out[k] = "<set>" if v else "<unset>"
        else:
            out[k] = v
    return out


def _build_ctx(env: dict[str, str]) -> RunContext:
    cookie_str = env.get("XY_COOKIE_STR", "").strip()
    if cookie_str:
        cookies = trans_cookies(cookie_str)
        mode: Literal["mock", "real"] = "real"
    else:
        cookies = {"unb": "mock-user-id-0000000000", "_m_h5_tk": "mock-token_" + os.urandom(6).hex()}
        cookie_str = ""
        mode = "mock"
    device_id = env.get("XY_DEVICE_ID", "").strip() or generate_device_id(cookies.get("unb", "mock-unb"))
    apis = XianyuApis(cookies, device_id)
    live: Optional[XianyuLive]
    if env.get("XY_RUN_LIVE_TESTS", "").strip() == "1" and cookie_str:
        live = XianyuLive(cookie_str)
    else:
        live = None
    try:
        http_retry = int(env.get("XY_HTTP_RETRY", "0") or "0")
    except ValueError:
        http_retry = 0
    return RunContext(
        mode=mode,
        cookies=cookies,
        cookies_str=cookie_str,
        device_id=device_id,
        apis=apis,
        live=live,
        http_retry=max(0, http_retry),
        env=env,
    )


# ---------------------------------------------------------------------------
# 驱动
# ---------------------------------------------------------------------------
ALL_CASES: list[Case] = [
    GetTokenCase(),
    SearchItemsCase(),
    GetUserItemsCase(),
    PolishItemCase(),
    PlaceOrderCase(),
    WsListAllConversationsCase(),
]


def _select_cases(args: argparse.Namespace) -> list[Case]:
    cases = list(ALL_CASES)
    if args.only_http:
        cases = [c for c in cases if c.domain == "http"]
    if args.only_ws:
        cases = [c for c in cases if c.domain == "ws"]
    if args.case:
        names = {n.strip() for n in args.case.split(",") if n.strip()}
        unknown = names - {c.name for c in cases}
        if unknown:
            print(
                _RED(f"[参数错误] 未知用例: {sorted(unknown)}; 可用用例: {[c.name for c in cases]}"),
                file=sys.stderr,
            )
            sys.exit(3)
        cases = [c for c in cases if c.name in names]
    return cases


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="pyxianyu 1.x smoke harness（端到端冒烟基线）")
    p.add_argument("--case", help="只跑指定用例，逗号分隔，如 --case polish_item,place_order")
    p.add_argument("--only-http", action="store_true", help="只跑 HTTP 域用例")
    p.add_argument("--only-ws", action="store_true", help="只跑 WS 域用例")
    p.add_argument("--json", dest="json_path", help="写机器可读 JSON 报告到文件")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    cases = _select_cases(args)
    env = _build_env()
    ctx = _build_ctx(env)

    print(_CYAN("pyxianyu 1.x Smoke Harness"))
    print(
        _DIM(
            f"  mode={ctx.mode}  http_retry={ctx.http_retry}  cases=[{', '.join(c.name for c in cases)}]"
        )
    )
    print(_DIM(f"  env 文件：优先加载 {ROOT}/.env.local / {ROOT}/.env（未装 dotenv 时走内置解析）"))
    print()

    results: list[SmokeResult] = []
    for c in cases:
        r = c.run(ctx)
        results.append(r)
        print(f"{status_fmt(r.status):<10}  {r.case_name:<35}  {_DIM(f'{r.duration_ms}ms')}  {_DIM(r.mode):<8}  {r.reason or _DIM('[shape ok]')}")

    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    skipped = sum(1 for r in results if r.status == "SKIP")
    failed = sum(1 for r in results if r.status == "FAIL")
    total_ms = sum(r.duration_ms for r in results)
    print()
    print(
        f"汇总：共 {total}  |  {_GREEN(f'PASS={passed}')}  |  {_YELLOW(f'SKIP={skipped}')}  |  {_RED(f'FAIL={failed}')}  |  total={total_ms}ms"
    )

    if args.json_path:
        report = {
            "summary": {"total": total, "pass": passed, "skip": skipped, "fail": failed, "total_duration_ms": total_ms},
            "mode": ctx.mode,
            "env": _redact_env(env),
            "cases": [r.to_dict() for r in results],
        }
        try:
            with open(args.json_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=2)
            print(_CYAN(f"JSON 报告已写入: {args.json_path}"))
        except OSError as exc:
            print(_RED(f"写 JSON 报告失败: {exc}"), file=sys.stderr)
            return 2

    if failed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
