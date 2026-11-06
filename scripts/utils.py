from __future__ import annotations

import json
import logging
import os
import tempfile
import time
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


def _request(method: Any, url: str, **kwargs: Any) -> requests.Response:
    """Retry transient network/server failures, never access denials or limits."""
    for attempt in range(3):
        try:
            response = method(url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
        else:
            if response.status_code not in {500, 502, 503, 504} or attempt == 2:
                response.raise_for_status()
                return response
        time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("Request retries exhausted")


def http_get_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    response = _request(
        requests.get, url,
        params=params,
        headers={
            **DEFAULT_HEADERS,
            "Accept": "application/json,text/plain,*/*",
            **(headers or {}),
        },
    )
    return response.json()


def http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
    response = _request(
        requests.post, url,
        json=payload,
        headers={**DEFAULT_HEADERS, "Accept": "application/json,text/plain,*/*", **(headers or {})},
    )
    return response.json()


def http_get_text(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    response = _request(
        requests.get, url,
        params=params,
        headers={**DEFAULT_HEADERS, "Accept": "text/html,text/plain,*/*", **(headers or {})},
    )
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
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
