# Snaplii Gateway — `getAllCardTags` API 接口文档

## 1. 概览

| 项 | 值 |
| --- | --- |
| URL | `POST /mrpay/getAllCardTags.do` |
| Content-Type | `application/json` |
| 鉴权 | 需要有效 session cookie（匿名访问请先走游客登录流程获得 session） |
| 用途 | 一次性拉取首页/送礼页上所有**卡标签（tag）**，每个 tag 下附带若干品牌摘要，是 App 首页"分类瀑布流"的数据源 |

## 2. 请求

### 业务字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `channel` | string | 否 | 访问入口。默认 `HOME_PAGE`；`SEND_GIFT` 表示送礼场景（返回的 tag/品牌面向礼品场景） |
| `locationProv` | string | 否 | 省份代码，如 `ON` / `QC`；用于地域化 tag 排序 |

### 必填公共字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `deviceInfo.deviceId` | string | 设备指纹，必填 |
| `deviceInfo.appLanguage` | string | 响应文案语言，如 `en` / `zh` |
| `deviceInfo.longitude` / `deviceInfo.latitude` | string | 可选；有值时会用于地域化 tag 排序 |

## 3. 响应

### 公共字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `rspMsgCd` | string | 业务返回码（成功为 `MCA00000`） |
| `rspMsgInf` | string | 返回码描述 |
| `serviceTime` | string | 服务器时间 |

### 业务字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data` | `CardTagDetail[]` | tag 列表 |

**`CardTagDetail`：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cardTagNo` | string | tag 编号（可作为 `/mrpay/queryBrands` 的 `cardTagId` 入参） |
| `name` | string | tag 名称（按 `appLanguage` 本地化） |
| `subtitle` | string | 副标题 |
| `tofuImageUrl` | string | 方块图（首页瀑布流用） |
| `categoryImageUrl` | string | 分类图 |
| `cardBrands` | `CardBrandSummary[]` | tag 下的品牌摘要（可直接用于展示，避免再次调用 `queryBrands`） |

**`CardBrandSummary`**（简要）：`cardBrandId`、`name`、`alternativeName`、`logoUrl`、`imageUrl`、`bestDiscount`、`allSameDiscount`、`regularDiscount`、`benefitType`。

## 4. 常见返回码

| code | 含义 |
| --- | --- |
| `MCA00000` | 成功 |
| `MCAP9999` | 会话失效或所在国家/区域不被支持 |
| `MACP6006` | 下游服务调用失败 |

## 5. 请求示例

```bash
curl -X POST https://<host>/mrpay/getAllCardTags.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{
    "channel": "HOME_PAGE",
    "locationProv": "ON",
    "deviceInfo": {
      "deviceId": "device-fingerprint-xxx",
      "appLanguage": "en",
      "longitude": "-79.3832",
      "latitude": "43.6532"
    }
  }'
```

## 6. 响应示例

```json
{
  "rspMsgCd": "MCA00000",
  "rspMsgInf": "Success",
  "serviceTime": "20260422164300",
  "data": [
    {
      "cardTagNo": "12",
      "name": "Food & Dining",
      "subtitle": "Coffee, fast food & more",
      "tofuImageUrl": "https://cdn.snaplii.com/tags/food-tofu.png",
      "categoryImageUrl": "https://cdn.snaplii.com/tags/food-cat.png",
      "cardBrands": [
        {
          "cardBrandId": "CB0000000000135",
          "name": "Tim Hortons",
          "alternativeName": "Tims",
          "logoUrl": "https://cdn.snaplii.com/brands/tim-logo.png",
          "imageUrl": "https://cdn.snaplii.com/brands/tim-cover.png",
          "bestDiscount": 0.08,
          "allSameDiscount": false,
          "regularDiscount": 0.05,
          "benefitType": "DISCOUNT"
        }
      ]
    },
    {
      "cardTagNo": "34",
      "name": "Shopping",
      "subtitle": "Apparel, electronics & more",
      "tofuImageUrl": "https://cdn.snaplii.com/tags/shop-tofu.png",
      "categoryImageUrl": "https://cdn.snaplii.com/tags/shop-cat.png",
      "cardBrands": []
    }
  ]
}
```
