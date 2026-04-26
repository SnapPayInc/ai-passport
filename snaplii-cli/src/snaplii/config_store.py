from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


_TOKEN_SAFETY_MARGIN = 90  # seconds before expiry to trigger refresh


class ConfigStore:
    def __init__(self, path: Path | None = None):
        self._path = path or Path.home() / ".snaplii" / "config.json"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> dict:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text())

    def save(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2) + "\n")
        os.chmod(self._path, 0o600)

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self.load()
        data[key] = value
        self.save(data)

    def set_many(self, updates: dict) -> None:
        data = self.load()
        data.update(updates)
        self.save(data)

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()

    def get_cached_token(self) -> str | None:
        data = self.load()
        token = data.get("access_token")
        expires_at = data.get("token_expires_at")
        if not token or not expires_at:
            return None
        if time.time() >= expires_at - _TOKEN_SAFETY_MARGIN:
            return None
        return token

    def cache_token(self, access_token: str, expires_in: int) -> None:
        self.set_many({
            "access_token": access_token,
            "token_expires_at": time.time() + expires_in,
        })

