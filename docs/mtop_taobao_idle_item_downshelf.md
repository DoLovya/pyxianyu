# `mtop.taobao.idle.item.downshelf` 接口记录

## 目的

用于将当前登录账号名下的指定商品执行下架操作。

本仓库已通过浏览器自动化确认：PC 商品详情页点击“下架”并在弹窗中确认后，会触发该接口。

## 取证来源

### 浏览器网络抓包

- 页面：`https://www.goofish.com/item?spm=a21ybx.personal.feeds.2.1b866ac29oNhur&id=897705472395&categoryId=50023914`
- 触发动作：
  1. 打开本人商品详情页
  2. 点击“下架”
  3. 在确认弹窗中点击“确定”
- 关键请求：
  - `POST https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.downshelf/2.0/`

### 前端源码定位

来源文件：

- `https://g.alicdn.com/idle-pc/xy-site/0.0.168/js/p_item-index.js`

运行时拦截到的前端封装参数：

```js
{
  api: "mtop.taobao.idle.item.downshelf",
  v: "2.0",
  data: {
    itemId: "897705472395"
  }
}
```

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.downshelf/2.0/
```

### Query 参数

```text
jsv=2.7.2
appKey=34839810
v=2.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=mtop.taobao.idle.item.downshelf
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.item.0.0
spm_pre=a21ybx.personal.feeds.2.1b866ac29oNhur
log_id=1b866ac29oNhur
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

表单字段：

```text
data=<JSON 字符串>
```

请求示例：

```json
{
  "itemId": "897705472395"
}
```

## 响应结构

抓包成功响应：

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "needDecryptKeys": [],
    "needDecryptKeysV2": [],
    "serverDecryptKeys": [],
    "serverTime": "2026-07-14 01:44:46",
    "success": true
  },
  "traceId": "215044ec17839646860616801e0ff5",
  "v": "2.0"
}
```

顶层关键字段：

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "success": true
  }
}
```

## 已验证行为

- 该接口由 PC 商品详情页卖家态“下架”按钮触发
- 需要先经过一次确认弹窗
- 当前抓包样本中，请求体仅包含 `itemId`
- 成功后页面按钮文案变为“已下架”

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py`：底层下架接口封装
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py`：统一 API 聚合入口
- `.mcp/XianYuApis_MCP/tools/xianyu_api_tools.py`：MCP 工具聚合
- `.mcp/XianYuApis_MCP/server.py`：对外暴露 `downshelf_item` 工具
