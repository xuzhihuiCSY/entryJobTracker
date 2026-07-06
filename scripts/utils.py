from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

USER_AGENT = (
    "US-Tech-Entry-Jobs-Tracker/0.1 "
    "(public career page crawler; low-frequency; contact: configure-in-repo)"
)
REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def http_get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        url,
        params=params,
        headers={**DEFAULT_HEADERS, "Accept": "application/json,text/plain,*/*"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
    response = requests.post(
        url,
        json=payload,
        headers={**DEFAULT_HEADERS, "Accept": "application/json,text/plain,*/*", **(headers or {})},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def http_get_text(url: str, params: dict[str, Any] | None = None) -> str:
    response = requests.get(
        url,
        params=params,
        headers={**DEFAULT_HEADERS, "Accept": "text/html,text/plain,*/*"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.text


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logging.warning("Could not parse JSON file %s; using fallback", path)
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
