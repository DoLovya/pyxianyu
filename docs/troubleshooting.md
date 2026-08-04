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
- 对照 `goofish_live.py` 的 headers 形态补齐

## 图片上传返回 `TYPE_NOT_CONFIRMED`

该错误通常表示上传网关对文件头/MIME 有强校验（例如拒绝 MP4）。

处理建议：

- 确认上传的是图片格式（jpg/png/webp 等）
- 确认文件扩展名与文件头匹配
