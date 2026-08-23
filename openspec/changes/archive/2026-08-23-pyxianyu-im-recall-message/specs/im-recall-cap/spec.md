## ADDED Requirements

### Requirement: recall_message 路由正确发送 body 数组位置正确，并按 `[message_id]` 格式发送

The system SHALL send recall via lwp `/r/MessageManager/recallMessage` the `body=[message_id] (a single-element list containing the string returned by the last send_msg receipt.

#### Scenario: 正常撤回自己 2 分钟内
- **WHEN** recall_message(ws, receipt.messageId)` in 2 分钟
- **THEN** success=True

#### Scenario: 发送时 message_id=空串
- **WHEN** message_id=""
- **THEN** 抛 `ValueError("message_id 不能为空"（避免瞎发）

### Requirement: 文档齐全，脱敏，供后续参考
- **WHEN** 完成变更时
- **THEN** `docs/protocol_ws_im_recall.md 存在，按规范 6 节结构，mid、message_id 均为占位符 <mid>/<message_id>

### Requirement: 测试覆盖解析，不真连公网
- **WHEN** unit tests run
- **THEN** 测试 mock websocket，不建真实网络依赖。
