"""
Database configuration - Primary backend is Firebase Realtime Database
Falls back to inline mock if neither Firebase nor Deta is available.
"""

from os import getenv
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Inline mock backend (zero dependencies, always available)
# ---------------------------------------------------------------------------

class _MockFetchResult:
    def __init__(self, items: List[Dict[str, Any]]):
        self.items = items
    def __len__(self):
        return len(self.items)

class _MockBase:
    def __init__(self):
        self._data: Dict[str, dict] = {}
        self._counter = 0

    def put(self, data: dict) -> dict:
        self._counter += 1
        key = f"key_{self._counter}"
        self._data[key] = dict(data)
        return {"key": key}

    def get(self, key: str) -> Optional[dict]:
        record = self._data.get(key)
        if record:
            return {**record, "key": key}
        return None

    def update(self, key: str, updates: dict):
        if key in self._data:
            self._data[key].update(updates)

    def delete(self, key: str):
        self._data.pop(key, None)

    def fetch(self, query: Optional[dict] = None) -> _MockFetchResult:
        items = []
        for k, v in self._data.items():
            item = {**v, "key": k}
            if query:
                if all(item.get(qk) == qv for qk, qv in query.items()):
                    items.append(item)
            else:
                items.append(item)
        return _MockFetchResult(items)

class _MockDrive:
    def put(self, name: str, f) -> str:
        return name
    def get(self, filename: str):
        return _MockStream()

class _MockStream:
    def iter_chunks(self, size: int):
        return [b"mock"]

# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

use_firebase = getenv("FIREBASE_DATABASE_URL") is not None

if use_firebase:
    from db.firebase import (
        client_db_wrapper,
        notification_db_wrapper,
        command_db_wrapper,
        auth_db_wrapper,
        init_firebase,
    )
    try:
        init_firebase()
        print("[DB] Using Firebase Realtime Database as primary backend")
    except Exception as e:
        print(f"[DB] Firebase initialization failed: {e}")
        use_firebase = False

if not use_firebase:
    try:
        from deta import Deta
        _deta = Deta(getenv("DETA_PROJECT_KEY", ""))
        _backend = "deta"
        print("[DB] Using Deta as backend")
    except Exception:
        _backend = "mock"
        _deta = None
        print("[DB] Using inline mock backend (no persistence across restarts)")


def _make_client():
    if use_firebase:
        return client_db_wrapper()
    elif _backend == "deta":
        return _deta.Base("client")
    return _MockBase()

def _make_notification():
    if use_firebase:
        return notification_db_wrapper()
    elif _backend == "deta":
        return _deta.Base("notification")
    return _MockBase()

def _make_command():
    if use_firebase:
        return command_db_wrapper()
    elif _backend == "deta":
        return _deta.Base("command")
    return _MockBase()

def _make_auth():
    if use_firebase:
        return auth_db_wrapper()
    elif _backend == "deta":
        return _deta.Base("auth")
    return _MockBase()


_client_instance = None
_notification_instance = None
_command_instance = None
_auth_instance = None


def client_db():
    global _client_instance
    if _client_instance is None:
        _client_instance = _make_client()
    return _client_instance


def notification_db():
    global _notification_instance
    if _notification_instance is None:
        _notification_instance = _make_notification()
    return _notification_instance


def command_db():
    global _command_instance
    if _command_instance is None:
        _command_instance = _make_command()
    return _command_instance


def auth_db():
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = _make_auth()
    return _auth_instance


async def tear_drive():
    if _backend == "deta":
        return _deta.Drive("mspaydo")
    raise RuntimeError("File storage not available - Deta backend required")
