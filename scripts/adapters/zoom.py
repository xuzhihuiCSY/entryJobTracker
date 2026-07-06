from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils import http_get_text

BASE_URL = "https://careers.zoom.us/jobs/search"


def _text(selector: str, card: Any) -> str:
    element = card.select_one(selector)
    return element.get_text(" ", strip=True) if element else ""


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for page in range(1, 11):
        html = http_get_text(BASE_URL, params={"country_codes[]": "US", "page": page})
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article.job-search-results-card-col")
        if not cards:
            break

        for card in cards:
            link = card.select_one(".job-search-results-card-title a")
            if not link:
                continue
            title = link.get_text(" ", strip=True)
            apply_url = urljoin(BASE_URL, str(link.get("href") or ""))
            external_id = _text(".job-component-requisition-identifier span", card) or apply_url
            if external_id in seen:
                continue
            seen.add(external_id)
            results.append(
                {
                    "external_id": external_id,
                    "title": title,
                    "location_raw": _text(".job-component-location span", card),
                    "description": _text(".job-search-results-summary", card),
                    "apply_url": apply_url,
                    "source_url": apply_url,
                    "source_platform": "zoom",
                }
            )

        if not soup.select_one('a[rel="next"]'):
            break

    return results
