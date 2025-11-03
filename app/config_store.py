"""Configuration management and caching helpers for Firefly III integration."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

CONFIG_FILENAME = "config.json"
CACHE_SECTION = "resource_cache"
LAST_SYNC_KEY = "last_synced_at"
CACHE_MAX_AGE = timedelta(hours=12)

_lock = Lock()


def _app_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _config_path() -> str:
    return os.path.join(_app_root(), CONFIG_FILENAME)


def _load_config_unlocked() -> Dict[str, Any]:
    path = _config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        # Return empty config if the file is corrupted or unreadable.
        return {}


def _write_config_unlocked(data: Dict[str, Any]) -> None:
    path = _config_path()
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
    except OSError:
        # If we cannot write the configuration file, silently ignore.
        # Downstream callers should still return API results so the UI remains usable.
        pass


def get_firefly_setting(key: str) -> Optional[str]:
    """Retrieve Firefly III configuration values stored in config.json."""
    with _lock:
        config = _load_config_unlocked()
    firefly_section = config.get("firefly", {})
    value = firefly_section.get(key)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def update_firefly_settings(updater: Callable[[Dict[str, Any]], None]) -> None:
    """Apply updates to the firefly settings block in the config file."""
    with _lock:
        config = _load_config_unlocked()
        firefly_section = config.setdefault("firefly", {})
        updater(firefly_section)
        _write_config_unlocked(config)


def get_cached_entry(resource: str) -> Tuple[Optional[Any], Optional[str]]:
    """Return cached data for a resource along with the last sync timestamp."""
    with _lock:
        config = _load_config_unlocked()
    cache = config.get(CACHE_SECTION, {})
    entry = cache.get(resource)
    if not isinstance(entry, dict):
        return None, None
    return entry.get("data"), entry.get(LAST_SYNC_KEY)


def update_cached_entry(resource: str, data: Any, synced_at: datetime) -> None:
    """Persist cached data for a resource."""
    serializable: Any = data
    timestamp = synced_at.replace(microsecond=0).isoformat()
    with _lock:
        config = _load_config_unlocked()
        cache = config.setdefault(CACHE_SECTION, {})
        cache[resource] = {"data": serializable, LAST_SYNC_KEY: timestamp}
        _write_config_unlocked(config)


def touch_cached_entry(resource: str, synced_at: datetime) -> None:
    """Update the last sync timestamp when the cached data remains unchanged."""
    timestamp = synced_at.replace(microsecond=0).isoformat()
    with _lock:
        config = _load_config_unlocked()
        cache = config.setdefault(CACHE_SECTION, {})
        entry = cache.get(resource)
        if isinstance(entry, dict):
            entry[LAST_SYNC_KEY] = timestamp
            _write_config_unlocked(config)


def cache_is_stale(last_synced: Optional[str]) -> bool:
    if not last_synced:
        return True
    try:
        synced_at = datetime.fromisoformat(last_synced)
    except ValueError:
        return True
    return datetime.utcnow() - synced_at >= CACHE_MAX_AGE
