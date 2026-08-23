# MTop 接口：收货地址列表 — `mtop.taobao.idle.logistic.address.list.query` v1.0

> 取证日期：2026-08-23
> 取证来源：`zhinianboke/xianyu-auto-reply@main` 中 `common/services/xianyu_order_client.py::_get_default_address_id()`
> 实现代码位置：[trade_api.py](file:///Users/huan.zhang/Code/xianyu-code/xianyu-mcp-server/third_party/pyxianyu/src/pyxianyu/apis/trade_api.py#L66-L110)（`TradeApi.get_address_list`）

---

## 1. 目的

查询闲鱼账号已配置的所有收货地址，返回 `addressList`，并按 **`status == 1` 优先**的规则选取**默认地址**（没有 status==1 时取列表第一个）。验货宝下单（§3.5/§3.6）需要此方法获取 `buyerAddressId`。

---

## 2. 请求

- **API**：`mtop.taobao.idle.logistic.address.list.query`
- **版本**：`1.0`
- **URL**：`https://h5api.m.goofish.com/h5/mtop.taobao.idle.logistic.address.list.query/1.0/`
- **方法**：`POST`（`application/x-www-form-urlencoded`）
- **签名**：标准 MTop sign（appKey=34839810，token 取 `_m_h5_tk` 按下划线切分第一段）。

### 2.1 请求 data_val（空对象）

```json
{}
```

> 不需要任何参数，直接空对象 `data={}` 提交即可。

### 2.2 其它 MTop 固定参数

| 字段 | 示例值 |
|---|---|
| `spm_cnt` | `a21ybx.order.0.0` |
| `spm_pre` | `a21ybx.order.address.1.f00bar` |
| `log_id` | `xianyu_address_list` |

---

## 3. 响应

### 3.1 正常结构

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "data": {
      "addressList": [
        {
          "addressId": 123456789,
          "status": 1,
          "fullName": "张三",
          "mobile": "138****1234",
          "province": "浙江省",
          "city": "杭州市",
          "area": "西湖区",
          "detailAddress": "文三路 100 号 A 座 501",
          "postCode": null
        },
        {
          "addressId": 987654321,
          "status": 0,
          "fullName": "李四",
          "mobile": "139****0000",
          "province": "上海市",
          "city": "上海市",
          "area": "浦东新区",
          "detailAddress": "陆家嘴金融中心 18F",
          "postCode": null
        }
      ]
    }
  }
}
```

### 3.2 关键字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `addressId` | int | 地址唯一 ID，验货宝 create 时作为 `buyerAddressId` 传入 |
| `status` | int | `1` = 默认地址/正常；其它值可能是历史地址；默认地址优先选 status==1，否则取列表第一个 |
| `fullName` / `mobile` / `province` / `city` / `area` / `detailAddress` | string | 收货人、手机（脱敏）、省、市、区、详细地址 |

---

## 4. 验证方法

- 单元测试：tests/test_trade_yhb.py 中 `GetAddressListTest`（3 条：status==1 默认、空列表 default=None、TOKEN_EXPIRED 抛错）。
- 三件套：`python -m compileall -q src scripts tests` → 0 错误，`unittest discover` ≥ 19 条 OK，`smoke_1_0.py` 退出码 0。

---

## 5. 用途

1. **验货宝下单**：`place_order_yhb(item_id)` 步骤 1，自动取默认地址的 `addressId`。
2. **用户地址管理**：上层 UI 或任务调度可以展示用户的完整收货地址列表，支持调用方手动选一个非默认地址下单（`place_order_yhb(..., buyer_address_id=<x>)`）。
