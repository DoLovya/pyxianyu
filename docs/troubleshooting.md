# Troubleshooting

## `FAIL_SYS_USER_VALIDATE`

表现：

- 返回 `ret` 包含 `FAIL_SYS_USER_VALIDATE`
- 或上层提示需要用户验证/人脸验证

常见原因：

- Cookie 失效/过期
- 需要人脸验证（高风险操作、异地登录、频繁请求）
- 调用节奏过快被风控

处理建议：

- 通过上层的扫码登录刷新 Cookie（建议自动补齐 `_m_h5_tk`）
- 降低调用频率（尤其是写操作）
- 在浏览器完成验证后再继续调用

## `FAIL_SYS_TOKEN_EXOIRED` / `ILLEGAL_ACCESS`

常见原因：

- `_m_h5_tk` 过期或缺失，导致 `sign` 无法通过校验
- `t`、`data` 与 `sign` 不一致（签名计算与实际请求 data 不一致）

处理建议：

- 重新获取登录态 Cookie，确保 `_m_h5_tk` / `_m_h5_tk_enc` 存在
- 确认 `data` 的序列化方式与签名一致（保持 `client.py` 逻辑）

## WebSocket 连接失败

常见原因：

- Cookie 无效（无法拿到 token 或被网关拒绝）
- 代理/网络阻断（公司网络、WSS 域名不可达）
- headers 不完整（缺 Origin / Cookie）

处理建议：

- 先确保 HTTP 的 `get_token()` 返回成功
- 检查网络是否允许访问 `wss://wss-goofish.dingtalk.com/`
- 对照 `src/pyxianyu/xianyu_live.py` 的 headers 形态补齐

## 图片上传返回 `TYPE_NOT_CONFIRMED`

该错误通常表示上传网关对文件头/MIME 有强校验（例如拒绝 MP4）。

处理建议：

- 确认上传的是图片格式（jpg/png/webp 等）
- 确认文件扩展名与文件头匹配

## Smoke Harness（`scripts/smoke_1_0.py`）常见 FAQ

### 1. 为什么很多用例显示 SKIP？
Harness 使用「显式 opt-in」策略。缺任一关键 env（如 `XY_COOKIE_STR`/`XY_TEST_ITEM_ID`/`XY_RUN_ORDER_TESTS=1`/`XY_RUN_LIVE_TESTS=1`）就会标记 SKIP，避免无凭证时触发 FAIL。
解决方式：复制 `scripts/smoke_env.example` 为 `.env.local` 并按需填写。

### 2. WS 用例默认不跑（提示需要 `XY_RUN_LIVE_TESTS=1`）
WS smoke 会发起公网连接（`wss://wss-goofish.dingtalk.com`），CI 与本地默认都关闭。需要调试 IM 链路时请手动设置 `XY_RUN_LIVE_TESTS=1`。

### 3. `place_order` 返回 `status=failed` 或 `status=yhb_required`，为什么仍然 PASS？
Harness 的目标是**验证调用面不抛异常 + 返回结构合法**，而不是保证下单成功。否则反复跑 harness 会产生大量真实未付款订单，也会因商品是验货宝专属而误报。

判定通过的三条规则：
1. 不抛未捕获异常；
2. 返回对象含 `status` 字段且值 ∈ `{success, yhb_required, account_invalid, failed}`；
3. 若 `status=success`，`order_id` 不能是空字符串。

需要对真实下单成功率做监控时，请在上层业务做专门的冒烟任务，不要用 Harness。

### 4. 遇到 IM 流控错误码 `400600001`，Harness 怎么判？
- HTTP 域（polish/order）可通过 `XY_HTTP_RETRY=2` 自动重试 2 次（指数退避 1s/2s）；
- WS 域的会话列表或心跳返回 400600001，则当前 WS case 会记为 **SKIP** 而非 FAIL，避免 CI 偶发抖动。
