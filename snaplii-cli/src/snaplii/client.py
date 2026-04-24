from __future__ import annotations

import httpx

from snaplii.config_store import ConfigStore
from snaplii.exceptions import ConfigError, GatewayApiError, GatewayConnectionError


class GatewayClient:
    def __init__(self, base_url: str, config_store: ConfigStore):
        self._base_url = base_url.rstrip("/")
        self._config = config_store
        self._http = httpx.Client(timeout=30.0)

    def login(self, agent_id: str, api_key: str) -> dict:
        url = self._base_url + "/apikey/login.do"
        try:
            resp = self._http.post(url, json={
                "agentId": agent_id,
                "apiKey": api_key,
                "deviceInfo": {
                    "device_id": f"snaplii-cli-{agent_id}",
                    "app_language": "en",
                },
            })
        except httpx.ConnectError as e:
            raise GatewayConnectionError(url, e)
        body = self._parse_response(resp, "/apikey/login.do")
        token = resp.headers.get("x-auth-token")
        if token:
            self._config.cache_token(token, 3600)
        return body

    def list_user_cards(self, status: str = "ACTIVE", page: int = 1, page_size: int = 20) -> dict:
        token = self._ensure_token()
        return self._post("/getUserCards.do", json={
            "status": status,
            "pageNo": str(page),
            "pageSize": str(page_size),
            "deviceInfo": {"app_language": "en"},
        }, token=token)

    def get_card_detail(self, card_no: str) -> dict:
        token = self._ensure_token()
        return self._post("/getSingleCardDetail.do", json={
            "cardNo": card_no,
            "cardType": "GIFT_CARD",
            "deviceInfo": {"app_language": "en"},
        }, token=token)

    # ── Card browsing ──────────────────────────────────────────────

    def get_all_card_tags(self, channel: str = "HOME_PAGE", location_prov: str = "ON") -> dict:
        token = self._ensure_token()
        return self._post("/getAllCardTags.do", json={
            "channel": channel,
            "locationProv": location_prov,
            "deviceInfo": {
                "deviceId": "snaplii-cli",
                "appLanguage": "en",
                "longitude": "-79.3832",
                "latitude": "43.6532",
            },
        }, token=token)

    def get_card_brand_by_id(self, card_brand_id: str, scenario: str = "PURCHASE") -> dict:
        token = self._ensure_token()
        return self._post("/getCardBrandById.do", json={
            "cardBrandId": card_brand_id,
            "scenario": scenario,
            "deviceInfo": {
                "deviceId": "snaplii-cli",
                "appLanguage": "en",
            },
        }, token=token)

    # ── Purchase ──────────────────────────────────────────────────

    def create_order_and_pay(
        self,
        item_id: str,
        price: str,
        payment_method: str = "SNAPLII_CREDIT",
        payment_token: str | None = None,
        location_prov: str = "ON",
    ) -> dict:
        token = self._ensure_token()
        payment_ctx = {
            "specifiedPrimaryPaymentMethod": payment_method,
            "voucherOption": "BEST_FIT",
            "cashbackOption": "USE",
        }
        if payment_token:
            payment_ctx["specifiedPrimaryPaymentToken"] = payment_token
        return self._post("/transaction/v2/createOrderAndPay.do", json={
            "orderInfo": {
                "orderType": "GIFT_CARD",
                "item": {"itemId": item_id, "price": price},
                "orderContext": {"giftOrder": "false"},
                "businessChannel": "APP",
            },
            "paymentContext": payment_ctx,
            "delivery": {"type": "WALLET", "immediateSend": "true"},
            "businessInfo": {"appLanguage": "en"},
            "locationProv": location_prov,
            "deviceInfo": {"deviceId": "snaplii-cli", "clientVer": "4.10.7"},
        }, token=token)

    # ── API key management ────────────────────────────────────────

    def create_api_key(self, name: str, scope: str, consumption_limit: float | None = None) -> dict:
        token = self._ensure_token()
        payload = {"name": name, "scope": scope}
        if consumption_limit is not None:
            payload["consumptionLimit"] = consumption_limit
        return self._post("/apikey/create.do", json=payload, token=token)

    def list_api_keys(self) -> dict:
        token = self._ensure_token()
        return self._post("/apikey/list.do", json={}, token=token)

    def delete_api_key(self, key_id: str) -> dict:
        token = self._ensure_token()
        return self._post("/apikey/delete.do", json={"keyId": key_id}, token=token)

    def _ensure_token(self) -> str:
        token = self._config.get_cached_token()
        if token:
            return token
        agent_id = self._config.get("agent_id")
        api_key = self._config.get("api_key")
        if agent_id and api_key:
            self.login(agent_id, api_key)
            token = self._config.get_cached_token()
            if token:
                return token
        raise ConfigError(
            "No valid token. Run 'snaplii init --agent-id ID --api-key KEY' to authenticate."
        )

    def _post(self, path: str, json: dict, token: str | None = None) -> dict:
        url = self._base_url + path
        headers = self._auth_header(token)
        try:
            resp = self._http.post(url, json=json, headers=headers)
        except httpx.ConnectError as e:
            raise GatewayConnectionError(url, e)
        return self._parse_response(resp, path)

    @staticmethod
    def _auth_header(token: str | None) -> dict:
        if token:
            return {"x-auth-token": token}
        return {}

    # Human-readable error messages for common error codes
    _ERROR_MESSAGES = {
        "MACP6005": "Payment failed. This usually means insufficient Snaplii Cash balance. Please top up your Snaplii Cash and try again.",
        "MACP6006": "Service call failed. The downstream gift card service is temporarily unavailable. Please try again later.",
        "MCAP9999": "Session expired. Please run 'snaplii init' to re-authenticate.",
        "MCA20101": "Invalid API key format or request parameters.",
        "MCA20102": "This API key has been deactivated.",
        "MCA20103": "An API key with this name already exists. Please choose a different name.",
        "MCA20104": "API key limit reached. Delete an existing key before creating a new one.",
        "MCA20105": "API key not found.",
        "MCA20106": "This API key does not belong to your account.",
        "APP_VERSION_NOT_SUPPORT": "App version too low. Minimum version 4.8.0 required.",
        "USR_NOT_EXIST": "User not found in session. Please re-authenticate.",
        "ORDER_STATUS_INCORRECT": "Order status error. The order may not exist or is not in a payable state.",
        "ORDER_CREATION_FAILED": "Order creation failed. You may have reached a spending limit.",
        "AUTH_VERIFY_FAILED": "Authentication verification failed.",
    }

    @classmethod
    def _parse_response(cls, resp: httpx.Response, path: str):
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text}
        if resp.is_success:
            rsp_code = body.get("rspMsgCd", "")
            if rsp_code and not rsp_code.endswith("00000"):
                friendly = cls._ERROR_MESSAGES.get(rsp_code)
                if friendly:
                    body["friendly_message"] = friendly
                raise GatewayApiError(resp.status_code, body, path)
            return body
        raise GatewayApiError(resp.status_code, body, path)
