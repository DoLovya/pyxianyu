# `mtop.idle.pc.idleitem.prepublish.check` 接口记录

## 目的

用于在 PC 编辑/发布页初始化时预检查当前商品是否允许网页端发布。

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
  api: "mtop.idle.pc.idleitem.prepublish.check",
  data: {}
})
```

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.pc.idleitem.prepublish.check/1.0/
```

### Body

```json
{}
```

## 响应关注点

- 本次浏览器样本返回：

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "limited": "false"
  }
}
```

- 页面会根据响应结果决定是否允许继续网页端发布。

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py`：预检查接口封装
- `third_party/pyxianyu/src/pyxianyu/goofish_apis.py`：统一 API 聚合入口
