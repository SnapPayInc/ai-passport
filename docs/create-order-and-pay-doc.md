# Snaplii Gateway — `createOrderAndPay` (v2) API 接口文档

## 1. 概览

| 项 | 值 |
| --- | --- |
| URL | `POST /mrpay/transaction/v2/createOrderAndPay.do` |
| 路由 `txn_cod` | `createOrderAndPay` |
| Spring 实现 | `CreateOrderAndPayAction`（`external-gateway-web/.../pay/web/action/transaction/CreateOrderAndPayAction.java`） |
| `check_session` | `true`（必须已登录） |
| Content-Type | `application/json` |
| 最低 App 版本 | `4.8.0`（`deviceInfo.clientVer < 4.8.0` 将返回 `APP_VERSION_NOT_SUPPORT`） |
| 用途 | 一次性完成"**创建订单 → 支付 → 发货**"三步；若前端已创建好订单，也可携带 `orderNo` 跳过创建阶段 |

### 处理流程

1. 校验 App 版本（`< 4.8.0` 直接拒绝）。
2. 从 session 取 `usr_no`；`usr_no` 为空返回 `USR_NOT_EXIST`。
3. 参数校验（`ParamCheckUtils.checkParam`）。
4. 补齐 `publicIp` / `deviceInfo` 并把 `deviceInfo` 写入 Redis（10 分钟 TTL），key 为 `DEVICE_INFO_<usr_no>`，供风控使用。
5. 若 `orderType = P70_RECHARGE` 且传入 `verificationId`，调 `VerificationChecker.isVerified` 做强验证。
6. `orderNo` 为空 → 先建单（`transactionService.createOrder`）；非空 → 直接按已有订单走。
7. 查询订单详情，确认订单属于当前用户且状态为 `WAIT_PAYMENT`；否则返回 `ORDER_STATUS_INCORRECT`。
8. `P70_RECHARGE` 额外做充值额度校验（`benefitService.checkIfReachRechargeQuota`）。
9. 调 `transactionService.payAndDeliver` 真正扣款并发货；抛异常时把错误码/描述回填到响应。
10. `TOP_UP` 且 `orderStatus = SUCCESS` 时，追加"用户订阅商户"记录、给推广员记流水 / 发短信。

## 2. 请求体

### 顶层业务字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `orderInfo` | object | 是 | 订单信息，详见 [2.1 orderInfo](#21-orderinfo) |
| `paymentContext` | object | 是 | 支付上下文，详见 [2.2 paymentContext](#22-paymentcontext) |
| `delivery` | object | 是 | 发货信息，详见 [2.3 delivery](#23-delivery) |
| `orderNo` | string | 否 | 已有订单号；传入时跳过"建单"阶段，直接支付该订单 |
| `transactionTrackNo` | string | 否 | 透传的业务跟踪号；不传则网关生成 |
| `verificationId` | string | 否 | `P70_RECHARGE` 场景下用于强验证（与 `VerificationChecker` 对应） |
| `riskSessionId` | string | 否 | 风控 session id（透传给下游风控） |
| `locationProv` | string | 是/建议 | 省份代码（`McaAbstractBaseReqBO` 公共字段），例如 `ON`、`QC`、`BC`；风控/税务规则使用 |

> `mblNoCipher`、`userNo`、`country` 等字段是**网关内部填充**，**请勿由调用方传入**（由 session 和服务端完成）。

### 必填公共字段（`McaAbstractBaseReqBO` / `McaDeviceInfoBO`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `deviceInfo.deviceId` | string | 设备指纹，`@ECPNotEmpty` |
| `deviceInfo.clientVer` | string | App 客户端版本，本接口**必须 ≥ 4.8.0** |
| `deviceInfo.publicIp` / 顶层 `publicIp` | string | 真实公网 IP；写入 Redis 设备信息，风控 / IP 画像使用 |
| `businessInfo.appLanguage` 或 `deviceInfo.appLanguage` | string | 下游文案语言（示例沿用 `businessInfo.appLanguage`） |

### 2.1 `orderInfo`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `orderType` | string enum | 是 | `EOrderType` 取值：`BUY_COUPON`、`QR_PAYMENT`、`TOP_UP`、`ONLINE_PAYMENT`、`GIFT_CARD`、`BILL_PAY`、`P70_RECHARGE` |
| `businessChannel` | string enum | 是 | `EBusinessChannel`：`APP`、`POS`、`H5`、`VIRGOCX_USER`、`CTRIP_USER`、`BOLT_USER`、`ALCHEMYPAY_USER`、`WECHAT_BILL_PAY`、`ALVINSCLUB_USER`、`GOAT_USER_CA`、`GOAT_USER_US`；未命中任何一个则默认 `APP` |
| `item.itemId` | string | 是 | 商品号，`@ECPNotEmpty`。礼品卡通常为 `CB<brandNo>-CT<templateNo>` |
| `item.price` | string | 是 | 商品金额，传入文本、服务端 `new BigDecimal(price)` |
| `item.merchantId` | string | 否 | 商户号（按业务需要） |
| `orderContext.giftOrder` | string | 否 | `"true" / "false"`；是否送礼单 |
| `orderContext.referralNo` | string | 否 | 推广员编号 |
| `orderContext.specifiedCouponNo` | string | 否 | 指定优惠券 |
| `orderContext.referCode` | string | 否 | 推荐码 |
| `orderContext.marketingChannelInfo` | object | 否 | 营销渠道信息 |

### 2.2 `paymentContext`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `specifiedPrimaryPaymentMethod` | string | 是 | 主支付方式，如 `SNAPLII_CREDIT`、`SNAPLII_DEBIT` 等 |
| `specifiedPrimaryPaymentToken` | string | 按卡种 | 多卡场景下的支付 token（命中具体卡片） |
| `cashbackOption` | string | 否 | `USE` / `NOT_USE` 等，是否使用返现 |
| `voucherOption` | string | 否 | `BEST_FIT` / `USE` / `NOT_USE`；代金券策略 |
| `specifiedVoucher` | string | 否 | 指定代金券号 |
| `deviceFingerprintingId` | string | 否 | 设备指纹 id（风控） |
| `forcedThreeDs` | string | 否 | 是否强制 3DS |
| `browserInfo.browserLanguage` | string | 是（Web/H5） | 浏览器语言，如 `en-CA` |
| `browserInfo.browserScreenHeight` | long/string | 是（Web/H5） | 浏览器屏高 |
| `browserInfo.browserScreenWidth` | long/string | 是（Web/H5） | 浏览器屏宽 |
| `browserInfo.browserUserAgent` | string | 是（Web/H5） | 浏览器 UA |

### 2.3 `delivery`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | 是 | `WALLET` / `EMAIL` / `MESSAGE` / `LINK` |
| `immediateSend` | string | 否 | `"true" / "false"`；是否即时发放 |
| `scheduleSendTime` | string | 否 | 预约发放时间 |
| `destination` | string | 否 | 目的地（`EMAIL` 类型下为收件邮箱等） |
| `giftDetail` | object | 否 | 送礼明细（文案/附言/封面等） |

## 3. 响应体

继承自 `PaysafeBaseRspBO → McaAbstractBaseRspBO`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `rspMsgCd` | string | 业务返回码，成功 `MCA00000` |
| `rspMsgInf` | string | 返回码描述 |
| `serviceTime` | string | 服务器时间（`yyyyMMddHHmmss`） |
| `orderNo` | string | 订单号 |
| `paymentNo` | string | 支付流水号 |
| `transactionTrackNo` | string | 业务跟踪号 |
| `orderStatus` | string | `OrderStatusEnum`：`INIT` / `WAIT_PAYMENT` / `WAIT_DELIVER` / `CANCELLED` / `SUCCESS` / `FAILED` / `DELETED` |
| `threeDSChallengeNeed` | boolean | 是否需要 3DS 挑战；为 `true` 时请结合 `challengeData` / `challengeURL` / `notificationURL` 完成挑战 |
| `challengeData` | string | 3DS 挑战 payload |
| `challengeURL` | string | 3DS 挑战地址 |
| `notificationURL` | string | 3DS 回调地址 |
| `sdkParams` | string | SDK 参数（如 Paysafe SDK 拉起） |
| `h5PayUrl` | string | H5 支付跳转 URL |
| `crdNo` | string | 资金卡账号 |
| `bal` | string | 余额（若适用） |
| `signUp` | boolean | 是否本次新开卡（触发订阅/推广员记账） |
| `sendGiftLink` | string | 送礼链接（`delivery.type = LINK` 场景） |
| `claimToken` | string | 送礼领取 token |
| `code` / `message` | string | Paysafe 透传错误码（异常时可能填充） |

### 常见错误码

| code | 含义 |
| --- | --- |
| `MCA00000` | 成功 |
| `APP_VERSION_NOT_SUPPORT` | 版本 `< 4.8.0` |
| `USR_NOT_EXIST` | 会话内找不到 `usr_no` |
| `AUTH_VERIFY_FAILED` | `P70_RECHARGE` 验证失败 |
| `ORDER_STATUS_INCORRECT` | 订单不存在 / 不属于当前用户 / 状态非 `WAIT_PAYMENT` |
| `ORDER_CREATION_FAILED` | 命中充值额度上限 |
| `ERROR` / `SVR_CALL_ERROR` / `TIME_OUT` | 下游支付/发货失败、发送失败、调用超时 |

## 4. 请求示例

```http
POST /mrpay/transaction/v2/createOrderAndPay.do HTTP/1.1
Content-Type: application/json
Cookie: SESSION=<sid>
```

```json
{
  "delivery": {
    "type": "WALLET",
    "immediateSend": "false"
  },
  "businessInfo": {
    "appLanguage": "en"
  },
  "paymentContext": {
    "voucherOption": "BEST_FIT",
    "cashbackOption": "USE",
    "specifiedPrimaryPaymentMethod": "SNAPLII_CREDIT",
    "deviceFingerprintingId": "",
    "browserInfo": {
      "browserLanguage": "en-CA",
      "browserScreenHeight": "891",
      "browserScreenWidth": "411",
      "browserUserAgent": "Mozilla/5.0 (Linux; Android 16; SM-S931W Build/BP2A.250605.031.A3; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.102 Mobile Safari/537.36;snaplii"
    },
    "specifiedPrimaryPaymentToken": "896c403fb175873"
  },
  "orderInfo": {
    "orderType": "GIFT_CARD",
    "item": {
      "itemId": "CB0000000000135-CT0000000000897",
      "price": "50"
    },
    "orderContext": {
      "giftOrder": "false"
    },
    "businessChannel": "APP"
  },
  "locationProv": "ON"
}
```

## 5. 响应示例

```json
{
  "paymentNo": "PPP1276741892423700480",
  "orderNo": "PPD1276741891563868160",
  "threeDSChallengeNeed": "false",
  "rspMsgCd": "MCA00000",
  "orderStatus": "SUCCESS",
  "rspMsgInf": "Success",
  "serviceTime": "20240730121256"
}
```

> 当 `threeDSChallengeNeed = true` 时，响应会额外带上 `challengeData` / `challengeURL` / `notificationURL`，前端需要据此跳转 ACS 完成 3DS 挑战，然后按支付渠道的回调流程续走。
