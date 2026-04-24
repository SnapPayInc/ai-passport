# Snaplii Gateway — API 调用文档

本文档覆盖以下六个接口：

| 接口名 | URL | 需要 Session |
| --- | --- | --- |
| apiKeyLogin | `/mrpay/apikey/login.do` | 否 |
| apiKeyCreate | `/mrpay/apikey/create.do` | 是 |
| apiKeyDelete | `/mrpay/apikey/delete.do` | 是 |
| apiKeyList | `/mrpay/apikey/list.do` | 是 |
| getUserCards | `/mrpay/getUserCards.do` | 是 |
| getSingleCardDetail | `/mrpay/getSingleCardDetail.do` | 是 |

## 通用约定

- **HTTP 方法**：`POST`
- **Content-Type**：`application/json`
- **请求体必填公共字段**（继承自 `McaAbstractBaseReqBO`，非必填字段不在此列出）：

| 字段 | 类型 | 用途 | 适用接口 |
| --- | --- | --- | --- |
| `deviceInfo.deviceId` | string | 设备指纹（`McaDeviceInfoBO` 声明 `@ECPNotEmpty`）。用于会话绑定；`apiKeyLogin` 额外要求**不得以 `API-KEY-` 开头**（保留前缀） | 全部 6 个接口 |
| `deviceInfo.publicIp` / `publicIp` | string | 调用方真实公网 IP，风控 / API key `verify` 调用上送 SOM；也是 `RiskInfoService` 写入 IP 地理画像的依据 | `apiKeyLogin`（风控必填）；其他接口若存量链路需要风控画像，建议一并上送 |
| `deviceInfo.appLanguage` | string | 下游 giftcard SOM 按语言返回文案 | `getUserCards`、`getSingleCardDetail` |

> 其余 `McaAbstractBaseReqBO` 里声明的字段（`partner` / `format` / `sign` / `signType` / `referenceNo` / `infoVersion` / `characterSet` / `countryCode` 等）在本批接口上均非必填；如外层网关/签名体系需要，按各自规范传入即可。
- **响应体公共字段**（继承自 `McaAbstractBaseRspBO`）：
  - `rspMsgCd`：业务返回码（成功为 `MCA00000`）
  - `rspMsgInf`：返回码描述
  - `serviceTime`：服务器时间
  - `sign`、`resultCode`、`error`：签名与错误扩展位
- **常用返回码**：

| code | 含义 |
| --- | --- |
| `MCA00000` | 成功 |
| `MACP6005` | 系统调用错误（下游 SOM 异常） |
| `MCAP9999` | 会话失效 / 未登录（`NO_SESSION_FAIL`） |
| `MCA20101` | API key 非法（格式错、agentId 为空、或提交了保留前缀 deviceId） |
| `MCA20102` | API key 已停用 |
| `MCA20103` | 同名 API key 已存在 |
| `MCA20104` | API key 数量已达上限 |
| `MCA20105` | API key 不存在 |
| `MCA20106` | API key 不属于当前用户 |

---

## 1. apiKeyLogin — 使用 API Key 登录

- **URL**：`POST /mrpay/apikey/login.do`
- **Session**：不要求。**调用成功后**网关会在服务端构造一个 `API-KEY-<keyId>-<agentId>` 的虚拟 deviceId 会话，后续三个 apiKey 管理接口以及 giftcard 接口都依赖该会话。
- **调用方 / 用途**：商户服务端用长期 API key 换取一个可用的登录态。
- **关键规则**：
  - `apiKey` 必须匹配正则 `^snp_sk_live_[A-Za-z0-9]{32}$`。
  - 请求 `deviceInfo.device_id` **不得以 `API-KEY-` 开头**（该前缀为服务端保留），否则直接拒绝（`MCA20101`）。

### 请求字段（业务部分）

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `agentId` | string | 是 | 调用方 agent 标识，参与会话隔离 |
| `apiKey` | string | 是 | 形如 `snp_sk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |

### 响应字段（业务部分）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `usrNo` | string | 用户号 |
| `regmbl` | string | 手机号明文 |
| `regmblCipher` | string | 手机号密文 |
| `name` | string | API key 的自定义名称 |
| `scope` | string | API key 的授权范围 |
| `consumptionLimitCents` | long | 消费限额（单位：分） |

### 请求示例

```bash
curl -X POST https://<host>/mrpay/apikey/login.do \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "agent-001",
    "apiKey": "snp_sk_live_abcdefghijklmnopqrstuvwxyz012345",
    "deviceInfo": {
      "device_id": "merchant-server-001",
      "app_language": "en"
    }
  }'
```

### 响应示例

```json
{
  "rspMsgCd": "MCA00000",
  "rspMsgInf": "Success",
  "usrNo": "1000001",
  "regmbl": "14161234567",
  "regmblCipher": "****",
  "name": "default",
  "scope": "PAY_READ",
  "consumptionLimitCents": 100000
}
```

### 典型错误

| 场景 | rspMsgCd |
| --- | --- |
| 缺少 agentId / apiKey 格式错误 / deviceId 命中保留前缀 | `MCA20101` |
| API key 在 SOM 不存在 | `MCA20105` |
| API key 被标记为 INACTIVE | `MCA20102` |
| 下游 SOM 调用失败 | `MACP6005` |

---

## 2. apiKeyCreate — 创建 API Key

- **URL**：`POST /mrpay/apikey/create.do`
- **Session**：**必须**已登录（普通用户登录或 apiKeyLogin 后）。
- **用途**：当前登录用户为自己生成一把新的 API key；生成的明文 `apiKey` 只在本接口返回一次，后续列表只会以原样返回存档项。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 当前用户下唯一的可读名称 |
| `scope` | string | 是 | 授权范围，例如 `PAY_READ` / `PAY_WRITE`，以 SOM 支持为准 |
| `consumptionLimit` | decimal | 否 | 消费限额，**单位：元**（`BigDecimal`），网关会乘以 100 转为分数（`HALF_UP`）写入 SOM |

### 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `keyId` | string | API key 的内部 ID，供 delete / list 使用 |
| `apiKey` | string | **只此一次返回**的明文 API key，形如 `snp_sk_live_…`，请立刻妥善保存 |
| `name` | string | 回显 |
| `scope` | string | 回显 |
| `consumptionLimitCents` | long | 实际入库的分单位限额 |
| `status` | string | 通常为 `ACTIVE` |
| `createdAt` | datetime | 创建时间（ISO-8601） |

### 请求示例

```bash
curl -X POST https://<host>/mrpay/apikey/create.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{
    "name": "checkout-prod",
    "scope": "PAY_WRITE",
    "consumptionLimit": 500.00
  }'
```

### 响应示例

```json
{
  "rspMsgCd": "MCA00000",
  "rspMsgInf": "Success",
  "keyId": "ak_01HXYZ...",
  "apiKey": "snp_sk_live_abcdefghijklmnopqrstuvwxyz012345",
  "name": "checkout-prod",
  "scope": "PAY_WRITE",
  "consumptionLimitCents": 50000,
  "status": "ACTIVE",
  "createdAt": "2026-04-22T16:43:00"
}
```

### 典型错误

| 场景 | rspMsgCd |
| --- | --- |
| 会话失效 | `MCAP9999` |
| 同名 key 已存在（SOM 返回 `NAME_EXISTS`） | `MCA20103` |
| 已达配额上限（SOM 返回 `LIMIT_REACHED`） | `MCA20104` |
| 入参不合法（其他 4xx） | `MCA20101` |
| SOM 调用失败 | `MACP6005` |

---

## 3. apiKeyDelete — 删除 API Key

- **URL**：`POST /mrpay/apikey/delete.do`
- **Session**：**必须**已登录。
- **用途**：把指定 `keyId` 置为停用；成功后网关会同时在 Redis 写入一条 `sessApiKey:status:<keyId> = INACTIVE`（TTL 由 `API_KEY_STATUS_CACHE_TTL_SECONDS` 控制），使后续使用该 key 登录立即失败。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyId` | string | 是 | 由 create / list 返回的 API key 主键 |

### 响应字段

无额外业务字段，仅含 `rspMsgCd` / `rspMsgInf`。

### 请求示例

```bash
curl -X POST https://<host>/mrpay/apikey/delete.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{"keyId": "ak_01HXYZ..."}'
```

### 典型错误

| 场景 | rspMsgCd |
| --- | --- |
| 会话失效 | `MCAP9999` |
| SOM 返回 `success=false`（key 不存在或不归属当前用户） | `MCA20106` |
| SOM 调用失败 | `MACP6005` |

---

## 4. apiKeyList — 列出我的 API Key

- **URL**：`POST /mrpay/apikey/list.do`
- **Session**：**必须**已登录。
- **用途**：返回当前用户所有 **有效** 的 API key。

### 请求字段

无业务字段（空 JSON 即可）。

### 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `keys` | Item[] | API key 列表 |

**Item：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `keyId` | string | 内部 ID |
| `apiKey` | string | 明文 key |
| `name` | string | 名称 |
| `scope` | string | 授权范围 |
| `consumptionLimitCents` | long | 消费限额（分） |
| `createdAt` | datetime | 创建时间 |

### 请求示例

```bash
curl -X POST https://<host>/mrpay/apikey/list.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{}'
```

### 响应示例

```json
{
  "rspMsgCd": "MCA00000",
  "rspMsgInf": "Success",
  "keys": [
    {
      "keyId": "ak_01HXYZ...",
      "apiKey": "snp_sk_live_abcdefghijklmnopqrstuvwxyz012345",
      "name": "checkout-prod",
      "scope": "PAY_WRITE",
      "consumptionLimitCents": 50000,
      "createdAt": "2026-04-22T16:43:00"
    }
  ]
}
```

---

## 5. getUserCards — 查询我的礼品卡列表

- **URL**：`POST /mrpay/getUserCards.do`
- **Session**：**必须**已登录。
- **txn_cod**：`getUserCards`（实现类 `CardUserRetrieveAction`）。
- **用途**：按状态（钱包页 / 归档页）分页返回当前用户的 giftcard 列表；结果内时间会由 UTC 转为 `America/Toronto`，`ACTIVE` 按创建时间倒序，其它按更新时间倒序。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 否 | `ACTIVE`（默认）/ `INACTIVE` 等 |
| `pageNo` | string | 否 | 页码，`"0"` 等价于 `"1"` |
| `pageSize` | string | 否 | 每页条数，`"0"` 等价于 `"10"` |
| `deviceInfo.appLanguage` | string | 是 | 下游 SOM 需要 |

### 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data` | UserCardDetail[] | 当前页的卡列表 |
| `pageNo` | int | 当前页码 |
| `totalCount` | int | 总条数 |
| `totalPage` | int | 总页数 |

**UserCardDetail**（主要字段）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cardNo` | string | 卡号 |
| `userNo` | string | 用户号 |
| `cardType` | string | 卡类型（默认 `GIFT_CARD`） |
| `status` | string | 卡状态 |
| `faceValue` | decimal | 面值 |
| `remainingBalance` | decimal | 剩余余额 |
| `userMarkedBalance` | decimal | 用户标注余额 |
| `cardTemplate` | object | 模板信息 |
| `cardBrandId` | string | 品牌 ID |
| `cardCode` / `displayCardCode` / `pin` / `barCodePath` | string | 兑换码/展示码/PIN/条码图 |
| `hosted` | bool | 是否托管 |
| `userCardId` | string | 用户卡 ID（送礼/收礼使用） |
| `claimToken` | string | 送礼信息查询 token |
| `redeemMethod` | string | 兑换方式 |
| `cardCoverUrl` | string | 卡面图 URL |
| `deliverNo` | string | 发卡单号 |
| `exchangeAmount` | decimal | 兑换金额 |
| `paymentETA` / `paymentReceived` | string | 付款 ETA / 已收款 |
| `createdAt` | string | 购买时间（字段名 `purchasedAt`，Toronto 时区 `yyyy-MM-dd HH:mm:ss`） |
| `updateTime` | string | 更新时间（Toronto 时区） |
| `legacyCpNo` / `legacyCardType` | string | 旧系统兼容字段 |
| `rechargeSlogan` | string | 充值文案 |

### 请求示例

```bash
curl -X POST https://<host>/mrpay/getUserCards.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{
    "status": "ACTIVE",
    "pageNo": "1",
    "pageSize": "20",
    "deviceInfo": {"app_language": "en"}
  }'
```

### 典型错误

| 场景 | rspMsgCd |
| --- | --- |
| 会话失效 | `MCAP9999` |
| 下游 SOM 失败（返回码末位非 0） | `MACP6006`（`SVR_CALL_FAIL`） |

---

## 6. getSingleCardDetail — 查询单张卡详情

- **URL**：`POST /mrpay/getSingleCardDetail.do`
- **Session**：**必须**已登录。
- **txn_cod**：`getSingleUserCard`（实现类 `CardUserSingleRetrieveAction`）。注意：URL 是 `getSingleCardDetail`，但 bean name 是 `getSingleUserCard`。

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `cardNo` | string | 是 | 卡号 |
| `cardType` | string | 否 | 默认 `GIFT_CARD` |
| `deviceInfo.appLanguage` | string | 是 | 下游 SOM 需要 |

### 响应字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `data` | UserCardDetail | 单张卡详情，字段同上表 |

### 请求示例

```bash
curl -X POST https://<host>/mrpay/getSingleCardDetail.do \
  -H "Content-Type: application/json" \
  --cookie "SESSION=<sid>" \
  -d '{
    "cardNo": "8801234567890123",
    "cardType": "GIFT_CARD",
    "deviceInfo": {"app_language": "en"}
  }'
```

### 典型错误

| 场景 | rspMsgCd |
| --- | --- |
| 会话失效 | `MCAP9999` |
| 下游 SOM 失败 | `MACP6006` |

---

## 附：会话模型与 API Key 调用链

1. 商户后端调用 `apiKeyLogin` → 网关向 SOM 调 `verify`，校验 key 有效性并拿到 `usrNo` 与 `keyId`。
2. 网关为本次登录生成 `deviceId = API-KEY-<keyId>-<agentId>`，建立 `usr_inf` 会话并把 `apiKey` id 存入 `api_key_id` 字段；Session ID 同步写入 Redis（TTL 30 天）。
3. 商户后端在**同一 SESSION cookie** 下调用 `getUserCards` / `getSingleCardDetail` / `apiKeyCreate` / `apiKeyDelete` / `apiKeyList` 等受保护接口。
4. 若商户自己想管理 key：拿到 session 后调 `apiKeyList`、`apiKeyCreate`、`apiKeyDelete`。`apiKeyDelete` 会同步把 `sessApiKey:status:<keyId>` 置 `INACTIVE`，新的 `apiKeyLogin` 将立即拒绝该 key。

> **注意**：客户端提交的 `deviceInfo.device_id` 不得以 `API-KEY-` 开头（保留前缀），否则 `apiKeyLogin` 将直接返回 `MCA20101`。
