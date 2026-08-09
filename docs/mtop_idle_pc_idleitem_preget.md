# `mtop.idle.pc.idleitem.preget` 接口记录

## 目的

用于在 PC 编辑/发布页初始化时拉取发布前置配置，供后续表单渲染和校验使用。

## 取证来源

### 浏览器页面

- 页面：
  - `https://www.goofish.com/publish`
  - `https://www.goofish.com/publish?itemId=1061041326003`
- 两个页面初始化后都会自动触发该请求。

### 前端源码定位

- 来源文件：`https://g.alicdn.com/idle-pc/xy-site/0.0.168/js/p_publish-index.js`
- 命中片段：

```js
window.lib.mtop.request({
  api: "mtop.idle.pc.idleitem.preget",
  data: {}
})
```

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.preget/1.0/
```

### Body

```json
{}
```

## 响应关注点

- 本次浏览器样本里，响应关键字段包括：

```json
{
  "commissionConfig": {
    "percent": "0.016",
    "commissionTitle": "预估鱼小铺软件服务费 (1.6%)"
  },
  "supportSkuOrInventory": "true",
  "needUpFirstHandItem": "false",
  "violationInfo": {
    "hasViolation": "false"
  }
}
```

- 该接口返回发布页初始化所需的辅助配置。
- 当前仓库只做底层封装，暂未把它直接暴露为 MCP 工具。

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py`：预取配置接口封装
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py`：统一 API 聚合入口
