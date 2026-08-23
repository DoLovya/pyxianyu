# `mtop.taobao.idle.item.polish` 接口记录

## 目的

用于将当前登录账号名下的指定在售商品执行「擦亮」（重新上架），每个商品每日限擦亮 1 次；今日已擦亮时，重复调用会返回幂等成功。

本实现取证来源：
- 外部仓库 `zhinianboke/xianyu-auto-reply`，文件 `scheduler/app/services/scheduler/polish_task.py::_polish_item()`

## 取证来源

### 外部源码定位

参考调用：
- `api = "mtop.taobao.idle.item.polish"`
- `v = "2.0"`
- 调用方式：`POST https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.polish/2.0/`，请求 data 表单：`{"itemId": "<item_id>"}`
- spm_cnt：`a21ybx.item.0.0`，spm_pre：`a21ybx.personal.feeds.1.42f86ac21eZ9zd`

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.taobao.idle.item.polish/2.0/
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
api=mtop.taobao.idle.item.polish
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.item.0.0
spm_pre=a21ybx.personal.feeds.1.42f86ac21eZ9zd
log_id=42f86ac21eZ9zd
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

```json
{
  "itemId": "7891234567"
}
```

## 响应结构

### 首次擦亮成功

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "success": true
  }
}
```

### 今日已擦亮（幂等成功，视为 success=true）

```json
{
  "ret": ["FAIL_BIZ_IDLEITEM_POLISH_AGAIN::宝贝已经擦亮过了，明天再来吧"]
}
```

或：

```json
{
  "ret": ["FAIL_BIZ_IDLEITEM_POLISH_AGAIN::一天只能擦亮一次哦"]
}
```

### 商品已下架

```json
{
  "ret": ["FAIL_BIZ_UNSUPPORTED_ITEM_STATUS::已下架商品不支持该操作"]
}
```

## 已验证行为

- `IDLEITEM_POLISH_AGAIN` / `宝贝已经擦亮过了` / `一天只能擦亮一次` 任一关键词出现时，本仓库视为**幂等成功**，不抛异常，返回 `already_polished: true`。
- `UNSUPPORTED_ITEM_STATUS` / `已下架商品不支持该操作` 由调用方自行处理（xianyu-auto-reply 中会删除本地商品记录）。

## 验证状态

⏳ 待验证（外部仓库生产环境调用，尚未在本项目做浏览器自动化抓包交叉验证）

## 当前在仓库中的用途

- `third_party/pyxianyu/src/pyxianyu/apis/item_api.py::ItemApi.polish_item(item_id)`：底层实现
- `third_party/pyxianyu/src/pyxianyu/xianyu_apis.py::XianyuApis.polish_item(item_id)`：统一门面
