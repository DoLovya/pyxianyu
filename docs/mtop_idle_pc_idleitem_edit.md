# `mtop.idle.pc.idleitem.edit` 接口记录

## 目的

用于在 PC 编辑页提交已有商品的修改。对于已下架商品，这条链路可以作为“重新上架/重发布”的实现入口。

## 取证来源

### 前端源码定位

- 来源文件：`https://g.alicdn.com/idle-pc/xy-site/0.0.168/js/p_publish-index.js`
- 浏览器验证页面：`https://www.goofish.com/publish?itemId=1061041326003`
- 命中片段：

```js
window.lib.mtop.request({
  api: "mtop.idle.pc.idleitem.edit",
  data: {
    ...payload,
    uniqueCode: "<运行时生成>",
    sourceId: "<页面来源>",
    bizcode: "pcMainPublish",
    publishScene: "pcMainPublish"
  }
})
```

页面按钮逻辑已确认：

- 有 `itemId` 时走 `mtop.idle.pc.idleitem.edit`
- 无 `itemId` 时走 `mtop.idle.pc.idleitem.publish`

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.edit/1.0/
```

### Body 关键字段

```json
{
  "itemId": "1061041326003",
  "uniqueCode": "<uuid>",
  "sourceId": "<来源，仓库默认回退到 itemId>",
  "bizcode": "pcMainPublish",
  "publishScene": "pcMainPublish",
  "itemTextDTO": {},
  "itemPriceDTO": {},
  "itemPostFeeDTO": {},
  "itemCatDTO": {},
  "itemLabelExtList": [],
  "userRightsProtocols": []
}
```

从前端 bundle 进一步确认的字段映射：

- 金额字段提交前会转成“分”：
  - `itemPriceDTO.origPriceInCent`
  - `itemPriceDTO.priceInCent`
  - `itemPostFeeDTO.postPriceInCent`
- 布尔字段会标准化：
  - `itemPostFeeDTO.canFreeShipping`
  - `itemPostFeeDTO.supportFreight`
  - `itemPostFeeDTO.onlyTakeSelf`
  - `userRightsProtocols[].enable`
- 编辑详情样本里还观察到可直接沿用的字段：
  - `canBargain`
  - `supportBargainPrice`
  - `imageInfoDOList`
  - `itemAddrDTO`

## 当前验证状态

- 已确认这是 PC 端编辑已有商品的真实提交接口。
- 由于当前抓包样本所属类目不支持网页端发布，尚未在浏览器中拿到一次成功的 `edit` 提交样本。
- 因此仓库实现采用“`editDetail` 原样抽取 + 最小必要标准化”的方式构造 payload，并保留 `source_id` 可覆盖入口。

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py`：底层 `edit` 与高层 `reshelf_item` 封装
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py`：统一 API 聚合入口
- `.mcp/XianYuApis_MCP/tools/xianyu_api_tools.py`：提供 `reshelf_item`
- `.mcp/XianYuApis_MCP/server.py`：对外暴露 `reshelf_item` MCP 工具
