## Context

现有测试缺口：
- `tests/test_smoke.py` 仅 import；
- `tests/test_release_readiness.py` 仅 mock 两个方法，未覆盖 polish / render / create / place_order / WS；
- `scripts/` 目录不存在，缺少统一入口给开发者或 CI 跑"整套行为是否还对"。

关键约束：
1. **不能让 harness 自动下真实订单**：`place_order` 必须"只要求结构合法，不要求 status==success"。
2. **不能让 harness 依赖真实凭证也能跑**：缺凭证时要 mock 并完成 shape 校验（HTTP mock 模式）。
3. **WS 连接默认关闭**：因为会连公网，需要 `XY_RUN_LIVE_TESTS=1` 才启。
4. **输出必须对人和 CI 都友好**：人看三色；CI 看退出码 + 可选 JSON 报告。

## Goals / Non-Goals

**Goals：**

1. 覆盖 A1 要求的 6 个用例：get_token、search_items、get_user_items、polish_item、place_order、WS list_all_conversations。
2. 设计为「每个用例 = Case 对象 + run() 返回 Result(case_name, status, duration, payload, reason)」，未来扩展到 8+ API 时只需加一个 Case 子类（不用改 harness 主流程）。
3. 对凭证做「显式 opt-in」：缺少关键 env 就标记 SKIP（不 FAIL），避免 CI 因没凭证变红。
4. `.gitignore` 更新保证 `.env.local` 不会被误提交。

**Non-Goals：**

1. 不把它写成 pytest 用例（避免引入额外依赖，脚本即开即用）。
2. 不做抓包/级联调用（例如 polish 前自动查在售列表、place_order 前自动搜商品）。
3. 不做 API 覆盖率统计（覆盖率统计放到后续 CI 扩展再做）。
4. 不替换/修改现有 `tests/` 下的两个单测，两者并行。

## Decisions

- **决策 1（脚本框架选型）**：纯标准库实现（argparse + dataclasses + 颜色用 ANSI 自绘、`unittest.mock` 按需启用），不加新第三方依赖（不引入 pytest/rich/click），保证 `pip install -e pyxianyu` 之后立刻就能跑。
- **决策 2（Mock vs Real 切换条件）**：当且仅当 `XY_COOKIE_STR` 非空 → 用真实 `requests.Session` 走网络；否则内置 `_MockTransport`，只模拟"ret=SUCCESS/结构合法"的最简数据。这样两类路径各跑一次（本地空环境跑 mock；CI 注入凭证跑 real）。
- **决策 3（place_order 宽松判定）**：`place_order` 用例**只断言**：① 返回值是 dict（或 future Result dataclass）；② 含 `status` 字段且值属于 `{success, yhb_required, account_invalid, failed}`；③ 如果 `status=success`，则 `order_id` 不能是 `""`（None 或非空都 OK，防止空串假阳性）。不要求真实 status==success，避免生成真订单。
- **决策 4（WS 策略）**：需要 `XY_RUN_LIVE_TESTS=1` 才启。连接建立后**最多 15 秒**内完成 `init()` → `list_all_conversations()`；超时时不阻塞整个 harness（标 SKIP，并打印 reason）。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 真实账号 polish 调用写操作，harness 反复跑会触发 POLISH_AGAIN | 无害，但可能误导为"失败" | A1 已将 POLISH_AGAIN 视为幂等成功；harness 同时要求 `success==true` 时 `already_polished ∈ {True, False}`，两种都算 PASS。 |
| 真实 HTTP/WS 调用网络抖动导致偶发 FAIL | 本地 CI 误报 | 对 HTTP 允许 `XY_HTTP_RETRY=2`（默认 0 不重试，可手动设）重试 2 次，指数退避 1s/2s；WS 用例默认 SKIP。 |
| 开发者误将 `.env.local` 提交 | 凭证泄漏 | `.gitignore` 追加 `.env`、`.env.local`、`.env.*.local`；同时 `scripts/smoke_env.example` 头部注释写明"复制为 .env.local，不要提交这个副本"。 |
| mock 模式"总是 PASS"给人一种"接口行为对"的错觉 | 假阳性 | 报告中为每个 case 打印 `mode=mock|real`，且 README 明确说明"mock 模式只验证 shape，不验证协议真实有效"；CI 若注入凭证会自动切到 real 模式。 |
