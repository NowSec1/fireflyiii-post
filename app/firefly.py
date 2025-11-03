"""Utilities and routes for interacting with the Firefly III API."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from flask import Blueprint, jsonify, request

from .config_store import (
    cache_is_stale,
    get_cached_entry,
    get_firefly_setting,
    touch_cached_entry,
    update_cached_entry,
)

firefly_blueprint = Blueprint("firefly", __name__)

FIREFLY_BASE_URL_ENV = "FIREFLY_BASE_URL"
FIREFLY_TOKEN_ENV = "FIREFLY_ACCESS_TOKEN"
CONFIG_BASE_URL_KEY = "base_url"
CONFIG_TOKEN_KEY = "access_token"


class FireflyConfigurationError(RuntimeError):
    """Raised when the Firefly III configuration is incomplete."""


def _get_configured_value(env_name: str, config_key: str) -> str:
    """Read configuration from config.json with environment fallback."""
    config_value = get_firefly_setting(config_key)
    if config_value:
        return config_value

    value = os.getenv(env_name)
    if value:
        return value
    raise FireflyConfigurationError(
        "请在 config.json 中配置 Firefly III 连接信息，"
        f"或设置环境变量 {env_name}。"
    )


def _firefly_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_configured_value(FIREFLY_TOKEN_ENV, CONFIG_TOKEN_KEY)}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _firefly_url(path: str) -> str:
    base_url = _get_configured_value(FIREFLY_BASE_URL_ENV, CONFIG_BASE_URL_KEY).rstrip("/")
    return f"{base_url}/api/v1/{path.lstrip('/')}"


def firefly_request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = requests.request(
            method,
            _firefly_url(path),
            headers=_firefly_headers(),
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as exc:
        return jsonify({"message": "无法连接到 Firefly III。", "details": str(exc)}), 502
    if not response.ok:
        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text}
        return jsonify(payload), response.status_code
    try:
        return response.json()
    except ValueError:
        return jsonify({"message": "Invalid response from Firefly III."}), 502


@firefly_blueprint.route("/accounts")
def accounts() -> Any:
    params = {"type": request.args.get("type") or "asset"}
    return _cached_resource("accounts", "accounts", params=params)


@firefly_blueprint.route("/budgets")
def budgets() -> Any:
    return _cached_resource("budgets", "budgets")


@firefly_blueprint.route("/categories")
def categories() -> Any:
    return _cached_resource("categories", "categories")


@firefly_blueprint.route("/tags")
def tags() -> Any:
    return _cached_resource("tags", "tags")


@firefly_blueprint.route("/transactions", methods=["POST"])
def create_transaction() -> Any:
    payload = request.get_json(force=True)
    if payload is None:
        return jsonify({"message": "Missing JSON payload."}), 400

    try:
        transaction = _build_transaction_payload(payload)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    response = firefly_request("POST", "transactions", json=transaction)
    return response


def _build_transaction_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = [
        "description",
        "source_account_id",
        "destination_account_id",
        "date",
        "amount",
    ]
    missing = [key for key in required_fields if not payload.get(key)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    tags = payload.get("tags")
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    notes = payload.get("notes")
    if notes:
        notes = notes.strip()

    transaction_entry: Dict[str, Any] = {
        "description": payload["description"],
        "type": payload.get("transaction_type", "transfer"),
        "date": payload["date"],
        "amount": str(payload["amount"]),
        "source_id": payload["source_account_id"],
        "destination_id": payload["destination_account_id"],
    }

    if payload.get("budget_id"):
        transaction_entry["budget_id"] = payload["budget_id"]
    if payload.get("category_id"):
        transaction_entry["category_id"] = payload["category_id"]
    if tags:
        transaction_entry["tags"] = tags
    if notes:
        transaction_entry["notes"] = notes

    return {"transactions": [transaction_entry]}


def _cache_key(name: str, params: Optional[Dict[str, Any]] = None) -> str:
    if not params:
        return name
    sorted_items = sorted((key, value) for key, value in params.items() if value is not None)
    suffix = "&".join(f"{key}={value}" for key, value in sorted_items)
    return f"{name}?{suffix}" if suffix else name


def _cached_resource(name: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    cache_key = _cache_key(name, params)
    cached_data, last_synced = get_cached_entry(cache_key)
    if cached_data is not None and not cache_is_stale(last_synced):
        return cached_data

    fresh_data = firefly_request("GET", path, params=params)
    if isinstance(fresh_data, tuple):
        # Fall back to cached data when the remote call fails.
        if cached_data is not None:
            return cached_data
        return fresh_data

    now = datetime.utcnow()
    if cached_data is None or fresh_data != cached_data:
        update_cached_entry(cache_key, fresh_data, now)
    else:
        touch_cached_entry(cache_key, now)
    return fresh_data
