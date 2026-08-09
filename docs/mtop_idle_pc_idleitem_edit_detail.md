# `mtop.idle.pc.idleitem.editDetail` 接口记录

## 目的

用于读取指定商品在 PC 编辑页中的可编辑详情数据，是“重新上架/重发布”链路的核心前置接口。

## 取证来源

### 浏览器页面

- 页面：`https://www.goofish.com/publish?itemId=1061041326003`
- 页面初始化后会自动触发该请求。

### 前端源码定位

- 来源文件：`https://g.alicdn.com/idle-pc/xy-site/0.0.168/js/p_publish-index.js`
- 命中片段：

```js
window.lib.mtop.request({
  api: "mtop.idle.pc.idleitem.editDetail",
  data: { itemId: "1061041326003" }
})
```

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.editDetail/1.0/
```

### Body

```json
{
  "itemId": "1061041326003"
}
```

## 响应结构

本次浏览器样本已确认这些关键字段存在：

```json
{
  "itemId": "1061041326003",
  "itemStatus": "1",
  "simpleItem": "true",
  "itemTextDTO": {},
  "itemPriceDTO": {},
  "itemPostFeeDTO": {},
  "itemCatDTO": {},
  "itemLabelExtList": [],
  "userRightsProtocols": [],
  "imageInfoDOList": [],
  "itemAddrDTO": {},
  "canBargain": "true",
  "supportBargainPrice": "true",
  "redirectUrl": "",
  "jumpUrl": ""
}
```

其中实测字段示例包括：

```json
{
  "itemPriceDTO": {
    "priceInCent": "12000",
    "origPriceInCent": "0"
  },
  "itemAddrDTO": {
    "prov": "...",
    "city": "...",
    "area": "...",
    "gps": "..."
  },
  "itemCatDTO": {
    "catId": "...",
    "catName": "...",
    "channelCatId": "..."
  },
  "itemPostFeeDTO": {
    "canFreeShipping": "...",
    "postPriceInCent": "..."
  },
  "imageInfoDOList": [],
  "itemTextDTO": {
    "title": "...",
    "desc": "..."
  }
}
```

实际响应里还可能带有：

- `itemAddrDTO`
- `itemGroupDTO`
- `itemTopicParams`
- `baseParams`
- `asyncSecurityInfo`
- `bizcode`
- `bucketId`
- `scene`

## 已验证行为

- 该接口确实由 PC 编辑页自动调用。
- 编辑页最终会把该接口返回的数据转换后，再提交给 `mtop.idle.pc.idleitem.edit`。

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py`：底层 `editDetail` 封装
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py`：统一 API 聚合入口
- `.mcp/XianYuApis_MCP/tools/xianyu_api_tools.py`：提供 `get_item_edit_detail`
- `.mcp/XianYuApis_MCP/server.py`：对外暴露 `get_item_edit_detail` MCP 工具
