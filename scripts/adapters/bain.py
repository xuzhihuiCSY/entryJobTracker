from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlsplit

from utils import http_get_json

TECH_ROLE_TERMS = (
    "software",
    "engineer",
    "developer",
    "data",
    "analytics",
    "machine learning",
    "artificial intelligence",
    "cloud",
    "security",
    "technology",
    "architect",
)


def _is_technical(posting: dict[str, Any]) -> bool:
    categories = posting.get("Categories") or []
    title = str(posting.get("JobTitle") or "").lower()
    category_values = {str(item).strip().lower() for item in categories}
    return "technology & engineering" in category_values or any(term in title for term in TECH_ROLE_TERMS)


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    career_url = str(company_config.get("career_url") or "").strip()
    source_url = str(company_config.get("source_base_url") or "").strip()
    if not career_url or not source_url:
        return []

    parsed = urlsplit(career_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    data = http_get_json(
        source_url,
        headers={
            "Origin": origin,
            "Referer": career_url,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    postings = data.get("results", []) if isinstance(data, dict) else []
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for posting in postings:
        if not isinstance(posting, dict) or not _is_technical(posting):
            continue
        external_id = str(posting.get("JobId") or "").strip()
        if not external_id or external_id in seen:
            continue
        seen.add(external_id)
        apply_url = urljoin(career_url, str(posting.get("Link") or ""))
        locations = posting.get("Location") or []
        results.append(
            {
                "external_id": external_id,
                "title": posting.get("JobTitle") or "",
                "location_raw": "; ".join(str(value).strip() for value in locations if str(value).strip()),
                "description": posting.get("JobDescription") or "",
                "apply_url": apply_url,
                "source_url": apply_url,
                "source_platform": "bain",
            }
        )
    return results
