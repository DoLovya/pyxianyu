# `mtop.idle.web.user.page.nav` 接口记录

## 目的

用于获取当前登录用户的个人页导航/个人信息相关数据（通常包含昵称、头像、地区、卖家信息等，具体字段以实际返回为准）。

本仓库将其作为上层 `get_my_profile` 工具的底层数据源。

## 取证来源

### 代码实现基线（XianYuClient）

- 仓库：`https://github.com/DoLovya/XianYuClient`
- 方法：`GetUserPageNavDataAsync`
- API：`mtop.idle.web.user.page.nav`
- URL：`https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/`
- `data`：`{}`

### 浏览器网络抓包

可在访问闲鱼个人页/导航相关页面时观察到该请求（不同账号/AB 实验可能存在差异）：

- 页面：`https://www.goofish.com/personal`
- 关键请求：
  - `POST https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/`

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.web.user.page.nav/1.0/
```

### Query 参数（常见）

```text
jsv=2.7.2
appKey=34839810
v=1.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=mtop.idle.web.user.page.nav
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.personal.0.0
spm_pre=a21ybx.im.nav.1.4deb4f10uD9XhK
log_id=4deb4f10uD9XhK
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

表单字段：

```text
data={}
```

## 响应结构（示意）

该接口的 `data` 内字段可能随版本与 AB 实验变动，建议以 raw 透传为主。常见返回形态：

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "...": "..."
  }
}
```

`pyxianyu` 上层会“尽力提取”以下字段用于展示（缺失不报错）：

- `user_id`
- `nick`
- `avatar_url`
- `location`
- `seller_level`
- `seller_score`

## 当前在仓库中的用途

- `third_party/pyxianyu/apis/user_api.py`：封装该接口并返回原始响应
- `xianyu-mcp-server`：通过 `get_my_profile` 工具对外暴露（结构化 `profile` + 原始 `raw`）
