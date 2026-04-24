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
        return {
            "error": friendly or "API error",
            "error_code": self.body.get("rspMsgCd", ""),
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
