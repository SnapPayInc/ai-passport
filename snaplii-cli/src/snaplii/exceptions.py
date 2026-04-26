class SnapliiCliError(Exception):
    pass


class GatewayApiError(SnapliiCliError):
    def __init__(self, status_code: int, body: dict, endpoint: str):
        self.status_code = status_code
        self.body = body
        self.endpoint = endpoint
        super().__init__(f"API error {status_code} on {endpoint}")

    def to_dict(self) -> dict:
        friendly = self.body.get("friendly_message")
        error_code = self.body.get("rspMsgCd", "")
        if not friendly:
            if self.status_code == 502:
                friendly = "Gateway temporarily unavailable. Please wait a moment and try again."
            elif self.status_code == 401 or self.status_code == 403:
                friendly = "Authentication failed. Run 'snaplii init' to re-authenticate."
            elif self.status_code == 404:
                friendly = "Endpoint not found. Check your gateway URL with 'snaplii config show'."
            elif error_code:
                friendly = f"Request failed with code {error_code}. Check the gateway logs for details."
            else:
                raw = self.body.get("rspMsgInf") or self.body.get("message") or self.body.get("raw", "")
                friendly = f"Request failed (HTTP {self.status_code}). {raw}".strip()
        return {
            "error": friendly,
            "error_code": error_code,
            "endpoint": self.endpoint,
        }


class GatewayConnectionError(SnapliiCliError):
    def __init__(self, url: str, cause: Exception):
        self.url = url
        self.cause = cause
        super().__init__(f"Connection failed: {url}")

    def to_dict(self) -> dict:
        return {
            "error": "Connection failed",
            "url": self.url,
            "cause": str(self.cause),
        }


class ConfigError(SnapliiCliError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"error": "Configuration error", "message": self.message}
