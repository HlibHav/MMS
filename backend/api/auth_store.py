"""
Simple persistent API key store with roles and rotation support.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

STORE_PATH = Path(__file__).resolve().parents[2] / "tmp" / "api_keys.json"
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> Dict[str, dict]:
    if not STORE_PATH.exists():
        return {}
    try:
        return json.loads(STORE_PATH.read_text())
    except Exception:
        return {}


def _save(data: Dict[str, dict]) -> None:
    STORE_PATH.write_text(json.dumps(data, default=str, indent=2))


def add_key(name: str, role: str = "read", ttl_days: int = 90) -> dict:
    data = _load()
    key = f"pk_live_{name}_{int(datetime.utcnow().timestamp())}"
    expires_at = (datetime.utcnow() + timedelta(days=ttl_days)).isoformat()
    rec = {"name": name, "role": role, "expires_at": expires_at, "revoked": False}
    data[key] = rec
    _save(data)
    rec_out = rec.copy()
    rec_out["api_key"] = key
    return rec_out


def get_key(token: str) -> Optional[dict]:
    data = _load()
    rec = data.get(token)
    if not rec:
        return None
    if rec.get("revoked"):
        return None
    exp = rec.get("expires_at")
    if exp:
        try:
            if datetime.fromisoformat(exp) < datetime.utcnow():
                return None
        except Exception:
            pass
    rec_with_key = rec.copy()
    rec_with_key["api_key"] = token
    return rec_with_key


def revoke_key(token: str) -> None:
    data = _load()
    if token in data:
        data[token]["revoked"] = True
        _save(data)
