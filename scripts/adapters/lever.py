from __future__ import annotations

from typing import Any

from utils import http_get_json


def fetch_company_jobs(company_config: dict[str, Any]) -> list[dict[str, Any]]:
    source_key = company_config.get("source_key")
    if not source_key:
        return []

    url = f"https://api.lever.co/v0/postings/{source_key}"
    payload = http_get_json(url, params={"mode": "json"})
    postings = payload if isinstance(payload, list) else []
    results: list[dict[str, Any]] = []
    for post in postings:
        categories = post.get("categories") or {}
        # Lever stores qualifications separately from the opening description.
        # Include them so education/experience rules see the actual requirements.
        description_parts = [post.get("descriptionPlain") or post.get("description") or ""]
        for section in post.get("lists") or []:
            description_parts.extend([section.get("text") or "", section.get("content") or ""])
        description_parts.append(post.get("additionalPlain") or post.get("additional") or "")
        results.append(
            {
                "external_id": str(post.get("id") or ""),
                "title": post.get("text") or "",
                "level_hint": "Intern" if "intern" in str(categories.get("commitment") or "").casefold() else "",
                "location_raw": categories.get("location") or "",
                "description": "\n".join(description_parts),
                "apply_url": post.get("hostedUrl") or "",
                "source_url": post.get("hostedUrl") or company_config.get("career_url", ""),
                "source_platform": "lever",
            }
        )
    return results
