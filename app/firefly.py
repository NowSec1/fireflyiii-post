"""Utilities and routes for interacting with the Firefly III API."""
from __future__ import annotations

import os
from typing import Any, Dict

import requests
from flask import Blueprint, jsonify, request

firefly_blueprint = Blueprint("firefly", __name__)

FIREFLY_BASE_URL_ENV = "FIREFLY_BASE_URL"
FIREFLY_TOKEN_ENV = "FIREFLY_ACCESS_TOKEN"


class FireflyConfigurationError(RuntimeError):
    """Raised when the Firefly III configuration is incomplete."""


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise FireflyConfigurationError(
            f"The environment variable {name} is required but was not provided."
        )
    return value


def _firefly_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_env(FIREFLY_TOKEN_ENV)}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _firefly_url(path: str) -> str:
    base_url = _get_env(FIREFLY_BASE_URL_ENV).rstrip("/")
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
    data = firefly_request("GET", "accounts", params=params)
    return data


@firefly_blueprint.route("/budgets")
def budgets() -> Any:
    return firefly_request("GET", "budgets")


@firefly_blueprint.route("/categories")
def categories() -> Any:
    return firefly_request("GET", "categories")


@firefly_blueprint.route("/tags")
def tags() -> Any:
    return firefly_request("GET", "tags")


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
