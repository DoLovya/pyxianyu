# MTop 协议说明（闲鱼 Web / PC 端）

## 目的

整理 `pyxianyu` 所调用的闲鱼 Web/PC 端 MTop（mtop.*）接口的通用协议形态，便于：

- 新增/扩展接口时快速对齐请求格式
- 排查常见鉴权与风控类错误
- 解释 `client.py` 内的签名与参数拼装逻辑

## 取证来源

- 浏览器网络抓包（`https://www.goofish.com/`）
- 前端资源与接口形态（h5api 网关）
- 本仓库现有 `third_party/pyxianyu/core/client.py` 的实现与已有 API 文档

## 基本形态

### 目标网关

MTop 接口通常通过以下网关访问：

```text
https://h5api.m.goofish.com/h5/<api-name>/<version>/
```

示例：

```text
https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/
```

### 请求方式

- HTTP 方法：`POST`
- Body：表单字段 `data=<JSON 字符串>`
- Query：携带 `api/v/appKey/t/sign/...` 等参数

## 通用 Query 参数

不同接口会有少量差异，但常见参数集合如下（以抓包为准）：

```text
jsv=2.7.2
appKey=34839810
v=1.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=<mtop api name>
sessionOption=AutoLoginOnly
spm_cnt=<埋点>
spm_pre=<埋点>
log_id=<埋点>
t=<毫秒时间戳>
sign=<签名>
```

其中：

- `appKey`：Web/PC 端常见为 `34839810`
- `t`：毫秒时间戳字符串
- `sign`：基于 token + t + data 生成的签名
- `sessionOption=AutoLoginOnly`：与登录态有关（非必须但常见）
- `spm_* / log_id`：埋点参数，通常不影响业务结果，但建议保留与浏览器一致的默认值

## Body: data 字段

Body 使用 `application/x-www-form-urlencoded` 表单提交：

```text
data=<JSON 字符串>
```

示例：

```json
{"pageNumber":1,"pageSize":20}
```

注意：

- `data` 在签名计算中会以“字符串形式”参与计算
- `data` 的 key 顺序可能影响签名（具体取决于实现），因此应保持 `client.py` 中的序列化方式一致

## 认证与 token

### Cookie

至少需要浏览器已登录 `goofish.com` 的 Cookie。常见关键项包括：

- `cookie2`
- `_tb_token_`
- `unb`
- `cna`
- `_m_h5_tk` / `_m_h5_tk_enc`（极关键，影响 sign）

本仓库上层（xianyu-mcp-server）支持扫码登录自动补齐这些字段。

### `_m_h5_tk` 参与签名

典型 `_m_h5_tk` 格式：

```text
<token>_<timestamp>
```

签名计算通常依赖其中的 `<token>` 部分（不同实现细节略有差异）。

## 响应结构

MTop 响应通常形态：

```json
{
  "api": "mtop.xxx",
  "ret": ["SUCCESS::调用成功"],
  "data": { }
}
```

错误时：

```json
{
  "ret": ["FAIL_SYS_USER_VALIDATE::用户验证失败"]
}
```

## 常见错误与排查

### `FAIL_SYS_USER_VALIDATE`

含义：强鉴权/风控信号，常见于 Cookie 失效、需要人脸验证、或调用节奏异常被风控。

排查建议：

- 先在上层通过扫码登录刷新 Cookie
- 控制调用频率（读写分离限速）
- 若提示人脸验证，需在浏览器完成验证后再继续

### `ILLEGAL_ACCESS` / `FAIL_SYS_TOKEN_EXOIRED`

含义：token/签名相关问题（token 过期、签名参数不一致等）。

排查建议：

- 检查 `_m_h5_tk` / `_m_h5_tk_enc` 是否存在且最新
- 检查 `t` 与 `sign` 是否由同一套 `data` 生成

## 在 pyxianyu 中的实现映射

- 请求参数与签名：`third_party/pyxianyu/core/client.py`
- 接口封装：`third_party/pyxianyu/apis/*.py`
- API 记录与取证：`third_party/pyxianyu/docs/*.md`
