# 如何新增一个 HTTP API（MTop）

## 目标

当你需要新增/扩展一个 mtop 接口时，按此流程可把“抓包 → 文档 → 代码 → 测试”闭环做完整，降低后续维护成本。

## 步骤

### 1. 抓包取证

- 打开 `https://www.goofish.com/` 对应页面
- DevTools → Network 过滤 `h5/mtop.`
- 记录：
  - URL（含 `/h5/<api>/<v>/`）
  - query 参数（`api/v/appKey/t/sign/sessionOption/spm_*`）
  - body 的 `data` 原文（字符串）
  - 响应的 `ret` 与 `data` 关键字段

### 2. 写 docs 记录

在 `docs/` 新建 `mtop_<api-name>.md`，建议包含：

- 目的
- 取证来源（页面、前端资源、抓包）
- 请求信息（URL/query/body）
- 响应结构（示例）
- 已验证行为（分页/排序/边界条件）
- 当前用途（对应到仓库代码位置）

参考：

- `docs/mtop_idle_web_xyh_item_list.md`
- `docs/mtop_idle_web_user_page_nav.md`

### 3. 加 URL 常量（如需要）

如果是一个新 URL（不是复用既有网关），在 `core/client.py` 初始化里加入：

- `self.<xxx>_url = "https://h5api.m.goofish.com/h5/<api>/<v>/"`

### 4. 增加 API 封装

在 `apis/` 增加/扩展一个 `*_api.py`：

- 调用 `client.build_mtop_params(api=..., ...)`
- 调用 `client.post_json(url, params=params, data_val="<json string>")`
- `client.parse_json_response` + `client.ensure_api_success`

### 5. 增加测试

优先用 fake client（不发网络）验证两件事：

- 生成的 URL / params / data_val 正确
- 解析与 success 判断路径正确

参考：

- `tests/test_user_profile.py`

## 常见坑

- `data` 必须是 JSON 字符串并与签名一致
- `_m_h5_tk` 缺失会导致签名失败（看起来像“接口坏了”，实际是登录态问题）
- 调用频率过高可能触发 `FAIL_SYS_USER_VALIDATE`（上层服务应做限速/护栏）
